#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор данных экскурсии по рейсам агентов (вкладка «Экскурсия» в AI Sandbox).

Читает машинный журнал (Workspace/logs/events.jsonl), карточки задач и параметры
артефактов с диска, собирает два реальных рейса («Флот в море», «Резюме-конвейер»)
и пишет eVo/dashboard/excursion-data.js (window.EVO_EXCURSION) — паттерн brief.js:
интерфейс читает снимок, источником остаётся журнал.

Приватная зона (Workspace/private/) не читается: только путь как факт существования.

Перегенерация: python tools/barrymore/build-excursion.py
"""

import json
import sys
from datetime import timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOURNAL = ROOT / "Workspace" / "logs" / "events.jsonl"
ACTIVE = ROOT / "Memory" / "Engineering" / "Tasks" / "Active"
OUT = ROOT / "eVo" / "dashboard" / "excursion-data.js"
LOCAL_TZ = timezone(timedelta(hours=5), "Tashkent")  # машина живёт в Tashkent (ADR-002)


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


def local(e: dict) -> str:
    return fmt_local(ts(e))


def fmt_local(raw: str) -> str:
    from datetime import datetime
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(LOCAL_TZ).strftime("%d.%m %H:%M")
    except Exception:
        return raw


def file_facts(rel: str) -> dict:
    path = ROOT / rel
    if not path.is_file():
        return {"path": rel, "exists": False}
    return {"path": rel, "exists": True, "size": path.stat().st_size}


def flight_fleet(events: list[dict]) -> dict:
    """Рейс «Флот в море»: полностью задокументирован в журнале."""
    by_fleet = [e for e in events if payload(e).get("by") == "Флот-строитель"]
    started = next((e for e in by_fleet if kind_of(e) == "agent.started"), None)
    storm = next((e for e in by_fleet if kind_of(e) == "agent.storm"), None)
    finished = next((e for e in by_fleet if kind_of(e) == "agent.finished"), None)
    lanes = [e for e in by_fleet if kind_of(e) == "agent.lane"]
    if not (started and finished and lanes):
        raise SystemExit("fleet: события рейса не найдены в журнале")

    card = json.loads((ACTIVE / "agents-fleet.json").read_text(encoding="utf-8"))
    idea = next((h for h in card.get("history", []) if h.get("note")), None)

    lane_chips = []
    for e in lanes:
        p = payload(e)
        lane_chips.append({
            "name": p.get("lane", "?"),
            "detail": f"{p.get('tests', '')}".strip() or "лейн закрыт",
            "refs": list(p.get("files", [])),
        })
    storm_detail = ""
    if storm:
        storm_detail = payload(storm).get("reason", "")

    artifacts = [file_facts(p) for p in (
        "eVo/dashboard/agents.html", "eVo/dashboard/agents.css", "eVo/dashboard/agents.js",
        "tools/tests/test_agents_live.py")]

    return {
        "id": "agents-fleet",
        "title": "«Флот в море» — дашборд запущенных агентов",
        "subtitle": "ночь 05→06.11 · агент «Флот-строитель» · 3 лейна · 1 шторм · 20 тестов",
        "verdict": payload(finished).get("verdict", "принято"),
        "nodes": [
            {"kind": "idea", "label": "Замысел", "time": fmt_local(idea["at"]) if idea else "—",
             "detail": idea["note"] if idea else "", "refs": ["Memory/Engineering/Tasks/Active/agents-fleet.json (history)"]},
            {"kind": "spec", "label": "ТЗ", "time": "05.11",
             "detail": "Полный план: события evo.agent.event → GET /api/agents/live + agents.html «корабли в море»; метрики лейнов, пульса, штормов, ETA.",
             "refs": ["Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md"]},
            {"kind": "agent", "label": "Спавн агента", "time": local(started),
             "detail": payload(started).get("task", ""), "refs": ["Workspace/logs/events.jsonl (agent.started)"]},
            {"kind": "lane", "label": "Лейны", "time": "",
             "chips": lane_chips},
            {"kind": "storm", "label": "Шторм", "time": local(storm) if storm else "",
             "detail": storm_detail, "refs": ["Workspace/logs/events.jsonl (agent.storm)"]},
            {"kind": "artifact", "label": "Артефакты", "time": "", "files": artifacts,
             "refs": ["tools/barrymore/dashboard-server.py (+/api/agents/*)"]},
            {"kind": "finish", "label": "Финиш рейса", "time": local(finished),
             "detail": f"Вердикт: {payload(finished).get('verdict', '')}", "refs": ["tools/tests/test_agents_live.py (20/20)"]},
            {"kind": "accept", "label": "Приёмка", "time": "06.11 вечер",
             "detail": "Панель agents.html жива после рестарта 8765; принята Sovereign (ночная вахта 06→07.11).",
             "refs": ["Memory/Engineering/LOG.md", "http://127.0.0.1:8765/agents.html"]},
        ],
    }


def flight_resume(events: list[dict]) -> dict:
    """Рейс «Резюме-конвейер»: пульсы 5 шагов + финиш с верификацией ZCode."""
    pulses = [e for e in events if kind_of(e) == "agent.pulse" and "master-profile" in str(payload(e).get("step", ""))]
    if not pulses:
        pulses = [e for e in events if kind_of(e) == "agent.pulse"
                  and str(payload(e).get("step", "")).count("/") == 1]
    finished = next((e for e in events if kind_of(e) == "agent.finished"
                     and "Резюме" in payload(e).get("task", "") or "master-profile" in payload(e).get("task", "")), None)
    if not pulses or not finished:
        raise SystemExit("resume: события рейса не найдены в журнале")

    steps = []
    for e in pulses:
        p = payload(e)
        nums = ", ".join(f"{k}={v}" for k, v in p.items() if k not in ("step", "status"))
        steps.append({"name": p.get("step", "?"), "detail": f"status={p.get('status', '?')}; {nums}" if nums else p.get("status", "")})

    return {
        "id": "resume-pipeline",
        "title": "«Резюме-конвейер» — фактура для откликов за ночь",
        "subtitle": "ночь 04→05.11 · диспетчер вахты + суб-агент · 5 шагов · 14 файлов",
        "verdict": payload(finished).get("verdict", "принято"),
        "nodes": [
            {"kind": "idea", "label": "Замысел", "time": "04.11 вечер",
             "detail": "Санкция Sovereign: «нужны агенты — ночью копают проект, утром я кайфую». Лейн Л-2 ночной вахты: три кейса по шаблону Ситуация→Действие→Результат, факт-чек по LOG E-001…E-046, ничего не выдумывать.",
             "refs": ["Workspace/reports/night-2026-11-05/QUEUE.md", "Docs/NIGHT-LOG-2026-11-05-ZCode.md"]},
            {"kind": "agent", "label": "Диспетчер вахты", "time": "04.11 ~23:58",
             "detail": "Крон-автоматизация ночной вахты берёт лейны из QUEUE.md по порядку; Л-2 отдан суб-агенту с жёстким пайком токенов.",
             "refs": ["Workspace/reports/night-2026-11-05/STATE-NIGHT.md"]},
            {"kind": "lane", "label": "Шаги конвейера", "time": fmt_local(ts(pulses[0])), "chips": steps},
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
        "generatedAt": __import__("datetime").datetime.now(LOCAL_TZ).isoformat(timespec="seconds"),
        "journal": "Workspace/logs/events.jsonl",
        "flights": [flight_fleet(events), flight_resume(events)],
    }
    body = json.dumps(data, ensure_ascii=False, indent=2)
    OUT.write_text(
        "/* Сгенерировано tools/barrymore/build-excursion.py — не править руками.\n"
        "   Перегенерация: python tools/barrymore/build-excursion.py\n"
        "   Источник: Workspace/logs/events.jsonl + карточки Memory/Engineering/Tasks. */\n"
        "window.EVO_EXCURSION = " + body + ";\n",
        encoding="utf-8",
    )
    print(f"OK: {OUT.relative_to(ROOT)} (рейсов: {len(data['flights'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
