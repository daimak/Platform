#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""olx_production.py — продакшен-парсер объявлений OLX.uz.

Отличие от tools/autoservices_search.py (референс, не редактируется):
  1. Основная стратегия цены — встроенное состояние страницы
     window.__PRERENDERED_STATE__ (JSON со всеми полями объявления, включая
     price.regularPrice и salary), а не обход HTML-карточек.
  2. Фолбэки: HTML-карточки div[data-cy="l-card"] и JSON-LD Product на
     детальной странице (--enrich-details N).
  3. CLI (--query/--category/--pages/--min-price/--max-price/--out),
     дедупликация по листинг-id/URL, вывод одновременно JSON и CSV,
     метрики покрытия, ретраи и вежливые паузы 1.5–3 с.

Правила вежливости: пауза 1.5–3 с между запросами, максимум 4 страницы
на категорию/запрос за прогон (жёсткий потолок --pages).

Зависимости: requests, beautifulsoup4 (pip install requests beautifulsoup4).
Запуск: python tools/olx_production.py --query avtoservis --pages 2 --out olx_run
"""

import argparse
import csv
import json
import random
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.olx.uz"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"}

MAX_PAGES_PER_TARGET = 4     # жёсткий потолок страниц на категорию/запрос
MAX_ENRICH_DETAILS = 15      # потолок детальных запросов за прогон
RETRY_BACKOFF_SEC = 2.0

CSV_COLUMNS = [
    "id", "url", "title", "price", "currency", "negotiable",
    "salary_from", "salary_to", "salary_currency", "salary_period",
    "city", "district", "region", "date", "is_job", "is_business",
    "category_id", "category_type", "price_source", "source", "page",
]


def log(msg):
    """Лог в stderr с таймстампом; stdout оставлен для итогов и путей."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def polite_sleep(delay_min, delay_max):
    time.sleep(random.uniform(delay_min, delay_max))


# --------------------------------------------------------------------------
# HTTP-слой: ретрай 1 раз, дальше честный пропуск с логом
# --------------------------------------------------------------------------

def fetch(url, session, timeout, retries=1):
    """GET с одним ретраем на сетевые ошибки/таймаут/5xx/429.

    Возвращает Response или None (после исчерпания ретраев или на
    постоянных ошибках вроде 404).
    """
    last_err = None
    for attempt in range(1 + retries):
        if attempt:
            log(f"  ретрай {attempt}/{retries}: {url}")
            time.sleep(RETRY_BACKOFF_SEC)
        try:
            resp = session.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code >= 500 or resp.status_code == 429:
                last_err = f"HTTP {resp.status_code}"
                continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_err = str(exc)[:160]
            if isinstance(exc, requests.HTTPError) and exc.response is not None \
                    and exc.response.status_code < 500 and exc.response.status_code != 429:
                break  # 404/403 и т.п. — ретраить бессмысленно
    log(f"  ПРОПУСК (не скачался, последняя ошибка: {last_err}): {url}")
    return None


# --------------------------------------------------------------------------
# Стратегия A: window.__PRERENDERED_STATE__ (основной источник полей)
# --------------------------------------------------------------------------

def extract_state(html):
    """Достаёт и распарсивает __PRERENDERED_STATE__ (строка в строке JSON)."""
    m = re.search(r'window\.__PRERENDERED_STATE__\s*=\s*', html)
    if not m:
        return None
    pos = m.end()
    while pos < len(html) and html[pos] in " \t\r\n":
        pos += 1
    if pos >= len(html) or html[pos] != '"':
        return None
    try:
        outer, _ = json.JSONDecoder().raw_decode(html, pos)  # целиком, с экранированием
    except ValueError:
        return None
    try:
        return json.loads(outer)
    except ValueError:
        pass
    try:  # на случай, если когда-нибудь отдают сырой JSON без двойной кодировки
        return json.loads(outer if isinstance(outer, dict) else html[pos:])
    except ValueError:
        return None


def parse_state_listing(lst, source, page):
    ads = []
    for a in (lst.get("ads") or []):
        if not isinstance(a, dict):
            continue
        price = a.get("price") or {}
        reg = price.get("regularPrice") or {}
        sal = a.get("salary") or {}
        loc = a.get("location") or {}
        cat = a.get("category") or {}
        url = a.get("url") or urljoin(BASE, a.get("urlPath") or "")
        ads.append({
            "id": a.get("id"),
            "url": url,
            "title": (a.get("title") or "").strip(),
            "price": reg.get("value"),
            "currency": reg.get("currencyCode"),
            "negotiable": bool(reg.get("negotiable")),
            "price_display": price.get("displayValue") or "",
            "salary_from": sal.get("from"),
            "salary_to": sal.get("to"),
            "salary_currency": sal.get("currencyCode"),
            "salary_period": sal.get("period"),
            "city": loc.get("cityName") or "",
            "district": loc.get("districtName") or "",
            "region": loc.get("regionName") or "",
            "date": a.get("createdTime") or "",
            "is_job": bool(a.get("isJob")),
            "is_business": bool(a.get("isBusiness")),
            "category_id": cat.get("id"),
            "category_type": cat.get("type") or "",
            "price_source": "state" if (reg.get("value") is not None) else (
                "state_salary" if sal else ""),
            "source": source,
            "page": page,
        })
    return ads, (lst.get("totalElements"), lst.get("totalPages"))


# --------------------------------------------------------------------------
# Стратегия B: фолбэк по HTML-карточкам div[data-cy="l-card"]
# --------------------------------------------------------------------------

def parse_price_text(text):
    """'95 834 сумДоговорная' -> (95834, negotiable=True); 'Бесплатно' -> (0, False)."""
    if not text:
        return None, False
    low = text.lower()
    if "бесплатно" in low or "bepul" in low:
        return 0, False
    negotiable = "договорная" in low or "kelishilgan" in low or "kelishamiz" in low
    mm = re.search(r"[\d\s\u00a0\u202f]+", text)
    if not mm:
        return None, negotiable
    digits = re.sub(r"\D", "", mm.group(0))
    return (int(digits) if digits else None), negotiable


def parse_cards(html, source, page):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", attrs={"data-cy": "l-card"}) or \
        soup.find_all("div", attrs={"data-testid": "l-card"})
    ads = []
    for card in cards:
        rec = {"price": None, "currency": None, "negotiable": False,
               "price_display": "", "salary_from": None, "salary_to": None,
               "salary_currency": None, "salary_period": None,
               "city": "", "district": "", "region": "", "date": "",
               "is_job": False, "is_business": False,
               "category_id": None, "category_type": "",
               "price_source": "", "source": source, "page": page}
        raw_id = card.get("id") or ""
        rec["id"] = int(raw_id) if raw_id.isdigit() else None
        a = card.find("a", href=True)
        href = a["href"] if a else ""
        rec["url"] = urljoin(BASE, href) if href else ""
        title_el = card.find("h6") or card.find("h4") or \
            card.find("div", class_=re.compile(r"title"))
        rec["title"] = title_el.get_text(strip=True) if title_el else ""
        price_el = card.find(attrs={"data-testid": "ad-price"})
        if price_el:
            text = price_el.get_text(" ", strip=True)
            rec["price_display"] = text
            value, negotiable = parse_price_text(text)
            rec["price"] = value
            rec["negotiable"] = negotiable
            rec["price_source"] = "card_html" if value is not None else ""
        loc_el = card.find(attrs={"data-testid": "location-date"})
        if loc_el:
            text = loc_el.get_text(" ", strip=True)
            if " - " in text:
                place, _, when = text.partition(" - ")
                rec["date"] = when.strip()
                place = place.strip()
            else:
                place = text
            parts = [p.strip() for p in place.split(",") if p.strip()]
            if len(parts) >= 1:
                rec["city"] = parts[0]
            if len(parts) >= 2:
                rec["district"] = parts[1]
        ads.append(rec)
    return ads


# --------------------------------------------------------------------------
# Стратегия C: JSON-LD Product на детальной странице (--enrich-details)
# --------------------------------------------------------------------------

def jsonld_price_from_html(html):
    for block in re.findall(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            html, re.S):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") == "Product":
                offer = item.get("offers") or {}
                val = offer.get("price")
                if isinstance(val, (int, float)):
                    return int(val), offer.get("priceCurrency"), "jsonld"
    return None, None, ""


def enrich_details(ads, session, timeout, budget, delay_min, delay_max):
    """Добирает цену по JSON-LD детальных страниц для объявлений без цены.

    Возвращает, сколько цен реально добрано (зарплатные job-объявления
    не тратят бюджет: у них цена и так есть — зарплата).
    """
    if budget <= 0:
        return 0
    fetched = recovered = 0
    for rec in ads:
        if fetched >= min(budget, MAX_ENRICH_DETAILS):
            break
        if rec["price"] is not None or rec.get("salary_from") is not None:
            continue
        if not rec["url"]:
            continue
        fetched += 1
        polite_sleep(delay_min, delay_max)
        log(f"  детальная (JSON-LD) {fetched}: {rec['url']}")
        resp = fetch(rec["url"], session, timeout)
        if resp is None:
            continue
        value, currency, src = jsonld_price_from_html(resp.text)
        if value is not None:
            rec["price"], rec["currency"], rec["price_source"] = value, currency, src
            recovered += 1
    return recovered


# --------------------------------------------------------------------------
# Сборка прогона: стратегии, дедуп, фильтр цены
# --------------------------------------------------------------------------

def listing_url(target, page, kind="query"):
    """URL листинга для запроса/категории и номера страницы."""
    if target.startswith("http://") or target.startswith("https://"):
        base_url = target
    elif kind == "category":
        base_url = f"{BASE}/{target.strip('/')}/"
    else:
        base_url = f"{BASE}/list/q-{quote(target, safe='')}/"
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}page={page}" if page > 1 else base_url


def merge_records(state_ads, card_ads):
    """State — приоритет; карточки добавляют только те id/URL, которых нет в state."""
    by_key = {}
    for rec in state_ads:
        key = ("id", rec["id"]) if rec["id"] else ("url", rec["url"])
        by_key[key] = rec
    merged_extra = 0
    out = list(state_ads)
    for rec in card_ads:
        key = ("id", rec["id"]) if rec["id"] else ("url", rec["url"])
        if key not in by_key:
            by_key[key] = rec
            out.append(rec)
            merged_extra += 1
    return out, merged_extra


def dedup(records):
    seen, unique, dup = set(), [], 0
    for rec in records:
        key = ("id", rec["id"]) if rec.get("id") else ("url", rec.get("url", ""))
        if key in seen:
            dup += 1
            continue
        seen.add(key)
        unique.append(rec)
    return unique, dup


def has_any_price(rec):
    return rec.get("price") is not None or rec.get("salary_from") is not None


def price_filter_match(rec, min_price, max_price):
    """Фильтр по цене: числовая цена в диапазоне ИЛИ пересечение с вилкой зарплаты.

    Объявления без числового показателя отсекаются, если фильтр задан.
    """
    if min_price is None and max_price is None:
        return True
    value = rec.get("price")
    if value is not None:
        if min_price is not None and value < min_price:
            return False
        if max_price is not None and value > max_price:
            return False
        return True
    s_from, s_to = rec.get("salary_from"), rec.get("salary_to")
    if s_from is not None or s_to is not None:
        lo = s_from if s_from is not None else s_to
        hi = s_to if s_to is not None else s_from
        if min_price is not None and (hi is None or hi < min_price):
            return False
        if max_price is not None and (lo is None or lo > max_price):
            return False
        return True
    return False


def run_target(target, kind, pages, args, session, metrics):
    """Прогон по одному запросу/категории; возвращает уникальные записи."""
    pages = min(pages, MAX_PAGES_PER_TARGET)
    if args.pages > MAX_PAGES_PER_TARGET:
        log(f"{kind}:{target}: --pages ограничен потолком {MAX_PAGES_PER_TARGET} "
            f"(правила вежливости)")
    all_records, state_total, errors, markup_misses = [], None, 0, 0
    fetched_pages, first_ids, pagination_broken = 0, None, False
    for page in range(1, pages + 1):
        if pagination_broken:
            log(f"  стр.{page} пропущена: URL не пагинируется через ?page= "
                f"(сервер отдаёт страницу 1)")
            continue
        url = listing_url(target, page, kind)
        polite_sleep(args.delay_min, args.delay_max) if page > 1 else None
        log(f"{kind}:{target} стр.{page}/{pages}: {url}")
        resp = fetch(url, session, args.timeout)
        if resp is None:
            errors += 1
            metrics["pages_failed"] += 1
            continue
        metrics["pages_ok"] += 1
        page_state_ads, page_card_ads, totals = [], [], None
        state = extract_state(resp.text)
        if state:
            lst = (state.get("listing") or {}).get("listing") or {}
            page_state_ads, totals = parse_state_listing(lst, f"{kind}:{target}", page)
        if not page_state_ads:
            page_card_ads = parse_cards(resp.text, f"{kind}:{target}", page)
            if not page_card_ads:
                markup_misses += 1
                log(f"  ВНИМАНИЕ: страница без ожидаемой разметки "
                    f"(нет state и карточек), пропуск")
        else:
            # детект отсутствия пагинации: сервер игнорирует ?page=
            offset = ((state.get("listing") or {}).get("listing") or {}).get("params", {}).get("offset")
            ids = {r["id"] for r in page_state_ads if r["id"]}
            if page == 1:
                first_ids = ids
            elif offset == 0 or (first_ids and len(first_ids & ids) >= 0.9 * max(len(ids), 1)):
                pagination_broken = True
                log(f"  ВНИМАНИЕ: ?page={page} проигнорирован сервером "
                    f"(offset={offset}, пересечение со стр.1: "
                    f"{len(first_ids & ids) if first_ids else '?'}) — "
                    f"страница не добавляется, дальнейшие пропускаются")
                continue
        fetched_pages += 1
        records, extra = merge_records(page_state_ads, page_card_ads)
        log(f"  извлечено {len(records)} объявлений "
            f"(state={len(page_state_ads)}, card-фолбэк={extra})")
        if totals and page == 1:
            state_total = totals
        all_records.extend(records)

    unique, dups = dedup(all_records)
    if args.enrich_details > 0:
        recovered = enrich_details(unique, session, args.timeout,
                                   args.enrich_details, args.delay_min, args.delay_max)
        log(f"  JSON-LD обогащение: запросов<= {args.enrich_details}, цен добрано {recovered}")
    block = {
        "target": target, "kind": kind, "pages_requested": args.pages,
        "pages_fetched": fetched_pages,
        "http_failed_pages": errors,
        "markup_misses": markup_misses,
        "pagination_broken": pagination_broken,
        "raw_records": len(all_records), "unique": len(unique),
        "duplicates": dups,
        "total_in_search": state_total[0] if state_total else None,
        "records": unique,
    }
    return block


# --------------------------------------------------------------------------
# Метрики, вывод
# --------------------------------------------------------------------------

def block_metrics(block):
    n = len(block["records"])
    priced = sum(1 for r in block["records"] if r["price"] is not None)
    salaried = sum(1 for r in block["records"] if r["salary_from"] is not None)
    any_price = sum(1 for r in block["records"] if has_any_price(r))
    empty = {
        "title": sum(1 for r in block["records"] if not r["title"]),
        "url": sum(1 for r in block["records"] if not r["url"]),
        "price_and_salary": sum(1 for r in block["records"] if not has_any_price(r)),
        "location": sum(1 for r in block["records"] if not (r["city"] or r["district"])),
        "date": sum(1 for r in block["records"] if not r["date"]),
    }
    return {
        "unique": block["unique"],
        "raw": block["raw_records"],
        "dup_pct": round(100.0 * block["duplicates"] / block["raw_records"], 1)
                   if block["raw_records"] else 0.0,
        "price_pct": round(100.0 * priced / n, 1) if n else 0.0,
        "salary_pct": round(100.0 * salaried / n, 1) if n else 0.0,
        "any_price_pct": round(100.0 * any_price / n, 1) if n else 0.0,
        "empty_fields": empty,
        "http_failed_pages": block["http_failed_pages"],
        "markup_misses": block["markup_misses"],
        "total_in_search": block["total_in_search"],
    }


def flat_row(rec):
    return {
        "id": rec["id"], "url": rec["url"], "title": rec["title"],
        "price": rec["price"], "currency": rec["currency"],
        "negotiable": rec["negotiable"],
        "salary_from": rec["salary_from"], "salary_to": rec["salary_to"],
        "salary_currency": rec["salary_currency"],
        "salary_period": rec["salary_period"],
        "city": rec["city"], "district": rec["district"], "region": rec["region"],
        "date": rec["date"], "is_job": rec["is_job"], "is_business": rec["is_business"],
        "category_id": rec["category_id"], "category_type": rec["category_type"],
        "price_source": rec["price_source"], "source": rec["source"],
        "page": rec["page"],
    }


def write_outputs(blocks, args, elapsed):
    unique_all, dup_total = dedup([r for b in blocks for r in b["records"]])
    metrics = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_sec": round(elapsed, 1),
        "targets": [block_metrics(b) for b in blocks],
        "total_raw": sum(b["raw_records"] for b in blocks),
        "total_unique": len(unique_all),
        "total_dup_pct": round(100.0 * sum(b["duplicates"] for b in blocks) /
                               max(sum(b["raw_records"] for b in blocks), 1), 1),
        "total_price_pct": round(100.0 * sum(1 for r in unique_all if r["price"] is not None)
                                 / max(len(unique_all), 1), 1),
        "total_salary_pct": round(100.0 * sum(1 for r in unique_all if r["salary_from"] is not None)
                                  / max(len(unique_all), 1), 1),
        "total_any_price_pct": round(100.0 * sum(1 for r in unique_all if has_any_price(r))
                                     / max(len(unique_all), 1), 1),
        "pages_ok": sum(b["pages_fetched"] for b in blocks),
        "pages_failed": sum(b["http_failed_pages"] for b in blocks),
    }

    json_path, csv_path = f"{args.out}.json", f"{args.out}.csv"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"meta": {
                        "tool": "tools/olx_production.py",
                        "params": {
                            "query": args.query, "category": args.category,
                            "pages": args.pages, "min_price": args.min_price,
                            "max_price": args.max_price,
                            "enrich_details": args.enrich_details,
                        },
                        "metrics": metrics},
                   "items": unique_all}, f, ensure_ascii=False, indent=2)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for rec in unique_all:
            writer.writerow(flat_row(rec))
    return metrics, json_path, csv_path


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_argparser():
    p = argparse.ArgumentParser(
        description="Продакшен-парсер объявлений OLX.uz (state JSON + HTML-фолбэк + JSON-LD).")
    p.add_argument("--query", action="append", default=[],
                   help="поисковый запрос; можно повторять (--query a --query b)")
    p.add_argument("--category", action="append", default=[],
                   help="категория: путь (nedvizhimost/arenda-pomescheniy) или полный URL; можно повторять")
    p.add_argument("--pages", type=int, default=2,
                   help=f"страниц на категорию/запрос (1-{MAX_PAGES_PER_TARGET}, по умолчанию 2)")
    p.add_argument("--min-price", type=float, default=None,
                   help="фильтр: минимальная цена (зарплатные — по пересечению вилки)")
    p.add_argument("--max-price", type=float, default=None,
                   help="фильтр: максимальная цена")
    p.add_argument("--out", default="olx_results",
                   help="префикс файлов вывода: PREFIX.json и PREFIX.csv (по умолчанию olx_results)")
    p.add_argument("--enrich-details", type=int, default=0,
                   help=f"добрать цены по JSON-LD детальных страниц (до {MAX_ENRICH_DETAILS} запросов)")
    p.add_argument("--delay-min", type=float, default=1.5,
                   help="нижняя граница паузы между запросами, сек (по умолчанию 1.5)")
    p.add_argument("--delay-max", type=float, default=3.0,
                   help="верхняя граница паузы между запросами, сек (по умолчанию 3.0)")
    p.add_argument("--timeout", type=int, default=20, help="таймаут HTTP-запроса, сек")
    return p


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = build_argparser().parse_args()
    if not args.query and not args.category:
        print("Укажите хотя бы один --query или --category (пример: "
              "python tools/olx_production.py --query avtoservis --pages 2)", file=sys.stderr)
        return 2
    if args.pages < 1:
        print("--pages должен быть >= 1", file=sys.stderr)
        return 2

    session = requests.Session()
    metrics = {"pages_ok": 0, "pages_failed": 0}
    started = time.monotonic()
    blocks = []
    try:
        for q in args.query:
            blocks.append(run_target(q, "query", args.pages, args, session, metrics))
        for c in args.category:
            blocks.append(run_target(c, "category", args.pages, args, session, metrics))
    except KeyboardInterrupt:
        log("Прервано пользователем — сохраняю уже собранное")

    # фильтр цены применяется к уже собранным блокам
    if args.min_price is not None or args.max_price is not None:
        for b in blocks:
            b["records"] = [r for r in b["records"]
                            if price_filter_match(r, args.min_price, args.max_price)]

    elapsed = time.monotonic() - started
    metrics, json_path, csv_path = write_outputs(blocks, args, elapsed)

    log(f"Готово за {metrics['elapsed_sec']} c; "
        f"страниц ок/ошибок: {metrics['pages_ok']}/{metrics['pages_failed']}")
    print(f"JSON: {json_path}")
    print(f"CSV : {csv_path}")
    for t, m in zip([b["kind"] + ":" + b["target"] for b in blocks], metrics["targets"]):
        print(f"{t}: уникальных {m['unique']}, дубли {m['dup_pct']}%, "
              f"с ценой {m['price_pct']}%, с зарплатой {m['salary_pct']}%, "
              f"любой ценовой показатель {m['any_price_pct']}%, "
              f"пустые поля: {m['empty_fields']}")
    print(f"ИТОГО: уникальных {metrics['total_unique']} "
          f"(дубли {metrics['total_dup_pct']}%), с ценой {metrics['total_price_pct']}%, "
          f"с зарплатой {metrics['total_salary_pct']}%, "
          f"любой ценовой показатель {metrics['total_any_price_pct']}%, "
          f"время {metrics['elapsed_sec']} c")
    return 0


if __name__ == "__main__":
    sys.exit(main())
