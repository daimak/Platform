#!/usr/bin/env python3
"""Радар уязвимостей: KEV (факт эксплуатации) + EPSS (вероятность) + NVD (свежие критические).

Один пассивный прогон: наружу — только GET к публичным фидам, данные платформы не уходят.
Приоритизация — воронкой: КЕВ-эксплуатация > EPSS >= 25% > CVSS 9+.
EUVD (ENISA) подключается позже — публичное API не документировано, см. tools/security/README.md.
"""

import argparse
import json
import sys
import urllib.parse
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    REPORTS_DIR,
    fetch_json,
    now_iso,
    print_summary,
    save_report,
)

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
EPSS_URL = "https://api.first.org/data/v1/epss"
KEV_CACHE = REPORTS_DIR / "cache-kev.json"


def load_kev() -> tuple[dict, str]:
    """KEV-каталог с суточным кэшем на диске. Возвращает (каталог, статус)."""
    if KEV_CACHE.exists():
        age_hours = (now_epoch_min() - KEV_CACHE.stat().st_mtime) / 3600
        if age_hours < 12:
            return json.loads(KEV_CACHE.read_text(encoding="utf-8")), "кэш"
    data = fetch_json(KEV_URL, timeout=60)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    KEV_CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data, "свежая загрузка"


def now_epoch_min() -> float:
    import time

    return time.time()


def fetch_nvd_critical(days: int) -> tuple[list, int]:
    """Критические CVE, опубликованные за последние N дней (API 2.0, без ключа)."""
    from datetime import datetime, timezone

    end = datetime.now(timezone(timedelta(hours=5), "Tashkent"))
    start = end - timedelta(days=days)
    params = urllib.parse.urlencode(
        {
            "pubStartDate": start.strftime("%Y-%m-%dT00:00:00.000%z")[:-2] + ":00",
            "pubEndDate": end.strftime("%Y-%m-%dT%H:%M:%S.000") + "+05:00",
            "cvssV3Severity": "CRITICAL",
            "resultsPerPage": 50,
        }
    )
    data = fetch_json(f"{NVD_URL}?{params}", timeout=60)
    items = []
    for wrapper in data.get("vulnerabilities", []):
        cve = wrapper.get("cve", {})
        metrics = cve.get("metrics", {})
        score = None
        for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            block = metrics.get(key) or []
            if block:
                score = block[0].get("cvssData", {}).get("baseScore")
                break
        descriptions = cve.get("descriptions", [])
        text = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")
        items.append({"cve": cve.get("id"), "published": cve.get("published"), "cvss": score, "desc": text})
    return items, int(data.get("totalResults", len(items)))


def fetch_epss(cves: list) -> dict:
    """EPSS-баллы пачками по 90 CVE. Возвращает {cve: (score, percentile)}."""
    result = {}
    for i in range(0, len(cves), 90):
        chunk = ",".join(cves[i : i + 90])
        try:
            data = fetch_json(f"{EPSS_URL}?cve={urllib.parse.quote(chunk)}", timeout=30)
            for row in data.get("data", []):
                result[row["cve"]] = (float(row.get("epss", 0)), row.get("percentile"))
        except Exception:
            continue
    return result


def build_radar(days: int, keywords: list, limit: int) -> dict:
    sources = {"kev": {"ok": False}, "nvd": {"ok": False}, "epss": {"ok": False}}
    items = []

    kev_new = []
    try:
        kev, kev_status = load_kev()
        sources["kev"] = {"ok": True, "count": int(kev.get("count", 0)), "status": kev_status}
        cutoff = (now_iso()[:10])
        from datetime import date

        border = str(date.today() - timedelta(days=days))
        for entry in kev.get("vulnerabilities", []):
            if str(entry.get("dateAdded", "")) >= border:
                kev_new.append(entry)
    except Exception as error:
        sources["kev"] = {"ok": False, "error": str(error)[:200]}

    nvd_items, nvd_total = [], 0
    try:
        nvd_items, nvd_total = fetch_nvd_critical(days)
        sources["nvd"] = {"ok": True, "total_critical": nvd_total, "fetched": len(nvd_items)}
    except Exception as error:
        sources["nvd"] = {"ok": False, "error": str(error)[:200]}

    cve_ids = [e.get("cveID") for e in kev_new] + [i.get("cve") for i in nvd_items]
    epss = fetch_epss([c for c in cve_ids if c]) if cve_ids else {}
    if epss:
        sources["epss"] = {"ok": True, "matched": len(epss)}

    for entry in kev_new:
        cve = entry.get("cveID")
        score = epss.get(cve, (None, None))[0]
        items.append(
            {
                "cve": cve,
                "title": entry.get("vulnerabilityName", ""),
                "vendor": entry.get("vendorProject", ""),
                "product": entry.get("product", ""),
                "kev": True,
                "epss": score,
                "cvss": None,
                "date": entry.get("dateAdded"),
                "ransomware": entry.get("knownRansomwareCampaignUse") == "Known",
                "severity": "red",
            }
        )
    for item in nvd_items:
        cve = item.get("cve")
        score = epss.get(cve, (None, None))[0]
        if score is not None and score >= 0.25:
            severity = "red"
        elif score is not None and score >= 0.10:
            severity = "orange"
        else:
            severity = "yellow"
        items.append(
            {
                "cve": cve,
                "title": (item.get("desc") or "")[:140],
                "vendor": "",
                "product": "",
                "kev": False,
                "epss": score,
                "cvss": item.get("cvss"),
                "date": (item.get("published") or "")[:10],
                "ransomware": False,
                "severity": severity,
            }
        )

    if keywords:
        lowered = [k.strip().lower() for k in keywords if k.strip()]
        items = [
            i
            for i in items
            if any(
                k in (i["title"] or "").lower()
                or k in (i["vendor"] or "").lower()
                or k in (i["product"] or "").lower()
                for k in lowered
            )
        ]

    order = {"red": 0, "orange": 1, "yellow": 2}
    items.sort(key=lambda i: (order[i["severity"]], -(i["epss"] or 0), -(i["cvss"] or 0)))
    shown = items[:limit]
    counts = {
        "red": sum(1 for i in items if i["severity"] == "red"),
        "orange": sum(1 for i in items if i["severity"] == "orange"),
        "yellow": sum(1 for i in items if i["severity"] == "yellow"),
        "total": len(items),
    }
    return {
        "tool": "vuln-radar",
        "generated": now_iso(),
        "days": days,
        "keywords": keywords,
        "sources": sources,
        "counts": counts,
        "items": shown,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Радар уязвимостей (KEV+EPSS+NVD)")
    parser.add_argument("--days", type=int, default=7, help="окно, дней (по умолчанию 7)")
    parser.add_argument("--keywords", default="", help="фильтр продуктов через запятую: windows,vmware,docker")
    parser.add_argument("--limit", type=int, default=25, help="сколько позиций в отчёте")
    args = parser.parse_args()
    keywords = [k for k in args.keywords.split(",") if k.strip()] if args.keywords else []

    radar = build_radar(args.days, keywords, args.limit)
    path = save_report("vuln-radar", radar)
    counts = radar["counts"]
    lines = [
        f"Радар уязвимостей: окно {args.days} дн., источники "
        f"KEV={'ок' if radar['sources']['kev']['ok'] else 'НЕДОСТУПЕН'}, "
        f"NVD={'ок' if radar['sources']['nvd']['ok'] else 'НЕДОСТУПЕН'}, "
        f"EPSS={'ок' if radar['sources']['epss']['ok'] else 'нет совпадений'}",
        f"Всего: {counts['total']} — красных {counts['red']}, оранжевых {counts['orange']}, жёлтых {counts['yellow']}",
    ]
    for item in radar["items"][:10]:
        epss = f"EPSS {round(item['epss'] * 100)}%" if item["epss"] is not None else "EPSS —"
        cvss = f"CVSS {item['cvss']}" if item["cvss"] else "CVSS —"
        flags = ("KEV" if item["kev"] else "") + ("+ransomware" if item["ransomware"] else "")
        lines.append(f"[{item['severity'].upper():6}] {item['cve']}  {epss}  {cvss}  {flags}  {item['title'][:70]}")
    lines.append(f"Отчёт: {path.name} ({path.parent})")
    print_summary(lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
