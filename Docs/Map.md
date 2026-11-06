# Карта репозитория Platform Evo

Дата съёмки: 2026-10-22; обновлён 2026-10-25 (реструктуризация контура — RFC-001); актуализирован 2026-10-31; актуализирован 2026-11-06 (фундамент данных Л-1…Л-5, канбан, миры, итоги ночной смены 05.11)  
Состояние: `VERSION` = 1.8.4 (заметки — `Docs/Releases/v1.8.4.md`; файл версии не поднят); активная ветка `release/1.8.6`, HEAD — коммит `a3ca29e develop/v1.8.6` (ночной журнал помечает его как «чужой» — вероятна параллельная сессия, флот git не использует; не откатывать и не судить вслепую). Рабочее дерево общее с параллельными сессиями: на утро 06.11 в нём изменены `eVo/dashboard/brief.js`, `hunter-report.js`, `orders-triage.js`, файлы `Workspace/higgsfield-pilot/`, `Docs/NIGHT-LOG-2026-11-05-ZCode.md`, карточка `higgsfield-pilot-test` — чужие правки не смешивать и не коммитить. Модель веток — D-002; слияние origin/main выполнено 04.11 (E-046), задача `merge-branches-d002` закрыта.  
Назначение: не изучать дерево проекта с нуля. Это фактическое состояние репозитория, а не целевая архитектура.

Смежные точки входа:

- идея системы: `README.md`
- быстрый вход для нового ИИ-ассистента: `Docs/AI-ONBOARDING.md` (снимок 06.11)
- точка входа смены: `Docs/ENTRY-POINT-2026-11-01-PM-ZCode.md`
- итоги ночной смены: `Docs/NIGHT-LOG-2026-11-05-ZCode.md`
- принципы: `Core/Principles.md`
- текущий фокус: `Memory/Context/CURRENT.md` (отстаёт от реальности, см. ниже)
- канонический реестр миров: `Memory/Worlds/README.md`
- каталоги по задумке: `Docs/Architecture/Structure.md`
- индекс архитектуры: `Docs/Architecture/README.md`

---

## Что это

Персональная «операционная система эволюции». Основа — обычные файлы (markdown + статический UI). Принцип: хранить не только результаты, но и контекст, почему они появились.

Рабочий код вторичен, но уже не пуст. Главный runnable-артефакт — карта Estate в `eVo/dashboard/`; при ней живёт loopback-сервер Barrymore (`tools/barrymore/dashboard-server.py`, `127.0.0.1:8765`) с ограниченным локальным API, машинный журнал событий `Workspace/logs/events.jsonl` и агентный рантайм `tools/agents/`. Внешних серверов и базы данных нет.

---

## Каталоги верхнего уровня

| Каталог | Задумка | Факт на 2026-11-06 |
|---|---|---|
| `Core/` | Ядро: принципы, глоссарий, ADR | Документы, не runtime; ADR-001…005 + INDEX |
| `eVo/` | Стюард: состояние, планирование, Command Center | Живой UI: `dashboard/` (миры, канбан, карта мира); `graphify-out/` (кэш), `scripts/`; рантайм агентов в `tools/agents/` |
| `Memory/` | Долговременный контекст системы | Markdown: CURRENT, сессии, решения, идеи; `Worlds/` — реестр архипелагов; `Agents/` — 16 паспортов + `estate-staff.json` |
| `Memory/Engineering/` | — (создан 25.10.2026) | Инженерный журнал: STATE, PLAN, FINDINGS, README; `LOG.md` — журнал E-001…E-047; `Reports/` (аудиты Холмса), `Tasks/` — task-лиджер (`Active/` — 20 карточек на 06.11) |
| `Interface/` | Способы взаимодействия с системой | Отдельный прототип Vue 3 + TypeScript + Vite, не runtime основного UI |
| `Workspace/` | Пользовательские проекты и артефакты | Аналитический контур `analytics/` (снапшоты по дням, `research/`, `token-spend/`, `hunter/`), `logs/` (машинный журнал, gitignored), `private/` (приватная зона Sovereign, gitignored), `higgsfield-pilot/`, `pentest/` + `reports/` (вне git), `main.py` (LangSmith Engine), `.env` (секреты, untracked) / `.env.example` |
| `Modules/` | Предметные домены | Почти пусто (`Carrier.md`) |
| `Vision/` | Концепты, визуал, истории Estate | Идеи и изображения |
| `tools/` | Скрипты обслуживания, протокол Barrymore | Python (агенты, аналитика, `lib/`, `ops/`, `security/`, тесты) + PowerShell + markdown-задачи; закоммичены (санитария 04.11, E-046) |
| `kali/` | Полигон Kali | Каталог в корне, gitignored; VM 192.168.238.128, снапшот `pre-pentest-2026-11-04`, SSH/guest-ops выключены (E-047) |
| `Docs/` | Архитектурные документы | Architecture/, Releases/ (v1.8.3, v1.8.4), Map, AI-ONBOARDING, Barrymore, Ops + планы и журналы смен (DATA-FOUNDATION-PLAN-2026-11-04, NIGHT-LOG-2026-11-05, AGENT-FLEET-PLAN, ENTRY-POINT-2026-11-01×2, KALI-*, SCRAPERS-LANDSCAPE и др.) |
| `RFC/` | Предложения изменений | README + процесс, каталоги Accepted/Backlog/Drafts/Rejected; RFC-001 (границы контура) — Accepted (файл лежит в `Drafts/`, статус внутри) |
| `Notes/` | Входящий поток | Inbox.md, Questions.md, evo-test-run.md |
| `Data/` | Служебные данные | `token_usage.json` — статические числа из v1.8.4, кодом не читаются; судьба решается (см. `tools/ops/README.md`) |
| `Backup/` | Старые визуалы Estate | Вынесен за контур 25.10.2026 в `C:/Work/Platform-archive/` (RFC-001); в дереве нет |
| `.obsidian/` | Настройки Obsidian | В корне отсутствует; правила остались в `.gitignore` |
| `.github/` | Мета репозитория | `copilot-instructions.md` |

В корне: `README.md`, `CHANGELOG.md`, `VERSION` (1.8.4), `PLATFORM.md`, `SYSTEM_SUMMARY.md`, `TOKEN_USAGE_LOG.md` (регенерируемый журнал, gitignored), `skills-lock.json`, `job_search_results.json`, `links.txt` (untracked); сервисные каталоги `.agents/`, `.aider-desk/`, `.zcode/`, `.vscode/` (gitignored) и мета — `.gitignore`, `.gitattributes`, `.claudeignore`, `.github/`. Корень снова разросся: правило «точки входа только в `Docs/` и `Notes/`» соблюдается не полностью.

---

## Где лежит рабочий код

### Estate dashboard (основной UI)

Путь: `eVo/dashboard/`

- `index.html` — карта островов, мир Estate (Level 1)
- `style.css`, `app.js` (`?v=12`), `languages.js` (`?v=3`) — взаимодействие и RU/EN
- `brief.js` — сгенерированный снимок Morning Brief (`window.EVO_BRIEF`); не править руками
- `workspace.html` — рабочий кабинет (Level 3)
- `engine-core.html/css/js` — мир Engine Core Atoll: консоль инженерного центра + переход в кабинет Hunter
- `maelstorm.html` — мир Maelstorm, исследовательский архипелаг
- `world-map.html` (+ `world-map-review.html`) — карта мира: маршрут корабля между тремя архипелагами; кнопка «🗺» в HUD каждого мира; корабль — `harbor-ship.css/js` (`ROUTE_PX`), фон `assets/world-map-v1.png`
- `kanban.html` + `kanban.js` (`?v=6`) — канбан лиджера: колонки Анализ → Сделать → В работе → Проверка → Готово; drag на pointer-механике (мышь и тач), клик = модалка карточки; переходы — `POST /api/tasks/<id>/stage/<колонка>` с подписью `by`
- `holmes.html` — кабинет Холмса (отчёты аудита из `/api/holmes/reports`, галочка инициативы → `/api/holmes/implement`)
- `ai-usage.html/css/js`, `ai-sandbox-history.html` — учёт AI-использования и журнал AI Sandbox
- «Целевой стенд» в модалке AI Sandbox (в `app.js`, E-047): чипы целей, галочки проверок (быстрый/все порты, CVE, внешние цели), прогон через `/api/sandbox/run`
- `tasks.js` — задачи Баррримора (localStorage + счётчик на плашке)
- `vacancies.js` (автогенерация `tools/job_search.py --js`), `orders-triage.js` (автогенерация `tools/orders_triage.py`), `hunter-report.js` (автогенерация `tools/hunter/report.py`) — не править руками
- `projects/` — скины-темы (`marvel_v`, `minimalism`, `organica`; к мирам не подключены, активный — `active_project.json`)
- `locales/` — JSON-локали (дублируют часть `languages.js`)
- `assets/estate_bg.png`, `assets/barrymore.png`, `assets/world-map-v1.png` — фоны и слой-портрет

Поведение: клик по острову открывает модалку. Задачи рычагов живут в `localStorage`. Morning Brief на острове Barrymore — живой: данные собирает генератор `tools/barrymore/morning-brief-agent.py`, свежий доклад отдаёт локальный сервер (`/api/refresh-brief`), статический снимок — `brief.js`.

Миры и острова: канон — `Memory/Worlds/README.md` (правило «кто живёт — `Memory/Agents`, где живут — `Memory/Worlds`»). Три архипелага: Estate (`index.html`), Engine Core Atoll (`engine-core.html`), Maelstorm (`maelstorm.html`). Острова Estate: Trading Quarter, Harbor, Navigation Observatory (Магеллан, Хантер), Memory Library, AI Sandbox, Workshop, Study, Sinbad Market. Бэрримор — кликабельная HTML-плашка в верхнем левом секторе (панель + слой-портрет, приветствие по времени суток, счётчик задач `tasks.js`). Инструкция — `Docs/Barrymore.md`.

### Trading Quarter — рынок вакансий и заказов

Модалка острова с вкладками:

- «Вакансии» — данные из `eVo/dashboard/vacancies.js` (автогенерация `tools/job_search.py --js`; агрегатор RemoteOK / Remotive / hh / HN / Telegram и др.). Группы источников свёрнуты по умолчанию, состояние раскрытия — `localStorage` (`evo_vacancies_expanded`).
- «Заказы» — биржи фриланса аккордеонами (fl.ru, upwork открыты по умолчанию) + репосты заказов из Telegram-каналов живой лентой.
- «Радар» — триаж заказов: `tools/orders_triage.py` ведёт доску `Workspace/analytics/orders_board.json` (ручные статусы сохраняются при перезапуске) и отчёт `orders_report.md` («Радар денег»); данные вкладки — `orders-triage.js`.

### Аналитический контур (с 29.10)

Снапшоты по дням: `Workspace/analytics/YYYY-MM-DD/` — на 06.11 пять прогонов: `2026-10-29`, `2026-11-01`, `2026-11-04`, `2026-11-05`, `2026-11-06` (внутри: `raw/` — копии живых источников, `chunks/` — LLM-готовые чанки, `jobs.csv`, `token_usage.csv`, `salary_extracted.csv` + кэш, `stats.md`, `manifest.json`; состав слегка меняется от дня ко дню).

Строитель — `tools/analytics_snapshot.py` (stdlib-only, ADR-003/004): читает `tools/job_search_results.json`, `tools/olx_autoservices_data.json`, `tools/autoservices_data.json`, корневой `TOKEN_USAGE_LOG.md` и пишет датированную папку; успешный прогон дописывает событие `snapshot.completed` в машинный журнал. Вспомогательное: `tools/analytics_report.py`, `tools/analytics_salary_extract.py`, `tools/orders_triage.py`, `tools/hunter/report.py` (digest Хантера → `Workspace/analytics/hunter/digest.json` + `hunter-report.js`). Рядом: `Workspace/analytics/token-spend/` (`ledger.jsonl` — замер расхода токенов z.ai, `tools/ops/token_meter.py`).

Тесты — `tools/tests/` (7 файлов, 48 тестов: аналитика, envelope, log_event, jobs registry, kanban metrics, task by, dashboard static). Research-отчёты в `Workspace/analytics/research/`: волны 30–31.10 (money-plan, agents-landscape, sqlite-migration, hosting-when-ready, jobs-data-quality ×2, interface-regression, hh406-experiments, money-radar-deep, olx-production, vacancy-requirements-matrix) и `2026-11-04-golang-hypothesis.md`; служебные файлы волн — `_wave*-state.md`, `_agents-2026-11-04/`.

### Фундамент данных (Л-1…Л-5, исполнено в ночь 05.11)

Единый формат фактуры + единый журнал + единый диспетчер (ТЗ — `Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md`; верифицировано ZCode, карточка в «Проверке»):

- `tools/lib/envelope.py` — конверт артефактов: `make_envelope` / `validate_envelope`; `schema_id` — два-три ascii-сегмента через точку (`evo.log.event`, `evo.ops.job_state`, `evo.resume.master`…)
- `tools/lib/log_event.py` — машинный журнал: `append_event(kind, source, payload)` дозаписывает JSONL-конверт в `Workspace/logs/events.jsonl` (gitignored, регенерируемый); исключение при записи наружу не выходит
- `tools/ops/jobs.json` — реестр джобов (`analytics-snapshot`, `token-meter`, `healthcheck`); сервер: `GET /api/jobs` + `POST /api/jobs/<id>/run`, статусы последнего запуска — `Workspace/logs/jobs_state.json` (envelope `evo.ops.job_state`)
- `tools/barrymore/task_store.py` — подписанные переходы: `set_stage()` / `mark_done()` принимают `by`, каждая новая запись history получает `"by"`; переход дублируется в журнал событием `task.stage`; `POST /api/tasks/<id>/stage/<col>` читает `by` из JSON-body (дефолт Sovereign). Записи без `by` — «до эпохи подписей», не мигрируют
- `tools/ops/kanban_metrics.py` — метрики конвейера: 4 блока (закрыто за 7 дней, средний возраст in-progress, карточки старше 7 дней, переходы по авторам) с fallбэком по `history[].by`; вывод — текст + JSON-envelope `evo.kanban.metrics`

### Резюме-конвейер и пилоты (Workspace/)

- `Workspace/private/` — приватная зона данных Sovereign (gitignored). Внутри — зона резюме-конвейера (`resume/`: master-профиль, кейсы RU+EN, `proposals/2026-11-05/` — 10 откликов) и `proposals/`. Ночная смена 05.11 наполнила зону (блокер «пустая резюме-зона» снят); содержимое НЕ картографируется, не показывается в UI и не коммитится.
- `Workspace/higgsfield-pilot/` — пилот Higgsfield: `pilot.py` (с `REAL_PAYMENT_SANCTIONED=False`), `pilot-report.json`, `progress.md`, главный артефакт `HIGGSFIELD-DOCS-2026-11-05.md` (~54 KB, 18 разделов по живым докам), `docs-cache/`, `openapi.json`, `dry-run-log.txt`. Платных вызовов 0; ждёт ключ в `Workspace/.env` и санкцию Sovereign. Карточка в «Проверке».
- `Workspace/pentest/`, `Workspace/reports/` — вне git: VULN-PROGRAM 12V/12I (`2026-11-04-vuln-program/VULN-PROGRAM.md`), ночные отчёты смен.

### Vue-каркас — снова в дереве, не runtime

`Interface/` был удалён по RFC-001 25.10.2026, но снова присутствует в дереве: отдельный прототип Vue 3 + TypeScript + Vite. Это не runtime основного UI: реальный интерфейс — `eVo/dashboard/` (так же трактует его и `Docs/AI-ONBOARDING.md`).

### Инструменты

- `tools/barrymore/dashboard-server.py` — loopback-сервер дашборда (`127.0.0.1:8765`). GET: `/api/tasks`, `/api/staff`, `/api/hunter/tasks`, `/api/ai-usage`, `/api/security/status`, `/api/{watson|riskscan}/reports`, `/api/{watson|riskscan}/run-status`, `/api/holmes/reports`, `/api/holmes/context`, `/api/holmes/run-status`, `/api/sandbox/run-status`, `/api/sandbox/report`, `/api/jobs`. POST: `/api/tasks/<id>/done`, `/api/tasks/<id>/stage/<analysis|todo|in-progress|test|done>` (by из body), `/api/jobs/<id>/run`, `/api/hunter/tasks`, `/api/security/check`, `/api/security/targets`, `/api/holmes/implement`, `/api/holmes/run`, `/api/watson/run`, `/api/riskscan/run`, `/api/sandbox/run`, `/api/ai-usage/snapshots`, `/api/ai-usage/settings`, `/api/ai-usage/ask-barrymore`, `/api/refresh-brief`. POST-эндпоинты проверяют заголовок `Origin: http://127.0.0.1:8765` — curl без него получает 403
- `tools/barrymore/morning-brief-agent.py` — детерминированный генератор Morning Brief + LLM-агент (локальный FreeLLMAPI-шлюз, stdlib-only). Находка F1 (неатомарная запись `brief.js`, `OUT_PATH.write_text`) всё ещё не исправлена
- `tools/barrymore/task_store.py` — task-лиджер: валидация, атомарная запись, подписи `by` в переходах, дублирование их в журнал; архивация done-задач через 48 ч в `Tasks/Archive/YYYY/MM/`
- `tools/barrymore/ai_usage.py`, `security_contour.py`, `hunter_store.py`, `logger.py` + их `test_*.py` — учёт AI-использования, защищённый контур, очередь Hunter
- `tools/agents/registry.json` (v5) + `tools/agents/run_agent.py` — агентный рантайм (см. «Агенты и боты»)
- `tools/lib/` — конверты и журнал (см. «Фундамент данных»)
- `tools/ops/` — `backup_workspace.py`, `healthcheck.py`, `import_olx_to_hunter.py`, `token_meter.py`, `jobs.json`, `kanban_metrics.py` + README-план; закоммичены (99a45f7)
- `tools/security/` — прототипы (тест 02.11, E-043): `vuln_radar.py` (CISA KEV + EPSS + NVD), `port_audit.py` + `port_allowlist.json`, `secret_scan.py`, `nmap_probe.py`, `common.py`. Кнопки — во вкладке «Инструменты» модалки AI Sandbox (`/api/sandbox/*`); отчёты — в `%LOCALAPPDATA%\Platform\SecurityReports\`, вне git
- `tools/pentest/` — цели pentest (README, TARGETS); `tools/hh406-lab/` — лаборатория обхода hh-406 (эксперименты 31.10, gitignored)
- `tools/hunter/report.py` — digest Хантера; `tools/analytics_snapshot.py`, `tools/job_search.py` (`--js` → `vacancies.js`), `tools/analytics_report.py`, `tools/analytics_salary_extract.py`, `tools/orders_triage.py` — аналитический контур
- `tools/tests/` (7 файлов, 48 тестов) + `tools/barrymore/test_*.py` (5 файлов, 35 тестов) — сьюты 48+35, зелёные по ночной верификации 05.11
- `tools/evo-check.ps1` — git release-gate (ветка, dirty, последний коммит)
- `tools/evo-save.ps1` — интерактивные add / commit / push
- `tools/barrymore/execute.ps1` — add + commit + отчёт в `tools/barrymore/reports/`
- `tools/barrymore/install-dashboard.ps1` — однократная установка автозапуска локального сервера при входе в Windows
- `eVo/scripts/bootstrap.ps1` — **создаёт** папки `agents/`, `runtime/`; не запускать без нужды
- `.vscode/tasks.json` — Add / Commit / Push

### Сгенерированный граф кода

Графа два: `eVo/graphify-out/` — кэш Graphify, не исходники; с 25.10.2026 не отслеживается Git (пересобирается). И корневой `graphify-out/` — отчётные файлы отслеживаются, кэш/манифест — нет (правила в `.gitignore`). Для навигации по связям файлов (`graphify query "..."`), не для правки.

---

## Как запускать

1. **Главный интерфейс:** `http://127.0.0.1:8765` (однократная установка автозапуска — `tools/barrymore/install-dashboard.ps1`; сервер стартует при входе в Windows и слушает только loopback). Без сервера карта открывается файлом `eVo/dashboard/index.html`, но живые данные (brief, задачи, Холмс, джобы) не обновятся.
2. **Morning Brief (Баррримор):** refresh-кнопка в дашборде, либо `python tools/barrymore/morning-brief-agent.py` (данные + доклад LLM) или `powershell tools/barrymore/morning-brief.ps1` (только данные); инструкция пользователя — `Docs/Barrymore.md`.
3. **Агентный рантайм:** `python tools/agents/run_agent.py --agent Holmes` (так же Watson, RiskScan; с `--no-llm` — детерминированный прогон без шлюза).
4. **Аналитика:** `python tools/analytics_snapshot.py [YYYY-MM-DD]` (создаёт `Workspace/analytics/YYYY-MM-DD/` + событие в журнал), `python tools/orders_triage.py` (радар заказов).
5. **Канбан-метрики:** `python tools/ops/kanban_metrics.py` (текст + JSON-envelope); джобы — `GET /api/jobs`, `POST /api/jobs/<id>/run` (UI-кнопок нет).
6. **Тесты:** `python -m unittest discover -s tools/tests` (48) и `python -m unittest discover -s tools/barrymore -p "test_*.py"` (35).
7. **Состояние системы** смотреть в файлах и Git, не в UI: хвост `Memory/Engineering/LOG.md` (E-001…E-047), `Memory/Engineering/PLAN.md`, task-лиджер `Memory/Engineering/Tasks/Active/` (20 карточек), машинный журнал `Workspace/logs/events.jsonl`.

---

## Агенты и боты

Агентный рантайм — `tools/agents/`: `registry.json` (**v5**, 04.11: каждый инструмент описывает контракт, права выдаются агенту явно по паспорту, всё read-only, кроме явно утверждённого; новые инструменты `git.diff` (diff/show read-only с маскированием секретов) и агенты Watson/RiskScan; новые поля агента `findings_kind/report_tag/report_glob/task_line`) и `run_agent.py` (запуск агента по паспорту, stdlib-only; параметризован вычислителями находок `compute_watson_findings` / `compute_riskscan_findings`; LLM — через локальный OpenAI-совместимый шлюз, модель не имеет доступа к ОС — ADR-004).

- **Barrymore** — стюард, частично активен (паспорт `Memory/Agents/Barrymore.md`). Рантайм: Morning Brief + локальный сервер. Оркестрация субагентами — целевое состояние.
- **Holmes** — аудит и расследования (`Memory/Agents/Holmes.md`). Права: read-only инструменты + единственное право записи `report.write` — отчёт `Memory/Engineering/Reports/Report-ГГГГ-ММ-ДД-holmes-audit.md` (прогоны 29.10, 30.10, 04.11). Инициативы из отчёта превращаются в задачи только через дашборд: галочки в модалке Холмса → `/api/holmes/implement` (санкция Sovereign).
- **Watson** — офицер полигона Kali и сверка хроники (E-044: роль снята с Лестрейда; паспорт `Memory/Agents/Watson.md`). Рантайм: кнопка «Сверка хроники» в Memory Library и кнопки в панели штата; `POST /api/watson/run`. Первые прогоны 04.11 поймали реальные пропуски E-003–005 в журнале.
- **RiskScan** — риск-скан диффов (паспорт `Memory/Agents/RiskScan.md`, на службе с 04.11); `POST /api/riskscan/run`.
- **Hunter** — локальная очередь поручений (`/api/hunter/tasks`), сидит на Navigation Observatory (E-041); digest — `tools/hunter/report.py`. Автономный поиск вакансий не подключён.
- **Solomon, Maelstorm** — роли с кабинетами/маячками на карте; отдельного рантайма нет.
- **Штат:** `Memory/Agents/` — 16 паспортов: 10 именных сущностей (Magellan, Cyrus Smith, Hephaestus, Watson, Nemo, Paganel, Bender, Sindbad, Leonardo, Maelstorm — E-042) + Barrymore, Holmes, Hunter, Solomon, RiskScan + `estate-staff.json`. Реальный рантайм у четверых: Хантер, Бэрримор (кратко), Холмс, Ватсон (E-045).
- Границы — ADR-003 (read-only), ADR-004 (доступ только через tools), ADR-005 («всё — инструмент»); индекс ADR — `Core/Architecture/ADR/INDEX.md`.
- Реестр миров — `Memory/Worlds/README.md`; концепты команды — `Memory/New_ideas/estate_archipelago_agents.md`, `Memory/New_ideas/syndicate_architecture.md`; ландшафт агентов — `Docs/AGENTS-LANDSCAPE-2026-10-29-ZCode.md`; план флота — `Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md`. Личный штат `~/.zcode/agents/` — 6 ролей, доступны как суб-агенты ZCode.
- Планируемые, но не созданные каталоги: `eVo/agents/`, `eVo/runtime/`; фактический рантайм агентов живёт в `tools/agents/`.

---

## Ключевые файлы контекста

| Файл | Зачем |
|---|---|
| `README.md` | Единственная точка входа в корень |
| `VERSION` + `Docs/Releases/` | Текущая версия (1.8.4) и заметки релизов |
| `Docs/AI-ONBOARDING.md` | Быстрый вход для нового ИИ-ассистента (снимок 06.11) |
| `Memory/Engineering/LOG.md` | Инженерный журнал E-NNN (хвост — E-047, 04.11); читать последние записи перед началом работы |
| `Workspace/logs/events.jsonl` | Машинный журнал событий (gitignored): пульсы агентов, task.stage, snapshot.completed |
| `Memory/Worlds/README.md` | Канонический реестр миров + карта источников |
| `Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md` | ТЗ фундамента данных (лейны Л-1…Л-5) |
| `Docs/NIGHT-LOG-2026-11-05-ZCode.md` | Итоги ночной смены 05.11 (data-foundation, резюме-конвейер, Higgsfield) |
| `Memory/Context/CURRENT.md` | Текущий фокус и next action (отстаёт от реальности) |
| `CHANGELOG.md` | Хроника изменений |
| `Docs/Architecture/README.md` | Индекс архитектуры |
| `Core/Architecture/ADR/ADR-002-Island-Architecture-Model.md` | Модель островов |
| `tools/agents/registry.json` | Реестр инструментов и прав агентов (v5) |
| `Memory/Agents/README.md` | Стандарт паспортов агентов |
| `Memory/Engineering/Tasks/Active/` | Task-лиджер — фактический список активных задач |
| `tools/barrymore/TASK-PROTOCOL.md` | Как должен работать Barrymore |
| `Workspace/eVo/Planning/Epics/EPIC-001-Control-And-Visibility.md` | Контроль и видимость изменений |

`CURRENT.md` отстаёт от реальности (задача `update-current-context` всё ещё в лиджере). Фактический план работ — `Memory/Engineering/PLAN.md` и task-лиджер `Memory/Engineering/Tasks/Active/` (20 карточек на 06.11: `data-foundation` и `higgsfield-pilot-test` в «Проверке», holmes-* находки, security-, staff- и money-задачи).

---

## Самый маленький следующий прототип

Устарело: минимальные шаги прежних разделов (Morning Brief, канбан, фундамент данных) реализованы — детерминированный генератор + сервер (25–29.10), канбан v6 с подписанными переходами (05.11), лейны Л-1…Л-5 исполнены и верифицированы (ночь 05.11).

Следующий минимальный шаг выбирается из task-лиджера `Memory/Engineering/Tasks/Active/` и санкций Sovereign. На 06.11 в очереди: «Флот в море» (agents-fleet), рестарт сервера 8765 с осмотром diff ночных лейнов (решение за Sovereign), Higgsfield-пилот ждёт ключа в `Workspace/.env` и санкции платежа (потолок первого живого цикла $1).

---

## Правила для следующих сессий

1. Сначала этот файл, затем хвост `Memory/Engineering/LOG.md` (E-NNN), `CURRENT.md` (помня, что он отстаёт) и `Docs/AI-ONBOARDING.md`.
2. Не путать `Interface/` (отдельный Vue/Vite-прототип, не runtime) с `eVo/dashboard/` (реальный UI).
3. Не приписывать агентам больше прав, чем в `tools/agents/registry.json` (v5): всё read-only; запись — только `report.write` Холмса и санкционированные API дашборда (`/api/holmes/implement`, Mark Done, stage-переходы канбана).
4. Не запускать `bootstrap.ps1` без явной задачи: он пишет файлы.
5. `eVo/graphify-out/` и корневой `graphify-out/` не править вручную; `brief.js`, `vacancies.js`, `orders-triage.js`, `hunter-report.js` — автогенерация, править их источники, не сами файлы.
6. Секреты — в `Workspace/.env` (untracked, шаблон `.env.example`); не читать и не выводить значения.
7. `Workspace/private/` — приватная зона данных Sovereign (gitignored): не читать, не выводить, не коммитить; в картах — только факт существования зоны и gitignore.
8. Машинный журнал `Workspace/logs/events.jsonl` — только дозапись через `tools.lib.log_event.append_event` внутри try/except (падение журнала не должно ломать вызывающий код); файл gitignored, чистить/переписывать его нельзя.
9. Канбан: переходы карточек — только через `task_store` (`POST /api/tasks/<id>/stage/<col>` с `by` или вызов `set_stage`), не правкой JSON руками; каждая запись history должна нести подпись `by`.
10. POST-эндпоинты сервера 8765 требуют заголовок `Origin: http://127.0.0.1:8765` — curl/скрипты без него получают 403.
11. Рабочее дерево общее с параллельными сессиями: чужие изменения не смешивать со своими и не коммитить их (прецедент `a3ca29e` — «чужой» коммит параллельной сессии).
12. Если структура репозитория изменилась существенно — обновить этот файл.
13. Не добавлять в корень новые точки входа: карта, help, questions и обзоры живут в `Docs/` и `Notes/` (корень и так разросся — см. выше).
