#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Шаг 2 аналитики: одностраничный markdown-отчёт по снапшотам вакансий.

Зачем: превратить дневные снапшоты (Workspace/analytics/<дата>/) в ответ на
пять вопросов аналитики поиска работы — где платят, какой источник годный,
что нового, что на OLX, сколько данных ещё грязное. Отчёт пишется в
<свежайший снапшот>/report.md и печатается в stdout.

Источники данных внутри снапшота:
- jobs.csv — сырые вакансии (обязателен);
- salary_extracted.csv — результат analytics_salary_extract.py (если есть:
  появляются зарплатные секции; если нет — отчёт честно скажет запустить);
- olx_structured.csv — экстракция OLX-автосервисов (если есть).

Дифф «новое против вчера» — по URL между свежайшим и предыдущим снапшотами.
«Свежая» вакансия — дата в записи не старше 14 дней на дату снапшота
(даты старше месяца — мусор кэша прошлых прогонов, см. README снапшота).

Топ «скорость до денег» — эвристика (не истина): баллы за зарплату в USD/мес,
свежесть ≤7/14 дней и локальный быстрый источник (OLX/hh.uz). Уточняется по
мере накопления данных.

Запуск: python tools/analytics_report.py [--dir ПУТЬ] [--no-write]
"""

import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS = ROOT / "Workspace" / "analytics"

SEGMENT_RULES = [
    ("remote-intl (HN/RemoteOK/Remotive)", ("HN", "RemoteOK", "Remotive")),
    ("tg-ru (@remote_jobs_ru)", ("Telegram @remote_jobs_ru",)),
    ("tg-devops (@devops_vacancies)", ("Telegram @devops_vacancies",)),
    ("hh-uz", ("hh (hh.uz",)),
    ("hh-ru", ("hh (hh.ru",)),
    ("olx-uz", ("OLX.uz",)),
]
SEGMENT_NAMES = [name for name, _ in SEGMENT_RULES]
FAST_LOCAL_SOURCES = {"OLX.uz", "hh (hh.uz, html)"}


def snapshot_dirs() -> list[Path]:
    return sorted((d for d in ANALYTICS.glob("[0-9]" * 4 + "-*-*/") if (d / "jobs.csv").exists()), key=lambda d: d.name)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def parse_date(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.replace(tzinfo=None)
    return parsed


def segment_of(source: str) -> str:
    for name, prefixes in SEGMENT_RULES:
        if any(source.startswith(prefix) for prefix in prefixes):
            return name
    return "прочее"


def median_or_dash(values: list[float]) -> str:
    return f"{statistics.median(values):,.0f}" if values else "—"


def salary_by_source(rows: list[dict]) -> dict[str, list[float]]:
    by_source: dict[str, list[float]] = {}
    for row in rows:
        try:
            usd_min = float(row.get("usd_month_min") or "")
        except ValueError:
            continue
        try:
            usd_max = float(row.get("usd_month_max") or "")
        except ValueError:
            usd_max = usd_min
        mid = usd_min if not usd_max or usd_min > usd_max else (usd_min + usd_max) / 2
        by_source.setdefault(row.get("source", "?"), []).append(mid)
    return by_source


def build_report(latest: Path, previous: Path | None) -> str:
    snapshot_date = datetime.strptime(latest.name, "%Y-%m-%d")
    jobs = read_csv(latest / "jobs.csv")
    lines: list[str] = []
    add = lines.append

    add(f"# Аналитика поиска работы — снапшот {latest.name}")
    add("")
    add(f"*Сгенерировано tools/analytics_report.py; предыдущий снапшот: {previous.name if previous else '— (это первый)*'}")
    add("")

    # 1. Сводка и дифф
    urls_now = {r.get("url", "") for r in jobs}
    add("## Сводка")
    add("")
    add(f"- Вакансий всего: **{len(jobs)}** (уникальных URL: {len(urls_now - {''})})")
    if previous:
        jobs_prev = read_csv(previous / "jobs.csv")
        urls_prev = {r.get("url", "") for r in jobs_prev}
        fresh_urls = urls_now - urls_prev
        gone = urls_prev - urls_now
        add(f"- Новых с {previous.name}: **{len(fresh_urls)}**; исчезло: {len(gone)}")
    else:
        add("- Предыдущего снапшота нет — дифф появится со второго прогона")

    # Свежесть
    dated = [(parse_date(r.get("date", "")), r) for r in jobs]
    ages = [(snapshot_date - d).days for d, _ in dated if d]
    fresh14 = sum(1 for a in ages if a <= 14)
    stale = len(jobs) - len(ages)
    add(f"- Свежих (≤14 дней): {fresh14}; без разборной даты: {stale}; старше: {len(ages) - fresh14}")
    add("")

    # 2. Зарплаты
    salary_path = latest / "salary_extracted.csv"
    sal_rows = read_csv(salary_path) if salary_path.exists() else None
    add("## Зарплаты (USD/месяц)")
    add("")
    if sal_rows is not None:
        sal_rows = read_csv(salary_path)
        by_source = salary_by_source(sal_rows)
        all_mid = [v for values in by_source.values() for v in values]
        covered = sum(1 for r in sal_rows if r.get("note") in ("from-csv", "extracted"))
        add(f"- **С зарплатой (✓ has_salary=yes): {covered}** из {len(sal_rows)}; без вилки: "
            f"{len(sal_rows) - covered} — не брак, вилку спрашиваем при первом контакте")
        add(f"- Фильтрация: `{salary_path.name}`, колонка `has_salary` (yes/no); "
            f"пересчитано в USD/мес: {len(all_mid)}")
        if all_mid:
            all_mid.sort()
            add(f"- По всей выборке: медиана **{statistics.median(all_mid):,.0f}**, "
                f"p25 {all_mid[len(all_mid) // 4]:,.0f}, p75 {all_mid[3 * len(all_mid) // 4]:,.0f}")
        add("")
        add("| Сегмент | n | медиана | min–max |")
        add("|---|---|---|---|")
        for name in SEGMENT_NAMES + ["прочее"]:
            values = sorted(v for source, vals in by_source.items() if segment_of(source) == name for v in vals)
            if values:
                add(f"| {name} | {len(values)} | {statistics.median(values):,.0f} | {values[0]:,.0f}–{values[-1]:,.0f} |")
        add("")
        add("*Внимание: UZS пересчитан по фиксированному курсу из флага --uzs-rate экстрактора — приближение.*")
    else:
        add("- **salary_extracted.csv отсутствует** — сначала `python tools/analytics_salary_extract.py --apply`")
    add("")

    # 3. По источникам
    add("## Источники")
    add("")
    salary_counter = Counter(
        r.get("source", "?") for r in (sal_rows or []) if r.get("note") in ("from-csv", "extracted")
    )
    add("| Источник | всего | свежих ≤14д | с ЗП ✓ |")
    add("|---|---|---|---|")
    counter = Counter(r.get("source", "?") for r in jobs)
    fresh_counter = Counter()
    for d, r in dated:
        if d and (snapshot_date - d).days <= 14:
            fresh_counter[r.get("source", "?")] += 1
    for source, count in counter.most_common():
        add(f"| {source} | {count} | {fresh_counter.get(source, 0)} | {salary_counter.get(source, 0)} |")
    add("")

    # 4. Топ «скорость до денег»
    if sal_rows is not None:
        sal_by_idx = {r["idx"]: r for r in sal_rows}
        scored = []
        for job in jobs:
            sal = sal_by_idx.get(job.get("idx", ""))
            if not sal:
                continue
            try:
                usd = float(sal.get("usd_month_min") or "")
            except ValueError:
                continue
            d = parse_date(job.get("date", ""))
            age = (snapshot_date - d).days if d else 999
            score = (2 if age <= 7 else 1 if age <= 14 else 0) + (1 if job.get("source") in FAST_LOCAL_SOURCES else 0)
            scored.append((score, -age, usd, job, sal))
        scored.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        if scored:
            add("## Топ-10 «скорость до денег» (эвристика)")
            add("")
            add("| балл | вакансия | источник | дата | USD/мес |")
            add("|---|---|---|---|---|")
            for score, neg_age, usd, job, sal in scored[:10]:
                title = (job.get("title", "") or "")[:70]
                add(f"| {score} | {title} | {job.get('source', '')} | {job.get('date', '')[:10] or '—'} | {usd:,} |")
            add("")

        # Свежие без вилки: галочки нет, но не брак — список для «спросить ЗП при контакте»
        no_salary_fresh = []
        for job in jobs:
            sal = sal_by_idx.get(job.get("idx", ""))
            if sal and sal.get("note") in ("from-csv", "extracted"):
                continue
            d = parse_date(job.get("date", ""))
            age = (snapshot_date - d).days if d else None
            if age is not None and age <= 14:
                no_salary_fresh.append((age, job))
        no_salary_fresh.sort(key=lambda item: item[0])
        if no_salary_fresh:
            add("## Свежие без вилки — спросить ЗП при контакте (has_salary=no, не брак)")
            add("")
            add("| вакансия | источник | дата | возраст, дн |")
            add("|---|---|---|---|")
            for age, job in no_salary_fresh[:10]:
                title = (job.get("title", "") or "")[:70]
                add(f"| {title} | {job.get('source', '')} | {job.get('date', '')[:10] or '—'} | {age} |")
            if len(no_salary_fresh) > 10:
                add(f"*…и ещё {len(no_salary_fresh) - 10} — фильтруй в `{salary_path.name}` по has_salary=no*")
            add("")

    # 5. OLX
    olx_path = latest / "olx_structured.csv"
    if olx_path.exists():
        olx = read_csv(olx_path)
        cats = Counter((r.get("category") or "?").strip() for r in olx)
        job_rows = [r for r in olx if (r.get("category") or "").strip() == "job"]
        housing = sum(1 for r in job_rows if (r.get("housing") or "").strip().lower() == "true")
        priced = [r for r in olx if (r.get("price_amount") or "").strip()]
        add("## OLX автосервисы (быстрый доход)")
        add("")
        add(f"- Объявлений: {len(olx)}; категории: {dict(cats.most_common())}")
        if job_rows:
            add(f"- Вакансий: {len(job_rows)}, из них с жильём: {housing}")
        add(f"- С явной ценой: {len(priced)} из {len(olx)} (цена в отдельном поле выдачи — парсер её пока не берёт)")
        add("")

    # 6. Честные ограничения
    add("## Ограничения данных")
    add("")
    no_date = sum(1 for d, _ in dated if not d)
    if sal_rows is not None:
        no_salary = sum(1 for r in sal_rows if r.get("has_salary") != "yes")
    else:
        no_salary = len(jobs)
    add(f"- Без даты: {no_date}; без вилки (has_salary=no — спросить при контакте): {no_salary}; "
        "location — свободный текст (не нормализован)")
    add("- Даты старше месяца — вероятно кэш прошлых прогонов; в трендах фильтровать")
    add("")

    # 7. Выводы (авто, честные)
    add("## Выводы")
    add("")
    if previous:
        add(f"- Поток: {len(fresh_urls) if previous else '—'} новых вакансий за день между снапшотами.")
    add("- Записываем всё: отсутствие вилки — не красный флаг; ✗ = спросить ЗП при первом контакте.")
    if sal_rows is not None and all_mid:
        add(f"- Рынок по вашей выборке: медиана {statistics.median(all_mid):,.0f} USD/мес (n={len(all_mid)}). "
            "Сравнивайте с целью ~2500 USD/мес и своей специализацией.")
    else:
        add("- Зарплатной картины пока нет — прогоните шаг 1 (extract) и перезапустите отчёт.")
    add("- Источники со свежими записями (см. таблицу «Источники») — там стоит смотреть в первую очередь.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Одностраничный отчёт по снапшотам вакансий (шаг 2 аналитики)")
    parser.add_argument("--dir", type=Path, help="каталог снапшота (по умолчанию свежайший)")
    parser.add_argument("--no-write", action="store_true", help="не писать report.md, только stdout")
    args = parser.parse_args()

    dirs = snapshot_dirs()
    if not dirs:
        print("[FAIL] снапшоты не найдены (сначала python tools/analytics_snapshot.py)", file=sys.stderr)
        return 1
    latest = args.dir if args.dir else dirs[-1]
    if latest not in dirs:
        print(f"[FAIL] в {latest} нет jobs.csv", file=sys.stderr)
        return 1
    previous = next((d for d in reversed(dirs) if d.name < latest.name), None)

    report = build_report(latest, previous)
    if not args.no_write:
        out_path = latest / "report.md"
        out_path.write_text(report, encoding="utf-8")
        print(f"[OK] отчёт записан: {out_path}\n")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
