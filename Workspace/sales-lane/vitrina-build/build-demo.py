# -*- coding: utf-8 -*-
"""Сборка демо-витрины Platform: белый список файлов eVo/dashboard -> vitrina-build/board/
+ санитизация хроники/экскурсии + демо-стабы личных виджетов.
Запуск: python -I build-demo.py  (из этого каталога)"""
import json, re, shutil, io, os

ROOT = r"C:\Work\Platform\eVo\dashboard"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "board")

# --- белый список показных страниц и их зависимостей ---
PAGES = ["index.html", "chronicle.html", "kanban.html", "world-map.html"]
SCRIPTS = ["style.css", "harbor-ship.css", "harbor-ship.js", "app.js",
           "languages.js", "excursion-data.js", "chronicle.js",
           "kanban.js", "chronicle.css"]
ASSETS = ["assets/barrymore.png", "assets/estate_bg.png",
          "assets/harbor-ship-sprite.png", "assets/world-map-v1.png",
          "projects/marvel_v/assets/logo_sunrise.png"]
if os.path.exists(OUT):
    shutil.rmtree(OUT)
for rel in PAGES + SCRIPTS + ASSETS:
    src = os.path.join(ROOT, rel)
    dst = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dst) or OUT, exist_ok=True)
    shutil.copy2(src, dst)
print("copied:", len(PAGES + SCRIPTS + ASSETS), "files")

def read_js(name, var=None):
    """Загрузка data-js: var находим автоматически (window.X = {...} или const X = {...})."""
    s = io.open(os.path.join(ROOT, name), encoding="utf-8").read()
    m = re.search(r"^(\s*(?:window\.\w+|const \w+)\s*)=\s*(\{.*\})\s*;?\s*$", s, re.S | re.M)
    if not m:
        raise SystemExit("no var match: " + name)
    return m.group(1), json.loads(m.group(2).rstrip().rstrip(";"))

SENSITIVE = re.compile(r"Dark Watch|Рокфеллер|финанс|пароль|KeePass|LangSmith|blocklist|Сторож|steward|feeds_radar|Hudson|intel|секрет|secret|password|rotat|sk-ant", re.I)

# --- хроника: выкинуть чувствительные коммиты ---
prefix, data = read_js("chronicle-data.js")
dropped = []
def scrub(o):
    if isinstance(o, dict):
        subj = str(o.get("s") or o.get("subject") or "")
        if subj and SENSITIVE.search(subj):
            dropped.append(subj[:60])
            return None
        return {k: scrub(v) for k, v in o.items()}
    if isinstance(o, list):
        return [x for x in (scrub(x) for x in o) if x is not None]
    return o
data = scrub(data)
io.open(os.path.join(OUT, "chronicle-data.js"), "w", encoding="utf-8").write(prefix + "= " + json.dumps(data, ensure_ascii=False) + ";")
print("chronicle: dropped", len(dropped), "commits")

# --- экскурсия: выкинуть узлы про отклики/резюме/private ---
prefix, exc = read_js("excursion-data.js")
PERSONAL = re.compile(r"Резюме|отклик|proposals|resume|ваканс|private", re.I)
exc_dropped = [0]
def scrub2(o):
    if isinstance(o, dict):
        t = str(o.get("title") or "") + str(o.get("path") or "")
        if t and PERSONAL.search(t):
            exc_dropped[0] += 1
            return None
        return {k: scrub2(v) for k, v in o.items()}
    if isinstance(o, list):
        return [x for x in (scrub2(x) for x in o) if x is not None]
    return o
exc = scrub2(exc)
io.open(os.path.join(OUT, "excursion-data.js"), "w", encoding="utf-8").write(prefix + "= " + json.dumps(exc, ensure_ascii=False) + ";")
print("excursion: dropped", exc_dropped[0], "nodes")

# --- демо-стабы личных виджетов (та же схема) ---
D = "2026-11-14T12:00:00"
demo_tasks_u = [
    {"id": "demo-deploy-188", "title": "Витрина: обновление до 1.8.8", "source": "VITRINA",
     "priority": "high", "status": "in-progress", "createdAt": D, "history": [], "stage": "demo", "type": "demo", "busy": False},
    {"id": "demo-demo-data", "title": "Демо-данные вместо реальных на витрине", "source": "VITRINA",
     "priority": "high", "status": "done", "createdAt": D, "description": "личные данные скрыты", "history": [], "stage": "demo", "type": "demo", "busy": False},
]
demo_tasks_r = [
    {"id": "demo-kwork", "title": "Кворки волны 1: парсер, деплой, n8n", "source": "SALES",
     "priority": "regular", "status": "open", "createdAt": D, "description": "демо-запись", "history": [], "stage": "demo", "type": "demo", "busy": False},
    {"id": "demo-board", "title": "Публичный дашборд на /board/", "source": "VITRINA",
     "priority": "regular", "status": "open", "createdAt": D, "description": "демо-запись", "history": [], "stage": "demo", "type": "demo", "busy": False},
    {"id": "demo-chronicle", "title": "Хроника: 381 коммит за 36 дней", "source": "VITRINA",
     "priority": "regular", "status": "open", "createdAt": D, "description": "демо-запись", "history": [], "stage": "demo", "type": "demo", "busy": False},
]
brief = {
    "generatedAt": "2026-11-14 12:00",
    "sources": ["demo"],
    "current": {"date": "2026-11-14", "nextAction": "Демо-режим витрины Platform: показан публичный контур. Штаб, финансы и внутренние контуры живут в защищённом интерьере и сюда не выносятся."},
    "state": {"nextStep": "Смотреть хронику 📜, канбан 📋 и карту мира — кнопки в шапке. Данные на этой доске — демо."},
    "changes": [
        "2026-11-14 | витрина: публичный дашборд с демо-данными",
        "2026-11-13 | стенд: диск расширен до 30 ГБ, безопасная чистка",
        "2026-11-09 | release 1.8.8",
        "2026-11-08 | фабрика продаж: тексты и демо-Excel",
        "2026-11-07 | облачный стенд поднят и проверен",
    ],
    "tasks": {"urgent": demo_tasks_u, "regular": demo_tasks_r, "done": [], "all": demo_tasks_u + demo_tasks_r},
    "hunter": {"generatedAt": D, "headline": "Демо: доска внешних возможностей — реальные данные в интерьере",
               "top": [
                   {"title": "Демо-заказ: парсер данных в Excel", "url": "#demo", "source": "demo", "date": "2026-11-14", "category": "demo", "status": "new"},
                   {"title": "Демо-заказ: VPS + Docker деплой", "url": "#demo", "source": "demo", "date": "2026-11-14", "category": "demo", "status": "new"},
               ], "full": "demo"},
    "peerNotes": {"last24h": 0},
    "git": {"branch": "main", "lastCommit": "demo: витрина-режим витрины продаж", "dirtyFiles": 0},
    "agent": {"model": "demo", "summary": "Демонстрационный контур Platform Evo. Реальный штаб и личные данные скрыты за защищённым интерьером.", "nextStep": "Осмотритесь: планета, канбан, карта, кораблик, хроника."},
    "_sourceFingerprint": "demo",
}
io.open(os.path.join(OUT, "brief.js"), "w", encoding="utf-8").write("window.EVO_BRIEF = " + json.dumps(brief, ensure_ascii=False) + ";")
print("brief.js stub: OK")

vac = {
    "generatedAt": D + " UTC",
    "total": 3,
    "jobs": [
        {"source": "DemoBoard", "title": "DevOps Engineer (demo)", "company": "Example Corp", "location": "Remote", "salary": "—", "date": "2026-11-13T12:00:03+00:00", "url": "#demo"},
        {"source": "DemoBoard", "title": "Python Automation (demo)", "company": "Demo Systems", "location": "Remote", "salary": "—", "date": "2026-11-13T10:00:03+00:00", "url": "#demo"},
        {"source": "DemoBoard", "title": "Data Engineer (demo)", "company": "Sample Ltd", "location": "EU/Remote", "salary": "—", "date": "2026-11-13T08:00:03+00:00", "url": "#demo"},
    ],
    "freelance": [],
}
io.open(os.path.join(OUT, "vacancies.js"), "w", encoding="utf-8").write("/* Демо-данные витрины. Реальные вакансии живут в интерьере. */\nconst EVO_VACANCIES = " + json.dumps(vac, ensure_ascii=False) + ";")
print("vacancies.js stub: OK")

tri = {
    "generatedAt": D, "snapshot": "2026-11-14",
    "counts": {"perspective": 2, "main": 1, "outset": 0},
    "categories": [
        {"key": "demo", "label": "демо-заказы", "count": 2, "items": [
            {"idx": "d1", "title": "Демо: собрать таблицу цен конкурентов", "source": "DemoExchange", "date": "2026-11-13"},
            {"idx": "d2", "title": "Демо: автоматизация отчётов через API", "source": "DemoMarket", "date": "2026-11-13"},
        ]},
    ],
    "main": [{"idx": "m1", "title": "Демо: парсер объявлений за 48 часов", "source": "DemoBoard", "date": "2026-11-13"}],
    "outset": [],
}
io.open(os.path.join(OUT, "orders-triage.js"), "w", encoding="utf-8").write("window.EVO_ORDERS_TRIAGE = " + json.dumps(tri, ensure_ascii=False) + ";")
print("orders-triage.js stub: OK")

hunt = {
    "generatedAt": D, "snapshot": "2026-11-14", "boardUpdated": D,
    "headline": "Демо-данные: доска возможностей обновляется в интерьере, витрина показывает обезличенные примеры",
    "counts": {"perspective": 2, "main": 1, "withSalary": 0},
    "top": [
        {"title": "Демо: интеграция Telegram-бота с таблицей", "url": "#demo", "source": "demo", "date": "2026-11-14", "category": "automation", "status": "new"},
        {"title": "Демо: деплой веб-сервиса на VPS", "url": "#demo", "source": "demo", "date": "2026-11-14", "category": "devops", "status": "new"},
    ],
    "observatory": [],
    "sources": ["demo"],
}
io.open(os.path.join(OUT, "hunter-report.js"), "w", encoding="utf-8").write("window.EVO_HUNTER_REPORT = " + json.dumps(hunt, ensure_ascii=False) + ";")
print("hunter-report.js stub: OK")

tasks = {
    "generatedAt": D,
    "urgent": [{"id": "demo-vitrina", "title": "Витрина: демо-режим включён", "source": "VITRINA"}],
    "regular": [{"id": "demo-sales", "title": "Кворки волны 1 готовы к публикации", "source": "SALES"}],
}
io.open(os.path.join(OUT, "tasks.js"), "w", encoding="utf-8").write(
    "// Демо-данные витрины (реальные задачи — в интерьере).\n// Формат: { generatedAt, urgent: [{title, source}], regular: [{title, source}] }\nwindow.EVO_TASKS = " + json.dumps(tasks, ensure_ascii=False) + ";")
print("tasks.js stub: OK")

total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
print("TOTAL board size: %.1f MB" % (total / 1e6))
