#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Доклад Хантера — массовая часть доклада (резидент Navigation Observatory).

Хантер (Memory/Agents/Hunter.md) сводит находки из внешнего мира из уже
собранных платформой данных — НОВЫХ обращений наружу не делает (режим «поводка»,
правило видимости AI Sandbox). Источники:
- доска заказов/вакансий Workspace/analytics/orders_board.json (tools/orders_triage.py);
- свежайший снапшот Workspace/analytics/YYYY-MM-DD/ (jobs.csv + salary_extracted.csv);
- находки OLX tools/olx_production_data.json (tools/olx_production.py);
- очередь поручений Хантера %LOCALAPPDATA%/Platform/Hunter/assignments.json.

Выходы (ровно два файла, stdlib-only, ключей не читает):
- Workspace/analytics/hunter/digest.json — источник истины (полная массовая часть);
- eVo/dashboard/hunter-report.js          — window.EVO_HUNTER_REPORT для дашборда.

Выжимку для Morning Brief из digest.json берёт tools/barrymore/morning-brief-agent.py.

Запуск: python tools/hunter/report.py   (из корня Platform; правило метра —
тяжёлые прогоны только из корня, не из подкаталогов).
"""

import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARD_PATH = ROOT / "Workspace" / "analytics" / "orders_board.json"
SNAP_ROOT = ROOT / "Workspace" / "analytics"
OLX_PATH = ROOT / "tools" / "olx_production_data.json"
QUEUE_PATH = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Platform" / "Hunter" / "assignments.json"
DIGEST_PATH = ROOT / "Workspace" / "analytics" / "hunter" / "digest.json"
JS_PATH = ROOT / "eVo" / "dashboard" / "hunter-report.js"
JS_PREFIX = "window.EVO_HUNTER_REPORT = "

TASHKENT = timezone(timedelta(hours=5), "Tashkent")
TOP_BRIEF = 6
TOP_PANEL = 8
TOP_OLX = 5


def now_iso() -> str:
    return datetime.now(TASHKENT).isoformat(timespec="seconds")


def load_board() -> tuple[dict, list[dict]]:
    if not BOARD_PATH.exists():
        return {}, []
    data = json.loads(BOARD_PATH.read_text(encoding="utf-8"))
    records = data.get("records") if isinstance(data, dict) else data
    if not isinstance(records, list):
        records = []
    meta = {k: v for k, v in data.items() if k != "records"} if isinstance(data, dict) else {}
    return meta, records


def load_salary_map() -> dict[str, dict]:
    """idx → строка salary_extracted.csv свежайшего снапшота."""
    snap_dir = latest_snapshot()
    if not snap_dir:
        return {}, None
    path = snap_dir / "salary_extracted.csv"
    if not path.exists():
        return {}, snap_dir
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {row.get("idx", ""): row for row in csv.DictReader(f)}, snap_dir


def latest_snapshot() -> Path | None:
    dirs = sorted(
        (d for d in SNAP_ROOT.iterdir() if d.is_dir() and len(d.name) == 10 and d.name[4] == d.name[7] == "-"),
        reverse=True,
    ) if SNAP_ROOT.exists() else []
    return dirs[0] if dirs else None


def usd_hint(sal_row: dict) -> str:
    lo, hi = sal_row.get("usd_month_min", ""), sal_row.get("usd_month_max", "")
    try:
        lo_i, hi_i = int(float(lo)), int(float(hi))
    except (TypeError, ValueError):
        return (sal_row.get("ext_text") or "").strip()[:60]
    if lo_i and hi_i and hi_i != lo_i:
        return "$%d–%d/мес" % (lo_i, hi_i)
    return "$%d/мес" % (lo_i or hi_i)


def item_from_record(rec: dict, sal_row: dict | None) -> dict:
    item = {
        "title": (rec.get("title") or "").strip()[:120],
        "url": rec.get("url") or "",
        "source": rec.get("source") or "",
        "date": rec.get("date") or "",
        "category": rec.get("category") or "",
        "status": rec.get("status") or "",
    }
    if sal_row:
        item["salary"] = usd_hint(sal_row)
    return item


def collect_top(records: list[dict], salaries: dict) -> list[dict]:
    with_salary, rest = [], []
    for rec in records:
        if rec.get("status") not in ("perspective", "main"):
            continue
        row = salaries.get(str(rec.get("idx", "")))
        item = item_from_record(rec, row if row and row.get("has_salary") == "yes" else None)
        (with_salary if item.get("salary") else rest).append(item)

    def date_key(item: dict) -> str:
        return item.get("date") or "0000-00-00"

    with_salary.sort(key=date_key, reverse=True)
    rest.sort(key=date_key, reverse=True)
    return (with_salary + rest)[:TOP_BRIEF]


def load_olx() -> tuple[int, str, list[dict]]:
    if not OLX_PATH.exists():
        return 0, "", []
    data = json.loads(OLX_PATH.read_text(encoding="utf-8"))
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        items = []
    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    generated = str(meta.get("metrics", {}).get("generated_at") or "")[:10]
    priced = [i for i in items if isinstance(i, dict) and i.get("price") is not None]
    priced.sort(key=lambda i: i.get("price") or 0, reverse=True)
    top = [
        {
            "title": (i.get("title") or "").strip()[:100],
            "url": i.get("url") or "",
            "price": i.get("price_display") or "",
            "city": i.get("city") or "",
        }
        for i in priced[:TOP_OLX]
    ]
    return len(items), generated, top


def load_queue() -> list[dict]:
    if not QUEUE_PATH.exists():
        return []
    try:
        data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [
        {"title": (a.get("title") or "")[:120], "category": a.get("category") or "", "createdAt": a.get("createdAt") or ""}
        for a in data if isinstance(a, dict)
    ]


def build_digest() -> dict:
    board_meta, records = load_board()
    salaries, snap_dir = load_salary_map()
    status_counts = {"perspective": 0, "main": 0, "outset": 0}
    for rec in records:
        st = rec.get("status")
        if st in status_counts:
            status_counts[st] += 1
    salaries_count = sum(
        1 for rec in records if salaries.get(str(rec.get("idx", "")), {}).get("has_salary") == "yes"
    )
    olx_count, olx_generated, olx_top = load_olx()
    queue = load_queue()
    snapshot = snap_dir.name if snap_dir else ""

    headline = (
        "Доска: %d перспективных + %d основных (снимок %s); находок с вилкой: %d; "
        "OLX-находки: %d (%s); очередь поручений: %d."
        % (
            status_counts["perspective"], status_counts["main"], snapshot or "нет",
            salaries_count, olx_count, olx_generated or "—", len(queue),
        )
    )

    panel_rows = records
    observatory = {
        "salaries": [
            item_from_record(rec, salaries[str(rec["idx"])])
            for rec in panel_rows
            if salaries.get(str(rec.get("idx", "")), {}).get("has_salary") == "yes"
        ][:TOP_PANEL],
        "perspective": [
            item_from_record(rec, None)
            for rec in panel_rows
            if rec.get("status") == "perspective"
        ][:TOP_PANEL],
        "olx": olx_top,
        "queue": queue[:TOP_PANEL],
    }
    return {
        "generatedAt": now_iso(),
        "snapshot": snapshot,
        "boardUpdated": board_meta.get("updated_at") or "",
        "headline": headline,
        "counts": {
            **status_counts,
            "jobsTotal": len(records),
            "jobsWithSalary": salaries_count,
            "olxItems": olx_count,
            "queue": len(queue),
        },
        "top": collect_top(records, salaries),
        "observatory": observatory,
        "sources": {
            "board": "Workspace/analytics/orders_board.json",
            "snapshot": "Workspace/analytics/%s/jobs.csv" % snapshot if snapshot else "",
            "olx": "tools/olx_production_data.json",
            "queue": "%LOCALAPPDATA%/Platform/Hunter/assignments.json",
        },
    }


def main() -> int:
    digest = build_digest()
    DIGEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    DIGEST_PATH.write_text(json.dumps(digest, ensure_ascii=False, indent=1), encoding="utf-8")
    JS_PATH.write_text(JS_PREFIX + json.dumps(digest, ensure_ascii=False, indent=1) + ";", encoding="utf-8")
    print("[Hunter] digest written: %s" % DIGEST_PATH)
    print("[Hunter] dashboard payload: %s" % JS_PATH)
    print("[Hunter] " + digest["headline"])
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
