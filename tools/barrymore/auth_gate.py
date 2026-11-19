#!/usr/bin/env python3
# auth-gate.py — единая входная дверь платформы eVo (план «Авторизация: 4 уровня», фаза 1).
# Роли: admin (абсолют) | agent (ТУЗ, по scope) | member (по scope, read-only в фазе 1) | guest (демо-профиль).
# Стек: stdlib-only (ADR-003/004). Секрет — AUTH_SECRET из env-файла (в git не хранится).
# Стор — атомарные JSON-файлы (паттерн task_store: tempfile + os.replace). Аудит — JSONL (паттерн log_event).
#
# Переменные окружения:
#   AUTH_PORT      (8767)   AUTH_HOST (127.0.0.1)
#   AUTH_DATA_DIR  (~/.evo-auth)            — users/requests/invites/sessions/events/demo-api
#   AUTH_ENV_FILE  (<repo>/Workspace/.env)  — где лежит AUTH_SECRET=...
#   AUTH_LOGIN_HTML (<repo>/eVo/dashboard/login.html)
#   BACKEND_URL    (http://127.0.0.1:8766)  — интерьер (dashboard-loopback на ВМ, 8765 локально)
#   FACE_URL       (http://127.0.0.1:80)    — витрина-фэйс
import base64, hashlib, hmac, json, os, re, secrets, sys, tempfile, threading, time, urllib.parse
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SESSION_COOKIE = 'evo_session'
SESSION_TTL_H = 24          # обычная сессия
SESSION_TTL_ADMIN_H = 168   # admin-remember
INVITE_NAME_RE = re.compile(r'^[a-z0-9_.-]{3,32}$')
FAILS_LIMIT, FAILS_WINDOW_S = 5, 900          # 5 неудач / 15 мин на IP
PBKDF2_ITERS = 200_000

# --- Гостевой белый список: страницы (HTML без личных данных; данные приходят только через /api/*) ---
GUEST_PAGES = {'command-center.html', 'agents.html', 'solomon.html'}
GUEST_STATIC_PREFIX = ('command-center', 'agents', 'solomon')   # их css/js
GUEST_STATIC_EXACT = {'style.css', 'languages.js', 'brief.js'}
GUEST_STATIC_EXT = ('.css', '.js', '.png', '.svg', '.woff2', '.map')
# Демо-API гостя: /api/<x> -> demo-api/<x>.json; отсутствует = 404. Dark Watch/финансы стабов НЕ имеют.
GUEST_FORBIDDEN_API = ('/api/darkwatch', '/api/security', '/api/hunter', '/api/internal')

NOW = lambda: datetime.now(timezone.utc)
ISO = lambda d: d.strftime('%Y-%m-%dT%H:%M:%SZ')


def env_conf():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/barrymore -> repo
    cfg = {
        'port': int(os.environ.get('AUTH_PORT', '8767')),
        'host': os.environ.get('AUTH_HOST', '127.0.0.1'),
        'data': os.environ.get('AUTH_DATA_DIR', os.path.join(os.path.expanduser('~'), '.evo-auth')),
        'env_file': os.environ.get('AUTH_ENV_FILE', os.path.join(root, 'Workspace', '.env')),
        'login_html': os.environ.get('AUTH_LOGIN_HTML', os.path.join(root, 'eVo', 'dashboard', 'login.html')),
        'backend': os.environ.get('BACKEND_URL', 'http://127.0.0.1:8766'),
        # Host, который должен увидеть бэк за dashboard-loopback (_is_local_host требует 127.0.0.1:8765)
        'backend_host': os.environ.get('BACKEND_HOST', ''),
        'face': os.environ.get('FACE_URL', 'http://127.0.0.1:80'),
    }
    return cfg


CFG = env_conf()
SECRET = None  # bytes; ставится при старте


def load_secret():
    """Читает AUTH_SECRET из env-файла (парсер: только строки KEY=VALUE)."""
    global SECRET
    p = CFG['env_file']
    if os.path.exists(p):
        for line in open(p, encoding='utf-8', errors='replace'):
            line = line.strip()
            if line.startswith('AUTH_SECRET='):
                val = line.split('=', 1)[1].strip().strip('"\'')
                if len(val) >= 32:
                    SECRET = val.encode('utf-8')
                    return True
    SECRET = None
    return False


def _atomic_write(path, data_bytes):
    """Атомарная запись (паттерн _atomic_write_json платформы)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix='.tmp-auth-')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data_bytes)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _load_store(name, default):
    p = os.path.join(CFG['data'], name)
    if not os.path.exists(p):
        return default
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def _save_store(name, obj):
    _atomic_write(os.path.join(CFG['data'], name), json.dumps(obj, ensure_ascii=False, indent=1).encode('utf-8'))


_LOCK = threading.Lock()


def audit(event, **fields):
    rec = {'ts': ISO(NOW()), 'event': event}
    rec.update(fields)
    with _LOCK:
        with open(os.path.join(CFG['data'], 'events.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')


# --- Пароли: PBKDF2-HMAC-SHA256 (stdlib) ---
def pw_hash(password):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERS)
    return 'pbkdf2$%d$%s$%s' % (PBKDF2_ITERS, salt.hex(), dk.hex())


def pw_verify(password, stored):
    try:
        scheme, iters, salt_hex, hash_hex = stored.split('$')
        if scheme != 'pbkdf2':
            return False
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


# --- Сессии ---
def create_session(login, role, scope, ttl_h):
    with _LOCK:
        sess = _load_store('sessions.json', {})
        sid = secrets.token_hex(32)
        exp = NOW() + timedelta(hours=ttl_h)
        sess[sid] = {'login': login, 'role': role, 'scope': scope, 'expires': ISO(exp), 'created': ISO(NOW())}
        # подрезка протухших, чтобы файл не рос
        cut = ISO(NOW())
        sess = {k: v for k, v in sess.items() if v.get('expires', '') > cut}
        _save_store('sessions.json', sess)
    return sid


def get_session(sid):
    if not sid:
        return None
    sess = _load_store('sessions.json', {})
    s = sess.get(sid)
    if not s:
        return None
    if s.get('expires', '') <= ISO(NOW()):
        return None
    return s


def drop_session(sid):
    with _LOCK:
        sess = _load_store('sessions.json', {})
        if sid in sess:
            del sess[sid]
            _save_store('sessions.json', sess)


# --- Инвайты (прямые ссылки для гостей): payload HMAC-подписан, uses/TTL/отзыв — в стор ---
def invite_make(scope, ttl_h, max_uses, created_by):
    nonce = secrets.token_hex(8)
    payload = {'nonce': nonce, 'scope': scope, 'ttl_h': ttl_h, 'created': ISO(NOW())}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode('utf-8')).decode('ascii').rstrip('=')
    sig = hmac.new(SECRET, body.encode('ascii'), hashlib.sha256).hexdigest()[:32]
    token = body + '.' + sig
    with _LOCK:
        inv = _load_store('invites.json', [])
        inv.append({'nonce': nonce, 'scope': scope, 'max_uses': max_uses, 'uses': 0,
                    'expires': ISO(NOW() + timedelta(hours=ttl_h)), 'revoked': False, 'created_by': created_by})
        _save_store('invites.json', inv)
    audit('invite.created', nonce=nonce, scope=scope, ttl_h=ttl_h, by=created_by)
    return token


def invite_check(token):
    """Возвращает (payload, invite) или (None, причина)."""
    if not SECRET or '.' not in token:
        return None, 'bad-token'
    body, sig = token.rsplit('.', 1)
    good = hmac.new(SECRET, body.encode('ascii'), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, good):
        return None, 'bad-signature'
    try:
        body += '=' * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(body.encode('ascii')).decode('utf-8'))
    except Exception:
        return None, 'bad-payload'
    inv = [i for i in _load_store('invites.json', []) if i.get('nonce') == payload.get('nonce')]
    if not inv:
        return None, 'unknown'
    inv = inv[0]
    if inv.get('revoked'):
        return None, 'revoked'
    if inv.get('expires', '') <= ISO(NOW()):
        return None, 'expired'
    if inv.get('uses', 0) >= inv.get('max_uses', 1):
        return None, 'exhausted'
    return payload, inv


def invite_use(nonce):
    with _LOCK:
        inv = _load_store('invites.json', [])
        for i in inv:
            if i.get('nonce') == nonce:
                i['uses'] = i.get('uses', 0) + 1
                i['last_used'] = ISO(NOW())
                break
        _save_store('invites.json', inv)


# --- Rate-limit на логин (в памяти процесса) ---
_FAILS = {}


def rl_blocked(ip):
    ts = _FAILS.get(ip, [])
    ts = [t for t in ts if time.time() - t < FAILS_WINDOW_S]
    _FAILS[ip] = ts
    return len(ts) >= FAILS_LIMIT


def rl_fail(ip):
    _FAILS.setdefault(ip, []).append(time.time())


# --- Proxy на бэк/фэйс ---
def proxy(base, method, path, query, headers, body, host_override=None):
    """Проксирует запрос; возвращает (status, [headers], body_bytes). Cookie бэка не пересылаются."""
    u = urllib.parse.urlparse(base)
    conn = HTTPConnection(u.hostname, u.port, timeout=20)
    target = u.path.rstrip('/') + path + (('?' + query) if query else '')
    fwd = {k: v for k, v in headers.items()
           if k.lower() not in ('host', 'cookie', 'origin', 'referer', 'connection', 'content-length')}
    fwd['Host'] = host_override or u.netloc
    try:
        conn.request(method, target, body=body, headers=fwd)
        r = conn.getresponse()
        data = r.read()
        hh = [(k, v) for k, v in r.getheaders()
              if k.lower() not in ('set-cookie', 'transfer-encoding', 'connection', 'content-length')]
        return r.status, hh, data
    finally:
        conn.close()


def scope_allows(scope, method, path):
    if scope in ('*', ['*']):
        return True
    for s in scope:
        pfx = s.rstrip('*')
        if path.startswith(pfx):
            return True
    return False


def guest_static_ok(path):
    name = path.rsplit('/', 1)[-1]
    if name in GUEST_STATIC_EXACT:
        return True
    low = path.lower()
    if not low.endswith(GUEST_STATIC_EXT):
        return False
    return any(name.startswith(pfx) for pfx in GUEST_STATIC_PREFIX)


class Gate(BaseHTTPRequestHandler):
    server_version = 'eVoAuthGate/1.0'

    def log_message(self, fmt, *args):  # краткий журнал в stdout (journald подхватит)
        sys.stdout.write('[gate] %s %s %s\n' % (self.command, self.path.split('?')[0], args[0] if args else ''))
        sys.stdout.flush()

    # ---------- утилиты ответа ----------
    def _send(self, status, body=b'', ctype='text/html; charset=utf-8', extra=None):
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        for k, v in (extra or []):
            self.send_header(k, v)
        self.end_headers()
        if body and self.command != 'HEAD':
            self.wfile.write(body)

    def _json(self, obj, status=200, extra=None):
        self._send(status, json.dumps(obj, ensure_ascii=False).encode('utf-8'),
                   'application/json; charset=utf-8', extra)

    def _cookie(self, sid, max_age_s):
        return ('Set-Cookie', '%s=%s; Path=/; Max-Age=%d; HttpOnly; SameSite=Lax; Secure' % (SESSION_COOKIE, sid, max_age_s))

    def _session(self):
        c = self.headers.get('Cookie', '')
        for part in c.split(';'):
            part = part.strip()
            if part.startswith(SESSION_COOKIE + '='):
                return get_session(part.split('=', 1)[1].strip())
        return None

    def _client_ip(self):
        """Реальный IP клиента: за nginx приходит X-Forwarded-For (rate-limit/аудит)."""
        xff = self.headers.get('X-Forwarded-For', '')
        return xff.split(',')[0].strip() if xff else self.client_address[0]

    def _proxy_pass(self, base, role=None, login=None, host_override=None):
        p = urllib.parse.urlsplit(self.path)
        st, hh, data = proxy(base, self.command, p.path, p.query, dict(self.headers), self._body(),
                             host_override=host_override)
        hh = list(hh)
        if role:
            hh.append(('X-Evo-Role', role))
            if login:
                hh.append(('X-Evo-User', login))
        self.send_response(st)
        for k, v in hh:
            self.send_header(k, v)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if data and self.command != 'HEAD':
            self.wfile.write(data)

    def _body(self):
        if not hasattr(self, '_cached_body'):
            n = int(self.headers.get('Content-Length', 0) or 0)
            self._cached_body = self.rfile.read(min(n, 65536)) if n > 0 else b''
        return self._cached_body

    # ---------- маршруты ----------
    def do_GET(self):
        self._handle('GET')

    def do_POST(self):
        self._handle('POST')

    def do_HEAD(self):
        self._handle('GET')

    def _handle(self, method):
        p = urllib.parse.urlsplit(self.path)
        path = p.path
        sess = self._session()
        role = sess['role'] if sess else None

        # --- 1) точки входа/выхода gate: доступны всегда ---
        if path == '/login.html':
            try:
                data = open(CFG['login_html'], 'rb').read()
                self._send(200, data)
            except OSError:
                self._send(500, b'login page missing', 'text/plain')
            return
        if path == '/auth/whoami':
            if sess:
                self._json({'ok': True, 'login': sess['login'], 'role': role, 'scope': sess['scope']})
            else:
                self._json({'ok': False, 'role': 'anonymous'})
            return
        if path == '/auth/logout':
            c = self.headers.get('Cookie', '')
            for part in c.split(';'):
                part = part.strip()
                if part.startswith(SESSION_COOKIE + '='):
                    drop_session(part.split('=', 1)[1].strip())
            self._send(302, b'', extra=[('Location', '/login.html'), ('Set-Cookie', '%s=; Path=/; Max-Age=0' % SESSION_COOKIE)])
            return
        if (path == '/l' or path.startswith('/l/') or path == '/auth/invite') and method == 'GET':
            token = p.query.replace('token=', '', 1) if 'token=' in p.query else (path.split('/l/', 1)[1] if path.startswith('/l/') else '')
            if not token:
                self._send(302, b'', extra=[('Location', '/login.html?invite=missing')])
                return
            payload, inv_or_err = invite_check(token)
            if not payload:
                audit('invite.denied', reason=inv_or_err, ip=self._client_ip())
                self._send(302, b'', extra=[('Location', '/login.html?invite=%s' % inv_or_err)])
                return
            invite_use(payload['nonce'])
            sid = create_session('guest@' + payload['nonce'][:6], 'guest', payload.get('scope', '*'),
                                 min(int(payload.get('ttl_h', 24)), SESSION_TTL_H))
            audit('invite.used', nonce=payload['nonce'], ip=self._client_ip())
            self._send(302, b'', extra=[('Location', '/command-center.html'), self._cookie(sid, int(payload.get('ttl_h', 24)) * 3600)])
            return

        # --- 2) POST /auth/* ---
        if method == 'POST' and path == '/auth/login':
            self._login(self._client_ip())
            return
        if method == 'POST' and path == '/auth/register':
            self._register()
            return

        # --- 3) фэйс-витрина: видна всем (и без сессии) ---
        if path == '/' or path.startswith(('/uslugi.html', '/board', '/demo')):
            self._proxy_pass(CFG['face'])
            return

        # --- 4) остальное требует сессии ---
        if not sess:
            if method == 'GET' and not path.startswith('/api/'):
                self._send(302, b'', extra=[('Location', '/login.html?next=' + urllib.parse.quote(path))])
            else:
                self._json({'ok': False, 'error': 'auth-required'}, 401)
            return

        # --- 5) auth API ---
        if path.startswith('/api/internal/'):
            if role == 'admin':
                self._proxy_pass(CFG['backend'], role, sess['login'], host_override=CFG['backend_host'] or None)
            else:
                audit('denied.internal', role=role, path=path, ip=self._client_ip())
                self._json({'ok': False, 'error': 'forbidden'}, 403)
            return

        if role in ('admin', 'agent'):
            self._proxy_pass(CFG['backend'], role, sess['login'], host_override=CFG['backend_host'] or None)
            return

        if role == 'member':
            if method == 'POST':
                self._json({'ok': False, 'error': 'read-only'}, 403)   # тонкие права — фаза 2
            elif scope_allows(sess['scope'], method, path):
                self._proxy_pass(CFG['backend'], role, sess['login'], host_override=CFG['backend_host'] or None)
            else:
                self._json({'ok': False, 'error': 'out-of-scope'}, 403)
            return

        if role == 'guest':
            if method == 'POST':
                self._json({'ok': False, 'error': 'read-only'}, 403)
                return
            if path.startswith('/api/'):
                if any(path.startswith(b) for b in GUEST_FORBIDDEN_API):
                    self._json({'ok': False, 'error': 'not-in-demo'}, 404)
                    return
                rel = path[len('/api/'):].strip('/')
                # гость: только плоские имена демо-API, без ../, \ и дисков
                if (not rel or '..' in rel.split('/')
                        or '\\' in rel or ':' in rel):
                    self._json({'ok': False, 'error': 'not-in-demo'}, 404)
                    return
                fp = os.path.join(CFG['data'], 'demo-api', rel + '.json')
                if os.path.exists(fp):
                    self._send(200, open(fp, 'rb').read(), 'application/json; charset=utf-8')
                else:
                    self._json({'ok': False, 'error': 'not-in-demo'}, 404)
                return
            name = path.rsplit('/', 1)[-1]
            if path.endswith('.html'):
                if name in GUEST_PAGES:
                    self._proxy_pass(CFG['backend'], role, sess['login'], host_override=CFG['backend_host'] or None)
                    return
                self._send(302, b'', extra=[('Location', '/command-center.html')])
                return
            if guest_static_ok(path):
                self._proxy_pass(CFG['backend'], role, sess['login'], host_override=CFG['backend_host'] or None)
                return
            self._json({'ok': False, 'error': 'not-in-demo'}, 404)
            return

        self._json({'ok': False, 'error': 'unknown-role'}, 403)

    # ---------- логин/регистрация ----------
    def _login(self, ip):
        if rl_blocked(ip):
            audit('login.ratelimited', ip=ip)
            self._json({'ok': False, 'error': 'rate-limited'}, 429)
            return
        try:
            req = json.loads(self._body().decode('utf-8') or '{}')
        except Exception:
            req = {}
        login = str(req.get('login', '')).strip().lower()
        password = str(req.get('password', ''))
        remember = bool(req.get('remember'))
        users = _load_store('users.json', [])
        u = next((x for x in users if x.get('login') == login and x.get('status') == 'active'), None)
        if not u or not password or not pw_verify(password, u.get('pwhash', '')):
            rl_fail(ip)
            audit('login.failed', login=login, ip=ip)
            self._json({'ok': False, 'error': 'bad-credentials'}, 401)
            return
        ttl = SESSION_TTL_ADMIN_H if (remember and u['role'] == 'admin') else SESSION_TTL_H
        sid = create_session(u['login'], u['role'], u.get('scope', ['*']), ttl)
        audit('login.ok', login=login, role=u['role'], ip=ip)
        self._json({'ok': True, 'role': u['role']}, 200, [self._cookie(sid, ttl * 3600)])

    def _register(self):
        try:
            req = json.loads(self._body().decode('utf-8') or '{}')
        except Exception:
            req = {}
        login = str(req.get('login', '')).strip().lower()
        password = str(req.get('password', ''))
        note = str(req.get('note', ''))[:200]
        if not INVITE_NAME_RE.match(login) or len(password) < 8:
            self._json({'ok': False, 'error': 'invalid-fields'}, 400)
            return
        with _LOCK:
            users = _load_store('users.json', [])
            reqs = _load_store('requests.json', [])
            if any(x.get('login') == login for x in users) or any(
                    x.get('login') == login and x.get('status') == 'pending' for x in reqs):
                self._json({'ok': False, 'error': 'exists'}, 409)
                return
            reqs.append({'login': login, 'pwhash': pw_hash(password), 'note': note,
                         'status': 'pending', 'created': ISO(NOW())})
            _save_store('requests.json', reqs)
        audit('request.created', login=login)
        self._json({'ok': True, 'status': 'pending'})


def main():
    os.makedirs(CFG['data'], exist_ok=True)
    ok = load_secret()
    if not ok:
        print('[gate] НЕТ AUTH_SECRET в %s — /auth/* вернёт 500, сторы работают' % CFG['env_file'])
    print('[gate] auth-gate жив на %s:%s | data=%s | backend=%s | face=%s | secret=%s'
          % (CFG['host'], CFG['port'], CFG['data'], CFG['backend'], CFG['face'], 'loaded' if SECRET else 'ABSENT'))
    srv = ThreadingHTTPServer((CFG['host'], CFG['port']), Gate)
    srv.serve_forever()


if __name__ == '__main__':
    main()
