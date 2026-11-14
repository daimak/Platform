# Карта репозитория Platform Evo

Дата съёмки: 2026-10-22; обновлён 2026-10-25 (реструктуризация контура — RFC-001); актуализирован 2026-10-31; 2026-11-06 (фундамент данных Л-1…Л-5, канбан, миры, итоги ночной смены 05.11); актуализирован 2026-11-09 (релиз 1.8.8: штаб COMMAND CENTER, обсерватория, worlds-draft, штат v4 с Рокфеллером, publish-blocklist, feeds_radar, облачный контур)  
Состояние: `VERSION` = 1.8.8 (коммит `7d9a7ee`, 2026-11-09; заметок в `Docs/Releases/` для 1.8.7/1.8.8 нет — только v1.8.3, v1.8.4; хроника в `CHANGELOG.md`). Активная ветка `main`, HEAD — коммит `a960875` «Штат v4: Рокфеллер — финансовый советник» (2026-11-09 05:25). Release-ветки `release/1.8.6`, `release/1.8.7`, `release/1.8.8` существуют локально и на origin. Хвост журнала — E-059 (08.11); сессия 08–09.11 (штаб, релиз, blocklist, Рокфеллер) записи в `LOG.md` ещё не имеет. Рабочее дерево общее с параллельными сессиями: на 09.11 изменены `eVo/dashboard/brief.js`, `hunter-report.js`, `orders-triage.js` (автогенерация — чужие правки не смешивать и не коммитить), untracked `Workspace/cloud/probes/`.  
Назначение: не изучать дерево проекта с нуля. Это фактическое состояние репозитория, а не целевая архитектура.

Смежные точки входа:

- идея системы: `README.md`
- быстрый вход для нового ИИ-ассистента: `Docs/AI-ONBOARDING.md` (снимок 06.11)
- точка входа смены: `Docs/ENTRY-POINT-2026-11-06-ZCode.md`
- итоги ночной смены: `Docs/NIGHT-LOG-2026-11-05-ZCode.md`; ночное задание — `Docs/NIGHT-TASKBOARD-2026-11-06-ZCode.md`
- принципы: `Core/Principles.md` (включая P12 «Нейтральность инструмента», 08.11)
- текущий фокус: `Memory/Context/CURRENT.md` (отстаёт от реальности: дата внутри 2026-08-05)
- канонический реестр миров: `Memory/Worlds/README.md` + предложения `Memory/Worlds/PROPOSALS-2026-11-08-ZCode.md`
- каталоги по задумке: `Docs/Architecture/Structure.md`
- индекс архитектуры: `Docs/Architecture/README.md`

---

## Что это

Персональная «операционная система эволюции». Основа — обычные файлы (markdown + статический UI). Принцип: хранить не только результаты, но и контекст, почему они появились.

Рабочий код вторичен, но уже не пуст. Главные runnable-артефакты — карта Estate и штаб COMMAND CENTER в `eVo/dashboard/`; при них живёт loopback-сервер Barrymore (`tools/barrymore/dashboard-server.py`, `127.0.0.1:8765`) с ограниченным локальным API, машинный журнал событий `Workspace/logs/events.jsonl` и агентный рантайм `tools/agents/`. Платформа также развёрнута на облачной ВМ «Мастерская» (см. «Облачный контур»); баз данных и внешних серверов за пределами этой ВМ нет.

---

## Каталоги верхнего уровня

| Каталог | Задумка | Факт на 2026-11-09 |
|---|---|---|
| `Core/` | Ядро: принципы, глоссарий, ADR | Документы, не runtime; ADR-001…005 + INDEX; `Principles.md` дополнен P12 «Нейтральность инструмента» (`ad071d4`, 08.11) |
| `eVo/` | Стюард: состояние, планирование, Command Center | Живой UI: `dashboard/` (штаб `command-center.html`, обсерватория `maelstorm-observatory.html`, драфты миров `worlds-draft/`, канбан, флот, карта мира); `graphify-out/` (кэш), `scripts/`; рантайм агентов в `tools/agents/` |
| `Memory/` | Долговременный контекст системы | Markdown: CURRENT (отстаёт), сессии, решения, идеи; `Worlds/` — реестр архипелагов + `PROPOSALS-2026-11-08-ZCode.md`; `Agents/` — 16 паспортов + `estate-staff.json` (v4) |
| `Memory/Engineering/` | — (создан 25.10.2026) | Инженерный журнал: STATE, PLAN, FINDINGS, README; `LOG.md` — E-001…E-059 (сессия 08–09.11 пока не записана); `Reports/` (аудиты Холмса, ночные доклады), `Tasks/Active/` — 27 карточек, `Tasks/Archive/` |
| `Interface/` | Способы взаимодействия с системой | Отдельный прототип Vue 3 + TypeScript + Vite, не runtime основного UI |
| `Workspace/` | Пользовательские проекты и артефакты | Аналитический контур `analytics/` (6 снапшотов по дням: 10-29, 11-01, 11-04, 11-05, 11-06, 11-09 + `pipeline/`, `research/`, `token-spend/`, `hunter/`), `logs/` (машинный журнал, gitignored), `private/` (приватная зона Sovereign, gitignored; vars шаблонизации), `intel/` (внутренний контур разведки, gitignored), `agents/` (переписка агентов, gitignored), `cloud/` (кит полигонов: bootstrap, cloud-init DO/YC, compose-стеки, k3s, probe; `probes/` untracked), `higgsfield-pilot/`, `pentest/` + `reports/` (вне git), `main.py` (LangSmith Engine), `.env` (секреты, untracked) / `.env.example` |
| `Modules/` | Предметные домены | Почти пусто (`Carrier.md`) |
| `Vision/` | Концепты, визуал, истории Estate | Идеи и изображения; база карты мира v2 — `First_evo_pictures/Good_references/World_map_v2.png` |
| `tools/` | Скрипты обслуживания, протокол Barrymore | Python (агенты, аналитика, `lib/`, `ops/`, `security/`, `cloud/`, `intel/` — внутренний контур разведки, в git не попадает, тесты) + PowerShell + markdown-задачи |
| `kali/` | Полигон Kali | Каталог в корне, gitignored; VM 192.168.238.128, снапшот `pre-pentest-2026-11-04` (E-047); кампания отложена Sovereign |
| `Docs/` | Архитектурные документы | Architecture/, Releases/ (v1.8.3, v1.8.4), Map, AI-ONBOARDING, Barrymore, Ops, TEMPLATING, CLOUD-VM-RUNBOOK-2026-11-07 (генерируемый артефакт), DARK-WATCH-PLAN-2026-11-08 (не отслеживается — правило видимости) + планы, журналы и задания смен (DATA-FOUNDATION-PLAN-2026-11-04, NIGHT-LOG-2026-11-05, NIGHT-TASKBOARD-2026-11-06, ENTRY-POINT-2026-11-06, AGENT-FLEET-PLAN, KALI-*, SCRAPERS-LANDSCAPE и др.) |
| `RFC/` | Предложения изменений | README + процесс, каталоги Accepted/Backlog/Drafts/Rejected; RFC-001 (границы контура) — Accepted (файл лежит в `Drafts/`, статус внутри) |
| `Notes/` | Входящий поток | Inbox.md, Questions.md, evo-test-run.md |
| `Data/` | Служебные данные | `token_usage.json` — статические числа из v1.8.4, кодом не читаются; судьба решается (см. `tools/ops/README.md`) |
| `Backup/` | Старые визуалы Estate | Вынесен за контур 25.10.2026 в `C:/Work/Platform-archive/` (RFC-001); в дереве нет |
| `.obsidian/` | Настройки Obsidian | В корне отсутствует; правила остались в `.gitignore` |
| `.github/` | Мета репозитория | `copilot-instructions.md` |

В корне: `README.md`, `CHANGELOG.md` (последняя строка — релиз 1.8.8 от 09.11), `VERSION` (1.8.8), `PLATFORM.md`, `SYSTEM_SUMMARY.md`, `TOKEN_USAGE_LOG.md` (регенерируемый журнал, gitignored), `skills-lock.json`, `job_search_results.json`, `links.txt` (untracked); сервисные каталоги `.agents/`, `.aider-desk/`, `.zcode/`, `.vscode/` (gitignored) и мета — `.gitignore`, `.gitattributes`, `.claudeignore`, `.github/`. Корень разросся: правило «точки входа только в `Docs/` и `Notes/`» соблюдается не полностью.

---

## Где лежит рабочий код

### Estate dashboard (основной UI)

Путь: `eVo/dashboard/`

- `index.html` — карта островов, мир Estate (Level 1) + планета/меню миров (v1.8.7)
- `style.css`, `app.js` (`?v=18`), `languages.js` — взаимодействие и RU/EN
- `command-center.html/css/js` — **штаб COMMAND CENTER**: панели «Токены» (+ расход по часам), «Конвейер», «Сторож», «Артефакты», «Ждёт слова», «Блокеры денег», «Сигналы»; данные — `/api/tokens/usage`, `/api/steward`, `/api/tasks`, `/api/agents/*`
- `maelstorm-observatory.html` + `observatory.css/js` — обсерватория Маэльшторма: живая canvas-картина работы агентов (воронка, корабли, шлюпки, дуга причалов, HTML-слой подписей)
- `worlds-draft/` — 13 standalone-страниц-превью миров (00–05, 07–12, 14) + каталог `index.html` + `SPEC.md` верфи миров (один HTML, всё инлайн, офлайн, 12–40 КБ); выбор четвёртого мира за Sovereign (коммит `58ec0d7` заявляет 14 драфт-вариаций — см. расхождение ниже)
- `agents.html/css/js` — «Флот в море»: оперативная таблица запущенных агентов, `/api/agents/live` + `/api/agents/history`
- `brief.js` — сгенерированный снимок Morning Brief (`window.EVO_BRIEF`); не править руками
- `workspace.html` — рабочий кабинет (Level 3)
- `engine-core.html/css/js` — мир Engine Core Atoll: консоль инженерного центра + переход в кабинет Hunter
- `maelstorm.html` — мир Maelstorm, исследовательский архипелаг
- `world-map.html` (+ `world-map-review.html`) — карта мира: маршрут корабля между архипелагами; корабль — `harbor-ship.css/js` (`ROUTE_PX`); база v2 — `Vision/First_evo_pictures/Good_references/World_map_v2.png`
- `kanban.html` + `kanban.js` (`?v=9`) — канбан лиджера: колонки Анализ → Сделать → В работе → Проверка → Готово; типы сущностей task/change/epic (бейджи ЗНИ/Эпик, фильтр со счётчиками); переходы — `POST /api/tasks/<id>/stage/<колонка>` с подписью `by` (врата `can_transition` — в test/done только source/owner/Sovereign/ZCode, остальным 403)
- `holmes.html` — кабинет Холмса (отчёты аудита из `/api/holmes/reports`, галочка инициативы → `/api/holmes/implement`)
- `ai-usage.html/css/js`, `ai-sandbox-history.html` — учёт AI-использования и журнал AI Sandbox
- Вкладка «Экскурсия» в AI Sandbox (`app.js` + `excursion-data.js`, генератор `tools/barrymore/build-excursion.py`) — визуальный граф рейсов агентов из живого журнала; «Целевой стенд» — чипы целей и проверки через `/api/sandbox/run`
- `tasks.js` — задачи Баррримора (localStorage + счётчик на плашке)
- `vacancies.js` (автогенерация `tools/job_search.py --js`), `orders-triage.js` (автогенерация `tools/orders_triage.py`), `hunter-report.js` (автогенерация `tools/hunter/report.py`) — не править руками
- `projects/` — скины-темы (`marvel_v`, `minimalism`, `organica`; к мирам не подключены, активный — `active_project.json`)
- `locales/` — JSON-локали (дублируют часть `languages.js`)
- `assets/estate_bg.png`, `assets/barrymore.png`, `assets/world-map-v1.png`, `assets/maelstorm_bg*.png`, `assets/engine-core-bg.png`, `assets/harbor-ship-sprite.png` — фоны и слои

Поведение: клик по острову открывает модалку. Morning Brief на острове Barrymore — живой: данные собирает генератор `tools/barrymore/morning-brief-agent.py`, свежий доклад отдаёт локальный сервер (`/api/refresh-brief`), статический снимок — `brief.js`. Плашка Бэрримора показывает счётчик непрочитанной переписки агентов (`/api/peer-notes`).

Миры и острова: канон — `Memory/Worlds/README.md` (правило «кто живёт — `Memory/Agents`, где живут — `Memory/Worlds`»). Три архипелага: Estate (`index.html`), Engine Core Atoll (`engine-core.html`), Maelstorm (`maelstorm.html`). Острова Estate: Trading Quarter, Harbor, Navigation Observatory (Магеллан, Хантер), Memory Library, AI Sandbox, Workshop, Study, Sinbad Market. Бэрримор — кликабельная HTML-плашка в верхнем левом секторе. Инструкция — `Docs/Barrymore.md`. Четвёртый мир выбирается из `worlds-draft/` (предложения 08.11 — `Memory/Worlds/PROPOSALS-2026-11-08-ZCode.md`).

### Trading Quarter — рынок вакансий и заказов

Модалка острова с вкладками:

- «Вакансии» — данные из `eVo/dashboard/vacancies.js` (автогенерация `tools/job_search.py --js`). Группы источников свёрнуты по умолчанию, состояние раскрытия — `localStorage` (`evo_vacancies_expanded`).
- «Заказы» — биржи фриланса аккордеонами (fl.ru, upwork открыты по умолчанию) + репосты заказов из Telegram-каналов живой лентой.
- «Радар» — триаж заказов: `tools/orders_triage.py` ведёт доску `Workspace/analytics/orders_board.json` и отчёт `orders_report.md`; данные вкладки — `orders-triage.js`.

### Аналитический контур (с 29.10)

Снапшоты по дням: `Workspace/analytics/YYYY-MM-DD/` — на 09.11 шесть прогонов: `2026-10-29`, `2026-11-01`, `2026-11-04`, `2026-11-05`, `2026-11-06`, `2026-11-09` (внутри: `raw/`, `chunks/`, `jobs.csv`, `token_usage.csv`, `salary_extracted.csv`, `stats.md`, `manifest.json`).

Строитель — `tools/analytics_snapshot.py` (stdlib-only, ADR-003/004); успешный прогон дописывает `snapshot.completed` в машинный журнал. Вспомогательное: `tools/analytics_report.py`, `tools/analytics_salary_extract.py`, `tools/orders_triage.py`, `tools/hunter/report.py`. Рядом: `Workspace/analytics/pipeline/` (воронка сделок: `pipeline_report.py`, шаблоны отчётов и первичных ответов, квалификация, `deals/`), `token-spend/` (`ledger.jsonl`, `tools/ops/token_meter.py`), `research/` (волны 30–31.10 + `2026-11-04-golang-hypothesis.md`), `hunter/`.

Тесты — `tools/tests/` (13 файлов, 105 тестов). Служебное: `_wave*-state.md`, `_agents-2026-11-04/`.

### Фундамент данных (Л-1…Л-5, исполнено в ночь 05.11)

Единый формат фактуры + единый журнал + единый диспетчер (ТЗ — `Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md`):

- `tools/lib/envelope.py` — конверт артефактов: `make_envelope` / `validate_envelope`; `schema_id` — два-три ascii-сегмента через точку
- `tools/lib/log_event.py` — машинный журнал: `append_event(kind, source, payload)` дозаписывает JSONL-конверт в `Workspace/logs/events.jsonl` (gitignored, регенерируемый)
- `tools/lib/task_lock.py` — busy-лок: атомарный захват `O_CREAT|O_EXCL`, heartbeat, TTL 600с с перехватом протухших, отклики Claims/, события `task.busy.*` (E-048)
- `tools/ops/jobs.json` — реестр джобов (`analytics-snapshot`, `token-meter`, `healthcheck`); сервер: `GET /api/jobs` + `POST /api/jobs/<id>/run`, статусы — `Workspace/logs/jobs_state.json`
- `tools/barrymore/task_store.py` — подписанные переходы (`by`), врата `can_transition` (E-048, ответ на инцидент «Резюме-конвейер»), типы task/change/epic (`set_type`, E-050); архивация done-задач через 48 ч
- `tools/ops/kanban_metrics.py` — метрики конвейера: 4 блока с фолбэком по `history[].by`; вывод — текст + JSON-envelope `evo.kanban.metrics`

### Облачный контур (E-052…E-059, 07–08.11)

- **ВМ «Мастерская»** (Яндекс.Облако, E-052): Ubuntu 24.04, 2 vCPU/4 ГБ, ufw (наружу только SSH), платформа v1.8.7 в `~/Platform`, дашборд = systemd `barrymore-dashboard.service`, nginx-loopback 8766→8765 (обход `_is_local_host`). **IP в репо не хранится** — плейсхолдер `<VM_PUBLIC_IP>` в шаблонизированном ранбуке.
- **Шаблонизация координат** (E-053, `Docs/TEMPLATING.md`): `templates/*.j2` в git — источник правды; реальные координаты — `Workspace/private/vars/*.json` (вне git, per-host); рендер `tools/render_templates.py` (`--repo` подставляет плейсхолдеры даже при наличии vars — repo-артефакт не может утечь значением). `Docs/CLOUD-VM-RUNBOOK-2026-11-07-ZCode.md` — генерируемый repo-артефакт, руками не править.
- **Лаба на ВМ** (всё биндинги 127.0.0.1 — урок «docker обходит ufw», E-055): кит полигонов `Workspace/cloud/` (bootstrap.sh, cloud-init для DigitalOcean/Yandex Cloud, compose-стеки DVWA/Juice Shop/n8n/Uptime Kuma/WireGuard, k3s, probe-machine.sh); Vulhub + `~/lab/up.sh` с safety-гейтом (E-056); reallab «мини-корпорация» nginx+WP+Keycloak+PostgreSQL+Redis (E-057); rl-console — кнопочная консоль атак 127.0.0.1:8788, плейбуки-белые списки argv без shell, история прогонов (E-058). Исходники лабы — в приватной зоне `Workspace/private/lab/` (не картографируется), копия на ВМ.
- **Туннель**: `tools/cloud/vm-tunnel.ps1` (E-059) — вечный reconnect-луп, координаты из `Workspace/private/vars/cloud-vm.json` (IP не хардкожен), форварды 18765/8080/8081/5432/6379/8788; задача планировщика «VM Tunnel reallab».
- Витрина :80 на ВМ — деплоится параллельной сессией (E-059), в этом репо не отслеживается.

### Резюме-конвейер и пилоты (Workspace/)

- `Workspace/private/` — приватная зона данных Sovereign (gitignored; pre-commit RED). Внутри — резюме-конвейер (`resume/`, `proposals/`), vars шаблонизации (`vars/`), лаба (`lab/`, `notes/`). Содержимое НЕ картографируется, не показывается в UI и не коммитится.
- `Workspace/higgsfield-pilot/` — пилот Higgsfield: `pilot.py` (с `REAL_PAYMENT_SANCTIONED=False`), `pilot-report.json`, `progress.md`, главный артефакт `HIGGSFIELD-DOCS-2026-11-05.md` (18 разделов по живым докам), `docs-cache/`, `openapi.json`. Платных вызовов 0; карточка `higgsfield-pilot-test` в «Проверке», ждёт ключ в `Workspace/.env` и санкцию Sovereign.
- `Workspace/pentest/`, `Workspace/reports/` — вне git: VULN-PROGRAM 12V/12I (`2026-11-04-vuln-program/VULN-PROGRAM.md`), ночные отчёты смен.

### Vue-каркас — снова в дереве, не runtime

`Interface/` был удалён по RFC-001 25.10.2026, но снова присутствует в дереве: отдельный прототип Vue 3 + TypeScript + Vite. Это не runtime основного UI: реальный интерфейс — `eVo/dashboard/`.

### Инструменты

- `tools/barrymore/dashboard-server.py` — loopback-сервер дашборда (`127.0.0.1:8765`). GET: `/api/tasks`, `/api/staff`, `/api/steward` (сторож, 6 слоёв самодиагностики — `9a87cf3`), `/api/tokens/usage` (агрегат по `model-io-*.jsonl`), `/api/agents/live`, `/api/agents/history`, `/api/peer-notes`, `/api/hunter/tasks`, `/api/ai-usage`, `/api/security/status`, `/api/{watson|riskscan}/reports`, `/api/{watson|riskscan}/run-status`, `/api/holmes/reports`, `/api/holmes/context`, `/api/holmes/run-status`, `/api/sandbox/run-status`, `/api/sandbox/report`, `/api/sandbox/pentest/rounds`, `/api/jobs`. POST: `/api/tasks/<id>/done`, `/api/tasks/<id>/stage/<analysis|todo|in-progress|test|done>` (by из body, врата can_transition), `/api/tasks/<id>/type`, `/api/jobs/<id>/run`, `/api/hunter/tasks`, `/api/security/check`, `/api/security/targets`, `/api/holmes/implement`, `/api/holmes/run`, `/api/watson/run`, `/api/riskscan/run`, `/api/sandbox/run`, `/api/sandbox/pentest/rounds/…`, `/api/ai-usage/snapshots`, `/api/ai-usage/settings`, `/api/ai-usage/ask-barrymore`, `/api/peer-notes/read`, `/api/refresh-brief`. POST-эндпоинты проверяют заголовок `Origin: http://127.0.0.1:8765` — curl без него получает 403
- `tools/barrymore/morning-brief-agent.py` — детерминированный генератор Morning Brief + LLM-агент (локальный FreeLLMAPI-шлюз, stdlib-only); с E-054 — дайджест переписки агентов (`peer_notes_digest`). Находка F1 (неатомарная запись `brief.js`) всё ещё не исправлена
- `tools/barrymore/task_store.py` — task-лиджер: валидация, атомарная запись, подписи `by`, врата `can_transition`, типы сущностей; `tools/barrymore/build-excursion.py` — генератор `excursion-data.js`
- `tools/barrymore/ai_usage.py`, `security_contour.py`, `hunter_store.py`, `logger.py` + их `test_*.py` (5 файлов, 35 тестов) — учёт AI-использования, защищённый контур, очередь Hunter
- `tools/agents/registry.json` (v5) + `tools/agents/run_agent.py` — агентный рантайм; с E-054 — peer notes (`extract_peer_note`/`save_peer_note` → `Workspace/agents/peer-notes.jsonl`, вне git)
- `tools/lib/` — конверты, журнал, busy-лок (см. «Фундамент данных»)
- `tools/ops/` — `backup_workspace.py`, `healthcheck.py`, `import_olx_to_hunter.py`, `token_meter.py`, `jobs.json`, `kanban_metrics.py`, `run_all.py` (единый раннер двух сьютов), `restart-dashboard.ps1` (канонический рестарт сервера через PID + полный путь python.exe, UTF-8 BOM обязателен) + README-план
- `tools/security/` — прототипы (тест 02.11, E-043): `vuln_radar.py` (CISA KEV + EPSS + NVD), `feeds_radar.py` (5 фидов обсуждений/новостей: HN Algolia, oss-security, GH Advisories, SecurityLab, Habr → секция 4 дайджеста; `38fa7f8`), `port_audit.py` + `port_allowlist.json`, `secret_scan.py`, `nmap_probe.py`, `common.py`; `hooks/` — pre-commit секрет-гейт (hard RED для `Workspace/private/` с `d87ba7b`, publish-blocklist внутренних контуров с `8162b8a`) + install.sh. Кнопки — во вкладке «Инструменты» модалки AI Sandbox (`/api/sandbox/*`); отчёты — в `%LOCALAPPDATA%\Platform\SecurityReports\`, вне git
- `tools/intel/` — внутренний контур разведки (Dark Watch): в git не попадает (исключён локально + закрыт publish-blocklist pre-commit). Содержимое не картографируется
- `tools/cloud/vm-tunnel.ps1` — постоянный туннель к ВМ (см. «Облачный контур»)
- `tools/render_templates.py` + `templates/*.j2` — протокол шаблонизации (см. «Облачный контур»)
- `tools/pentest/` — цели pentest (README, TARGETS); `tools/hh406-lab/` — лаборатория обхода hh-406 (gitignored)
- `tools/hunter/report.py` — digest Хантера; `tools/analytics_snapshot.py`, `tools/job_search.py` (`--js` → `vacancies.js`), `tools/analytics_report.py`, `tools/analytics_salary_extract.py`, `tools/orders_triage.py` — аналитический контур
- `tools/tests/` (13 файлов, 105 тестов) + `tools/barrymore/test_*.py` (5 файлов, 35 тестов); единый раннер — `python tools/ops/run_all.py`
- `tools/evo-check.ps1` — git release-gate; `tools/evo-save.ps1` — интерактивные add / commit / push; `tools/barrymore/execute.ps1` — add + commit + отчёт; `tools/barrymore/install-dashboard.ps1` — автозапуск сервера при входе в Windows
- `eVo/scripts/bootstrap.ps1` — **создаёт** папки `agents/`, `runtime/`; не запускать без нужды
- `.vscode/tasks.json` — Add / Commit / Push

### Сгенерированный граф кода

Графа два: `eVo/graphify-out/` — кэш Graphify, не исходники; с 25.10.2026 не отслеживается Git (пересобирается). И корневой `graphify-out/` — отчётные файлы отслеживаются, кэш/манифест — нет (правила в `.gitignore`). Для навигации по связям файлов (`graphify query "..."`), не для правки.

---

## Как запускать

1. **Главный интерфейс:** `http://127.0.0.1:8765` (автозапуск — `tools/barrymore/install-dashboard.ps1`; рестарт — `powershell tools/ops/restart-dashboard.ps1`). Без сервера карта открывается файлом, но живые данные не обновятся.
2. **Morning Brief (Баррримор):** refresh-кнопка в дашборде, либо `python tools/barrymore/morning-brief-agent.py` или `powershell tools/barrymore/morning-brief.ps1`; инструкция — `Docs/Barrymore.md`.
3. **Агентный рантайм:** `python tools/agents/run_agent.py --agent Holmes` (так же Watson, RiskScan; `--no-llm` — детерминированный прогон).
4. **Аналитика:** `python tools/analytics_snapshot.py [YYYY-MM-DD]`, `python tools/orders_triage.py` (радар заказов).
5. **Канбан-метрики:** `python tools/ops/kanban_metrics.py`; джобы — `GET /api/jobs`, `POST /api/jobs/<id>/run`.
6. **Тесты:** `python tools/ops/run_all.py` (два сьюта) либо `python -m unittest discover -s tools/tests` (105) и `python -m unittest discover -s tools/barrymore -p "test_*.py"` (35). Гоча: в Git Bash этой машины `python` — Store-заглушка, реальный интерпретатор — `py` или полный путь `python.exe`.
7. **Туннель к ВМ:** `powershell tools/cloud/vm-tunnel.ps1` (обычно уже висит задачей планировщика «VM Tunnel reallab»); штаб — `http://127.0.0.1:8765/command-center.html`, обсерватория — `maelstorm-observatory.html`.
8. **Состояние системы** смотреть в файлах и Git, не в UI: хвост `Memory/Engineering/LOG.md` (E-001…E-059; сессия 08–09.11 не записана), `Memory/Engineering/PLAN.md`, task-лиджер `Memory/Engineering/Tasks/Active/` (27 карточек), машинный журнал `Workspace/logs/events.jsonl`.

---

## Агенты и боты

Агентный рантайм — `tools/agents/`: `registry.json` (**v5**; каждый инструмент описывает контракт, права выдаются агенту явно по паспорту, всё read-only, кроме явно утверждённого) и `run_agent.py` (stdlib-only; вычислители находок `compute_watson_findings` / `compute_riskscan_findings`; LLM — через локальный OpenAI-совместимый шлюз; с E-054 — peer notes «Заметка соседу»).

- **Barrymore** — стюард, ведёт штат (`led_by` в estate-staff.json). Рантайм: Morning Brief + локальный сервер + свод переписки агентов + сторож-плитка в штабе.
- **Holmes** — аудит и расследования. Права: read-only + единственное право записи `report.write`; прогоны 29.10–07.11. Инициативы — только через `/api/holmes/implement` (санкция Sovereign).
- **Watson** — смотритель Memory Library + офицер пентест-лаборатории; испытательный срок. Кнопки «Сверка хроники» и панель штата; `POST /api/watson/run`.
- **RiskScan** — риск-скан диффов, на службе; `POST /api/riskscan/run`.
- **Hunter** — внешняя очередь поручений, испытательный срок; digest — `tools/hunter/report.py`.
- **Rockefeller** — финансовый советник Sovereign, стратег капитала (паспорт `Memory/Agents/Rockefeller.md`, кандидат, назначен 09.11, `a960875`). Мандат: денежная сводка (касса Бендера + радар денег + топливо `/api/tokens/usage`), план недели с суммами, флаги на сжигание токенов без результата. Рантайм не собран — пилот-дайджест ждёт слова Sovereign.
- **Solomon, Maelstorm, Analyst** — кандидаты штата (Solomon — фильтр Notes/Inbox); отдельного рантайма нет.
- **Штат v4** (`Memory/Agents/estate-staff.json`, updated 2026-11-09): на службе — Бэрримор, Холмс, Risk scan; испытательный срок — Ватсон, Хантер; кандидаты — Рокфеллер, Соломон, Аналитик; уволен — Chief of Staff; приглашённые спецы — Сэнку (рецензент ландшафта скраперов) и личный штат CLI (5 ролей). Режим «поводка» (Sovereign, 31.10): автономных расписаний нет, запуск — кнопкой или рукой Sovereign; поле `last_pocket_result` — «результат в кармане» последнего прогона. Всего 16 паспортов в `Memory/Agents/`.
- Границы — ADR-003 (read-only), ADR-004 (доступ только через tools), ADR-005 («всё — инструмент»), P12 (нейтральность инструмента: опасно применение, не предмет); индекс ADR — `Core/Architecture/ADR/INDEX.md`.
- Реестр миров — `Memory/Worlds/README.md`; предложения миров — `Memory/Worlds/PROPOSALS-2026-11-08-ZCode.md`; план флота — `Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md`. Личный штат `~/.zcode/agents/` — 6 ролей.
- Планируемые, но не созданные каталоги: `eVo/agents/`, `eVo/runtime/`; фактический рантайм агентов живёт в `tools/agents/`.

---

## Ключевые файлы контекста

| Файл | Зачем |
|---|---|
| `README.md` | Единственная точка входа в корень |
| `VERSION` + `CHANGELOG.md` | Текущая версия (1.8.8) и хроника (в `Docs/Releases/` — только v1.8.3, v1.8.4) |
| `Docs/AI-ONBOARDING.md` | Быстрый вход для нового ИИ-ассистента (снимок 06.11) |
| `Memory/Engineering/LOG.md` | Инженерный журнал E-NNN (хвост — E-059, 08.11; сессия 08–09.11 не записана) |
| `Memory/Engineering/STATE.md` | Живая сводка для возобновления работы (актуализирована 09.11) |
| `Workspace/logs/events.jsonl` | Машинный журнал событий (gitignored): пульсы агентов, task.stage, snapshot.completed |
| `Memory/Worlds/README.md` | Канонический реестр миров; `PROPOSALS-2026-11-08-ZCode.md` — предложения четвёртого мира |
| `eVo/dashboard/worlds-draft/SPEC.md` | Требования верфи draft-миров |
| `Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md` | ТЗ фундамента данных (лейны Л-1…Л-5) |
| `Docs/TEMPLATING.md` | Протокол шаблонизации приватных координат |
| `Docs/CLOUD-VM-RUNBOOK-2026-11-07-ZCode.md` | Ранбук ВМ (генерируемый repo-артефакт — руками не править) |
| `Docs/NIGHT-LOG-2026-11-05-ZCode.md` | Итоги ночной смены 05.11 |
| `Memory/Context/CURRENT.md` | Текущий фокус и next action (отстаёт: дата внутри 2026-08-05) |
| `Core/Principles.md` | Принципы, включая P12 «Нейтральность инструмента» (08.11) |
| `Core/Architecture/ADR/ADR-002-Island-Architecture-Model.md` | Модель островов |
| `tools/agents/registry.json` | Реестр инструментов и прав агентов (v5) |
| `Memory/Agents/estate-staff.json` | Штат поместья v4 (Рокфеллер — кандидат) |
| `Memory/Agents/README.md` | Стандарт паспортов агентов |
| `Memory/Engineering/Tasks/Active/` | Task-лиджер — фактический список активных задач (27 карточек) |
| `tools/barrymore/TASK-PROTOCOL.md` | Как должен работать Barrymore |
| `Workspace/eVo/Planning/Epics/EPIC-001-Control-And-Visibility.md` | Контроль и видимость изменений |

`CURRENT.md` отстаёт от реальности (задача `update-current-context` в лиджере). Фактический план работ — `Memory/Engineering/PLAN.md` и task-лиджер `Memory/Engineering/Tasks/Active/` (27 карточек на 09.11: `agents-fleet` и `higgsfield-pilot-test` в «Проверке», `money-radar-orders` в «Анализе», holmes-* находки, security-, staff-, money- и ops-задачи).

---

## Самый маленький следующий прототип

Реализовано: Morning Brief, канбан с подписанными переходами и вратами, фундамент данных Л-1…Л-5, штаб COMMAND CENTER, обсерватория, fleet-панель, peer notes, облачный контур с лабой и консолью атак.

Следующие минимальные шаги (по санкциям Sovereign и лиджеру):

1. Пилот Рокфеллера — денежный дайджест (касса + радар + топливо) ждёт слова.
2. Выбор четвёртого мира из `worlds-draft/` (13 превью; коммит заявляет 14 вариантов — расхождение уточнить).
3. Витрина :80 на ВМ — параллельная сессия, не трогать.

---

## Правила для следующих сессий

1. Сначала этот файл, затем хвост `Memory/Engineering/LOG.md` (E-NNN), `CURRENT.md` (помня, что он отстаёт) и `Docs/AI-ONBOARDING.md`.
2. Не путать `Interface/` (отдельный Vue/Vite-прототип, не runtime) с `eVo/dashboard/` (реальный UI).
3. Не приписывать агентам больше прав, чем в `tools/agents/registry.json` (v5) и паспортах: всё read-only; запись — `report.write` Холмса и санкционированные API дашборда (`/api/holmes/implement`, Mark Done, stage-переходы канбана через врата `can_transition`).
4. Не запускать `bootstrap.ps1` без явной задачи: он пишет файлы.
5. `eVo/graphify-out/` и корневой `graphify-out/` не править вручную; `brief.js`, `vacancies.js`, `orders-triage.js`, `hunter-report.js`, `excursion-data.js` — автогенерация, править их источники, не сами файлы.
6. Секреты — в `Workspace/.env` (untracked, шаблон `.env.example`); не читать и не выводить значения. Ключ шлюза восстановлен 07.11 (E-054), LangSmith — нет.
7. Приватные зоны — `Workspace/private/`, `Workspace/intel/`, `tools/intel/` (внутренний контур разведки): не читать, не выводить, не картографировать, не коммитить. Pre-commit: hard RED для `Workspace/private/` (`d87ba7b`), publish-blocklist для внутренних контуров (`8162b8a`).
8. Машинный журнал `Workspace/logs/events.jsonl` — только дозапись через `tools.lib.log_event.append_event` внутри try/except; файл gitignored, чистить/переписывать нельзя.
9. Канбан: переходы — только через `task_store` (`POST /api/tasks/<id>/stage/<col>` с `by`), не правкой JSON руками; каждая запись history несёт подпись `by`; в test/done — только source/owner/Sovereign/ZCode.
10. POST-эндпоинты сервера 8765 требуют заголовок `Origin: http://127.0.0.1:8765` — curl/скрипты без него получают 403.
11. Рабочее дерево общее с параллельными сессиями: чужие изменения не смешивать со своими и не коммитить их (витрина :80 на ВМ — чужая работа, не тронута).
12. Docker обходит ufw: любой compose-стек — биндинги только `127.0.0.1`, наружу только через туннель/WireGuard (урок E-055; правило зашито в `Workspace/cloud/` и `~/lab/up.sh` на ВМ).
13. В Git Bash этой машины `python`/`python3` — Store-заглушка; реальный интерпретатор — `py` (3.12.10) или полный путь `python.exe`.
14. Если структура репозитория изменилась существенно — обновить этот файл.
15. Не добавлять в корень новые точки входа: карта, help, questions и обзоры живут в `Docs/` и `Notes/`.
