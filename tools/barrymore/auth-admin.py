#!/usr/bin/env python3
# auth-admin.py — CLI управления учётками/заявками/инвайтами auth-gate (фаза 1; плитка в штабе — фаза 2).
# Запуск: python auth-admin.py <cmd> ...   Работает с теми же сторами, что и gate (AUTH_DATA_DIR/AUTH_ENV_FILE).
import argparse, json, sys, os
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auth_gate as G  # noqa: E402

ISO = G.ISO


def need_secret():
    if not G.load_secret():
        print('ОШИБКА: нет AUTH_SECRET в %s (для инвайтов). Учётки работают и без него.' % G.CFG['env_file'])


def cmd_create_user(a):
    scope = a.scope.split(',') if a.scope not in (None, '*', '') else ['*']
    pw = a.password or (os.urandom(9).hex() if a.genpass else None)
    if not pw or len(pw) < 8:
        print('ОШИБКА: пароль обязателен (>=8) или --genpass')
        return 1
    with G._LOCK:
        users = G._load_store('users.json', [])
        if any(x['login'] == a.login for x in users):
            print('ОШИБКА: логин %s уже есть' % a.login)
            return 1
        users.append({'login': a.login, 'pwhash': G.pw_hash(pw), 'role': a.role, 'scope': scope,
                      'status': 'active', 'created': ISO(G.NOW()), 'created_by': a.by})
        G._save_store('users.json', users)
    G.audit('user.created', login=a.login, role=a.role, by=a.by)
    print('OK: %s создан, роль %s, scope=%s' % (a.login, a.role, scope))
    if a.genpass:
        print('ПАРОЛЬ (один раз, сохранить): %s' % pw)
    return 0


def cmd_requests(a):
    reqs = G._load_store('requests.json', [])
    for r in reqs:
        if a.status == 'all' or r['status'] == a.status:
            print('%s | %s | %s | %s' % (r['created'], r['status'], r['login'], r.get('note', '')))
    if not reqs:
        print('(пусто)')


def cmd_approve(a):
    need_secret()
    with G._LOCK:
        reqs = G._load_store('requests.json', [])
        r = next((x for x in reqs if x['login'] == a.login and x['status'] == 'pending'), None)
        if not r:
            print('ОШИБКА: заявка %s не найдена' % a.login)
            return 1
        users = G._load_store('users.json', [])
        if any(x['login'] == a.login for x in users):
            print('ОШИБКА: логин уже занят')
            return 1
        users.append({'login': a.login, 'pwhash': r['pwhash'], 'role': a.role, 'scope': (a.scope.split(',') if a.scope not in (None, '*', '') else ['*']),
                      'status': 'active', 'created': ISO(G.NOW()), 'created_by': a.by})
        for x in reqs:
            if x is r:
                x['status'] = 'approved'
        G._save_store('requests.json', reqs)
        G._save_store('users.json', users)
    G.audit('request.approved', login=a.login, role=a.role, by=a.by)
    print('OK: %s одобрен, роль %s' % (a.login, a.role))
    return 0


def cmd_reject(a):
    with G._LOCK:
        reqs = G._load_store('requests.json', [])
        n = 0
        for x in reqs:
            if x['login'] == a.login and x['status'] == 'pending':
                x['status'] = 'rejected'
                n += 1
        G._save_store('requests.json', reqs)
    G.audit('request.rejected', login=a.login, by=a.by)
    print('OK: отклонено %d' % n)
    return 0


def cmd_invite(a):
    need_secret()
    scope = '*' if (a.scope in (None, '*', '')) else a.scope
    token = G.invite_make(scope, a.ttl_hours, a.max_uses, a.by)
    print('ССЫЛКА (прямая, гостевой демо-профиль): https://<IP>/l/%s' % token)
    print('scope=%s ttl=%dч max_uses=%d' % (scope, a.ttl_hours, a.max_uses))
    return 0


def cmd_revoke_invite(a):
    with G._LOCK:
        inv = G._load_store('invites.json', [])
        for i in inv:
            if i.get('nonce') == a.nonce:
                i['revoked'] = True
        G._save_store('invites.json', inv)
    G.audit('invite.revoked', nonce=a.nonce, by=a.by)
    print('OK: инвайт %s отозван' % a.nonce)
    return 0


def cmd_revoke_user(a):
    with G._LOCK:
        users = G._load_store('users.json', [])
        for x in users:
            if x['login'] == a.login:
                x['status'] = 'revoked'
        G._save_store('users.json', users)
        sess = G._load_store('sessions.json', {})
        for sid in [k for k, v in sess.items() if v.get('login') == a.login]:
            del sess[sid]
        G._save_store('sessions.json', sess)
    G.audit('user.revoked', login=a.login, by=a.by)
    print('OK: %s отозван, сессии снесены' % a.login)
    return 0


def cmd_list(a):
    print('== users ==')
    for x in G._load_store('users.json', []):
        print('%s | %s | %s | scope=%s | %s' % (x['login'], x['role'], x['status'], x.get('scope'), x.get('created')))
    print('== invites ==')
    for i in G._load_store('invites.json', []):
        print('%s | uses %d/%d | %s | scope=%s | %s' % (i['nonce'], i.get('uses', 0), i.get('max_uses', 0),
                                                        'REVOKED' if i.get('revoked') else i.get('expires'), i.get('scope'), i.get('created')))
    cmd_requests(argparse.Namespace(status='pending'))


def main():
    ap = argparse.ArgumentParser(description='eVo auth-admin: учётки/заявки/инвайты')
    ap.add_argument('--by', default='Sovereign', help='кто исполняет (в аудит)')
    sub = ap.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('create-user'); s.add_argument('--login', required=True); s.add_argument('--role', required=True, choices=['admin', 'agent', 'member']); s.add_argument('--password'); s.add_argument('--genpass', action='store_true'); s.add_argument('--scope', default='*'); s.set_defaults(f=cmd_create_user)
    s = sub.add_parser('requests'); s.add_argument('--status', default='pending', choices=['pending', 'approved', 'rejected', 'all']); s.set_defaults(f=cmd_requests)
    s = sub.add_parser('approve'); s.add_argument('--login', required=True); s.add_argument('--role', default='member', choices=['admin', 'agent', 'member']); s.add_argument('--scope', default='*'); s.set_defaults(f=cmd_approve)
    s = sub.add_parser('reject'); s.add_argument('--login', required=True); s.set_defaults(f=cmd_reject)
    s = sub.add_parser('invite'); s.add_argument('--ttl-hours', type=int, default=72); s.add_argument('--max-uses', type=int, default=5); s.add_argument('--scope', default='*'); s.set_defaults(f=cmd_invite)
    s = sub.add_parser('revoke-invite'); s.add_argument('--nonce', required=True); s.set_defaults(f=cmd_revoke_invite)
    s = sub.add_parser('revoke-user'); s.add_argument('--login', required=True); s.set_defaults(f=cmd_revoke_user)
    s = sub.add_parser('list'); s.set_defaults(f=cmd_list)

    a = ap.parse_args()
    sys.exit(a.f(a) or 0)


if __name__ == '__main__':
    main()
