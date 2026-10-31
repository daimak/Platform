#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Мост: результаты автосервисного парсера OLX -> очередь поручений Hunter.

Читает JSON парсера (по умолчанию tools/olx_autoservices_data.json) и создаёт
поручения Hunter штатной функцией hunter_store.create_assignment — с её
валидацией полей и атомарной записью (temp-файл + os.replace).

Безопасен по умолчанию: DRY-RUN — только показывает, что будет импортировано.
Запись выполняется только с флагом --apply. Дедупликация по URL объявления:
то, что уже лежит в очереди Hunter, пропускается. Отказывается работать при
запущенном дашборд-сервере (порт 8765): очередь Hunter защищена замком только
внутри процесса сервера, одновременная запись из двух процессов не согласована
— сначала остановите сервер.

Поддерживает оба формата данных парсера:
- список [{"title": ..., "url": ..., "description": ...}, ...] (olx_autoservices_data.json);
- словарь {"hh": [...], "olx": [...], "duckduckgo": [...]} (autoservices_data.json).

Запуск:
  python tools/ops/import_olx_to_hunter.py                 # план без записи
  python tools/ops/import_olx_to_hunter.py --apply         # импортировать
Опции: --file ПУТЬ, --category ИМЯ (quick-income|employment|organize|other)
"""

import argparse
import json
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BARRYMORE = ROOT / "tools" / "barrymore"
sys.path.insert(0, str(BARRYMORE))

import hunter_store  # noqa: E402

DEFAULT_DATA = ROOT / "tools" / "olx_autoservices_data.json"
DEFAULT_CATEGORY = "quick-income"
SERVER_PORT = 8765
MAX_TITLE = hunter_store.MAX_TITLE_LENGTH
MAX_DETAILS = hunter_store.MAX_DETAILS_LENGTH


def server_is_running() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", SERVER_PORT), timeout=0.5):
            return True
    except OSError:
        return False


def load_items(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        merged: list[dict] = []
        for source, items in data.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        item = {**item, "_source": source}
                        merged.append(item)
        return merged
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    raise ValueError(f"Непонятный формат данных: {path}")


def build_details(item: dict) -> str:
    url = str(item.get("url", "")).strip()
    description = str(item.get("description", "")).strip()
    parts = [url] if url else []
    if description and description not in ("Описание отсутствует", "Ошибка при получении описания"):
        parts.append(description)
    details = "\n\n".join(parts)
    return details[:MAX_DETAILS]


def main() -> int:
    parser = argparse.ArgumentParser(description="Импорт находок OLX-парсера в очередь Hunter")
    parser.add_argument("--file", type=Path, default=DEFAULT_DATA, help=f"JSON парсера (по умолчанию {DEFAULT_DATA})")
    parser.add_argument("--category", default=DEFAULT_CATEGORY, choices=sorted(hunter_store.CATEGORIES),
                        help=f"категория поручения (по умолчанию {DEFAULT_CATEGORY})")
    parser.add_argument("--apply", action="store_true", help="реально записать (без флага — только план)")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"[FAIL] файл данных не найден: {args.file}", file=sys.stderr)
        return 1
    if server_is_running():
        print(f"[FAIL] дашборд-сервер запущен (порт {SERVER_PORT}). Остановите его и повторите — "
              "очередь Hunter не рассчитана на запись из двух процессов.", file=sys.stderr)
        return 1

    try:
        items = load_items(args.file)
        existing = hunter_store.list_assignments()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1

    seen_texts = " \n".join(
        f"{a.get('title', '')} {a.get('details', '')}" for a in existing
    )

    planned = []
    skipped_duplicates = 0
    skipped_empty = 0
    for item in items:
        url = str(item.get("url", "")).strip()
        title = str(item.get("title", "")).strip()
        if not url or url == "Нет ссылки":
            skipped_empty += 1
            continue
        if url in seen_texts:
            skipped_duplicates += 1
            continue
        planned.append(item)

    source = args.file.name
    print(f"Файл: {args.file}")
    print(f"Записей в файле: {len(items)}; уже в Hunter: {skipped_duplicates}; без ссылки: {skipped_empty}; "
          f"к импорту: {len(planned)} (категория: {args.category} — {hunter_store.CATEGORIES[args.category]})")
    for item in planned[:5]:
        title = str(item.get("title", "")).strip()[:MAX_TITLE]
        print(f"  - {title} | {item.get('url', '')[:80]}")
    if len(planned) > 5:
        print(f"  ... и ещё {len(planned) - 5}")

    if not planned:
        print("Импортировать нечего — новых находок нет.")
        return 0
    if not args.apply:
        print("\nDRY-RUN: ничего не записано. Для импорта добавьте --apply.")
        return 0

    created = 0
    for item in planned:
        payload = {
            "category": args.category,
            "title": str(item.get("title", "")).strip()[:MAX_TITLE] or "Без названия",
            "details": build_details(item),
        }
        try:
            assignment = hunter_store.create_assignment(payload)
        except ValueError as error:
            print(f"[FAIL] {payload['title'][:60]}: {error}", file=sys.stderr)
            continue
        created += 1
        print(f"[OK] {assignment['id']}: {assignment['title'][:60]}")
    print("-" * 60)
    print(f"Создано {created} поручений из {len(planned)}; очередь теперь: "
          f"{len(hunter_store.list_assignments())} записей. (Источник: {source})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
