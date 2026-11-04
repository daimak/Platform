# olx_production.py — шпаргалка

Продакшен-парсер объявлений OLX.uz: цена (3 стратегии: state-JSON → HTML-карточки →
JSON-LD детальных страниц), дедуп по id/URL, вывод JSON + CSV, ретраи, вежливые паузы.

## Запуск

```bash
python tools/olx_production.py --query avtoservis --pages 2 --out olx_results

# несколько целей: запросы и категории можно повторять
python tools/olx_production.py \
  --query "iphone 15" \
  --category nedvizhimost/arenda-pomescheniy \
  --pages 2 --out tools/olx_production_data

# фильтр по цене (зарплатные job-объявления — по пересечению вилки)
python tools/olx_production.py --query iphone --min-price 3000000 --max-price 10000000

# добор цен по JSON-LD детальных страниц (бюджет запросов, максимум 15)
python tools/olx_production.py --query avtoservis --enrich-details 5
```

## Параметры

| Параметр | По умолчанию | Смысл |
|---|---|---|
| `--query` | — | поисковый запрос (можно повторять) |
| `--category` | — | категория: путь (`nedvizhimost/arenda-pomescheniy`) или полный URL (можно повторять) |
| `--pages` | 2 | страниц на цель, жёсткий потолок 4 (вежливость) |
| `--min-price` / `--max-price` | — | фильтр по числовой цене/вилке зарплаты |
| `--out` | `olx_results` | префикс: `PREFIX.json` + `PREFIX.csv` |
| `--enrich-details` | 0 | сколько детальных страниц запросить за недостающие цены (≤15) |
| `--delay-min/--delay-max` | 1.5 / 3.0 | пауза между запросами, сек |
| `--timeout` | 20 | таймаут HTTP, сек |

## Выход

- `PREFIX.json` — полные записи (цена, зарплата, локация, ISO-дата, id, флаги) + метрики.
- `PREFIX.csv` — плоские 21 колонок (utf-8-sig, открывается в Excel), колонка
  `price_source`: `state` / `state_salary` / `card_html` / `jsonld` / пусто.

## Ключевые метрики (stdout в конце)

`дубли %` · `с ценой %` · `с зарплатой %` · `любой ценовой показатель %` · `пустые поля` ·
время. Полные — в `meta.metrics` внутри JSON.

## Нюансы

- Категории не пагинируются через `?page=` (сервер игнорирует) — инструмент сам детектит
  и пропускает повторные страницы; у запросов `/list/q-.../` пагинация работает.
- Цены, которые продавец не ставил, не добрать (JSON-LD их не содержит) — это потолок сайта.
- Внутренний API `/api/v1/offers` цену не отдаёт — не использовать для цен.
- Полный разбор хрупких мест: `Workspace/analytics/research/2026-10-31-olx-production.md`.
- Зависимости: `pip install requests beautifulsoup4`. Git-команды в лейне запрещены.
