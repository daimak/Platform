#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Радар денег: триаж вакансий и заказов снапшота по перспективности.

Зачем: чтобы каждый раз не рыть сотни объявлений. Каждая запись снапшота
получает статус: perspective (перспективные заказы/вакансии по категориям),
main (основной блок — изучать вручную), outset (отсев — явный не-ИТ).
Человек постепенно перетасовывает записи между блоками; при повторном прогоне
ручные решения СОХРАНЯЮТСЯ: если пользователь сменил status относительно
status_auto, скрипт его не трогает.

Категории perspective (первое совпадение — по приоритету, все совпадения в tags):
  1. скраперы/парсеры   2. боты/автоматизация   3. сайты/вёрстка
  4. AI/LLM             5. DevOps/инфраструктура

Артефакты (в Workspace/analytics/, общие для всех снапшотов):
- orders_board.json — живая доска (все записи + статусы; можно править руками);
- orders_report.md — отчёт-разбивка (перегенерируется каждым прогоном).

Запуск: python tools/orders_triage.py [--dir ПУТЬ]
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS = ROOT / "Workspace" / "analytics"
BOARD_PATH = ANALYTICS / "orders_board.json"
REPORT_PATH = ANALYTICS / "orders_report.md"
SNIPPET_MAX = 600

TASHKENT = timezone(timedelta(hours=5), "Tashkent")

# (категория, приоритет, регулярки по title+snippet)
CATEGORY_RULES = [
    ("скраперы/парсеры", [
        r"парсер", r"парсинг", r"скрап", r"parser", r"scrap", r"сбор данных",
        r"data.{0,10}extraction", r"spider", r"краул", r"crawl",
    ]),
    ("боты/автоматизация", [
        r"\w?бот", r"\bbot\b", r"автоматизац", r"автопост", r"интеграци",
        r"макрос", r"скрипт", r"no-?code", r"make\.com", r"n8n", r"zapier",
    ]),
    ("сайты/вёрстка", [
        r"доработк\w? сайт", r"сайт\w*\b", r"верст", r"лендинг", r"landing",
        r"wordpress", r"тільда", r"тильда", r"tilda", r"front-?end", r"фронтенд",
        r"html", r"css", r"react", r"vue", r"интернет-магазин", r"shopify",
    ]),
    ("AI/LLM", [
        r"\bllm\b", r"\bgpt", r"chatgpt", r"нейросет", r"\bai\b", r"ии-агент",
        r"ai-агент", r"промпт", r"prompt", r"openai", r"gemini", r"claude",
        r"machine learning", r"\bml\b", r"нейронн",
    ]),
    ("DevOps/инфраструктура", [
        r"devops", r"ci\s*/\s*cd", r"docker", r"kubernetes", r"\bk8s\b",
        r"terraform", r"ansible", r"мониторинг", r"grafana", r"zabbix",
        r"prometheus", r"linux", r"администратор", r"сисадмин", r"\bvps\b",
        r"\bvpn\b", r"nginx", r"сервера", r"настройк\w? сервер", r"gitlab", r"\bjenkins\b",
        r"\bsre\b", r"\bsap\b", r"инфраструктур", r"настройк\w? серверов",
    ]),
]

OUTSET_RULES = [
    r"курьер", r"\bводитель\b", r"продавец", r"грузчик", r"официант", r"уборщ",
    r"разнорабоч", r"сторож", r"оператор колл", r"контакт-цент", r"няня",
    r"репетитор", r"консультант в магазин",
]


def match_rules(text: str, rules: list[str]) -> bool:
    return any(re.search(rule, text, re.IGNORECASE) for rule in rules)


def classify(title: str, snippet: str) -> tuple[str, str, list[str]]:
    """Возвращает (status, category, tags)."""
    text = f"{title} {snippet[:SNIPPET_MAX]}"
    tags = [name for name, rules in CATEGORY_RULES if match_rules(text, rules)]
    if tags:
        return "perspective", tags[0], tags
    if match_rules(text, OUTSET_RULES):
        return "outset", "не-ИТ", []
    return "main", "", []


def snapshot_dirs() -> list[Path]:
    return sorted((d for d in ANALYTICS.glob("[0-9]" * 4 + "-*-*/") if (d / "jobs.csv").exists()), key=lambda d: d.name)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def load_board() -> dict:
    if BOARD_PATH.exists():
        try:
            return json.loads(BOARD_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {"schema_version": 1, "updated_at": None, "records": []}


def main() -> int:
    parser = argparse.ArgumentParser(description="Триаж заказов/вакансий по перспективности (радар денег)")
    parser.add_argument("--dir", type=Path, help="каталог снапшота (по умолчанию свежайший)")
    args = parser.parse_args()

    dirs = snapshot_dirs()
    if not dirs:
        print("[FAIL] снапшоты не найдены (сначала python tools/analytics_snapshot.py)", file=sys.stderr)
        return 1
    snapshot = args.dir if args.dir else dirs[-1]
    jobs = read_csv(snapshot / "jobs.csv")

    salary_flags = {}
    salary_path = snapshot / "salary_extracted.csv"
    if salary_path.exists():
        salary_flags = {r["idx"]: r.get("has_salary", "") for r in read_csv(salary_path)}

    board = load_board()
    previous = {r["idx"]: r for r in board.get("records", [])}

    records = []
    for job in jobs:
        idx = job.get("idx", "")
        status_auto, category, tags = classify(job.get("title", ""), job.get("snippet", ""))
        old = previous.get(idx)
        status = status_auto
        if old and old.get("status") != old.get("status_auto") and old.get("status") in ("perspective", "main", "outset"):
            status = old["status"]  # ручное решение Sovereign — сохраняем
        records.append({
            "idx": idx,
            "source": job.get("source", ""),
            "title": (job.get("title", "") or "")[:160],
            "url": job.get("url", ""),
            "date": (job.get("date", "") or "")[:10],
            "has_salary": salary_flags.get(idx, ""),
            "status": status,
            "status_auto": status_auto,
            "category": category,
            "tags": tags,
            "note": (old or {}).get("note", ""),
        })

    board["records"] = records
    board["updated_at"] = datetime.now(TASHKENT).isoformat(timespec="seconds")
    board["snapshot"] = snapshot.name
    ANALYTICS.mkdir(parents=True, exist_ok=True)
    BOARD_PATH.write_text(json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8")

    # Отчёт
    persp = [r for r in records if r["status"] == "perspective"]
    main = [r for r in records if r["status"] == "main"]
    outset = [r for r in records if r["status"] == "outset"]
    by_cat = Counter(r["category"] for r in persp)

    lines = []
    add = lines.append
    add(f"# Радар денег — разбивка по перспективности (снапшот {snapshot.name})")
    add("")
    add(f"*Доска: `{BOARD_PATH.name}` (правь статусы руками — при перезапуске они сохранятся). "
        f"Обновлено: {board['updated_at']}.*")
    add("")
    add(f"**Перспективные: {len(persp)} · Основной блок: {len(main)} · Отсев: {len(outset)}** "
        f"(всего {len(records)})")
    add("")
    add(f"Категории перспективных: {dict(by_cat.most_common())}")
    add("")
    add("> Как пользоваться: перспективные — рабочие кандидаты на отклик/кворк; основной — изучать по мере сил; "
        "отсев — не тратить время. Перетасовка руками: поменяй поле \"status\" в доске (perspective/main/outset).")
    add("")
    for cat, count in by_cat.most_common():
        add(f"## Перспективные: {cat} ({count})")
        add("")
        add("| вакансия/заказ | источник | дата | ЗП |")
        add("|---|---|---|---|")
        for r in [x for x in persp if x["category"] == cat][:25]:
            salary_mark = "✓" if r["has_salary"] == "yes" else "—"
            add(f"| {r['title'][:80]} | {r['source'].split(' ')[0]} | {r['date'] or '—'} | {salary_mark} |")
        if count > 25:
            add(f"*…ещё {count - 25} — в доске.*")
        add("")
    add("## Основной блок (изучать) — первые 25")
    add("")
    add("| вакансия/заказ | источник | дата | ЗП |")
    add("|---|---|---|---|")
    for r in main[:25]:
        salary_mark = "✓" if r["has_salary"] == "yes" else "—"
        add(f"| {r['title'][:80]} | {r['source'].split(' ')[0]} | {r['date'] or '—'} | {salary_mark} |")
    if len(main) > 25:
        add(f"*…ещё {len(main) - 25} — в доске.*")
    add("")
    if outset:
        add(f"## Отсев ({len(outset)})")
        add("")
        add("| вакансия | источник |")
        add("|---|---|")
        for r in outset[:15]:
            add(f"| {r['title'][:80]} | {r['source'].split(' ')[0]} |")
        add("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] доска: {BOARD_PATH}")
    print(f"[OK] отчёт: {REPORT_PATH}")
    print(f"Перспективные: {len(persp)} {dict(by_cat.most_common())}; "
          f"основной блок: {len(main)}; отсев: {len(outset)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
