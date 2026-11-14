# Engineering STATE

> Живая сводка для возобновления работы. **Не является источником истины**:
> истина — реальные файлы репозитория и Git. Каждое утверждение ниже — со ссылкой
> на доказательство в FINDINGS.md или LOG.md.

## Контроль

- Обновлено: 2026-11-09 (полная актуализация; предыдущая запись — 2026-10-26, эпоха `feature_1.8.2`/E-015, была протухшей примерно на 45 записей журнала и 3 релиза)
- Ветка: `main`. Смежные ветки: `release/1.8.6`, `release/1.8.7`, `release/1.8.8` (локально и на origin), `release/v1.8.1`, `develop` (только origin). Работа идёт на `main`; release-ветки — точки фиксации релизов
- HEAD: `a960875` (2026-11-09 05:25) «Штат v4: Рокфеллер — финансовый советник (паспорт, кандидат, пилот-дайджест ждёт слова)»
- `VERSION` = 1.8.8 (коммит `7d9a7ee` «Release 1.8.8: version bump + changelog», 2026-11-09). Заметок в `Docs/Releases/` для 1.8.7/1.8.8 нет — там по-прежнему только v1.8.3 и v1.8.4; хроника 1.8.7/1.8.8 живёт в `CHANGELOG.md`
- Рабочее дерево: изменены `eVo/dashboard/brief.js`, `hunter-report.js`, `orders-triage.js` — все три автогенерируемые, правки параллельных сессий (не смешивать со своими, не коммитить); untracked: `Workspace/cloud/probes/`
- Журнал: хвост `LOG.md` — E-059 (2026-11-08, 00:3x, постоянный туннель + первый полный цикл атак через rl-console). Сессия 08–09.11 (штаб COMMAND CENTER, релиз 1.8.8, publish-blocklist, Рокфеллер) записи E-060 в LOG ещё не имеет — коммиты опережают журнал (`113bb9e`…`a960875`)

## Статус аудита

**Аудит эпохи старта завершён и заархивирован** (E-001…E-008; архивная копия: `Memory/Archive/Reports/Report-2026-10-25-audit.md`). Инженерный журнал давно в производственной фазе: E-001…E-059.

Вехи после предыдущей записи STATE (26.10): v1.8.3/v1.8.4 (29.10, бриф+сервер, AI Sandbox, Hunter), паспорта штата и реестр миров (04.11, E-042/E-045), санитария git + Watson/RiskScan (E-046), VULN-PROGRAM и целевой стенд (E-047), ночная смена data-foundation Л-1…Л-5 + врата + busy-лок (E-048/049), типы сущностей канбана + секрет-гейт фаза 2 (E-050), экскурсия в AI Sandbox (E-051), облачная ВМ «Мастерская» (E-052), шаблонизация приватных координат (E-053), «Заметка соседу» (E-054), лабораторный контур на ВМ — DVWA/Juice Shop/Vulhub/reallab/rl-console (E-055…E-058), постоянный туннель (E-059), релиз 1.8.8 — штаб + обсерватория + worlds-draft + Рокфеллер (08–09.11).

## Подтверждено (кратко; доказательства в LOG и Git)

- **Релиз 1.8.8** (`7d9a7ee`, 09.11; строка в `CHANGELOG.md` от 2026-11-09): штаб COMMAND CENTER + `/api/tokens/usage`, обсерватория Maelstorm (воронка/корабли/шлюпки), 14 драфт-миров + 13 превью (`worlds-draft`, выбор за Sovereign), принцип P12 нейтральности инструмента (`ad071d4`, 08.11), план Dark Watch и intel-картотека выведены из git (visibility rule, `113bb9e`).
- **Штаб COMMAND CENTER** (`585f225`): `eVo/dashboard/command-center.html/css/js` — панели: токены (+расход по часам), конвейер, сторож, артефакты, «ждёт слова», блокеры денег, сигналы. Данные: `GET /api/tokens/usage` (агрегат по `model-io-*.jsonl`, `dashboard-server.py:tokens_usage_snapshot`), `/api/tasks`, `/api/agents/*`. Сторож `/api/steward` — 6 слоёв самодиагностики + плитка в штабе (`9a87cf3`, 09.11).
- **Обсерватория Maelstorm**: `maelstorm-observatory.html` + `observatory.css/js` — canvas-картина работы агентов (воронка, корабли, шлюпки, дуга причалов).
- **worlds-draft** (`58ec0d7`, 09.11): `eVo/dashboard/worlds-draft/` — 13 standalone-страниц-превью (00–05, 07–12, 14) + каталог `index.html` + `SPEC.md` (требования верфи: один HTML, всё инлайн, офлайн). Коммит заявляет 14 драфт-вариаций — расхождение с числом файлов не разрулено (см. «Под вопросом»). Предложения миров: `Memory/Worlds/PROPOSALS-2026-11-08-ZCode.md`.
- **Штат v4** (`a960875`, 09.11): `Memory/Agents/estate-staff.json` (version 4, updated 2026-11-09, led_by Barrymore, режим «поводка» — запуски только кнопкой или рукой Sovereign). На службе: Бэрримор, Холмс, Risk scan; испытательный срок: Ватсон, Хантер; кандидаты: Рокфеллер, Соломон, Аналитик; уволен: Chief of Staff; приглашённые спецы: Сэнку, личный штат CLI (5 ролей). Рокфеллер — финансовый советник (паспорт `Memory/Agents/Rockefeller.md`, статус «кандидат», рантайм не собран, пилот-дайджест денег ждёт слова). Всего 16 паспортов в `Memory/Agents/`.
- **Безопасность / публикация**: pre-commit hook установлен (`d87ba7b` — hard RED для `Workspace/private/`) и расширен publish-blocklist'ом (`8162b8a`, 09.11): `Workspace/private/`, `Workspace/intel/`, `tools/intel/`, `Docs/*DARK-WATCH` — RED. `tools/intel/` и `Workspace/intel/` — внутренний контур разведки (Dark Watch), в git не попадает, содержимое не картографируется. `tools/security/`: `vuln_radar.py` (CISA KEV + EPSS + NVD), `feeds_radar.py` (5 проверенных фидов: HN Algolia, oss-security, GH Advisories, SecurityLab, Habr → секция 4 дайджеста; `38fa7f8`, 09.11), `port_audit.py` + `port_allowlist.json`, `secret_scan.py`, `nmap_probe.py`, `hooks/` (pre-commit + install.sh).
- **Облачный контур**: ВМ Яндекс.Облака «Мастерская» (E-052; systemd `barrymore-dashboard.service`, доступ только SSH-туннель, IP в репо не хранится — плейсхолдер в шаблонизированном ранбуке); лаба: DVWA/Juice Shop на loopback (E-055, урок «docker обходит ufw»), Vulhub + `up.sh` с safety-гейтом (E-056), reallab nginx+WP+Keycloak+pg+redis (E-057), кнопочная консоль rl-console 127.0.0.1:8788 — плейбуки вместо shell (E-058), постоянный туннель `tools/cloud/vm-tunnel.ps1` через планировщик (E-059). Кит полигонов: `Workspace/cloud/`. Витрина :80 на ВМ — правки параллельной сессии, не тронута.
- **Шаблонизация координат** (E-053): `templates/*.j2` — источник правды, приватные vars в `Workspace/private/vars/*.json` (вне git), рендер `tools/render_templates.py` (режим `--repo` подставляет плейсхолдеры даже при наличии vars); `Docs/TEMPLATING.md`, `Docs/generated/` gitignored, ранбук ВМ — генерируемый артефакт.
- **Дашборд v1.8.7** (строка CHANGELOG 2026-11-07): планета/меню миров на index, карта мира v2 (база `World_map_v2.png` в `Vision/First_evo_pictures/Good_references/`), fleet-панель `agents.html` + `/api/agents/live|history`, канбан с типами task/change/epic (`kanban.js?v=9`), вкладка «Экскурсия» (`excursion-data.js` + `tools/barrymore/build-excursion.py`), классические кнопки окон в модалках.
- **Peer notes «Заметка соседу»** (E-054): агенты в обычных LLM-прогонах могут оставить одну строку соседу; `Workspace/agents/peer-notes.jsonl` (вне git), `GET/POST /api/peer-notes(/read)`, счётчик непрочитанных на плашке Бэрримора, дайджест-строка в брифе.
- **Ключ шлюза восстановлен 07.11** (E-054, санкция Sovereign): `Workspace/.env` снова на месте, LLM-прогоны авторизуются; LangSmith-ключи НЕ восстановлены (не найдены на диске) — задача `rotate-langsmith-freellmapi` в лиджере. Значения ключей не картографируются.
- **Лиджер**: `Memory/Engineering/Tasks/Active/` — 27 карточек; архив `Tasks/Archive/` (`3f6b34e` — архивированы ops-commit-push, sec-secret-gate). Тесты: `tools/tests/` — 13 файлов / 105 тестов, `tools/barrymore/test_*.py` — 5 файлов / 35 тестов; последние зафиксированные зелёные сьюты — E-050 (07.11, 107+35).
- **Гоча окружения** (E-054): в Git Bash этой машины `python`/`python3` — Store-заглушка; реальный интерпретатор — `py` (3.12.10) или полный путь `python.exe` (как в `tools/ops/restart-dashboard.ps1`).

## Под вопросом

- Расхождение «14 драфт-вариаций» (коммит `58ec0d7`, CHANGELOG) против 13 html-превью в `worlds-draft/` на диске — либо один вариант без превью, либо счёт от другого множества; уточнить при выборе мира.
- Витрина :80 на ВМ «Мастерская» — деплоится параллельной сессией (E-059), в этом репо её состояние не отслеживается.
- `Workspace/cloud/probes/` untracked — состав и судьба (в git или приватная зона) не определены.
- Непрочитанный остаток аудита E-001 (FINDINGS §11.3) — `Vision/Stories`, eVo-2.0-концепты — актуальность не перепроверялась.

## Открытые вопросы

1. Пилот Рокфеллера (дайджест денег: касса + радар + топливо) ждёт слова Sovereign; рантайма нет.
2. Выбор четвёртого мира из `worlds-draft/` — решение Sovereign.
3. Ротация ключей LangSmith — только пользователь (задача `rotate-langsmith-freellmapi` в Active).
4. Higgsfield-пилот — карточка в «Проверке», ждёт ключ в `Workspace/.env` и санкцию платежа (карточка `higgsfield-pilot-test`).
5. `Memory/Context/CURRENT.md` отстаёт от реальности (дата внутри — 2026-08-05; задача `update-current-context` в лиджере).
6. Запись E-060 в LOG за сессию 08–09.11 (штаб, релиз 1.8.8, blocklist, Рокфеллер) — не написана.

## Следующий шаг

По санкциям Sovereign: пилот Рокфеллера и/или выбор мира из drafts; при следующей смене — зафиксировать сессию 08–09.11 записью в `LOG.md`. Текущий пул работ — task-лиджер `Memory/Engineering/Tasks/Active/` (27 карточек).

## Как возобновить работу

1. `Docs/Map.md` → этот файл → `PLAN.md` → хвост `LOG.md` (E-NNN; помнить, что журнал отстаёт от HEAD).
2. Проверить: если STATE старше последних коммитов или в дереве есть неизвестные изменения — начать с ревалидации по файлам и Git (`git log --oneline -15`, `git status`), зафиксировать расхождения в LOG.
3. Не смешивать правки параллельных сессий: сейчас в дереве изменены автогенерируемые `brief.js`, `hunter-report.js`, `orders-triage.js`.
