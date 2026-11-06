# -*- coding: utf-8 -*-
"""Машинный журнал событий Platform Evo (Лейн Л-2, Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md).

Один журнал на платформу: JSONL построчная дозапись конвертов
(schema_id="evo.log.event"). Атомарность по ТЗ: запись целиком одной операцией
open(..., "a", encoding="utf-8") + write("\n" + line). Исключение при записи
не роняет вызывающий код — возвращается {"ok": False, "error": ...}.

Читателям журнала: пропускать пустые строки (первая запись в чистый файл
начинается с "\n" — это осознанное поведение формата записи из ТЗ).
stdlib-only (ADR-003/004).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_PATH = ROOT / "Workspace" / "logs" / "events.jsonl"

SCHEMA_ID = "evo.log.event"


def append_event(kind: str, source: str, payload=None, log_path=None) -> dict:
    """Дописать одно событие в JSONL-журнал.

    kind — тип события ("snapshot.completed", "task.stage", ...); source — автор
    (попадает в конверт как produced_by); payload — словарь деталей (может быть None).
    Путь журнала по умолчанию Workspace/logs/events.jsonl, переопределяется log_path
    (тесты пишут во tmp). Возвращает {"ok": True, ...} при успехе и
    {"ok": False, "error": ...} при любой ошибке — наружу исключения не выходят.
    """
    try:
        path = Path(log_path) if log_path is not None else Path(DEFAULT_LOG_PATH)
        produced_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        envelope = {
            "schema_id": SCHEMA_ID,
            "schema_version": 1,
            "produced_by": source,
            "produced_at": produced_at,
            "payload": {"kind": kind, **(payload or {})},
            "refs": {},
            "ts": produced_at,
        }
        line = json.dumps(envelope, ensure_ascii=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            # В пустой файл пишем без ведущего "\n": первая строка журнала — JSON.
            # (fix Д-2 ночной смены 2026-11-05: раньше образовывалась пустая строка 1.)
            prefix = "" if handle.tell() == 0 else "\n"
            handle.write(prefix + line)
        return {"ok": True, "path": str(path), "ts": produced_at}
    except Exception as error:  # падение журнала никогда не ломает вызывающий код
        return {"ok": False, "error": str(error)}
