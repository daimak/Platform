# -*- coding: utf-8 -*-
"""Радар фидов обсуждений/новостей — поле зрения вокруг CVE-воронки vuln_radar.py
(KEV+EPSS+NVD дают CVE-ID; здесь — кто это обсуждает и о чём говорят).

Источники проверены вживую 07.11 (фактура: Workspace/intel/sources.md, «Обсуждения уязвимостей»):
  - HN Algolia (англ): треды по CVE за 24 ч
  - oss-security / openwall (англ): раскрытия и дискуссии исследователей
  - GitHub Security Advisories (англ): advisory + severity за 24 ч
  - SecurityLab RSS news (рус): ГОЧА — сайт за Qrator, curl/urllib = 403 (JS-челлендж),
    скрипт честно фиксирует отказ; живой путь = браузерный фетч
  - Habr хаб «Информационная безопасность» (рус)

Соглашения станции: stdlib only, запуск `python -I`, UTF-8. Кронов нет (Поводок).
Запуск: python -I tools/security/feeds_radar.py [--stdout-only]
Выход:  stdout (счётчики) + Workspace/intel/digests/scripts/out/feeds/ГГГГ-ММ-ДД.json
        + фрагмент Workspace/intel/digests/fragments/feeds-ГГГГ-ММ-ДД.md (секция 4 дайджеста).
"""
import argparse
import datetime as dt
import email.utils
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

UA = "platform-feeds-radar/0.1 (osint read-only)"
ROOT = pathlib.Path(__file__).resolve().parents[2]
DIGESTS = ROOT / "Workspace" / "intel" / "digests"
OUT = DIGESTS / "scripts" / "out" / "feeds"
FRAGMENTS = DIGESTS / "fragments"
TODAY = dt.date.today()
CUTOFF = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)


def fetch(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.getcode(), r.read(), None
    except urllib.error.HTTPError as e:
        return e.code, b"", f"HTTP {e.code}"
    except Exception as e:
        return None, b"", str(e)


def rss_items(raw: bytes):
    """(title, link, pubDate) из RSS; пойдёт и без namespace."""
    items = []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return None
    for it in root.iter("item"):
        get = lambda tag: (it.findtext(tag) or "").strip()
        items.append({"title": get("title"), "link": get("link"), "date": get("pubDate")})
    return items


def within_24(date_str: str) -> bool:
    if not date_str:
        return False
    try:
        d = email.utils.parsedate_to_datetime(date_str)
    except (TypeError, ValueError):
        return False
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d >= CUTOFF


def hn_cve():
    """HN Algolia: треды вокруг CVE за 24 ч. ГОЧА (09.11): query=CVE матчит и тексты
    комментариев к постам про AI/железо (110 хитов, шум) — фильтруем по заголовку
    локально; точные CVE-ID в заголовках за 24 ч обычно 0 (проверено: query=CVE-20 → 0)."""
    since = int(CUTOFF.timestamp())
    url = (f"https://hn.algolia.com/api/v1/search_by_date?query=CVE&tags=story"
           f"&numericFilters=created_at_i%3E{since}&hitsPerPage=100")
    code, raw, err = fetch(url)
    if err:
        return {"live": False, "http": code, "error": err}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"live": False, "http": code, "error": f"не JSON: {e}"}
    hits = data.get("hits") or []
    key = re.compile(r"cve-|security|vulnerab|exploit|breach|ransomware|malware|backdoor", re.I)
    rel = [h for h in hits if key.search(h.get("title") or "")]
    top = sorted(rel, key=lambda h: (h.get("points") or 0), reverse=True)[:3]
    return {
        "live": True, "http": code,
        "matched_raw": len(hits),
        "threads_24h": len(rel),
        "top": [{"title": (h.get("title") or "")[:90], "points": h.get("points") or 0,
                 "comments": h.get("num_comments") or 0} for h in top],
    }


def oss_security():
    """openwall: HTML-листинг тредов; считаем посты за 24 ч."""
    code, raw, err = fetch("https://www.openwall.com/lists/oss-security/", timeout=30)
    if err:
        return {"live": False, "http": code, "error": err}
    text = raw.decode("utf-8", "replace")
    # листинг: строки вида href="2026/11/08/...">тема</a>
    rows = re.findall(r'href="(\d{4}/\d{2}/\d{2})/[^"]*"[^>]*>([^<]+)</a>', text)
    fresh = [{"date": d.replace("/", "-"), "subject": s.strip()[:90]} for d, s in rows
             if d.replace("/", "-") >= CUTOFF.date().isoformat()]
    return {"live": True, "http": code, "threads_24h": len(fresh), "latest": fresh[:5],
            "parsed_rows": len(rows)}


def github_advisories():
    """GH Advisories за 24 ч: severity-разрез, критические отдельно."""
    since = CUTOFF.date().isoformat()
    url = f"https://api.github.com/advisories?published=%3E%3D{since}&per_page=50"
    code, raw, err = fetch(url, timeout=30)
    if err:
        return {"live": False, "http": code, "error": err}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"live": False, "http": code, "error": f"не JSON: {e}"}
    if not isinstance(data, list):
        return {"live": False, "http": code, "error": "ожидался список"}
    sev = {}
    for a in data:
        k = a.get("severity") or "н/д"
        sev[k] = sev.get(k, 0) + 1
    crit = [{"cve": a.get("cve_id") or a.get("ghsa_id"), "summary": (a.get("summary") or "")[:90]}
            for a in data if a.get("severity") in ("critical", "high")][:5]
    return {"live": True, "http": code, "advisories_24h": len(data), "severity": sev, "critical": crit}


def securitylab():
    """SecurityLab RSS news. Гоча: Qrator JS-челлендж — urllib ждёт 403, фиксируем честно."""
    code, raw, err = fetch("https://www.securitylab.ru/_Services/Export/RSS/news/", timeout=30)
    if err:
        return {"live": False, "http": code, "error": err + " (Qrator: живой путь — браузерный фетч)"}
    items = rss_items(raw)
    if items is None:
        return {"live": False, "http": code, "error": "не распарсился RSS"}
    fresh = [i for i in items if within_24(i["date"])]
    return {"live": True, "http": code, "items": len(items), "items_24h": len(fresh),
            "latest": [i["title"][:90] for i in fresh[:5]]}


def habr():
    """Habr RSS: сначала хаб «Информационная безопасность», фолбэк — новости."""
    for url in ("https://habr.com/ru/rss/hubs/infosecurity/articles/",
                "https://habr.com/ru/rss/news/"):
        code, raw, err = fetch(url, timeout=30)
        if err:
            continue
        items = rss_items(raw)
        if items is not None and items:
            fresh = [i for i in items if within_24(i["date"])]
            return {"live": True, "http": code, "url": url, "items": len(items),
                    "items_24h": len(fresh), "latest": [i["title"][:90] for i in fresh[:5]]}
    return {"live": False, "http": code, "error": "все RSS-эндпоинты не ответили"}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--stdout-only", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    FRAGMENTS.mkdir(parents=True, exist_ok=True)
    stamp = TODAY.isoformat()

    report = {"date": stamp, "cutoff": CUTOFF.isoformat(),
              "channels": {
                  "mon-hn-algolia": hn_cve(),
                  "mon-oss-security": oss_security(),
                  "mon-gh-advisories": github_advisories(),
                  "mon-securitylab": securitylab(),
                  "mon-habr-infosec": habr(),
              }}
    (OUT / f"{stamp}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    live = sum(1 for c in report["channels"].values() if c.get("live"))
    print(f"=== FEEDS RADAR, прогон {stamp} · живых каналов {live}/5 ===")
    for name, c in report["channels"].items():
        if not c.get("live"):
            print(f"{name}: НЕ СОБРАН (http={c.get('http')}, err={c.get('error')})")
        elif name == "mon-hn-algolia":
            print(f"HN: тредов по CVE за 24ч: {c['threads_24h']} · топ: " +
                  "; ".join(f"{t['title'][:50]} ({t['points']}★/{t['comments']}к)" for t in c["top"]))
        elif name == "mon-oss-security":
            print(f"oss-security: тредов за 24ч: {c['threads_24h']} (распознано строк {c['parsed_rows']})")
        elif name == "mon-gh-advisories":
            print(f"GH Advisories: за 24ч {c['advisories_24h']} · severity: {c['severity']}")
        else:
            print(f"{'SecurityLab' if 'securitylab' in name else 'Habr'}: items {c['items']}, за 24ч {c['items_24h']}")

    if args.stdout_only:
        return

    L = [f"### ИБ-фиды обсуждений (feeds_radar.py, прогон от {stamp} {dt.datetime.now():%H:%M})", ""]
    parts = [f"Счётчики: живых каналов {live}/5"]
    ch = report["channels"]
    if ch["mon-hn-algolia"]["live"]:
        parts.append(f"HN тредов по CVE за 24ч {ch['mon-hn-algolia']['threads_24h']}")
    if ch["mon-oss-security"]["live"]:
        parts.append(f"oss-security {ch['mon-oss-security']['threads_24h']}")
    if ch["mon-gh-advisories"]["live"]:
        gha = ch["mon-gh-advisories"]
        crit = gha["severity"].get("critical", 0) + gha["severity"].get("high", 0)
        parts.append(f"GH advisory {gha['advisories_24h']} (critical+high {crit})")
    if ch["mon-habr-infosec"]["live"]:
        parts.append(f"Habr {ch['mon-habr-infosec']['items_24h']}")
    if ch["mon-securitylab"]["live"]:
        parts.append(f"SecurityLab {ch['mon-securitylab']['items_24h']}")
    L += [" · ".join(parts), ""]
    for name, label in (("mon-hn-algolia", "HN топ"), ("mon-gh-advisories", "GH critical+high"),
                        ("mon-habr-infosec", "Habr"), ("mon-securitylab", "SecurityLab")):
        c = ch[name]
        if c.get("live") and c.get("latest"):
            L.append(f"{label}:")
            L += [f"- {t}" for t in c["latest"][:5]]
        elif not c.get("live"):
            L.append(f"{label}: не собран ({c.get('error')})")
    L += ["", "Δ к 08.11: база нет — первый прогон feeds_radar"]
    (FRAGMENTS / f"feeds-{stamp}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"фрагмент: {FRAGMENTS / f'feeds-{stamp}.md'}")


if __name__ == "__main__":
    main()
