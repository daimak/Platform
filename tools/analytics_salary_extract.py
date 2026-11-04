#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Шаг 1 аналитики: извлечение зарплат из снапшота вакансий через LLM-шлюз.

Зачем: в jobs.csv поле salary пусто у ~96% записей, но зарплата почти всегда
есть в title/snippet (например, «💰 $54K - $205K/год» в заголовке TG). Скрипт
прогоняет записи снапшота через локальный шлюз FreeLLMAPI (Workspace/.env,
ключ не выводится) чанками по 30 и складывает результат рядом с jobs.csv:
Workspace/analytics/<дата>/salary_extracted.csv (+ кэш salary_extract_cache.json).

Безопасность и гигиена:
- DRY-RUN по умолчанию: без --apply ни одного запроса к LLM не делается;
- кэш по idx: повторный запуск доэкстрагирует только недостающее (crash-recovery);
- ни одна вакансия не модифицируется, пишутся только новые файлы снапшота;
- вызов фиксируется в журнале AI-Usage (purpose="Analytics salary extraction");
- правило промпта: только то, что написано в тексте; нет зарплаты — null.

Нормализация: monthly = year/12, day*22, hour*160; USD как есть, UZS через
курс --uzs-rate (ПРИБЛИЖЕНИЕ — курс не тянется из сети, поменяй флагом).
Другие валюты (EUR и пр.) остаются без пересчёта (usd_* пустые).

Запуск:
  python tools/analytics_salary_extract.py                     # план
  python tools/analytics_salary_extract.py --apply             # экстракция
Опции: --dir ПУТЬ (по умолчанию свежайший снапшот), --uzs-rate 12700,
       --chunk 30, --model ИМЯ (по умолчанию FREE_LLM_MODEL из .env)
"""

import argparse
import json
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "barrymore"))

from ai_usage import record_request  # noqa: E402

ANALYTICS = ROOT / "Workspace" / "analytics"
ENV_PATH = ROOT / "Workspace" / ".env"
LLM_TIMEOUT_SEC = 120
SNIPPET_MAX = 500
TITLE_MAX = 150
PERIOD_TO_MONTH = {"month": 1.0, "year": 1.0 / 12, "day": 22.0, "hour": 160.0}
SYSTEM_PROMPT = (
    "Ты — экстрактор структурированных данных для аналитики вакансий. Тебе дан список "
    "записей (idx, title, snippet). Для КАЖДОЙ записи найди зарплату, ТОЛЬКО если она "
    "явно упомянута в тексте записи. Правила: ничего не выдумывай; суммарные бонусы "
    "и опцион зарплатой не считаются; если зарплаты нет — все поля null. Ответ дай "
    "СТРОГО в JSON без пояснений: массив объектов "
    '{"idx": <number>, "min": <number|null>, "max": <number|null>, '
    '"currency": <"USD"|"UZS"|"EUR"|строка|null>, '
    '"period": <"month"|"year"|"day"|"hour"|"task"|null>, '
    '"text": "<как написано в тексте, до 60 символов>"}.'
)


def load_env(path: Path) -> dict:
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"?([^"\r\n]*)"?\s*$', line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


def find_snapshot_dir(explicit: Path | None) -> Path:
    if explicit:
        if not (explicit / "jobs.csv").exists():
            raise SystemExit(f"[FAIL] в {explicit} нет jobs.csv")
        return explicit
    candidates = sorted(
        (d for d in ANALYTICS.glob("[0-9]" * 4 + "-*-*/") if (d / "jobs.csv").exists()),
        key=lambda d: d.name,
    )
    if not candidates:
        raise SystemExit(f"[FAIL] снапшоты не найдены в {ANALYTICS} (сначала python tools/analytics_snapshot.py)")
    return candidates[-1]


def read_jobs(snapshot: Path) -> list[dict]:
    import csv
    with (snapshot / "jobs.csv").open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def ask_llm(env: dict, model: str, records: list[dict]) -> tuple[dict[int, dict], str, dict, dict]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    [
                        {
                            "idx": int(r["idx"]),
                            "title": r.get("title", "")[:TITLE_MAX],
                            "snippet": (r.get("snippet", "") or "")[:SNIPPET_MAX],
                        }
                        for r in records
                    ],
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0,
    }
    request = urllib.request.Request(
        env.get("FREE_LLM_BASE_URL", "http://localhost:31415/v1").rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + env.get("FREE_LLM_API_KEY", "")},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=LLM_TIMEOUT_SEC) as response:
        data = json.loads(response.read().decode("utf-8"))
    text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    match = re.search(r"\[.*\]", text.strip(), re.S)
    if not match:
        raise ValueError("LLM вернул ответ без JSON-массива")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, list):
        raise ValueError("LLM вернул не массив")
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    cost = data.get("cost") if isinstance(data.get("cost"), dict) else {}
    result = {}
    for item in parsed:
        if isinstance(item, dict) and isinstance(item.get("idx"), int):
            result[item["idx"]] = item
    return result, data.get("model") or model, usage, cost


def to_monthly_usd(item: dict, uzs_rate: float) -> tuple[float | None, float | None]:
    """Пересчёт экстракта в USD/месяц. (None, None) — период/валюта не пересчитываются."""
    rates = {"USD": 1.0, "UZS": 1.0 / uzs_rate if uzs_rate else None}
    currency = (item.get("currency") or "").strip().upper() or None
    period = (item.get("period") or "").strip().lower() or None
    factor = PERIOD_TO_MONTH.get(period or "")
    rate = rates.get(currency or "")
    if not factor or not rate:
        return None, None
    def convert(value):
        if isinstance(value, (int, float)) and value > 0:
            return round(value * factor * rate)
        return None
    return convert(item.get("min")), convert(item.get("max"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Извлечение зарплат из снапшота вакансий (шаг 1 аналитики)")
    parser.add_argument("--dir", type=Path, help="каталог снапшота (по умолчанию свежайший)")
    parser.add_argument("--apply", action="store_true", help="выполнить запросы к LLM (без флага — только план)")
    parser.add_argument("--uzs-rate", type=float, default=12700.0,
                        help="курс UZS за 1 USD для пересчёта (приближение, default 12700)")
    parser.add_argument("--chunk", type=int, default=30, help="записей на один запрос LLM (default 30)")
    parser.add_argument("--model", help="модель (по умолчанию FREE_LLM_MODEL из .env)")
    args = parser.parse_args()

    snapshot = find_snapshot_dir(args.dir)
    jobs = read_jobs(snapshot)
    with_salary_csv = [r for r in jobs if (r.get("salary") or "").strip()]
    to_extract = [r for r in jobs if not (r.get("salary") or "").strip()]
    env = load_env(ENV_PATH)
    model = args.model or env.get("FREE_LLM_MODEL", "auto")
    chunks = [to_extract[i:i + args.chunk] for i in range(0, len(to_extract), args.chunk)]

    print(f"Снапшот: {snapshot}")
    print(f"Записей: {len(jobs)}; с зарплатой в jobs.csv: {len(with_salary_csv)}; "
          f"к экстракции: {len(to_extract)} ({len(chunks)} чанков по ~{args.chunk})")
    print(f"Шлюз: {env.get('FREE_LLM_BASE_URL', 'http://localhost:31415/v1').rstrip('/')}, модель: {model}; "
          f"курс UZS/USD: {args.uzs_rate:g} (приближение)")
    if not chunks:
        print("Экстрагировать нечего — все зарплаты уже есть.")
        return 0
    if not env.get("FREE_LLM_API_KEY"):
        print("[FAIL] Workspace/.env: нет FREE_LLM_API_KEY.", file=sys.stderr)
        return 1
    if not args.apply:
        print("\nDRY-RUN: запросы к LLM не выполнялись. Для запуска добавьте --apply.")
        return 0

    cache_path = snapshot / "salary_extract_cache.json"
    cache: dict[str, dict] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cache = {}

    done_llm = sum(1 for r in to_extract if str(r["idx"]) in cache)
    print(f"Кэш: {done_llm} записей уже экстрагировано — пропускаются.")
    calls = 0
    call_errors = 0
    last_model = model
    usage_total = {}
    for number, chunk in enumerate(chunks, 1):
        pending = [r for r in chunk if str(r["idx"]) not in cache]
        if not pending:
            continue
        for attempt in (1, 2):
            try:
                extracted, last_model, usage, cost = ask_llm(env, model, pending)
                break
            except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError, json.JSONDecodeError,
                    KeyError, IndexError) as error:
                call_errors += 1
                if attempt == 2:
                    print(f"[WARN] чанк {number}: LLM недоступен/ошибка ({error}) — записи останутся без зарплаты")
                    extracted = {}
                else:
                    time.sleep(2)
        calls += 1
        for key, item in extracted.items():
            cache[str(key)] = item
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            if isinstance(usage.get(key), (int, float)):
                usage_total[key] = usage_total.get(key, 0) + usage[key]
        print(f"[OK] чанк {number}/{len(chunks)}: извлечено {len(extracted)}/{len(pending)}")
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    rows = []
    monthly_usd = []
    for record in jobs:
        idx = record["idx"]
        raw_csv = (record.get("salary") or "").strip()
        item = cache.get(str(idx))
        usd_min = usd_max = None
        note = "not-found"
        if raw_csv:
            note = "from-csv"
        elif item:
            usd_min, usd_max = to_monthly_usd(item, args.uzs_rate)
            note = "extracted" if usd_min or usd_max else "no-salary-in-text"
        rows.append({
            "idx": idx,
            "source": record.get("source", ""),
            "title": (record.get("title", "") or "")[:TITLE_MAX],
            "url": record.get("url", ""),
            "salary_raw_csv": raw_csv,
            "has_salary": "yes" if note in ("from-csv", "extracted") else "no",
            "ext_min": item.get("min") if item else "",
            "ext_max": item.get("max") if item else "",
            "ext_currency": item.get("currency") if item else "",
            "ext_period": item.get("period") if item else "",
            "ext_text": (item.get("text") or "")[:60] if item else "",
            "usd_month_min": usd_min if usd_min is not None else "",
            "usd_month_max": usd_max if usd_max is not None else "",
            "note": note,
        })
        if usd_min:
            monthly_usd.append(usd_min if usd_max and usd_min <= usd_max else usd_max or usd_min)

    out_path = snapshot / "salary_extracted.csv"
    import csv
    with out_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    covered = sum(1 for r in rows if r["note"] in ("from-csv", "extracted"))
    converted = sum(1 for r in rows if r["usd_month_min"] != "")
    print("-" * 60)
    print(f"salary_extracted.csv записан: {out_path}")
    print(f"Покрытие зарплатами: {covered}/{len(rows)} ({covered * 100 // max(len(rows), 1)}%); "
          f"пересчитано в USD/месяц: {converted}. Фильтр — колонка has_salary: "
          f"yes={covered}, no={len(rows) - covered} (без вилки не бракуем — спросить при контакте).")
    if monthly_usd:
        monthly_usd.sort()
        print(f"USD/мес: медиана {statistics.median(monthly_usd):,.0f}, "
              f"p25 {monthly_usd[len(monthly_usd) // 4]:,.0f}, p75 {monthly_usd[3 * len(monthly_usd) // 4]:,.0f} "
              f"(n={len(monthly_usd)}, UZS по курсу {args.uzs_rate:g})")
    print(f"LLM: вызовов {calls}, ошибок {call_errors}, модель {last_model}")
    try:
        record_request(
            "freellmapi", last_model, usage_total or None, None,
            "Analytics salary extraction",
            f"chunks={len(chunks)} extracted={sum(1 for r in rows if r['note'] == 'extracted')} "
            f"covered={covered}/{len(rows)}",
        )
    except (OSError, ValueError) as error:
        print(f"[WARN] usage не записан в AI-Usage журнал: {error}", file=sys.stderr)
    return 0 if covered else 1


if __name__ == "__main__":
    sys.exit(main())
