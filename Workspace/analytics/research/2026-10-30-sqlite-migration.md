# Исследование: миграция JSON-сторов на SQLite (однопользовательское Python-приложение)

Дата: 2026-10-30. Контекст: всё на Python stdlib, Windows, атомарная запись через `os.replace`, БД локальная (без сети). Планируется недельная история снапшотов и запросы: «дифф по URL между днями», «медианы зарплат по сегментам», «тренды источников».

---

## Сводка

**Вердикт: полноценная миграция не нужна; нужен гибрид — SQLite как производный аналитический индекс поверх JSON.**

Аргументы:
- Объёмы смешные для БД: день снапшота ≈ 544 KB, ~213 вакансий; неделя ≈ 1.5–2 тыс. строк. Ни SQLite, ни JSON не упрутся в производительность ещё долго.
- Но запрошенные запросы — **SQL-образные**: дифф множеств URL между днями, групповые медианы, тренды по (день × источник). Сейчас это будут ручные скрипты на `dict`/`set` в Python — каждый такой скрипт дублирует то, что SQLite делает одной декларативной строкой (`EXCEPT`, `GROUP BY`, оконные функции). Это и есть точка, где JSON-сторы начинают «сопротивляться».
- Задачный леджер и Hunter-очередь — документы и операционные очереди, а не запросные данные. Их в БД тащить не надо.

Практическая схема: **JSON-файлы остаются source of truth и git-следом; рядом живёт `jobs.db` — производный, регенерируемый (не в git), собранный скриптом импорта из снапшотов.** Нет двойной записи, нет рассинхрона «истин»: БД всегда можно снести и пересобрать из JSON за секунды.

---

## Что мигрировать, что оставить JSON (по нашим сторам)

| Стор | Решение | Почему |
|---|---|---|
| `Workspace/analytics/YYYY-MM-DD/raw/job_search_results.json` + `salary_extracted.csv` (~213 записей/день) | **В БД** (таблица `vacancies`, производный индекс) | Кросс-дневные множественные операции (дифф URL), медианы по сегментам, тренды — это SQL. Растёт с каждым днём. |
| `Workspace/analytics/YYYY-MM-DD/olx_structured.json` / `.csv` | **В БД** (таблица `olx_listings`, производный индекс) | То же: история по категориям rent/job/service/product, цены, тренды. |
| `Workspace/analytics/YYYY-MM-DD/token_usage.csv` / `TOKEN_USAGE_LOG.md` | Оставить, опц. таблица `token_usage` | Маленький, читается глазами; в БД — только если появятся запросы по стоимости моделей за период. |
| `manifest.json`, `report.md`, `stats.md`, `chunks/` | **Оставить как есть** | Человеко-читаемые артефакты дня, git-диффы по осмысленным изменениям. |
| `Memory/Engineering/Tasks/*.json` (~9 файлов) | **Не мигрировать никогда (ближайшим планом)** | Это документы, редактируемые руками и агентами; git-след по ним — фича, а не баг. Объём крошечный, запросов «по всем задачам за неделю» нет. БД здесь = потеря читаемости + новый слой записи без выгоды. |
| Hunter-очередь в `%LOCALAPPDATA%` | **Оставить JSON + `os.replace`** | Операционная очередь «прочитал-сделал-архивировал», не аналитика. Носить в SQLite стоит только если появятся сложные запросы по истории поручений. |

Когда JSON честно лучше (чтобы не переусложнить): человекочитаемые документы с ручным редактированием; один файл = одна логическая запись; объёмы до единиц МБ; уже решённая атомарность (`os.replace`); данные нужны «целиком», а не выборками. Анти-паттерн наоборот — городить на JSON ручные индексы, локи и множественные диффы в Python: это симуляция БД без БД. Мы ровно на границе первого анти-паттерна по вакансиям.

---

## Схема БД под вакансионную историю (DDL)

Файл, например: `Workspace/analytics/jobs.db` (производный, в `.gitignore`). Ключевая модель — **по строке на (день, URL)**: это прямое отражение дневных снапшотов и делает все три целевых запроса тривиальными.

```sql
PRAGMA journal_mode = WAL;        -- персистентно в файле БД, достаточно выполнить один раз
PRAGMA busy_timeout = 5000;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- Вакансии: срез "день x URL". Повторы дня = INSERT OR IGNORE (или upsert по нужде).
CREATE TABLE IF NOT EXISTS vacancies (
  date         TEXT    NOT NULL,           -- 'YYYY-MM-DD' из имени папки снапшота
  url          TEXT    NOT NULL,
  source       TEXT,                       -- 'olx.uz', 'hh.uz', ... (домен/доска)
  title        TEXT,
  category     TEXT,
  salary_min   REAL,
  salary_max   REAL,
  currency     TEXT,
  payload_json TEXT,                       -- запись целиком, json.dumps(..., ensure_ascii=False)
  PRIMARY KEY (date, url)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_vac_url    ON vacancies(url, date);
CREATE INDEX IF NOT EXISTS idx_vac_cat    ON vacancies(category, date);
CREATE INDEX IF NOT EXISTS idx_vac_salary ON vacancies(date, salary_min);

-- OLX-объявления (не вакансии): аренда/услуги/товары
CREATE TABLE IF NOT EXISTS olx_listings (
  date         TEXT    NOT NULL,
  url          TEXT    NOT NULL,
  kind         TEXT,                       -- rent | job | service | product
  title        TEXT,
  price_amount REAL,
  currency     TEXT,
  payload_json TEXT,
  PRIMARY KEY (date, url)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_olx_kind ON olx_listings(kind, date);

-- (опционально) расход токенов по дням
CREATE TABLE IF NOT EXISTS token_usage (
  date TEXT NOT NULL, ts TEXT, model TEXT, dir TEXT,   -- dir: in|out|cache
  tokens INTEGER, cost REAL,
  PRIMARY KEY (date, ts, model, dir)
) WITHOUT ROWID;

-- Служебное
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
PRAGMA user_version = 1;          -- версия схемы; миграции = "if user_version < N"
```

Целевые запросы:

```sql
-- Дифф по URL: новые в d1 относительно d2
SELECT url FROM vacancies WHERE date = :d1
EXCEPT
SELECT url FROM vacancies WHERE date = :d2;
-- (обратный EXCEPT = «исчезнувшие»; FULL OUTER JOIN по url даёт оба множества сразу)

-- Медиана зарплаты по сегменту (в SQLite НЕТ встроенного median(), паттерн через ROW_NUMBER)
SELECT category, AVG(salary_min) AS median_salary
FROM (
  SELECT category, salary_min,
         ROW_NUMBER() OVER (PARTITION BY category ORDER BY salary_min) AS rn,
         COUNT(*)     OVER (PARTITION BY category)                     AS cnt
  FROM vacancies
  WHERE date = :d AND salary_min IS NOT NULL
)
WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
GROUP BY category;

-- Тренд источников
SELECT date, source, COUNT(*) AS n
FROM vacancies GROUP BY date, source ORDER BY date, n DESC;
```

---

## План миграции на 1 вечер

1. **(15 мин)** `scripts/analytics/db.py` — `connect()` с прагмами (`journal_mode=WAL`, `busy_timeout=5000`, `synchronous=NORMAL`) и `init_schema()`: `CREATE TABLE IF NOT EXISTS ...` + `PRAGMA user_version`. Соединение с `isolation_level=None` и явным `BEGIN IMMEDIATE`/`COMMIT` (см. гоча №4).
2. **(30 мин)** `scripts/analytics/import_snapshots.py` — идемпотентный импорт: обходит `Workspace/analytics/*/`, читает `raw/job_search_results.json`, `salary_extracted.csv`, `olx_structured.json` → `INSERT OR IGNORE` пачками `executemany()` **в одной транзакции** (день = транзакция). Дата — из имени папки, не из содержимого.
3. **(15 мин)** Верификация: `COUNT(*) GROUP BY date` из БД сверить с `manifest.json` (`jobs.count`); spot-check 3 URL.
4. **(30 мин)** `scripts/analytics/queries.py` — три функции: `url_diff(d1, d2)` (EXCEPT в обе стороны), `median_by_segment(d)`, `source_trend()`; CLI через `argparse`. Это то, ради чего всё затевалось.
5. **(10 мин)** `.gitignore`: `Workspace/analytics/*.db`, `*.db-wal`, `*.db-shm`. JSON остаётся в git — читаемый след никуда не девается. Пометить в `analytics/README.md`, что `jobs.db` — регенерируемый производный.
6. **(опц., 15 мин)** Импорт `token_usage`. Задачный леджер и Hunter-очередь **не трогать**.

Откат тривиален: снести `jobs.db` — вся система продолжает жить на JSON, как сегодня.

---

## Гочи Windows + WAL

1. **WAL — только на локальном NTFS.** У нас `C:\Work\Platform` локальный — ок. Но: **никогда** не класть `.db` в папку, синхронизируемую OneDrive/Dropbox (клиент не уважает локи SQLite → «database is locked», конфликты, коррупция и откат файла к старой версии), и не на сетевые/SMB-шары (ломается вся lock-модель и `-shm`, это не лечится WAL, а усугубляется им).
2. **«Один файл БД» — иллюзия при WAL.** Рядом лежат `jobs.db-wal` и `jobs.db-shm`. Копировать/бэкапить только через `con.backup()` или `VACUUM INTO 'backup.db'` — голый `cp` недозаписанного WAL-файла даёт битую копию.
3. **Антивирус.** Windows Defender/сканеры, держащие файл открытым, — частая причина спорадических `SQLITE_BUSY` на локальном диске; лечится исключением папки из сканирования.
4. **`busy_timeout` не спасает везде.** Он работает при попытке стартовать транзакцию, но «upgrade» отложенной read-транзакции до записи даёт немедленный `SQLITE_BUSY` без ретраев. Практика: `isolation_level=None` + явный `BEGIN IMMEDIATE` для записей (или `isolation_level="IMMEDIATE"`) и один писатель.
5. **Python 3.12+:** параметр `autocommit` новый, legacy-механика `isolation_level` объявлена устаревающей; известная ловушка — `sqlite3.connect(autocommit=False)` ломает `executescript()` (он неявно коммитит). Для простоты: `isolation_level=None` + ручные `BEGIN IMMEDIATE`, и не смешивать оба механизма.
6. **Bulk-load:** `executemany()` внутри одной транзакции; индексы (у нас PK уже есть — ок) не пересоздавать на каждый импорт; на наших объёмах всё займёт миллисекунды.
7. `PRAGMA journal_mode=WAL` персистентен в файле, `busy_timeout` — **per-connection** (задавать в `connect()` всегда). Атомарность через `os.replace` для записей, попадающих в БД, больше не нужна — транзакции её заменяют; для JSON-сторов оставить как есть.

---

## FTS5: брать не сразу

При 1.5–2 тыс. строк за неделю обычный `LIKE '%query%'` по `title`/`payload_json` отвечает за миллисекунды — FTS5 ничего не даёт по скорости. Брать, когда: (а) объём > ~50 тыс. строк, (б) нужен ранжинг релевантности (`bm25()`), поиск по словоформам (`tokenize='porter'`), префиксные/фразовые запросы. Включение копеечное (встроен в stdlib-сборку; проверить `SELECT sqlite_compileoption_used('ENABLE_FTS5');`), так что это «потом, за 20 минут», а не «сейчас». Резерв уже заложен: `payload_json` — готовый источник для external-content FTS-таблицы (`content='vacancies'`), без дублирования данных.

---

## Источники

- [SQLite As An Application File Format](https://www.sqlite.org/appfileformat.html) — канон про SQLite как формат файла приложения.
- [Using SQLite as a Custom File Format (M. Summerfield)](https://mark-summerfield.github.io/pysqlite.html) — замена JSON/XML-форматов на SQLite.
- [Simon Willison: isolation_level="IMMEDIATE"](https://simonwillison.net/2024/Jun/19/isolation-level-immediate/) — против `SQLITE_BUSY` при upgrade-транзакциях.
- [Simon Willison: declarative schema migration gist](https://gist.github.com/simonw/664b4b0851c1899dc55e1fb655181037) — паттерн миграций через `user_version` без зависимостей.
- [Python docs: sqlite3](https://docs.python.org/3/library/sqlite3.html) — `autocommit`/`isolation_level`, управление транзакциями.
- [CPython issue #112441](https://github.com/python/cpython/issues/112441) — гоча `autocommit=False` + `executescript()`.
- [SQLite FTS5](https://www.sqlite.org/fts5.html) — официальная документация полнотекстового модуля.
- [SQLite percentile extension](https://www.sqlite.org/percentile.html) + [Built-in Aggregate Functions](https://www.sqlite.org/lang_aggfunc.html) — почему `median()` нет из коробки.
- [SQLite throws 'database locked' way before timeout (SO)](https://stackoverflow.com/questions/77780582/sqlite-throws-database-locked-exception-way-before-timeout-has-passed) и [berthub.eu про SQLITE_BUSY](https://berthub.eu/articles/posts/a-brief-post-on-sqlite3-database-locked-despite-timeout) — пределы `busy_timeout`.
- [SQLite on Azure Files SMB: A Debugging Story](https://dev.to/argha_dev/sqlite-on-azure-files-smb-a-debugging-story-with-a-humbling-ending-1p93) и [SQLite forum: locking over network](https://sqlite.org/forum/info/a6675453ecd9af62d13d55fb38562a2e93c434c57f7994b34a4fae91506a3214) — почему WAL+сеть не работают.
- [OneDrive + SQLite locking (skilion/onedrive #54)](https://github.com/skilion/onedrive/issues/54) и [Synopse forum: SQLite в синхронизируемых папках](https://synopse.info/forum/viewtopic.php?id=5542) — коррупция в облако-синхронизируемых папках.
- [Getting the most out of SQLite3 with Python (remusao)](https://remusao.github.io/posts/few-tips-sqlite-perf.html) — `executemany`, транзакции, прагмы для bulk-load.
- [Flat File vs Relational DB for Single User Desktop App (SE.SE)](https://softwareengineering.stackexchange.com/questions/369750/flat-file-vs-relational-database-for-single-user-desktop-application) — когда плоские файлы честно достаточны.
