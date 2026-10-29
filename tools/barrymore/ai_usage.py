#!/usr/bin/env python3
"""Local, extensible ledger for AI usage snapshots and request metadata."""

import json
import math
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Platform" / "AI-Usage"
LEDGER_PATH = DATA_DIR / "usage.json"
PROVIDER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
MAX_RECORDS = 5000

PROVIDERS = {
    "github-copilot": {"name": "GitHub Copilot", "kind": "subscription"},
    "chatgpt-subscription": {"name": "ChatGPT subscription", "kind": "subscription"},
    "openai-api": {"name": "OpenAI API", "kind": "api"},
    "anthropic-api": {"name": "Anthropic API", "kind": "api"},
    "freellmapi": {"name": "FreeLLMAPI", "kind": "gateway"},
}

DEFAULT_LEDGER = {
    "schema_version": 1,
    "snapshots": [],
    "requests": [],
    "settings": {"include_in_morning_brief": False},
}

SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:sk-[a-z0-9_-]{12,}|gh[pousr]_[a-z0-9]{20,})\b"),
    re.compile(r"(?i)\bBearer\s+[a-z0-9._~+/-]+=*"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_ledger() -> dict:
    if not LEDGER_PATH.exists():
        return json.loads(json.dumps(DEFAULT_LEDGER))
    data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported AI usage ledger format.")
    for key in ("snapshots", "requests"):
        if not isinstance(data.get(key), list):
            raise ValueError(f"Invalid AI usage ledger field: {key}")
    settings = data.get("settings")
    if not isinstance(settings, dict) or not isinstance(settings.get("include_in_morning_brief"), bool):
        raise ValueError("Invalid AI usage ledger settings.")
    return data


def _write_ledger(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".usage-", suffix=".tmp", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp_name, LEDGER_PATH)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


@contextmanager
def _ledger_lock():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with (DATA_DIR / ".usage.lock").open("a+b") as lock_file:
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _redact(value: str, limit: int = 240) -> str:
    result = value
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("[redacted]", result)
    return result[:limit]


def _valid_number(value, name: str, minimum: float = 0, maximum: float | None = None):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} is outside the allowed range.")
    return value


def _valid_tokens(value, name: str):
    value = _valid_number(value, name)
    if value is not None and not float(value).is_integer():
        raise ValueError(f"{name} must be a whole number.")
    return int(value) if value is not None else None


def _provider(provider_id: str, provider_name: str | None = None) -> dict:
    if not isinstance(provider_id, str) or not PROVIDER_ID_PATTERN.fullmatch(provider_id):
        raise ValueError("Provider ID must use lowercase letters, digits, dot, underscore, or hyphen.")
    if provider_id not in PROVIDERS:
        if not provider_name or not isinstance(provider_name, str) or not provider_name.strip():
            raise ValueError("A display name is required for a new provider adapter.")
        return {"name": _redact(provider_name.strip(), 80), "kind": "custom"}
    return PROVIDERS[provider_id]


def record_request(
    provider_id: str,
    model: str,
    usage: dict | None,
    cost: dict | None,
    purpose: str,
    result_summary: str,
) -> dict:
    provider = _provider(provider_id)
    usage = usage if isinstance(usage, dict) else {}
    cost = cost if isinstance(cost, dict) else {}
    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    total_tokens = usage.get("total_tokens")
    input_tokens = _valid_tokens(input_tokens, "input_tokens")
    output_tokens = _valid_tokens(output_tokens, "output_tokens")
    total_tokens = _valid_tokens(total_tokens, "total_tokens")
    if total_tokens is None and (input_tokens is not None or output_tokens is not None):
        total_tokens = (input_tokens or 0) + (output_tokens or 0)
    amount = _valid_number(cost.get("amount"), "cost.amount")
    currency = cost.get("currency")
    if currency is not None and (not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency)):
        raise ValueError("cost.currency must be a three-letter uppercase currency code.")

    record = {
        "id": f"req-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}",
        "recorded_at": _now(),
        "provider_id": provider_id,
        "provider_name": provider["name"],
        "model": _redact(str(model or "unknown"), 80),
        "purpose": _redact(purpose, 100),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost_amount": amount,
        "currency": currency,
        "usage_source": "provider_response" if usage else "unavailable",
        "cost_source": cost.get("source", "unavailable") if amount is not None else "unavailable",
        "result_summary": _redact(result_summary),
    }
    with _ledger_lock():
        data = _read_ledger()
        data["requests"].append(record)
        data["requests"] = data["requests"][-MAX_RECORDS:]
        _write_ledger(data)
    return record


def add_snapshot(snapshot: dict) -> dict:
    if not isinstance(snapshot, dict):
        raise ValueError("Snapshot must be an object.")
    provider_id = snapshot.get("provider_id")
    provider = _provider(provider_id, snapshot.get("provider_name"))
    percent = _valid_number(snapshot.get("credits_used_percent"), "credits_used_percent", maximum=100)
    input_tokens = _valid_tokens(snapshot.get("input_tokens"), "input_tokens")
    output_tokens = _valid_tokens(snapshot.get("output_tokens"), "output_tokens")
    amount = _valid_number(snapshot.get("cost_amount"), "cost_amount")
    currency = snapshot.get("currency")
    if currency is not None and (not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency)):
        raise ValueError("currency must be a three-letter uppercase currency code.")
    period = snapshot.get("period")
    if period is not None and (not isinstance(period, str) or len(period) > 80):
        raise ValueError("period must be at most 80 characters.")
    note = snapshot.get("note", "")
    if not isinstance(note, str):
        raise ValueError("note must be text.")
    if all(value is None for value in (percent, input_tokens, output_tokens, amount)) and not note.strip():
        raise ValueError("Provide at least one measured value or a note.")

    record = {
        "id": f"snap-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}",
        "recorded_at": _now(),
        "provider_id": provider_id,
        "provider_name": provider["name"],
        "period": _redact(period, 80) if period else None,
        "credits_used_percent": percent,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_amount": amount,
        "currency": currency,
        "note": _redact(note, 240),
        "source": "manual",
    }
    with _ledger_lock():
        data = _read_ledger()
        data["snapshots"].append(record)
        data["snapshots"] = data["snapshots"][-MAX_RECORDS:]
        _write_ledger(data)
    return record


def set_include_in_morning_brief(enabled: bool) -> dict:
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be a boolean.")
    with _ledger_lock():
        data = _read_ledger()
        data["settings"]["include_in_morning_brief"] = enabled
        _write_ledger(data)
    return data["settings"]


def settings() -> dict:
    return dict(_read_ledger()["settings"])


def _summary(data: dict, include_barrymore: bool) -> dict:
    requests = data["requests"]
    if not include_barrymore:
        requests = [r for r in requests if r.get("purpose") not in ("Morning Brief", "AI usage review")]
    known_token_records = [r for r in requests if r.get("total_tokens") is not None]
    costs_by_currency = {}
    for record in requests:
        amount = record.get("cost_amount")
        currency = record.get("currency")
        if amount is not None and currency:
            costs_by_currency[currency] = costs_by_currency.get(currency, 0) + amount
    latest = {}
    for snapshot in data["snapshots"]:
        latest[snapshot["provider_id"]] = snapshot
    return {
        "request_count": len(requests),
        "known_token_requests": len(known_token_records),
        "input_tokens": sum(r.get("input_tokens") or 0 for r in known_token_records)
        if known_token_records and all(r.get("input_tokens") is not None for r in known_token_records) else None,
        "output_tokens": sum(r.get("output_tokens") or 0 for r in known_token_records)
        if known_token_records and all(r.get("output_tokens") is not None for r in known_token_records) else None,
        "total_tokens": sum(r["total_tokens"] for r in known_token_records) if known_token_records else None,
        "costs": [{"currency": currency, "amount": amount} for currency, amount in sorted(costs_by_currency.items())],
        "snapshots": sorted(latest.values(), key=lambda s: s["provider_name"].casefold()),
    }


def dashboard_data() -> dict:
    data = _read_ledger()
    return {
        "providers": [{"id": key, **value} for key, value in PROVIDERS.items()],
        "custom_providers": sorted(
            {
                (r["provider_id"], r["provider_name"])
                for r in data["snapshots"] + data["requests"]
                if r["provider_id"] not in PROVIDERS
            }
        ),
        "snapshots": sorted(data["snapshots"], key=lambda s: s["recorded_at"], reverse=True),
        "requests": sorted(data["requests"], key=lambda r: r["recorded_at"], reverse=True),
        "summary": _summary(data, include_barrymore=True),
        "settings": dict(data["settings"]),
    }


def data_for_barrymore() -> dict:
    data = _read_ledger()
    summary = _summary(data, include_barrymore=False)
    return {
        "note": "Unknown values are unavailable, not zero. Subscription limits and spending are separate from API token usage.",
        "providers": summary["snapshots"],
        "request_count": summary["request_count"],
        "known_token_requests": summary["known_token_requests"],
        "input_tokens": summary["input_tokens"],
        "output_tokens": summary["output_tokens"],
        "total_tokens": summary["total_tokens"],
        "costs": summary["costs"],
    }
