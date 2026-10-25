# Карта репозитория Platform Evo

Дата съёмки: 2026-10-22; обновлён 2026-10-25 (реструктуризация контура — RFC-001)  
Назначение: не изучать дерево проекта с нуля. Это фактическое состояние репозитория, а не целевая архитектура.

Смежные точки входа:

- идея системы: `README.md`
- принципы: `Core/Principles.md`
- текущий фокус: `Memory/Context/CURRENT.md`
- каталоги по задумке: `Docs/Architecture/Structure.md`
- индекс архитектуры: `Docs/Architecture/README.md`

---

## Что это

Персональная «операционная система эволюции». Основа — обычные файлы (markdown + статический UI). Принцип: хранить не только результаты, но и контекст, почему они появились.

Рабочий код вторичен. Главный runnable-артефакт — карта Estate в `eVo/dashboard/`. Бэкенда, API и базы нет.

---

## Каталоги верхнего уровня

| Каталог | Задумка | Факт на 2026-10-22 |
|---|---|---|
| `Core/` | Ядро: принципы, глоссарий, ADR | Документы, не runtime |
| `eVo/` | Стюард: состояние, планирование, Command Center | Живой UI: `dashboard/`; `agents/` нет |
| `Memory/` | Долговременный контекст системы | Markdown: CURRENT, сессии, решения, идеи |
| `Memory/Engineering/` | — (создан 25.10.2026) | Инженерный журнал работ: STATE, LOG, FINDINGS, PLAN |
| `Interface/` | Способы взаимодействия с системой | Удалён 25.10.2026 (RFC-001): неиспользуемый Vue-шаблон; реальный UI — `eVo/dashboard/` |
| `Workspace/` | Пользовательские проекты и артефакты | Почти пусто: EPIC-001 |
| `Modules/` | Предметные домены | Почти пусто (`Carrier.md`) |
| `Vision/` | Концепты, визуал, истории Estate | Идеи и изображения |
| `Tools/` | Скрипты обслуживания, протокол Barrymore | PowerShell + markdown-задачи |
| `Docs/` | Архитектурные документы | Structure / Principles / Decisions, Map, Ops |
| `RFC/` | Предложения изменений | Создан 25.10.2026: README + процесс; RFC-001 (границы контура) — Accepted |
| `Notes/` | Входящий поток | Inbox, открытые вопросы |
| `Backup/` | Старые визуалы Estate | Вынесен за контур 25.10.2026 в `C:/Work/Platform-archive/` (RFC-001) |
| `.obsidian/` | Настройки Obsidian | Репозиторий ещё и как knowledge base |

В корне остаются только `README.md`, `CHANGELOG.md` и git/редактор мета. Остальные бывшие корневые точки входа разнесены по `Docs/` и `Notes/`.

---

## Где лежит рабочий код

### Estate dashboard (основной UI)

Путь: `eVo/dashboard/`

- `index.html` — карта островов (Level 1)
- `style.css`, `app.js`, `languages.js` — взаимодействие и RU/EN
- `workspace.html` — рабочий кабинет (Level 3)
- `projects/` — активный визуальный проект (`marvel_v`, `minimalism`, `organica`)
- `locales/` — JSON-локали (дублируют часть `languages.js`)
- `Backup/` — предыдущая версия дашборда
- `assets/estate_bg.png` — фон карты

Поведение: клик по острову открывает модалку. Задачи рычагов живут в `localStorage`. Morning Brief на острове Barrymore — захардкоженный текст, не чтение Memory.

Острова на карте: Main Estate, Navigator, Memory Library, Harbor, Career Guild, Knowledge Archive, AI Sandbox, Workshop. Бэрримор — не маячок, а кликабельная HTML-плашка в верхнем левом секторе: деревянная панель + отдельный слой-портрет `assets/barrymore.png`, приветствие по времени суток и счётчик задач (`tasks.js`); под ней ссылка «Review» при новом непрочитанном докладе. Фон карты — чистый арт без нарисованного текста (исходник `Vision/First_evo_pictures/Good_references/Clear_main.png`). Инструкция — `Docs/Barrymore.md`.

### Vue-каркас — удалён (25.10.2026)

`Interface/` был неиспользуемым шаблоном Vite+Vue и удалён по RFC-001. Реальный UI — `eVo/dashboard/`.

### Инструменты

- `tools/evo-check.ps1` — git release-gate (ветка, dirty, последний коммит)
- `tools/evo-save.ps1` — интерактивные add / commit / push
- `tools/barrymore/execute.ps1` — add + commit + отчёт в `tools/barrymore/reports/`
- `eVo/scripts/bootstrap.ps1` — **создаёт** папки `agents/`, `runtime/` (ADR больше не создаёт — решения в `Core/Architecture/ADR/`); не запускать без нужды
- `.vscode/tasks.json` — Add / Commit / Push

### Сгенерированный граф кода

`eVo/graphify-out/` — кэш Graphify, не исходники; с 25.10.2026 не отслеживается Git (пересобирается). Для навигации по связям файлов, не для правки.

---

## Как запускать

Отдельного сервера приложения нет.

1. **Главный интерфейс:** открыть `eVo/dashboard/index.html` в браузере.
2. **Morning Brief (Баррримор):** `python tools/barrymore/morning-brief-agent.py` (данные + доклад LLM) или `powershell tools/barrymore/morning-brief.ps1` (только данные); инструкция пользователя — `Docs/Barrymore.md`.
3. **Состояние системы** смотреть в файлах, не в UI: `Memory/Context/CURRENT.md`; инженерный контекст работ — `Memory/Engineering/STATE.md`.

Чтение markdown с диска из статического `index.html` через `file://` ограничено браузером. Для живой подгрузки Memory нужен простой static server или встроенный снимок файла.

---

## Агенты и боты

Исполняемого бота нет: нет LLM-клиента, Telegram, runtime, цикла агента, `geminiClient.js`.

Что есть:

- **Barrymore** — роль стюарда и протокол задач (`tools/barrymore/`). Код: git-commit скрипт. Приватная память агента не реализована (`Memory/Barrymore/README.md`).
- Дашборд показывает статусы агентов **статичными строками** (ADR-003 read-only, ADR-004 доступ только через tools; индекс ADR — `Core/Architecture/ADR/INDEX.md`).
- Концепты команды: `Memory/New_ideas/estate_archipelago_agents.md`, `Memory/New_ideas/syndicate_architecture.md`.
- Идея локального агента: `Vision/Future/Experiments/Local_AI_Agent_Experiment.md`.
- Gemini: лог ручного теста `Memory/Context/2026-10-19-gemini-api-first-test.md`, в приложение не вшит.
- Планируемые, но не созданные каталоги: `eVo/agents/`, `eVo/runtime/` (их должен создать bootstrap).

---

## Ключевые файлы контекста

| Файл | Зачем |
|---|---|
| `README.md` | Единственная точка входа в корень |
| `Memory/Context/CURRENT.md` | Текущий фокус и next action |
| `CHANGELOG.md` | Хроника изменений |
| `Docs/Architecture/README.md` | Индекс архитектуры |
| `Core/Architecture.md` | Слои v0.1 |
| `Core/Architecture/ADR/ADR-002-Island-Architecture-Model.md` | Модель островов |
| `tools/barrymore/TASK-PROTOCOL.md` | Как должен работать Barrymore |
| `tools/barrymore/initiatives/INITIATIVE-0001-live-state-view.md` | Живое состояние из источников истины |
| `Workspace/eVo/Planning/Epics/EPIC-001-Control-And-Visibility.md` | Контроль и видимость изменений |

Зафиксированный next action в CURRENT (на дату съёмки): кнопка Barrymore → Morning Brief (поместье, деньги, задачи, риски, возможности).

---

## Самый маленький следующий прототип

Не начинать с мультиагентной системы, Gemini или Vue.

Минимальный полезный шаг на существующем коде: **read-only Morning Brief** в модалке острова Barrymore, собранный из:

1. `Memory/Context/CURRENT.md`
2. списка рычагов в `eVo/dashboard/app.js` / `localStorage`
3. при необходимости — короткой выдержки из последней сессии или решения

Это совпадает с INITIATIVE-0001 и с незакрытой задачей дашборда «интеграция Context / Decisions».

---

## Правила для следующих сессий

1. Сначала этот файл, затем `CURRENT.md`.
2. Не путать `Interface/` (Vue-заглушка) с `eVo/dashboard/` (реальный UI).
3. Не считать markdown-роли агентов существующим runtime.
4. Не запускать `bootstrap.ps1` без явной задачи: он пишет файлы.
5. `eVo/graphify-out/` не править вручную.
6. Если структура репозитория изменилась существенно — обновить этот файл.
7. Не добавлять в корень новые точки входа: карта, help, questions и обзоры живут в `Docs/` и `Notes/`.
