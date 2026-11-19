#!/usr/bin/env python3
# make-demo-api.py — генератор санитизированных демо-стабов /api/* для гостевого профиля auth-gate.
# Формы сняты с живых API штаба; значения — условные, без личных цифр/URL/путей.
# Dark Watch (/api/darkwatch) стаба НЕ получает никогда — RED-контур наружу не светится.
# Запуск: python make-demo-api.py [--dir ПУТЬ]  (дефолт: <AUTH_DATA_DIR>/demo-api)
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auth_gate as G  # noqa: E402  (ради CFG/AUTH_DATA_DIR)

def ts(day, hour, minute=0):
    return '2026-11-14T%02d:%02d:00Z' % (hour, minute) if day == 0 else '2026-11-%02dT12:00:00Z' % day

def tokens_usage():
    per_hour = [{'bucket': '%02d:00' % (8 + i // 2), 'tokens': 120000 + (i * 37000) % 260000} for i in range(12)]
    per_day = [{'bucket': '2026-11-%02d' % d, 'tokens': 900000 + (d * 210000) % 1500000} for d in range(8, 15)]
    return {
        'generated_at': ts(0, 14, 22),
        'total_observed': 4250000,
        'per_hour': per_hour,
        'per_day': per_day,
        'sessions': [
            {'session': 'demo-shore', 'tokens': 1850000, 'first_ts': ts(14, 9), 'last_ts': ts(0, 14, 20)},
            {'session': 'demo-bridge', 'tokens': 1500000, 'first_ts': ts(13, 12), 'last_ts': ts(0, 11)},
            {'session': 'demo-lantern', 'tokens': 900000, 'first_ts': ts(12, 10), 'last_ts': ts(14, 8, 30)},
        ],
    }

def steward():
    return {
        'generated_at': ts(0, 14, 23),
        'runtimes': [
            {'name': 'demo-radar-orders', 'running': True, 'finished_at': None, 'returncode': None},
            {'name': 'demo-radar-career', 'running': True, 'finished_at': None, 'returncode': None},
            {'name': 'demo-vitrina-ping', 'running': False, 'finished_at': ts(0, 12), 'returncode': 0},
        ],
        'journal': {'size_kb': 640, 'tail': [
            'demo: конвейер в норме, рейсы по расписанию',
            'demo: ночной прогон завершён без штормов',
            'demo: витрина отвечает, пинг 200',
        ]},
        'processes': {'agent_processes': [], 'dashboard_servers': 1},
        'scheduler': {'task': 'Demo Dashboard Server', 'found': True, 'status': 'Готово'},
        'automations': {'enabled_count': 2, 'enabled': [
            {'title': 'demo-радар: ежедневный обход'},
            {'title': 'demo-сторож: пинг каждые 10 минут'},
        ]},
        'sessions': {'alive': 3, 'idle': 0, 'newest_age_min': 2.0},
    }

def agents_live():
    def ship(owner, task, status='sailing', pulse=1.4, storms=0):
        return {'by': 'demo', 'task': task, 'owner': owner, 'status': status, 'pulse_status': 'ok',
                'lanes': {'lane-1': 'demo'}, 'pulse_min': pulse, 'storms': storms,
                'started_at': ts(0, 9), 'eta_min': 45.0, 'elapsed_min': 120.0, 'events_recent': []}
    return {'generated_at': ts(0, 14, 23), 'ships': [
        ship('Демо-корабль Альфа', 'Демо-рейс: сбор данных с витрины'),
        ship('Демо-корабль Браво', 'Демо-рейс: дайджест цен конкурентов', status='moored', pulse=0.0, storms=1),
    ]}

def agents_history():
    return {'generated_at': ts(0, 14, 23), 'voyages': [
        {'by': 'demo', 'task': 'Демо: парсер доски объявлений', 'started_at': ts(14, 8), 'finished_at': ts(14, 10),
         'verdict': 'сдан', 'files': 6, 'tests': 2, 'tokens': 410000.0, 'minutes': 118.0,
         'lanes': {'demo': 'lane-1'}, 'storms': 0, 'chain': ['demo→lane-1']},
        {'by': 'demo', 'task': 'Демо: дайджест цен конкурентов', 'started_at': ts(13, 15), 'finished_at': ts(13, 18),
         'verdict': 'сдан', 'files': 3, 'tests': None, 'tokens': 380000.0, 'minutes': 164.0,
         'lanes': {}, 'storms': 1, 'chain': []},
        {'by': 'demo', 'task': 'Демо: разбор входящих заявок', 'started_at': ts(12, 11), 'finished_at': ts(12, 14, 30),
         'verdict': 'сдан', 'files': 2, 'tests': None, 'tokens': 210000.0, 'minutes': 210.0,
         'lanes': {}, 'storms': 0, 'chain': []},
    ]}

def agents_ops():
    return {'generated_at': ts(0, 14, 23), 'flights': [
        {'id': 'demo-flight-1', 'task': 'Демо: разбор входящих заявок', 'started_at': ts(0, 9), 'updated_at': ts(0, 14),
         'age_min': 310.0, 'bytes': 48210, 'state': 'sailing', 'tail': 'demo: шаг 4 из 6 — сборка отчёта', 'artifact': None},
        {'id': 'demo-flight-2', 'task': 'Демо: ночной обход радаров', 'started_at': ts(0, 2), 'updated_at': ts(0, 8),
         'age_min': 760.0, 'bytes': 21980, 'state': 'moored', 'tail': 'demo: рейс завершён', 'artifact': 'demo-digest.md'},
    ]}

STABS = {
    'tokens/usage.json': tokens_usage,
    'steward.json': steward,
    'agents/live.json': agents_live,
    'agents/history.json': agents_history,
    'agents/ops.json': agents_ops,
    # darkwatch.json — СОЗНАТЕЛЬНО НЕТ (см. шапку)
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default=os.path.join(G.CFG['data'], 'demo-api'))
    a = ap.parse_args()
    for rel, fn in STABS.items():
        path = os.path.join(a.dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(fn(), f, ensure_ascii=False, indent=1)
        print('OK %s' % path)
    print('Стабов: %d (darkwatch — сознательно отсутствует)' % len(STABS))


if __name__ == '__main__':
    main()
