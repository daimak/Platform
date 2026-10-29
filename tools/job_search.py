# -*- coding: utf-8 -*-
"""
Агрегатор поиска работы и фриланс-заказов (DevOps и смежные компетенции).

Источники:
  hh.uz / hh.ru  - HeadHunter API (вакансии, локальные и удалённые)
  RemoteOK       - международные remote-вакансии (публичное API)
  Remotive       - международные remote-вакансии (публичное API)
  Hacker News    - свежий тред "Ask HN: Who is hiring?" (поиск devops-комментариев)
  Telegram       - каналы с заказами/вакансиями через превью t.me/s/<канал>
  OLX.uz         - локальный раздел rabota

Запуск:
  python tools/job_search.py                # все источники
  python tools/job_search.py --source tg,hh # только выбранные
  python tools/job_search.py --q devops     # своя строка поиска (hh + olx)

Результат: дайджест в консоль + tools/job_search_results.json
"""
import argparse
import html
import json
import re
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Не хватает зависимостей. Установи:  pip install requests beautifulsoup4")
    sys.exit(1)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ------------------------- НАСТРОЙКИ (правь под себя) -------------------------

# Строки поиска для hh и OLX
QUERIES = ["DevOps", "SRE", "администратор Linux"]

# Хосты HeadHunter: hh.uz - Узбекистан, hh.ru - Россия/СНГ
HH_HOSTS = ["api.hh.uz", "api.hh.ru"]

# Telegram-каналы (проверены 2026-10-29, что живы). Добавляй свои - полный
# каталог каналов ищется на tgstat.ru по слову "devops" / "freelance".
TG_CHANNELS = [
    "devops_vacancies",
    "freelance_orders",
    "remote_jobs_ru",
    "jobs_in_uzbekistan",
    "kwork_orders",
]

# Ключевые слова-фильтр для TG, RemoteOK, Remotive, HN.
# Компетенции - расширяй свободно, сравнение без учёта регистра.
KEYWORDS = [
    "devops", "sre", "linux", "kubernetes", "k8s", "docker", "ansible",
    "terraform", "ci/cd", "jenkins", "gitlab", "nginx", "prometheus",
    "grafana", "zabbix", "monitoring", "python", "sysadmin", "dba",
    "postgres", "llm", "ai engineer", "машинное обучение",
    "системный администратор", "администратор", "настройк", "сервер",
]

MAX_PER_SOURCE_IN_DIGEST = 5   # сколько строк каждого источника печатать
MAX_SNIPPET = 220              # длина сниппета в выдаче

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# ------------------------------------------------------------------------------


def fetch_hh(host, query):
    """Вакансии HeadHunter через публичное API (без ключа)."""
    url = f"https://{host}/vacancies?text={quote(query)}&per_page=20&order_by=publication_time"
    r = requests.get(url, headers={**UA, "HH-User-Agent": "job-search-aggregator"}, timeout=15)
    r.raise_for_status()
    out = []
    for it in r.json().get("items", []):
        snip = it.get("snippet") or {}
        text = snip.get("requirement") or snip.get("responsibility") or ""
        salary = it.get("salary")
        sal = ""
        if salary:
            lo, hi, cur = salary.get("from"), salary.get("to"), salary.get("currency")
            if lo and hi:
                sal = f"{lo}-{hi} {cur}"
            elif lo or hi:
                sal = f"{lo or ''}{'-' if lo and hi else ''}{hi or ''} {cur}".strip()
        out.append({
            "source": f"hh ({host})",
            "title": it.get("name") or "",
            "company": (it.get("employer") or {}).get("name") or "",
            "location": (it.get("area") or {}).get("name") or "",
            "salary": sal,
            "date": it.get("published_at") or "",
            "url": it.get("alternate_url") or "",
            "snippet": re.sub(r"<[^>]+>", " ", text).strip()[:MAX_SNIPPET],
        })
    return out


def fetch_hh_html(host, query):
    """Резерв HH: скрап HTML-выдачи, когда API отдаёт 403 (блок по IP)."""
    r = requests.get(f"https://{host}/search/vacancy?text={quote(query)}", headers=UA, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for card in soup.select('article[data-qa*="vacancy-serp__vacancy"]'):
        title_el = card.select_one('a[data-qa="serp-item__title"]')
        if not title_el:
            continue
        emp = card.select_one('[data-qa="vacancy-serp__vacancy-employer"]')
        addr = card.select_one('[data-qa="vacancy-serp__vacancy-address"]')
        sal = card.select_one('[data-qa="serp-item__compensation"], [data-qa="vacancy-serp__vacancy-compensation"]')
        remote = card.select_one('[data-qa="vacancy-label-work-schedule-remote"]')
        href = title_el.get("href", "")
        loc = addr.get_text(" ", strip=True) if addr else ""
        if remote:
            loc = (loc + " / remote").strip(" /")
        out.append({
            "source": f"hh ({host}, html)",
            "title": title_el.get_text(" ", strip=True),
            "company": emp.get_text(" ", strip=True) if emp else "",
            "location": loc,
            "salary": sal.get_text(" ", strip=True) if sal else "",
            "date": "",
            "url": href if href.startswith("http") else f"https://{host}{href}",
            "snippet": "",
        })
    return out


def fetch_remoteok():
    """Публичное API remoteok.com. Первый элемент массива - легальная плашка, пропускаем."""
    r = requests.get("https://remoteok.com/api", headers=UA, timeout=15)
    r.raise_for_status()
    out = []
    for job in r.json():
        if not isinstance(job, dict) or not job.get("position"):
            continue
        hay = (job.get("position", "") + " " + " ".join(job.get("tags") or [])).lower()
        if not any(kw in hay for kw in KEYWORDS):
            continue
        out.append({
            "source": "RemoteOK",
            "title": job.get("position") or "",
            "company": job.get("company") or "",
            "location": job.get("location") or "remote",
            "salary": _salary_range(job.get("salary_min"), job.get("salary_max"), "USD"),
            "date": job.get("date") or "",
            "url": job.get("url") or "",
            "snippet": "tags: " + ", ".join((job.get("tags") or [])[:8]),
        })
    return out


def fetch_remotive():
    """Публичное API remotive.com."""
    r = requests.get("https://remotive.com/api/remote-jobs?limit=100", headers=UA, timeout=15)
    r.raise_for_status()
    out = []
    for job in r.json().get("jobs", []):
        hay = (job.get("title", "") + " " + " ".join(job.get("tags") or [])).lower()
        if not any(kw in hay for kw in KEYWORDS):
            continue
        out.append({
            "source": "Remotive",
            "title": job.get("title") or "",
            "company": job.get("company_name") or "",
            "location": job.get("candidate_required_location") or "remote",
            "salary": job.get("salary") or "",
            "date": job.get("publication_date") or "",
            "url": job.get("url") or "",
            "snippet": (job.get("title") or "") + " | tags: " + ", ".join((job.get("tags") or [])[:8]),
        })
    return out


def fetch_hn():
    """Свежий тред 'Ask HN: Who is hiring?' - комментарии по devops-запросам."""
    r = requests.get("https://hn.algolia.com/api/v1/search_by_date"
                     "?query=%22who%20is%20hiring%22&tags=ask_hn&hitsPerPage=1", timeout=15)
    r.raise_for_status()
    hits = r.json().get("hits", [])
    if not hits:
        return []
    story_id = hits[0]["objectID"]
    thread = hits[0].get("title", "")
    out, seen = [], set()
    for q in ["devops", "kubernetes", "linux"]:
        cr = requests.get(f"https://hn.algolia.com/api/v1/search"
                          f"?tags=comment,story_{story_id}&query={quote(q)}&hitsPerPage=15", timeout=15)
        cr.raise_for_status()
        for c in cr.json().get("hits", []):
            oid = c.get("objectID")
            if not oid or oid in seen:
                continue
            seen.add(oid)
            text = html.unescape(re.sub(r"<[^>]+>", " ", c.get("comment_text") or ""))
            out.append({
                "source": f"HN ({thread[:40]})",
                "title": thread,
                "company": c.get("author") or "",
                "location": "remote/HN",
                "salary": "",
                "date": c.get("created_at") or "",
                "url": f"https://news.ycombinator.com/item?id={oid}",
                "snippet": " ".join(text.split())[:MAX_SNIPPET],
            })
    return out


def fetch_telegram(channel):
    """Посты канала через веб-превью t.me/s/<channel> (без API и авторизации)."""
    r = requests.get(f"https://t.me/s/{channel}", headers=UA, timeout=15)
    if r.status_code != 200 or "tgme_widget_message" not in r.text:
        print(f"  [skip] t.me/{channel} недоступен или не существует")
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for msg in soup.select(".tgme_widget_message"):
        body = msg.select_one(".tgme_widget_message_text")
        if not body:
            continue
        text = body.get_text(" ", strip=True)
        if not any(kw in text.lower() for kw in KEYWORDS):
            continue
        post = msg.get("data-post") or f"{channel}/0"
        t = msg.find("time")
        out.append({
            "source": f"Telegram @{channel}",
            "title": text.split("\n")[0][:90],
            "company": f"t.me/{channel}",
            "location": "",
            "salary": "",
            "date": t["datetime"] if t and t.has_attr("datetime") else "",
            "url": f"https://t.me/{post}",
            "snippet": text[:MAX_SNIPPET * 2],
        })
    return out


def fetch_olx(query):
    """Локальные объявления OLX.uz в разделе rabota (карточки l-card, заголовок h4)."""
    r = requests.get(f"https://www.olx.uz/rabota/q-{quote(query)}/", headers=UA, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # OLX fuzzy-поиск подмешивает шум (железо, недвижимость) - оставляем похожее на работу/заказ
    job_words = ("devops", "sre", "linux", "админ", "admin", "сервер", "server", "python",
                 "developer", "разработ", "программист", "инженер", "engineer", "ваканси",
                 "работ", "требуется", "ищем", "ищу", "freelance", "заказ", "бот", "bot",
                 "сайт", "webapp", "backend", "frontend", "kubernetes", "docker", "настрой")
    out = []
    for card in soup.select('div[data-cy="l-card"]'):
        title_el = card.select_one("h4") or card.select_one("[data-testid='ad-card-title']")
        link_el = card.select_one("a[href]")
        if not title_el or not link_el:
            continue
        title = title_el.get_text(" ", strip=True)
        if not any(w in title.lower() for w in job_words):
            continue
        price_el = card.select_one("[data-testid='ad-price']")
        href = link_el["href"]
        out.append({
            "source": "OLX.uz",
            "title": title,
            "company": "",
            "location": "UZ",
            "salary": price_el.get_text(strip=True) if price_el else "",
            "date": "",
            "url": "https://www.olx.uz" + href if href.startswith("/") else href,
            "snippet": "",
        })
    return out


def fetch_flru():
    """Живые заказы FL.ru (лента /projects/, фильтр по IT/DevOps-ключевым словам)."""
    r = requests.get("https://www.fl.ru/projects/", headers={**UA, "Accept-Language": "ru,en;q=0.9"}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Помимо общих KEYWORDS - широкий IT-набор: лента FL.ru межотраслевая
    it_words = KEYWORDS + ["сайт", "парс", "интеграц", "api", "скрипт",
                           "android", "ios", "1с", "crm", "панел", "настро"]
    out = []
    for card in soup.select('div.b-post[id^="project-item"]'):
        a = card.select_one("h2 a, .b-post__title a")
        if not a or not a.get("href"):
            continue
        title = a.get_text(" ", strip=True)
        title_lower = title.lower()
        # "бот" только с границы слова: иначе матчится в "разрабоТка"
        if not (any(w in title_lower for w in it_words) or re.search(r"\bбот", title_lower)):
            continue
        price_el = card.select_one("[class*=price], [class*=budget]")
        href = a["href"]
        out.append({
            "source": "FL.ru",
            "title": title,
            "company": "fl.ru",
            "location": "",
            "salary": price_el.get_text(" ", strip=True) if price_el else "",
            "date": "",
            "url": "https://www.fl.ru" + href if href.startswith("/") else href,
            "snippet": "",
        })
    return out


def _salary_range(lo, hi, cur):
    if not lo and not hi:
        return ""
    if lo and hi:
        return f"{lo}-{hi} {cur}"
    return f"{lo or hi} {cur}"


def parse_date(s):
    """Дата в UTC для сортировки; нераспознанные уходят в конец."""
    if not s:
        return datetime.min.replace(tzinfo=timezone.utc)
    for parser in (
        lambda x: datetime.fromisoformat(x.replace("Z", "+00:00")),
        lambda x: parsedate_to_datetime(x),
    ):
        try:
            return parser(s).astimezone(timezone.utc)
        except (ValueError, TypeError):
            continue
    return datetime.min.replace(tzinfo=timezone.utc)


def safe(name, fn):
    try:
        return fn()
    except Exception as e:
        print(f"  [warn] {name}: {type(e).__name__}: {str(e)[:120]}")
        return []


def main():
    ap = argparse.ArgumentParser(description="Агрегатор вакансий/фриланса")
    ap.add_argument("--source", default="hh,remoteok,remotive,hn,tg,olx,flru",
                    help="источники через запятую: hh,remoteok,remotive,hn,tg,olx")
    ap.add_argument("--q", default=None, help="своё ключевое слово вместо QUERIES (hh + olx)")
    ap.add_argument("--json", default="job_search_results.json", help="путь к выгрузке")
    ap.add_argument("--js", default=None, help="куда записать vacancies.js для дашборда eVo")
    args = ap.parse_args()

    queries = [args.q] if args.q else QUERIES
    enabled = {s.strip() for s in args.source.split(",")}
    results = []

    if "hh" in enabled:
        for host in HH_HOSTS:
            html_host = host.replace("api.", "", 1)  # выдача живёт на hh.uz, не на api.hh.uz
            for q in queries:
                got = safe(f"hh {host} '{q}'", lambda h=host, qq=q: fetch_hh(h, qq))
                if not got:
                    # API заблокирован (403 с датацентрового IP) - берём HTML-выдачу
                    got = safe(f"hh-html {html_host} '{q}'", lambda h=html_host, qq=q: fetch_hh_html(h, qq))
                results += got
    if "remoteok" in enabled:
        results += safe("remoteok", fetch_remoteok)
    if "remotive" in enabled:
        results += safe("remotive", fetch_remotive)
    if "hn" in enabled:
        results += safe("hackernews", fetch_hn)
    if "tg" in enabled:
        for ch in TG_CHANNELS:
            results += safe(f"telegram @{ch}", lambda c=ch: fetch_telegram(c))
            time.sleep(0.3)
    if "olx" in enabled:
        for q in queries[:2]:
            results += safe(f"olx.uz '{q}'", lambda qq=q: fetch_olx(qq))
    if "flru" in enabled:
        results += safe("fl.ru", fetch_flru)

    # дедуп по URL
    seen, unique = set(), []
    for job in sorted(results, key=lambda j: parse_date(j["date"]), reverse=True):
        if job["url"] and job["url"] not in seen:
            seen.add(job["url"])
            unique.append(job)

    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    # выгрузка для дашборда eVo (подключается как <script src="vacancies.js">)
    if args.js:
        # FL.ru - заказы, а не вакансии: в дашборде идут в раздел "Фриланс-биржи"
        flru = [j for j in unique if j["source"] == "FL.ru"]
        jobs_dash = [j for j in unique if j["source"] != "FL.ru"][:60]
        js_data = {
            "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "total": len(jobs_dash) + len(flru),
            "jobs": jobs_dash,
            "freelance": {"flru": flru[:40]},
        }
        with open(args.js, "w", encoding="utf-8") as f:
            f.write("/* Автогенерация tools/job_search.py --js. Не править руками. */\nconst EVO_VACANCIES = ")
            json.dump(js_data, f, ensure_ascii=False, indent=2)
            f.write(";\n")
        print(f"Выгрузка для дашборда: {args.js}")

    # дайджест по источникам
    by_source = {}
    for job in unique:
        by_source.setdefault(job["source"].split(" (")[0], []).append(job)
    print(f"\n=== Дайджест: {len(unique)} позиций (полный список в {args.json}) ===")
    for src, jobs in by_source.items():
        print(f"\n--- {src}: {len(jobs)} ---")
        for job in jobs[:MAX_PER_SOURCE_IN_DIGEST]:
            meta = " | ".join(x for x in (job["company"], job["location"], job["salary"]) if x)
            line = f"  {job['title'][:80]}" + (f"  [{meta}]" if meta else "")
            print(line)
            if job["snippet"]:
                print(f"      {job['snippet'][:140]}")


if __name__ == "__main__":
    main()
