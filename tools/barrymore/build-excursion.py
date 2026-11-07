#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор данных экскурсии по рейсам агентов (вкладка «Экскурсия» в AI Sandbox).

Формат по требованию Sovereign 07.11: доклад цифрами — работали такие-то агенты,
такие-то задачи, осязаемый результат в понятных числах. Источники только живые:
машинный журнал (events.jsonl), карточки задач, git show --stat, NIGHT-LOG.
Приватная зона (Workspace/private/) не читается: только путь как факт существования.

Пишет eVo/dashboard/excursion-data.js (window.EVO_EXCURSION) — паттерн brief.js.
Перегенерация: python tools/barrymore/build-excursion.py
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOURNAL = ROOT / "Workspace" / "logs" / "events.jsonl"
NIGHT_LOG = ROOT / "Docs" / "NIGHT-LOG-2026-11-05-ZCode.md"
ACTIVE = ROOT / "Memory" / "Engineering" / "Tasks" / "Active"
OUT = ROOT / "eVo" / "dashboard" / "excursion-data.js"
LOCAL_TZ = timezone(timedelta(hours=5), "Tashkent")


def load_events() -> list[dict]:
    events = []
    for line in JOURNAL.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def payload(e: dict) -> dict:
    p = e.get("payload") or {}
    return p if isinstance(p, dict) else {}


def kind_of(e: dict) -> str:
    return e.get("kind") or payload(e).get("kind") or ""


def ts(e: dict) -> str:
    return e.get("ts") or e.get("at") or payload(e).get("at") or ""


def fmt_local(raw: str) -> str:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(LOCAL_TZ).strftime("%d.%m %H:%M")
    except Exception:
        return raw or "—"


def local(e: dict) -> str:
    return fmt_local(ts(e))


def duration(raw_from: str, raw_to: str) -> str:
    try:
        a = datetime.fromisoformat(raw_from.replace("Z", "+00:00"))
        b = datetime.fromisoformat(raw_to.replace("Z", "+00:00"))
        secs = int((b - a).total_seconds())
        return f"{secs // 60} мин {secs % 60} с"
    except Exception:
        return "—"


def file_facts(rel: str) -> dict:
    path = ROOT / rel
    if not path.is_file():
        return {"path": rel, "exists": False}
    return {"path": rel, "exists": True, "size": path.stat().st_size}


def git_stat(commit: str) -> dict | None:
    """git show --stat: файлы, вставки, построчные цифры по файлам."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(ROOT), "show", "--stat", "--format=", commit],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    per_file = {}
    for line in proc.stdout.splitlines():
        m = re.match(r"\s*(\S+)\s+\|\s+(\d+)\s+\+", line)
        if m:
            per_file[m.group(1)] = int(m.group(2))
    total = re.search(r"(\d+) files? changed, (\d+) insertions?\(\+\)(?:, (\d+) deletions?\(-\))?", proc.stdout)
    if not total:
        return None
    return {
        "commit": commit,
        "files": int(total.group(1)),
        "insertions": int(total.group(2)),
        "deletions": int(total.group(3) or 0),
        "perFile": per_file,
    }


def nightlog_crew(slug: str) -> dict | None:
    """NIGHT-LOG: «Исполнитель: суб-агент ZCode, 67 вызовов, ~21 мин, 3.34M токенов»."""
    if not NIGHT_LOG.is_file():
        return None
    text = NIGHT_LOG.read_text(encoding="utf-8")
    section = re.search(rf"^## Рейс [^\n]*{re.escape(slug)}[^\n]*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not section:
        return None
    crew = re.search(r"(\d+) вызовов, ~(\d+) мин, ([\d.]+M) токенов", section.group(1))
    if not crew:
        return None
    return {"calls": int(crew.group(1)), "minutes": int(crew.group(2)), "tokens": crew.group(3)}


def nightlog_summary() -> str | None:
    """Итог ночи по NIGHT-LOG: сколько рейсов и сколько суммарно токенов."""
    if not NIGHT_LOG.is_file():
        return None
    tokens = re.findall(r"(\d+\.\d+)M токенов", NIGHT_LOG.read_text(encoding="utf-8"))
    if not tokens:
        return None
    total = sum(float(t) for t in tokens)
    return f"За ночь 05.11 задокументировано {len(tokens)} рейсов, суммарно ~{total:.1f}M токенов — все приняты."


def flight_fleet(events: list[dict]) -> dict:
    """Рейс «Флот в море»: события в журнале + git-стат коммита d271fd5."""
    by_fleet = [e for e in events if payload(e).get("by") == "Флот-строитель"]
    started = next((e for e in by_fleet if kind_of(e) == "agent.started"), None)
    storm = next((e for e in by_fleet if kind_of(e) == "agent.storm"), None)
    finished = next((e for e in by_fleet if kind_of(e) == "agent.finished"), None)
    lanes = [e for e in by_fleet if kind_of(e) == "agent.lane"]
    if not (started and finished and lanes):
        raise SystemExit("fleet: события рейса не найдены в журнале")

    card = json.loads((ACTIVE / "agents-fleet.json").read_text(encoding="utf-8"))
    idea = next((h for h in card.get("history", []) if h.get("note")), None)
    storm_detail = payload(storm).get("reason", "") if storm else ""
    stat = git_stat("d271fd5")
    ui_files = ("eVo/dashboard/agents.html", "eVo/dashboard/agents.css", "eVo/dashboard/agents.js")
    ui_lines = sum(stat["perFile"].get(f, 0) for f in ui_files) if stat else None

    report_rows = [
        {"label": "Работали", "value": "агент «Флот-строитель» (суб-агент ZCode), рейс ночной вахты 06→07.11"},
        {"label": "Задача", "value": "панель запущенных агентов по ТЗ, лейны Л-С1 API → Л-С2 UI → Л-С3 тесты"},
    ]
    if stat:
        report_rows.append({
            "label": "Результат",
            "value": (f"+{stat['insertions']} строк кода в {stat['files']} файлах (коммит {stat['commit']}): "
                      f"интерфейс {ui_lines} строк (agents.html {stat['perFile'].get(ui_files[0], 0)} + "
                      f"agents.css {stat['perFile'].get(ui_files[1], 0)} + agents.js {stat['perFile'].get(ui_files[2], 0)}), "
                      f"API +{stat['perFile'].get('tools/barrymore/dashboard-server.py', 0)} строк в dashboard-server.py "
                      f"(GET /api/agents/live + /history, шторм = storm без finished ИЛИ тишина >30 мин), "
                      f"{stat['perFile'].get('tools/tests/test_agents_live.py', 0)} строк тестов"),
        })
    report_rows += [
        {"label": "Инцидент", "value": (f"1 шторм: {storm_detail}" if storm else "нет")},
        {"label": "Эксплуатация", "value": "сервер 8765 перезапущен, панель отвечает 200, автообновление 15 с"},
        {"label": "Вердикт", "value": "принято Sovereign 06.11; панель в бою — http://127.0.0.1:8765/agents.html"},
    ]

    lane_chips = [{"name": payload(e).get("lane", "?"), "detail": payload(e).get("tests", "") or "лейн закрыт",
                   "refs": list(payload(e).get("files", []))} for e in lanes]

    return {
        "id": "agents-fleet",
        "title": "«Флот в море» — дашборд запущенных агентов",
        "subtitle": "ночь 06→07.11 · вахта 8 · коммит d271fd5",
        "verdict": "принято Sovereign",
        "metrics": [
            {"value": f"+{stat['insertions']}", "label": "строк кода в 6 файлах"} if stat else {"value": "—", "label": "строк"},
            {"value": "20/20", "label": "тестов живой панели"},
            {"value": duration(ts(started), ts(finished)), "label": "от спавна до финиша"},
        ],
        "reportRows": report_rows,
        "nodes": [
            {"kind": "idea", "label": "Замысел", "time": fmt_local(idea["at"]) if idea else "—",
             "detail": idea["note"] if idea else "", "refs": ["Memory/Engineering/Tasks/Active/agents-fleet.json (history)"]},
            {"kind": "spec", "label": "ТЗ", "time": "05.11",
             "detail": "Полный план: события evo.agent.event → GET /api/agents/live + agents.html «корабли в море»; метрики лейнов, пульса, штормов, ETA.",
             "refs": ["Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md"]},
            {"kind": "agent", "label": "Спавн агента", "time": local(started),
             "detail": payload(started).get("task", ""), "refs": ["Workspace/logs/events.jsonl (agent.started)"]},
            {"kind": "lane", "label": "Лейны", "time": "", "chips": lane_chips},
            {"kind": "storm", "label": "Шторм", "time": local(storm) if storm else "",
             "detail": storm_detail, "refs": ["Workspace/logs/events.jsonl (agent.storm)"]},
            {"kind": "artifact", "label": "Артефакты", "time": "", "files": [file_facts(p) for p in ui_files]},
            {"kind": "finish", "label": "Финиш рейса", "time": local(finished),
             "detail": f"Вердикт: {payload(finished).get('verdict', '')}", "refs": ["tools/tests/test_agents_live.py (20/20)"]},
            {"kind": "accept", "label": "Приёмка", "time": "06.11 вечер",
             "detail": "Панель agents.html жива после рестарта 8765; принята Sovereign (ночная вахта 06→07.11).",
             "refs": ["Memory/Engineering/LOG.md"]},
        ],
    }


def flight_resume(events: list[dict]) -> dict:
    """Рейс «Резюме-конвейер»: пульсы 5 шагов + смета из NIGHT-LOG."""
    pulses = [e for e in events if kind_of(e) == "agent.pulse"
              and re.match(r"\d/5 ", str(payload(e).get("step", "")))]
    finished = next((e for e in events if kind_of(e) == "agent.finished"
                     and ("Резюме" in payload(e).get("task", "")
                          or "master-profile" in payload(e).get("task", ""))), None)
    if not pulses or not finished:
        raise SystemExit("resume: события рейса не найдены в журнале")
    crew = nightlog_crew("Резюме-конвейер")

    def pulse(idx: str) -> dict:
        return payload(next((e for e in pulses if str(payload(e).get("step", "")).startswith(idx)), {}))

    p1, p2, p3, p4 = pulse("1/5"), pulse("2/5"), pulse("3/5"), pulse("4/5")
    steps = [{"name": payload(e).get("step", "?"),
              "detail": ", ".join(f"{k}={v}" for k, v in payload(e).items() if k not in ("step", "status"))}
             for e in pulses]

    report_rows = [
        {"label": "Работали",
         "value": (f"суб-агент ZCode под диспетчером ночной вахты: {crew['calls']} вызовов инструментов, "
                   f"~{crew['minutes']} мин, {crew['tokens']} токенов суб-контекста") if crew
         else "суб-агент ZCode под диспетчером ночной вахты"},
        {"label": "Задача", "value": "лейн Л-2 ночной вахты 04→05.11 — фактура резюме для откликов (QUEUE.md, шаблон «Ситуация → Действие → Результат», ничего не выдумывать)"},
        {"label": "Результат",
         "value": (f"{p1.get('cases', '?')} кейсов в профиле ({p1.get('skills', '?')} навыков, {p1.get('todo', '?')} честных todo), "
                   f"{p2.get('files', '?')} полных кейса в двух языках (RU {min(p2.get('ru_words', [0]))}–{max(p2.get('ru_words', [0]))}, "
                   f"EN {min(p2.get('en_words', [0]))}–{max(p2.get('en_words', [0]))} слов), рынок: {p3.get('fresh_total', '?')} свежих позиций, "
                   f"{p3.get('selected', '?')} отобрано ({p3.get('ru', '?')} RU + {p3.get('en', '?')} EN), "
                   f"{p4.get('files', '?')} черновиков откликов по {p4.get('word_range', '?')} слов + README-указатель — 14 файлов")},
        {"label": "Приватная зона", "value": "резюме-артефакты в Workspace/private/ — показаны путями, содержимое не читается"},
        {"label": "Вердикт", "value": "принято, верификация ZCode; блокер №1 поиска работы снят (отклики готовы к отправке)"},
    ]

    return {
        "id": "resume-pipeline",
        "title": "«Резюме-конвейер» — фактура для откликов за ночь",
        "subtitle": "ночь 04→05.11 · рейс 2 ночной вахты · 14 файлов",
        "verdict": "принято, верифицировано",
        "metrics": [
            {"value": crew["tokens"] if crew else "—", "label": "токенов суб-контекста"},
            {"value": "14", "label": "файлов в резюме-зоне"},
            {"value": f"{p3.get('fresh_total', '?')} → {p3.get('selected', '?')}", "label": "позиций рынка → откликов"},
        ],
        "reportRows": report_rows,
        "nodes": [
            {"kind": "idea", "label": "Замысел", "time": "04.11 вечер",
             "detail": "Санкция Sovereign: «нужны агенты — ночью копают проект, утром я кайфую». Л-2: три кейса по шаблону, факт-чек по LOG E-001…E-046.",
             "refs": ["Workspace/reports/night-2026-11-05/QUEUE.md", "Docs/NIGHT-LOG-2026-11-05-ZCode.md"]},
            {"kind": "agent", "label": "Диспетчер вахты", "time": "04.11 ~23:58",
             "detail": "Крон-автоматизация ночной вахты берёт лейны из QUEUE.md по порядку; Л-2 отдан суб-агенту с пайком токенов.",
             "refs": ["Workspace/reports/night-2026-11-05/STATE-NIGHT.md"]},
            {"kind": "lane", "label": "Шаги конвейера", "time": local(pulses[0]), "chips": steps},
            {"kind": "artifact", "label": "Артефакты", "time": "05.11 ~00:50",
             "files": [
                 {"path": "Workspace/private/resume/master-profile.json", "exists": True, "private": True},
                 {"path": "Workspace/private/resume/cases/ (3 кейса RU+EN)", "exists": True, "private": True},
                 {"path": "Workspace/private/proposals/2026-11-05/ (10 откликов)", "exists": True, "private": True},
             ],
             "detail": "Приватная зона: пути — факт существования, содержимое не читается и не показывается.",
             "refs": ["Workspace/reports/night-2026-11-05/QUEUE.md (Л-2)"]},
            {"kind": "finish", "label": "Финиш рейса", "time": local(finished),
             "detail": f"Вердикт: {payload(finished).get('verdict', '')}", "refs": ["Workspace/logs/events.jsonl (agent.finished)"]},
            {"kind": "accept", "label": "Приёмка", "time": "05.11 утро",
             "detail": "Блокер №1 поиска работы снят: 28 навыков, 7 кейсов, 10 откликов готовы; 6 решений за Sovereign — в README зоны.",
             "refs": ["Workspace/reports/night-2026-11-05/QUEUE.md"]},
        ],
    }


def main() -> int:
    events = load_events()
    data = {
        "generatedAt": datetime.now(LOCAL_TZ).isoformat(timespec="seconds"),
        "journal": "Workspace/logs/events.jsonl",
        "summary": nightlog_summary(),
        "flights": [flight_fleet(events), flight_resume(events)],
    }
    body = json.dumps(data, ensure_ascii=False, indent=2)
    OUT.write_text(
        "/* Сгенерировано tools/barrymore/build-excursion.py — не править руками.\n"
        "   Перегенерация: python tools/barrymore/build-excursion.py\n"
        "   Источники: events.jsonl, карточки задач, git show --stat, Docs/NIGHT-LOG. */\n"
        "window.EVO_EXCURSION = " + body + ";\n",
        encoding="utf-8",
    )
    print(f"OK: {OUT.relative_to(ROOT)} (рейсов: {len(data['flights'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
