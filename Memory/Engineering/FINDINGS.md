# Engineering FINDINGS

## Как читать

- Статусы: `ПОДТВЕРЖДЕНО` — прочитано/выполнено в зафиксированной работе, есть доказательство; `ПРЕДПОЛОЖЕНИЕ` — правдоподобно, но не доказано; `НЕ ПРОВЕРЕНО` — не изучалось.
- Доказательства: `путь:строки`, команда или коммит. Привязка к работе — номер записи в LOG.md.
- Правка фактов здесь допустима (статус/уточнение), но любая правка сопровождается блоком «Корректировка» со ссылкой на запись LOG, где она зафиксирована. История правок — в LOG.
- «Подтверждено, что документ утверждает X» ≠ «X верно». Утверждения документов отмечаются отдельно от фактов о репозитории.

---

## §1. Общие факты о репозитории — ПОДТВЕРЖДЕНО (LOG E-000, 2026-10-25)

- Корень — `C:\Work\Platform`, git-репозиторий; на 2026-10-25 14:38: ветка `release/v1.8.1`, HEAD `1164ed7` («add Summary 24.10.2026»). Доказательство: команды `git branch --show-current`, `git log -1`, `git status --porcelain`.
- Каталоги первого уровня (полный список): `.agents`, `.claude`, `.github`, `.obsidian`, `.vscode`, `Backup`, `Core`, `Docs`, `Interface`, `Memory`, `Modules`, `Notes`, `Vision`, `Workspace`, `claude-chief-of-staff`, `eVo`, `tools`; файлы: `README.md`, `CHANGELOG.md`, `SYSTEM_SUMMARY.md`, `skills-lock.json`, `.claudeignore`, `.gitattributes`, `.gitignore`, `.graphifyignore`. Доказательство: `ls -la` корня, 2026-10-25.
- Каталог `RFC/` **не существует**, хотя описан в `Docs/Ops.md` (раздел «RULE: Source of Truth»: «изменения дизайна: RFC/») и `Docs/Architecture/Structure.md:125-141` («## RFC» — строка 125, «## RFC/Backlog» — 141). Доказательство: `ls` корня, отфильтрованный по `rfc` — пусто; полного `RFC/` нет в `ls -la` корня. [Корректировка 2026-10-25, LOG E-000-CORR: диапазон строк ошибочно указан как 126-140.]
- `Memory/Engineering/` не существовал до 2026-10-25 14:38 (создан при E-000). Доказательство: проверка `test -e` перед созданием.

## §2. Существующие механизмы журналирования, состояния и решений — ПОДТВЕРЖДЕНО (LOG E-000, 2026-10-25)

### §2.1 Точки входа и правила

- `Docs/Map.md` — живая карта репозитория, дата съёмки 2026-10-22 (`Docs/Map.md:3`). Правила для следующих сессий: вход через Map → `Memory/Context/CURRENT.md`; обновлять карту при существенных изменениях структуры (`Docs/Map.md:147-155`). Map утверждает: главный runnable-артефакт — `eVo/dashboard/`, «бэкенда, API и базы нет» (`Docs/Map.md:20`); «исполняемого бота нет» (`Docs/Map.md:102`).
- `Docs/Ops.md` — Source of Truth: точка входа `README.md`, структура — `Docs/Map.md`, изменения — `CHANGELOG.md`, изменения дизайна — `RFC/` (каталога нет, §1).
- `CHANGELOG.md` — формат `YYYY-MM-DD | change | reason | RFC` (`CHANGELOG.md:6`; строка 5 — заголовок «## Format»); последние записи: 2026-10-19 (Gemini-тест), 2026-10-22 (консолидация корневых документов). [Корректировка 2026-10-25, LOG E-000-CORR: ссылка ошибочно указана как `:5`.]

### §2.2 Состояние и возобновление

- `Memory/Context/CURRENT.md` — живое состояние + Next Action; датирован **2026-08-05** (`CURRENT.md:3`) — на 2026-10-25 устарел на ~2,5 месяца. Next Action в нём: Morning Brief (`CURRENT.md:34-40`).
- `Memory/Context/Handoffs/` — два файла от 2026-07-08 (`HANDOFF-2026-07-08.md`, `HANDOFF-2026-07-08-eVo.md`). Прочитан только `-eVo`: формат «Current state / Git / Current task / Next topics / Do not restart architecture discussion». Содержимое второго — НЕ ПРОВЕРЕНО.
- `Memory/Snapshots/`, `Memory/Archive/` (Memos, Reports) — снимки и архивные отчёты; в Archive/Reports два файла. `Report-2026-10-23-Platform-eVo.md` — «единая сводка» разведки и графа eVo, срез 2026-10-20 (`:1`, `:3`); в нём применялось разделение «подтверждено / INFERRED» (раздел «Граф eVo»: 29 связей INFERRED из 105). [Корректировка 2026-10-25, LOG E-000-CORR: файлу ошибочно приписан «Интегрированный отчет» с датой фиксации 2026-10-24 — содержимое перепутано с `SYSTEM_SUMMARY.md`.]

### §2.3 Решения — три параллельных места

- `Memory/Decisions/` — формат D-0xx (Context/Decision/Reason/Consequences); фактически один D-001 (git + branching main/experiment). Доказательство: перечень `find Memory/Decisions` — README.md и D-001.md.
- `Docs/Architecture/Decisions.md` — ADR-001 (UTF-8) + «История подтверждений» DEC-001 (тест evo-save, коммит 7bf160d).
- `tools/barrymore/decisions/` — DECISION-0001…0003 (прочитан только 0001 — «Barrymore как управляемый исполнительный помощник»).

### §2.4 Прочие механизмы

- `Memory/Sessions/` — append-only «журнал изменений мышления» (README); жизненно-стратегический уровень (пример: сессия 2026-08-05 о переезде/казначействе), не инженерный лог.
- `Memory/Timeline.md` — файл из 1 строки, содержимое не фиксировалось (практически пуст).
- `Memory/Commit-map.md` — перевод 4 коммитов в смысловые этапы.
- `Memory/Capture.md` — одна запись 2026-06-30.
- `tools/barrymore/reports/` — один автогенерированный отчёт 2026-07-09 (git-снимок от `execute.ps1`); runtime-агента нет (§2.1).
- `SYSTEM_SUMMARY.md` (в корне) — «Интегрированный отчет» (агентная архитектура «архипелаг Estate», статус проекта, раздел «Как с этим работать (для LLM)»), дата фиксации 2026-10-24 (`:1`, `:3`). Находится в корне, что противоречит правилу «не добавлять в корень новые точки входа» (`Docs/Map.md:155`). [Корректировка 2026-10-25, LOG E-000-CORR: файл ошибочно описан как «сводка разведки и графа eVo, срез 2026-10-20» — содержимое перепутано с `Report-2026-10-23-Platform-eVo.md`.]

### §2.5 Выводы, принятые пользователем 2026-10-25

На основе §2: возобновление работы через CURRENT.md/Handoffs сейчас ненадёжно (устаревание); инженерного журнала действий и накопителя подтверждённых фактов нет. Принято решение создать `Memory/Engineering/` (5 файлов, LOG E-000). Решения продолжают фиксироваться в `Memory/Decisions/`.

## §3. Что утверждают ключевые документы (содержание документов — ПОДТВЕРЖДЕНО; истинность утверждений — НЕ ПРОВЕРЕНО до аудита)

- `Core/Architecture.md` (v0.1): три слоя — Core / Modules / Knowledge (раздел 2); адаптивность — новые модули без изменения ядра (раздел 3); переносимость — независимость от устройства/сервиса, «основа — обычные файлы» (раздел 4).
- `Docs/Architecture/Structure.md` (v0.1, обновлено 12.07.2026): четыре области (Платформа/Память/Workspace/Документация), правила зависимостей слоёв (раздел «Архитектурные правила»), RFC-процесс (каталога нет, §1), документация на русском.
- `Docs/Map.md:26-40` — таблица «задумка vs факт» по всем каталогам верхнего уровня на 2026-10-22 (например, `Workspace/` — «почти пусто: EPIC-001», `Modules/` — «почти пусто (Carrier.md)»). Эти строки Map — утверждения карты, напрямую этой работой не перепроверялись (см. §4).
- `Memory/Archive/Reports/Report-2026-10-23-Platform-eVo.md` (раздел «Граф eVo»): 123 узла, 105 связей, 29 INFERRED, построено по `eVo/` через Graphify; материалы в `eVo/graphify-out/` (не перепроверялось). [Корректировка 2026-10-25, LOG E-000-CORR: путь ошибочно указан как `SYSTEM_SUMMARY.md`.]
- `SYSTEM_SUMMARY.md`: описание агентной архитектуры «архипелаг Estate» и статуса проекта (не перепроверялось). [Корректировка 2026-10-25, LOG E-000-CORR: путь ошибочно указан как `Memory/Archive/Reports/Report-2026-10-23-Platform-eVo.md`.]

## §4. НЕ ПРОВЕРЕНО (не читалось в зафиксированных работах)

- Содержимое: `Interface/` (включая package.json, src/), `eVo/` (dashboard, scripts, graphify-out, Bootstrap), `Core/` кроме `Architecture.md` (Principles, глоссарий, `Core/Architecture/ADR/` — на ADR-0001/0002 ссылаются Map и Decisions, сами файлы не читались), `Modules/`, `Vision/`, `Backup/`, `claude-chief-of-staff/`, `.agents/`, `.claude/`, `.github/`.
- Файлы: корневой `README.md`, `Notes/Inbox.md`, `Notes/Questions.md`, `Notes/evo-test-run.md`, `Workspace/*` (.env, CURRENT.md, main.py, EPIC-001), `Memory/Agents/Solomon.md`, `Memory/Archive/Memos/*`, `Memory/New_ideas/*`, `Memory/Context/learning-*.md`, `Memory/Context/2026-10-19-gemini-api-first-test.md`, `Memory/Snapshots/SNAPSHOT-2026-07-24…`, `Memory/Context/CURRENT_11_07_2026.md`, `eVo-SNAPSHOT-2026-07-12.md`, второй Handoff, `tools/barrymore/decisions/0002-0003`, `tools/barrymore/tasks/*`, `tools/evo-*.ps1` (назначения — из Map, код не читался).
- Номера строк для непрочитанных файлов нигде в этом файле не приводятся.

[Актуализация 2026-10-25, LOG E-001: большая часть этого списка проверена аудитом E-001 — см. §5-§10. Оставшееся непроверенным перечислено в §11.]

---

## §5. E-001: точки входа и запускаемое — ПОДТВЕРЖДЕНО (LOG E-001, 2026-10-25)

### §5.1 Реально запускаемое (выводы из чтения кода; скрипты/UI не запускались)

- `eVo/dashboard/index.html` — статическая карта: 9 островов захардкожены (`index.html:64-178`); контент модалок Level 2 строится из словаря `LANG` в `languages.js` (`app.js:202-362`); RU/EN через localStorage (`app.js:40-59`, `languages.js:264`); задачи рычагов в localStorage (`app.js:21-25, 399, 417`). В `app.js` нет ни одного `fetch`/XHR — связи с Memory нет; Morning Brief — статические строки (`languages.js:24-26`).
- `eVo/dashboard/workspace.html` — автономный Level 3, статический (`workspace.html:33-52`); Level 3 существует дважды: модалка в `index.html:217-266` и эта страница.
- `tools/evo-check.ps1` — read-only release gate (ветка/статус/коммит/remote).
- `tools/evo-save.ps1` — интерактивные `git add .` / commit / push с подтверждением y/n.
- `tools/barrymore/execute.ps1` — `git add .` + commit + отчёт в `reports/` БЕЗ подтверждения.
- `Workspace/main.py` — LLM-эксперимент: OpenAI-клиент к `http://localhost:31415/v1` (`main.py:26`), трассировка LangSmith, «деплой» — фикция (`main.py:64-67`). См. §10.1 — секреты.
- `Interface/` — Vite+Vue3-шаблон: зависимость только vue, тестовых скриптов нет (`Interface/package.json:6-19`); `src/App.vue` целиком статичен; заголовок «Vite App» (`Interface/index.html:7`); README — нетронутый шаблон Vite. `node_modules` УСТАНОВЛЕН (173 каталога) — против `Docs/Map.md:93` («пакеты могут быть не установлены»).
- `eVo/scripts/bootstrap.ps1` ни разу не запускался: каталогов `eVo/agents|runtime|memory|docs` на диске нет (проверено `find`).
- Сервера, API, БД, CI нет: в `.github/` только `copilot-instructions.md`. Внешняя зависимость UI — Google Fonts (`index.html:8-10`).

### §5.2 Пустые файлы-заглушки (проверено размерами)

`eVo/dashboard/locales/{ru,en,fr}/dashboard.json` — 0 байт ×3; `Modules/Carrier.md` — 1 байт; `Memory/Timeline.md` — 0 байт; `Vision/Estate/Decomposition/ESTATE_INTERACTIVE_CALLOUTS_V2.1.md` — 0 байт. `Core/Identity.md` — 4 раздела из 6 заполнены «...» (`Identity.md:3-23`); `Core/Glossary.md` — 12 терминов без определений.

## §6. E-001: классификация компонентов

- **Реализовано:** dashboard L1+L2 (статически работающий); git-скрипты (3); Graphify-граф (`eVo/graphify-out/`, 34 файла, сгенерирован и закоммичен).
- **Частично:** Level 3 (две статические реализации, контролы ничего не делают); Memory-подсистема (ведётся, но `Memory/Context/CURRENT.md` датирован 2026-08-05); ADR (2 файла на диске, 3 — только в heredoc `bootstrap.ps1`).
- **Заглушки:** §5.2 + `Interface/` (шаблон).
- **Только документация/планы:** агентный слой (`Memory/Agents/Solomon.md` от 2026-10-24 упоминает 7+ агентов, файл существует только для Соломона); Morning Brief (`tools/barrymore/decisions/DECISION-0003.md`: «Не реализовывать AI. Первый шаг: Morning Brief»); Kingdom Status (`TASK-0002` — Status: Open); i18n-движок (план в `Memory/Context/CURRENT_11_07_2026.md`); RFC-процесс (см. §1); приватная память Barrymore (`Memory/Barrymore/README.md:15`).

## §7. E-001: дублирование и конкурирующие механизмы

Побайтовые дубли (diff/cmp, 2026-10-25): `eVo/dashboard/Backup/` — копия 7 файлов dashboard; `Handoffs/HANDOFF-2026-07-08.md` ≡ `…-eVo.md`; `Archive/CURRENT-…-before-citadel.md` ≡ `…-before-refactor.md`; `tools/evo-save.ps1` ≈ `.backup` (разница — BOM/перевод строки); `Workspace/.env` ≡ `.env.backup`.

Конкурирующие механизмы:
1. Два «текущих состояния»: `Memory/Context/CURRENT.md` (2026-08-05) и `Workspace/CURRENT.md` (без даты) — оба CURRENT.
2. Решения в 3 местах + потенциальное 4-е: `Memory/Decisions/`, `Docs/Architecture/Decisions.md`, `tools/barrymore/decisions/`, и ADR-0001…0003, создаваемые bootstrap в `eVo/docs/adr/`. Пространства нумерации ADR пересекаются с разным смыслом: ADR-001 = UTF-8 (Docs), ADR-002 = острова (Core), ADR-0001 = «Barrymore is Read Only» (только в bootstrap).
3. Принципы в двух нумерациях: `Core/Principles.md` P1–P11 против черновиков P9–P21 в `Notes/Inbox.md:5-17` (номера совпадают, смысл другой; `Memory/Archive/Memos/SESSION-NOTES.md` подтверждает: P9–P14 обсуждались, но не фиксируются).
4. Три «chief of staff / утренних брифа»: Morning Brief (CURRENT.md:34-40, DECISION-0003, TASK-0002), сторонний `claude-chief-of-staff/` (gitlink-подмодуль, его `/gm` — утренний брифинг) и скилл chief-of-staff в `.agents/` + `.claude/` (версии файлов различаются: 3884 против 876 байт).
5. Локализация: работающий `languages.js` против пустых `locales/*.json`.
6. Навигация по архитектуре: `Docs/Map.md` против Graphify (`.github/copilot-instructions.md`).

## §8. E-001: фактические связи слоёв

Связи Core ↔ eVo ↔ Interface ↔ Memory ↔ Modules ↔ Workspace почти отсутствуют; слои существуют в документах, не в коде:

- Interface → ничего не читает (статический `App.vue`).
- dashboard → Memory: связи нет (нет `fetch` в `app.js`) при заявленном источнике `CURRENT.md`; нарушает ADR-002 «Interface should discover entities instead of hardcoding them» (`Core/Architecture/ADR/ADR-002…md:90`).
- Workspace («принадлежит пользователю», `Structure.md:186`) содержит системные по виду артефакты: `main.py` с ключами, второй CURRENT.md.
- Modules пуст (§5.2) — принцип адаптивности (`Core/Architecture.md`, раздел 3) не опробован.
- `eVo/README.md:13-17` описывает Steward в настоящем времени — риторика реализованности без runtime.

## §9. E-001: Barrymore — исполняется vs описано

- Исполняется: только `tools/barrymore/execute.ps1` (git add + commit + отчёт). Единственный завершённый автотест — 2026-07-14, коммит `3c75bad` (INITIATIVE-0001, блок Completed).
- Только описано: Morning Brief (статический текст `languages.js:24-26` вместо чтения CURRENT.md); Kingdom Status (TASK-0002 — Open); подпись дашборда «ЛИЧНЫЙ СТЮАРД ПЛАТФОРМЫ (ADR-0001)» (`app.js:227`) ссылается на ADR, отсутствующий на диске (есть только в heredoc bootstrap.ps1; существующий ADR-001 — про UTF-8); TASK-0003 (Status: In Progress) содержит блок Required Result, скопированный из TASK-0002, — дефект шаблона.

## §10. E-001: противоречия и риски

### §10.1 БЕЗОПАСНОСТЬ (критично; требует решения пользователя)

- `Workspace/main.py:16, 27` — настоящие ключи: LangSmith (`lsv2_pt_…`, значение в файле, здесь не приводится) и FreeLLMAPI (`freellmapi-…`). Файл закоммичен в HEAD `1164ed7` («add Summary 24.10.2026»; `git log --follow -- Workspace/main.py` — единственный коммит).
- Не запушено: `git grep 'lsv2_pt'` по `origin/release/v1.8.1` и `origin/main` — 0 совпадений; ветка ahead 1. Окно для очистки коммита до push открыто на 2026-10-25 15:29.
- `Workspace/.env` содержит ключ с тем же префиксом; файл и `.env.backup` НЕ отслеживаются (`.gitignore: .env`) — проверено `git ls-files`.
- Ротация ключей рекомендована независимо от очистки истории (ключи существуют в локальной истории).

### §10.2 Противоречия документов

1. Версии: `Core/Architecture.md` «v0.1»; `Docs/Architecture/README.md:3` «0.2»; `tools/barrymore/decisions/DECISION-0002.md` «0.1.0-alpha»; текущая ветка `release/v1.8.1`.
2. Веточные модели: D-001 (main + experiment) vs `SNAPSHOT-2026-07-24` (main + develop + refactor/platform-boundaries-v2) vs факт — 6 веток, работа в release/v1.8.1.
3. `RFC/` описан в 4 документах (`Structure.md:125-141`, `Docs/Ops.md`, `README.md:31`, `Docs/Map.md`), не существует (§1).
4. Root drift: `SYSTEM_SUMMARY.md` и сторонний `claude-chief-of-staff/` в корне вопреки `Map.md:155` и Ops.md.
5. Dashboard имитирует живое состояние: «Активные процессы: 5», пульс «1.2с», «3 изменения» (`index.html:33-43`, `languages.js:11-13, 25`) — статические строки; противоречит INITIATIVE-0001 («Состояние должно вычисляться на основе источников истины»).
6. `bootstrap.ps1` создал бы `eVo/memory/` и `eVo/docs/` — дубликаты корневых Memory/ и Docs/.
7. Кодировка: `.github/copilot-instructions.md` содержит mojibake («how do iтАж») — нарушение ADR-001 (UTF-8); `eVo/project-tree.txt` — UTF-16-артефакт с mojibake.
8. Git-гигиена: ~30 МБ PNG в `Backup/` (21 tracked-файл) и сгенерированный кэш `eVo/graphify-out/` (34 tracked-файла) под версионным контролем; отчёт barrymore отслежен, хотя `.gitignore` теперь исключает `tools/barrymore/reports/`.

## §11. E-001: доказательная база, неопределённости, непроверенное

### §11.1 Факты для целевой архитектуры

1. Единственный живой артефакт — статический dashboard без связи с источниками истины; соединение UI ↔ Memory — центральная задача (ограничение file:// отмечено в `Docs/Map.md:96`).
2. Memory — самая ценная работающая подсистема, но с конкурирующими точками входа (§7).
3. Interface/Vue ни с чем не связан — решение «развивать или удалить».
4. Модульность не опробована (Modules пуст).
5. Агентный слой существует только в документах; исполнимая форма — PowerShell-обёртки над git.
6. ADR нуждаются в едином пространстве нумерации.
7. Нужна политика секретов (§10.1).
8. UI зависит от Google Fonts — офлайн-хрупкость.
9. Graphify уже принят как механизм навигации (`.github/copilot-instructions.md`).

### §11.2 Критические неопределённости (за пользователем)

Судьба `claude-chief-of-staff/` (инструмент или исследование; наложение на Morning Brief); rationale версии/ветки v1.8.1; судьба дубликатов (dashboard/Backup, locales, второй CURRENT, evo-save.backup, .env.backup); обработка секрета до первого push.

### §11.3 Не проверено в E-001

Не читались: `Vision/Stories/*`, `Vision/Future/*` (кроме `Local_AI_Agent_Experiment.md`), `claude-chief-of-staff/CLAUDE.md` и его yaml, `eVo/graphify-out/GRAPH_REPORT.md`, `eVo/dashboard/style.css`, хвосты `Memory/Genesis.md`, `Memory/New_ideas/*`, `learning-plan.md`, `Report-2026-10-20.md`, различия `.claude/skills/…` от `.agents/…` (установлено только, что файлы разные); значения переменных `Workspace/.env` (сознательно — только имена). Скрипты и UI не запускались — выводы о поведении из чтения кода.
