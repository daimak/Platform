#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Метрики конвейера канбана Platform Evo (Лейн Л-5, Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md).

Мотивация (01:1-тимлид, 04.11): «кто закрыл?» и «покажи цифры». Каждое движение
карточки — подписанное событие в журнале (Л-5), метрики — выборка по событиям.

Читает Memory/Engineering/Tasks/Active/*.json + Workspace/logs/events.jsonl и печатает
4 блока: (1) закрыто за 7 дней; (2) средний возраст карточек в in-progress;
(3) карточки старше 7 дней; (4) переходы по авторам за 7 дней — из журнала
(task.stage) плюс fallбэк по history[].by карточек (переход, которого нет в
журнале: append_event мог не записаться или журнал отсутствует).
Вывод: человекочитаемый текст + JSON-envelope schema_id="evo.kanban.metrics".
Без UI, без логинов/ролей/графиков; старые карточки без подписей не мигрируют.
stdlib-only (ADR-003/004). Запуск: python tools/ops/kanban_metrics.py
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # запуск как скрипта: python tools/ops/kanban_metrics.py
    sys.path.insert(0, str(ROOT))

from tools.lib.envelope import make_envelope  # noqa: E402

ACTIVE_DIR = ROOT / "Memory" / "Engineering" / "Tasks" / "Active"
EVENTS_PATH = ROOT / "Workspace" / "logs" / "events.jsonl"

WINDOW_DAYS = 7
SCHEMA_ID = "evo.kanban.metrics"


def _parse_ts(value) -> datetime | None:
    """Распарсить ISO-8601 ("Z" на конце допускается); None если не парсится."""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _read_cards(active_dir: Path) -> list:
    cards = []
    for path in sorted(Path(active_dir).glob("*.json")):
        try:
            card = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue  # одна битая карточка не валит метрики (толерантность task_store)
        if isinstance(card, dict):
            cards.append(card)
    return cards


def _read_stage_events(events_path: Path, window_start: datetime) -> list:
    """Подписанные переходы task.stage из журнала за окно; битые строки пропускаются."""
    try:
        text = Path(events_path).read_text(encoding="utf-8")
    except OSError:
        return []
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue  # формат записи "\n"+line из Л-2 даёт пустые строки — это норма
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("schema_id") != "evo.log.event":
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict) or payload.get("kind") != "task.stage":
            continue
        ts = _parse_ts(event.get("ts") or event.get("produced_at"))
        if ts is None or ts < window_start:
            continue
        events.append({
            "id": payload.get("id"),
            "from": payload.get("from"),
            "to": payload.get("to"),
            "by": str(event.get("produced_by") or "unknown"),
            "ts": event.get("ts") or event.get("produced_at"),
            "source": "journal",
        })
    return events


# Подпись history и строка журнала ставятся в одном вызове set_stage/mark_done,
# но двумя вызовами системных часов — допускаем расхождение в секунды при дедупликации.
FALLBACK_TOLERANCE_S = 5.0


def _history_fallback(cards: list, window_start: datetime, journal_events: list) -> list:
    """Fallбэк Л-5: переходы из history[].by карточек Active, которых нет в журнале.

    Записи без "by" (до эпохи подписей) и не-переходы (archived) пропускаются;
    дубли против журнала снимаются по паре (id, to) с допуском по времени."""
    journal_keys = []
    for event in journal_events:
        ts = _parse_ts(event.get("ts"))
        if ts is not None:
            journal_keys.append((event.get("id"), event.get("to"), ts.timestamp()))
    fallback = []
    for card in cards:
        history = card.get("history")
        if not isinstance(history, list):
            continue
        for entry in history:
            if not isinstance(entry, dict):
                continue
            by = entry.get("by")
            if not isinstance(by, str) or not by.strip():
                continue  # запись до эпохи подписей — не мигрируем и не считаем
            to = entry.get("stage") or ("done" if entry.get("status") == "done" else None)
            if not to:
                continue  # archived и прочие не-переходы
            at = _parse_ts(entry.get("at"))
            if at is None or at < window_start:
                continue
            if any(key_id == card.get("id") and key_to == to
                   and abs(key_ts - at.timestamp()) <= FALLBACK_TOLERANCE_S
                   for key_id, key_to, key_ts in journal_keys):
                continue  # этот переход уже посчитан по журналу
            fallback.append({
                "id": card.get("id"),
                "from": None,
                "to": to,
                "by": by.strip(),
                "ts": entry.get("at"),
                "source": "history",
            })
    return fallback


def build_metrics(active_dir: Path, events_path: Path, now: datetime | None = None) -> dict:
    """Собрать 4 блока метрик конвейера. now — точка отсчёта окна (по умолчанию часы UTC)."""
    moment = now or datetime.now(timezone.utc)
    window_start = moment - timedelta(days=WINDOW_DAYS)

    done_last_7d = []
    in_progress = []
    older_than_7d = []
    cards = _read_cards(active_dir)
    for card in cards:
        created = _parse_ts(card.get("createdAt"))
        age_days = (moment - created).total_seconds() / 86400 if created is not None else None
        if card.get("status") == "done":
            completed = _parse_ts(card.get("completedAt"))
            if completed is not None and completed >= window_start:
                done_last_7d.append({
                    "id": card.get("id"),
                    "title": card.get("title"),
                    "completed_at": card.get("completedAt"),
                })
            continue
        if card.get("status") != "active":
            continue
        entry = {
            "id": card.get("id"),
            "title": card.get("title"),
            "stage": card.get("stage"),
            "age_days": round(age_days, 1) if age_days is not None else None,
        }
        if card.get("stage") == "in-progress":
            in_progress.append(entry)
        if age_days is not None and age_days > WINDOW_DAYS:
            older_than_7d.append(entry)

    stage_events = _read_stage_events(events_path, window_start)
    fallback_events = _history_fallback(cards, window_start, stage_events)
    transitions = stage_events + fallback_events
    by_author: dict = {}
    for event in transitions:
        by_author[event["by"]] = by_author.get(event["by"], 0) + 1

    ages = [entry["age_days"] for entry in in_progress if entry["age_days"] is not None]
    avg_age = round(sum(ages) / len(ages), 1) if ages else None

    return {
        "generated_at": moment.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "window_days": WINDOW_DAYS,
        "block_1_done_last_7d": done_last_7d,
        "block_2_in_progress_avg_age_days": avg_age,
        "block_2_in_progress_count": len(in_progress),
        "block_3_older_than_7d": older_than_7d,
        "block_4_transitions_by_author": by_author,
        "block_4_transitions_total": len(transitions),
        "block_4_fallback_count": len(fallback_events),
        "block_4_transitions_log": transitions[-50:],
    }


def render_text(metrics: dict) -> str:
    """Человекочитаемый вывод 4 блоков."""
    done = metrics["block_1_done_last_7d"]
    avg_age = metrics["block_2_in_progress_avg_age_days"]
    in_progress_count = metrics["block_2_in_progress_count"]
    older = metrics["block_3_older_than_7d"]
    by_author = metrics["block_4_transitions_by_author"]
    total = metrics["block_4_transitions_total"]
    fallback_count = metrics.get("block_4_fallback_count", 0)

    lines = [f"Метрики канбана на {metrics['generated_at']} (окно {metrics['window_days']} дн.)", ""]
    lines.append(f"1) Закрыто за {metrics['window_days']} дней: {len(done)}")
    for card in done:
        lines.append(f"   - {card['id']} «{card['title']}» closed_at={card['completed_at']}")
    lines.append("")
    if avg_age is None:
        lines.append(f"2) Средний возраст карточек в in-progress: n/a (карточек: {in_progress_count})")
    else:
        lines.append(f"2) Средний возраст карточек в in-progress: {avg_age} дн. (карточек: {in_progress_count})")
    lines.append("")
    lines.append(f"3) Карточки старше {metrics['window_days']} дней: {len(older)}")
    for card in older:
        lines.append(f"   - {card['id']} «{card['title']}» stage={card['stage']} возраст={card['age_days']} дн.")
    lines.append("")
    lines.append(f"4) Переходы по авторам за {metrics['window_days']} дней (всего {total}):")
    if fallback_count:
        lines.append(f"   - из них {fallback_count} — fallбэк по history[].by (в журнале не найдено)")
    if not by_author:
        lines.append("   - переходов в журнале нет (Workspace/logs/events.jsonl пуст или только без task.stage)")
    for author, count in sorted(by_author.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"   - {author}: {count}")
    return "\n".join(lines)


def build_envelope(metrics: dict, active_dir: Path, events_path: Path) -> dict:
    """Конверт schema_id="evo.kanban.metrics" с метриками в payload (tools.lib.envelope)."""
    return make_envelope(
        SCHEMA_ID,
        "kanban_metrics",
        metrics,
        refs={"active_dir": str(active_dir), "events": str(events_path)},
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # кириллица не зависит от кодовой страницы консоли
    metrics = build_metrics(ACTIVE_DIR, EVENTS_PATH)
    print(render_text(metrics))
    print()
    print(f"=== JSON envelope {SCHEMA_ID} ===")
    print(json.dumps(build_envelope(metrics, ACTIVE_DIR, EVENTS_PATH), ensure_ascii=False))


if __name__ == "__main__":
    main()
