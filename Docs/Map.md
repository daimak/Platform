# Карта репозитория Platform Evo

Дата съёмки: 2026-10-22; обновлён 2026-10-25 (реструктуризация контура — RFC-001); актуализирован 2026-10-31  
Состояние: `VERSION` = 1.8.4 (заметки — `Docs/Releases/v1.8.4.md`); активная ветка `feature_1.8.5`; `feature_1.8.2` — живая история (последний коммит 29.10), PR #3 не снят (требует проверки); модель веток — D-002.  
Назначение: не изучать дерево проекта с нуля. Это фактическое состояние репозитория, а не целевая архитектура.

Смежные точки входа:

- идея системы: `README.md`
- быстрый вход для нового ИИ-ассистента: `Docs/AI-ONBOARDING.md` (снимок 29.10)
- принципы: `Core/Principles.md`
- текущий фокус: `Memory/Context/CURRENT.md` (отстаёт от реальности, см. ниже)
- каталоги по задумке: `Docs/Architecture/Structure.md`
- индекс архитектуры: `Docs/Architecture/README.md`

---

## Что это

Персональная «операционная система эволюции». Основа — обычные файлы (markdown + статический UI). Принцип: хранить не только результаты, но и контекст, почему они появились.

Рабочий код вторичен, но уже не пуст. Главный runnable-артефакт — карта Estate в `eVo/dashboard/`; при ней живёт loopback-сервер Barrymore (`tools/barrymore/dashboard-server.py`, `127.0.0.1:8765`) с ограниченным локальным API и агентный рантайм `tools/agents/`. Внешних серверов и базы данных нет.

---

## Каталоги верхнего уровня

| Каталог | Задумка | Факт на 2026-10-31 |
|---|---|---|
| `Core/` | Ядро: принципы, глоссарий, ADR | Документы, не runtime; ADR-001…005 + INDEX |
| `eVo/` | Стюард: состояние, планирование, Command Center | Живой UI: `dashboard/`; `graphify-out/` (кэш), `scripts/`; `agents/` нет — рантайм агентов в `tools/agents/` |
| `Memory/` | Долговременный контекст системы | Markdown: CURRENT, сессии, решения, идеи |
| `Memory/Engineering/` | — (создан 25.10.2026) | Инженерный журнал: STATE, LOG, FINDINGS, PLAN, README; `Reports/` (аудиты Холмса), `Tasks/` — task-лиджер с `Active/` |
| `Interface/` | Способы взаимодействия с системой | Снова в дереве (восстановлен после удаления по RFC-001, ~27.10.2026 — точная дата требует проверки): отдельный прототип Vue/Vite, не runtime основного UI |
| `Workspace/` | Пользовательские проекты и артефакты | Аналитический контур `analytics/` (снапшоты по дням, `research/`, доска заказов), `eVo/Planning/Epics/EPIC-001`, `main.py` (LangSmith Engine), `.env` (секреты, untracked) / `.env.example` |
| `Modules/` | Предметные домены | Почти пусто (`Carrier.md`) |
| `Vision/` | Концепты, визуал, истории Estate | Идеи и изображения |
| `Tools/` | Скрипты обслуживания, протокол Barrymore | В дереве — `tools/`: Python (агенты, аналитика, тесты, ops) + PowerShell + markdown-задачи |
| `Docs/` | Архитектурные документы | Architecture/, Releases/ (v1.8.3, v1.8.4), Map, AI-ONBOARDING, Barrymore, Ops, отчёты ландшафтов |
| `RFC/` | Предложения изменений | README + процесс, каталоги Accepted/Backlog/Drafts/Rejected; RFC-001 (границы контура) — Accepted (файл лежит в `Drafts/`, статус внутри) |
| `Notes/` | Входящий поток | Inbox.md, Questions.md, evo-test-run.md |
| `Data/` | Служебные данные | `token_usage.json` — статические числа из v1.8.4, кодом не читаются; судьба решается (см. `tools/ops/README.md`) |
| `Backup/` | Старые визуалы Estate | Вынесен за контур 25.10.2026 в `C:/Work/Platform-archive/` (RFC-001); в дереве нет |
| `.obsidian/` | Настройки Obsidian | В корне отсутствует; правила остались в `.gitignore` |
| `.github/` | Мета репозитория | `copilot-instructions.md` |

В корне: `README.md`, `CHANGELOG.md`, `VERSION` (1.8.4), `PLATFORM.md`, `SYSTEM_SUMMARY.md` (сводка 2026-10-24), `TOKEN_USAGE_LOG.md` (регенерируемый журнал, gitignored), `skills-lock.json`; мета — `.gitignore`, `.gitattributes`, `.claudeignore`, `.github/`, `.vscode/`. Корень снова разросся: правило «точки входа только в `Docs/` и `Notes/`» соблюдается не полностью.

---

## Где лежит рабочий код

### Estate dashboard (основной UI)

Путь: `eVo/dashboard/`

- `index.html` — карта островов (Level 1)
- `style.css`, `app.js`, `languages.js` — взаимодействие и RU/EN
- `brief.js` — сгенерированный снимок Morning Brief (`window.EVO_BRIEF`); не править руками
- `workspace.html` — рабочий кабинет (Level 3)
- `engine-core.html/css/js` — Core Citadel: консоль инженерного центра + переход в кабинет Hunter
- `ai-usage.html/css/js`, `ai-sandbox-history.html` — учёт AI-использования и журнал AI Sandbox (v1.8.4)
- `maelstorm.html` — исследовательские маячки Maelstorm
- `holmes.html` — кабинет Холмса
- `harbor-ship.css/js` — остров Harbor
- `tasks.js` — задачи Баррримора (localStorage + счётчик на плашке)
- `vacancies.js` — автогенерация `tools/job_search.py --js` для Trading Quarter; не править руками
- `projects/` — активный визуальный проект (`marvel_v`, `minimalism`, `organica`)
- `locales/` — JSON-локали (дублируют часть `languages.js`)
- `assets/estate_bg.png`, `assets/barrymore.png` — фон карты и слой-портрет

Поведение: клик по острову открывает модалку. Задачи рычагов живут в `localStorage`. Morning Brief на острове Barrymore — живой: данные собирает генератор `tools/barrymore/morning-brief-agent.py`, свежий доклад отдаёт локальный сервер (`/api/refresh-brief`), статический снимок — `brief.js`.

Острова на карте: Main Estate, Navigator, Memory Library, Harbor, Trading Quarter (рынок вакансий и заказов — на месте прежнего Career Guild), Knowledge Archive, AI Sandbox, Workshop, Holmes Study (с 26.10). Бэрримор — не маячок, а кликабельная HTML-плашка в верхнем левом секторе: деревянная панель + отдельный слой-портрет `assets/barrymore.png`, приветствие по времени суток и счётчик задач (`tasks.js`); под ней ссылка «Review» при новом непрочитанном докладе. Фон карты — чистый арт без нарисованного текста (исходник `Vision/First_evo_pictures/Good_references/Clear_main.png`). Инструкция — `Docs/Barrymore.md`.

### Trading Quarter — рынок вакансий и заказов

Модалка острова с двумя вкладками:

- «Вакансии» — данные из `eVo/dashboard/vacancies.js` (автогенерация `tools/job_search.py --js`; на 30.10 — 64 записи, агрегатор RemoteOK / Remotive / hh / HN / Telegram и др.). Группы источников свёрнуты по умолчанию, состояние раскрытия хранится в `localStorage` (`evo_vacancies_expanded`).
- «Заказы» — биржи фриланса аккордеонами (fl.ru, upwork открыты по умолчанию) + репосты заказов из Telegram-каналов живой лентой.

Рядом лежит triage заказов: `tools/orders_triage.py` ведёт доску `Workspace/analytics/orders_board.json` и отчёт `orders_report.md` («Радар денег»).

### Аналитический контур (с 29.10)

Снапшоты по дням: `Workspace/analytics/YYYY-MM-DD/` — на 31.10 один прогон, `2026-10-29/` (README, `raw/` — копии живых источников, `chunks/` — LLM-готовые чанки, `jobs.csv`, `olx_structured.csv/json`, `token_usage.csv`, `report.md`, `stats.md`, `manifest.json`).

Строитель — `tools/analytics_snapshot.py` (stdlib-only, ADR-003/004): читает `tools/job_search_results.json`, `tools/olx_autoservices_data.json`, `tools/autoservices_data.json`, корневой `TOKEN_USAGE_LOG.md` и пишет датированную папку. Повторный запуск создаёт новую папку по дате. Вспомогательное: `tools/analytics_report.py`, `tools/analytics_salary_extract.py`, `tools/orders_triage.py`. Тесты — `tools/tests/` (11 тестов: `test_analytics_snapshot.py`, `test_dashboard_static.py`).

Research-отчёты: `Workspace/analytics/research/` (2026-10-30: money-plan, agents-landscape, sqlite-migration, hosting-when-ready, jobs-data-quality, jobs-data-quality-2).

### Vue-каркас — снова в дереве, не runtime

`Interface/` был удалён по RFC-001 25.10.2026, но снова присутствует в дереве (восстановлен после 25.10, ~27.10.2026 — точная дата требует проверки): отдельный прототип Vue 3 + Vite. Это не runtime основного UI: реальный интерфейс — `eVo/dashboard/` (так же трактует его и `Docs/AI-ONBOARDING.md`).

### Инструменты

- `tools/barrymore/dashboard-server.py` — loopback-сервер дашборда (`127.0.0.1:8765`): `/api/tasks`, `/api/refresh-brief`, `/api/hunter/tasks`, `/api/ai-usage`, `/api/security/*`, `/api/holmes/reports`, `/api/holmes/implement`
- `tools/barrymore/morning-brief-agent.py` — детерминированный генератор Morning Brief + LLM-агент (локальный FreeLLMAPI-шлюз, stdlib-only)
- `tools/barrymore/task_store.py` — task-лиджер: валидация записей, атомарная запись, архивация done-задач через 48 ч в `Tasks/Archive/YYYY/MM/`
- `tools/barrymore/ai_usage.py`, `security_contour.py`, `hunter_store.py` + их `test_*.py` — учёт AI-использования, защищённый контур, очередь Hunter
- `tools/agents/registry.json` (v4) + `tools/agents/run_agent.py` — агентный рантайм (см. «Агенты и боты»)
- `tools/analytics_snapshot.py`, `tools/job_search.py` (режим `--js` генерирует `vacancies.js`), `tools/analytics_report.py`, `tools/analytics_salary_extract.py`, `tools/orders_triage.py` — аналитический контур (см. выше)
- `tools/tests/` — тесты аналитического контура (11 тестов)
- `tools/evo-check.ps1` — git release-gate (ветка, dirty, последний коммит)
- `tools/evo-save.ps1` — интерактивные add / commit / push
- `tools/barrymore/execute.ps1` — add + commit + отчёт в `tools/barrymore/reports/`
- `tools/barrymore/install-dashboard.ps1` — однократная установка автозапуска локального сервера при входе в Windows
- `tools/ops/` — `backup_workspace.py`, `healthcheck.py`, `import_olx_to_hunter.py` + README-план: в работе, не закоммичено (untracked)
- `eVo/scripts/bootstrap.ps1` — **создаёт** папки `agents/`, `runtime/` (ADR больше не создаёт — решения в `Core/Architecture/ADR/`); не запускать без нужды
- `.vscode/tasks.json` — Add / Commit / Push

### Сгенерированный граф кода

Графа два: `eVo/graphify-out/` — кэш Graphify, не исходники; с 25.10.2026 не отслеживается Git (пересобирается). И корневой `graphify-out/` — отчётные файлы отслеживаются, кэш/манифест — нет (правила в `.gitignore`). Для навигации по связям файлов (`graphify query "..."`), не для правки.

---

## Как запускать

1. **Главный интерфейс:** `http://127.0.0.1:8765` (однократная установка автозапуска — `tools/barrymore/install-dashboard.ps1`; сервер стартует при входе в Windows и слушает только loopback). Без сервера карта открывается файлом `eVo/dashboard/index.html`, но живые данные (brief, задачи, Холмс) не обновятся.
2. **Morning Brief (Баррримор):** refresh-кнопка в дашборде, либо `python tools/barrymore/morning-brief-agent.py` (данные + доклад LLM) или `powershell tools/barrymore/morning-brief.ps1` (только данные); инструкция пользователя — `Docs/Barrymore.md`.
3. **Агентный рантайм:** `python tools/agents/run_agent.py --agent Holmes` (с `--no-llm` — детерминированный прогон без шлюза).
4. **Аналитика:** `python tools/analytics_snapshot.py [YYYY-MM-DD]` (создаёт `Workspace/analytics/YYYY-MM-DD/`), `python tools/orders_triage.py` (радар заказов).
5. **Тесты:** `python -m unittest discover -s tools/tests` (11 тестов) и `python -m unittest discover -s tools/barrymore -p "test_*.py"` (21 тест на 29.10).
6. **Состояние системы** смотреть в файлах и Git, не в UI: `Memory/Context/CURRENT.md` (отстаёт), `Memory/Engineering/STATE.md` (обновлялся 26.10), task-лиджер `Memory/Engineering/Tasks/Active/` — фактический список активных задач.

---

## Агенты и боты

Агентный рантайм появился. Общий каркас — `tools/agents/`: `registry.json` (v4, 2026-10-30: каждый инструмент описывает контракт, права выдаются агенту явно по паспорту, всё read-only, кроме явно утверждённого) и `run_agent.py` (запуск агента по паспорту, stdlib-only; LLM — через локальный OpenAI-совместимый шлюз, модель не имеет доступа к ОС — ADR-004).

- **Barrymore** — стюард, частично активен (паспорт `Memory/Agents/Barrymore.md`). Рантайм: Morning Brief — генератор + LLM-агент и локальный сервер (см. «Как запускать»). Оркестрация субагентами — целевое состояние.
- **Holmes** — аудит и расследования (паспорт `Memory/Agents/Holmes.md`). Права: read-only инструменты (`git.inspect`, `journal.read`, `tree.inspect`, `reports.inspect`, `gateway.chat`) + единственное право записи `report.write` — отчёт `Memory/Engineering/Reports/Report-ГГГГ-ММ-ДД-holmes-audit.md` (прогоны 29.10 и 30.10). Инициативы из отчёта превращаются в задачи только через дашборд: галочки в модалке Холмса → `/api/holmes/implement` (санкция Sovereign).
- **Solomon, Hunter, Maelstorm** — роли с кабинетами/маячками на карте; отдельного рантайма нет. Hunter — локальная очередь поручений (`/api/hunter/tasks`), автономный поиск вакансий не подключён.
- Дашборд показывает статусы агентов; границы — ADR-003 (read-only), ADR-004 (доступ только через tools), ADR-005 («всё — инструмент»); индекс ADR — `Core/Architecture/ADR/INDEX.md`.
- Концепты команды: `Memory/New_ideas/estate_archipelago_agents.md`, `Memory/New_ideas/syndicate_architecture.md`; ландшафт агентов — `Docs/AGENTS-LANDSCAPE-2026-10-29-ZCode.md`.
- Идея локального агента: `Vision/Future/Experiments/Local_AI_Agent_Experiment.md`.
- Gemini: лог ручного теста `Memory/Context/2026-10-19-gemini-api-first-test.md`, в приложение не вшит.
- Планируемые, но не созданные каталоги: `eVo/agents/`, `eVo/runtime/` (их должен создать bootstrap); фактический рантайм агентов живёт в `tools/agents/`.

---

## Ключевые файлы контекста

| Файл | Зачем |
|---|---|
| `README.md` | Единственная точка входа в корень |
| `VERSION` + `Docs/Releases/` | Текущая версия (1.8.4) и заметки релизов |
| `Docs/AI-ONBOARDING.md` | Быстрый вход для нового ИИ-ассистента (снимок 29.10) |
| `Memory/Context/CURRENT.md` | Текущий фокус и next action (отстаёт от реальности) |
| `CHANGELOG.md` | Хроника изменений |
| `Docs/Architecture/README.md` | Индекс архитектуры |
| `Core/Architecture.md` | Слои v0.1 |
| `Core/Architecture/ADR/ADR-002-Island-Architecture-Model.md` | Модель островов |
| `tools/agents/registry.json` | Реестр инструментов и прав агентов (v4) |
| `Memory/Agents/README.md` | Стандарт паспортов агентов |
| `Memory/Engineering/Tasks/Active/` | Task-лиджер — фактический список активных задач |
| `tools/barrymore/TASK-PROTOCOL.md` | Как должен работать Barrymore |
| `tools/barrymore/initiatives/INITIATIVE-0001-live-state-view.md` | Живое состояние из источников истины |
| `Workspace/eVo/Planning/Epics/EPIC-001-Control-And-Visibility.md` | Контроль и видимость изменений |

`CURRENT.md` отстаёт от реальности (дата внутри — 2026-08-05; задача `update-current-context` ждёт в лиджере). Зафиксированный там next action «кнопка Barrymore → Morning Brief» уже реализован (25–29.10). Фактический план работ — `Memory/Engineering/PLAN.md` и task-лиджер `Memory/Engineering/Tasks/Active/` (11 задач на 30.10: слияние веток по D-002, актуализация CURRENT, research-задачи и пр.).

---

## Самый маленький следующий прототип

Устарело: минимальный шаг этого раздела — read-only Morning Brief в модалке Barrymore — уже реализован (25–29.10: детерминированный генератор + LLM-агент, локальный сервер, история задач, refresh-кнопка).

Следующий минимальный шаг теперь выбирается из task-лиджера `Memory/Engineering/Tasks/Active/` и инициатив Холмса в последнем отчёте `Memory/Engineering/Reports/` (на 30.10 в лиджере, в частности: слияние веток по D-002, актуализация `CURRENT.md`, `tools/ops/` — атомарная запись `brief.js` и толерантность `task_store` к битым записям).

---

## Правила для следующих сессий

1. Сначала этот файл, затем `CURRENT.md` (помня, что он отстаёт) и `Docs/AI-ONBOARDING.md`.
2. Не путать `Interface/` (отдельный Vue/Vite-прототип, не runtime) с `eVo/dashboard/` (реальный UI).
3. Не приписывать агентам больше прав, чем в `tools/agents/registry.json` (v4): всё read-only; запись — только `report.write` Холмса и санкционированные API дашборда (`/api/holmes/implement`, Mark Done).
4. Не запускать `bootstrap.ps1` без явной задачи: он пишет файлы.
5. `eVo/graphify-out/` и корневой `graphify-out/` не править вручную; `brief.js` и `vacancies.js` — автогенерация, править их источники, не сами файлы.
6. Секреты — в `Workspace/.env` (untracked, шаблон `.env.example`); не читать и не выводить значения.
7. `tools/ops/` — рабочие скрипты, не закоммичены (untracked); не считать их частью закоммиченного контура и не удалять как «мусор».
8. Если структура репозитория изменилась существенно — обновить этот файл.
9. Не добавлять в корень новые точки входа: карта, help, questions и обзоры живут в `Docs/` и `Notes/` (корень и так разросся — см. выше).
