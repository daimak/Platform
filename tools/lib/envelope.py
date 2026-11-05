# -*- coding: utf-8 -*-
"""Конверт артефактов Platform Evo (Лейн Л-1, Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md).

Единый формат фактуры: любой отчёт/событие/выгрузка оборачивается в конверт
с schema_id, версией схемы, автором и UTC-временем создания. Ничего не удаляем
и не мигрируем: существующие форматы данных продолжают жить как есть.
stdlib-only (ADR-003/004).
"""
import re
from datetime import datetime, timezone

# schema_id: два-три сегмента из ascii-букв/цифр/подчёркиваний через точку
# ("evo.log.event", "evo.ops.job_state", "evo.resume.master", ...).
SCHEMA_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+){1,2}$")

REQUIRED_FIELDS = ("schema_id", "schema_version", "produced_by", "produced_at", "payload")


def utc_now_iso() -> str:
    """Текущее время по системным часам: UTC ISO-8601 с суффиксом "Z"."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def make_envelope(schema_id: str, produced_by: str, payload, version: int = 1, refs=None) -> dict:
    """Собрать конверт артефакта.

    produced_at ставится автоматически из системных часов (UTC, ISO-8601 "Z").
    payload передаётся как есть (любой JSON-тип); refs — словарь (по умолчанию {}).
    """
    return {
        "schema_id": schema_id,
        "schema_version": version,
        "produced_by": produced_by,
        "produced_at": utc_now_iso(),
        "payload": payload,
        "refs": refs if refs is not None else {},
    }


def _present(env: dict, field: str) -> bool:
    return field in env


def validate_envelope(env) -> list:
    """Проверить конверт; вернуть список ошибок (пустой список = конверт корректен).

    Правила по ТЗ Л-1: обязательные поля присутствуют; schema_id — 2-3 ascii-сегмента
    через точку; produced_at парсится; payload присутствует (любой JSON-тип,
    но None считается отсутствием).
    """
    if not isinstance(env, dict):
        return ["конверт должен быть JSON-объектом"]

    errors = []
    for field in REQUIRED_FIELDS:
        if not _present(env, field):
            errors.append(f"нет обязательного поля: {field}")

    if _present(env, "schema_id"):
        schema_id = env.get("schema_id")
        if not isinstance(schema_id, str) or not SCHEMA_ID_PATTERN.fullmatch(schema_id):
            errors.append("schema_id: ожидаются 2-3 ascii-сегмента через точку (например evo.log.event)")

    if _present(env, "produced_at"):
        produced_at = env.get("produced_at")
        if not isinstance(produced_at, str):
            errors.append("produced_at: ожидалась строка ISO-8601")
        else:
            try:
                datetime.fromisoformat(produced_at.replace("Z", "+00:00"))
            except ValueError:
                errors.append("produced_at: не парсится как ISO-8601")

    if _present(env, "payload") and env.get("payload") is None:
        errors.append("payload: отсутствует (None считается отсутствием)")

    if _present(env, "produced_by"):
        produced_by = env.get("produced_by")
        if not isinstance(produced_by, str) or not produced_by.strip():
            errors.append("produced_by: ожидалась непустая строка")

    if _present(env, "schema_version"):
        schema_version = env.get("schema_version")
        if isinstance(schema_version, bool) or not isinstance(schema_version, int):
            errors.append("schema_version: ожидалось целое число")

    if _present(env, "refs") and not isinstance(env.get("refs"), dict):
        errors.append("refs: ожидался объект (dict)")

    return errors
