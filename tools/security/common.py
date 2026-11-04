#!/usr/bin/env python3
"""Общие помощники инструментов безопасности Platform Evo.

stdlib-only (ADR-003/004). Отчёты пишутся в %LOCALAPPDATA%/Platform/SecurityReports/ —
вне git и публичных data-файлов (правило видимости AI Sandbox, Sovereign 31.10).
Наружу — только пассивные GET к публичным фидам, без данных платформы.
"""

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

TASHKENT = timezone(timedelta(hours=5), "Tashkent")
REPORTS_DIR = (
    Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Platform" / "SecurityReports"
)
USER_AGENT = "PlatformEvo-SecurityTools/0.1 (local dashboard; passive public-feed reader)"


def save_report(tool: str, payload: dict) -> Path:
    """Атомарно сохранить JSON-отчёт с меткой времени; вернуть путь."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(TASHKENT).strftime("%Y-%m-%d-%H%M%S")
    path = REPORTS_DIR / f"{tool}-{stamp}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return path


def latest_report(file_prefix: str):
    """Самый свежий отчёт данного инструмента или None."""
    if not REPORTS_DIR.exists():
        return None
    files = sorted(REPORTS_DIR.glob(f"{file_prefix}-*.json"), reverse=True)
    return files[0] if files else None


def fetch_json(url: str, timeout: int = 30):
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def fetch_text(url: str, timeout: int = 60) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def now_iso() -> str:
    return datetime.now(TASHKENT).isoformat(timespec="seconds")


def print_summary(lines):
    for line in lines:
        print(line)
