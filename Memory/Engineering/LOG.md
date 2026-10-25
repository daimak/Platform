# Engineering LOG

Append-only журнал фактически выполненных действий. Правила — `README.md`.
Прошлые записи не исправляются и не удаляются; ошибка закрывается корректирующей
записью со ссылкой на ошибочную.

---

## E-000 | 2026-10-25 14:38 | Согласование и создание протокола журналирования

### Ранее выполненное исследование (до создания протокола, 2026-10-25, та же сессия)

Время начала не фиксировалось — протокола ещё не было. Все действия — чтение,
состояние репозитория не менялось.

- Цель: проверить существующие механизмы журнала/планирования/решений/передачи контекста, чтобы не дублировать их.
- Действия:
  - `ls -la` корня `C:\Work\Platform` (состав первого уровня).
  - Прочитаны полностью: `Docs/Map.md`; `Core/Architecture.md`; `Memory/Context/README.md`; `Memory/Context/CURRENT.md`; `Memory/Sessions/README.md`; `Memory/Sessions/2026-08-05-Relocation-and-Treasury.md`; `Memory/Decisions/README.md`; `Memory/Decisions/D-001.md`; `Memory/Context/Handoffs/HANDOFF-2026-07-08-eVo.md`; `Memory/Timeline.md` (1 строка, содержимое не зафиксировано); `Memory/Commit-map.md`; `Memory/Capture.md`; `Memory/Snapshots/README.md`; `Docs/Ops.md`; `Docs/Architecture/README.md`; `Docs/Architecture/Decisions.md`; `Docs/Architecture/Structure.md`; `CHANGELOG.md`; `SYSTEM_SUMMARY.md`; `Memory/Archive/Reports/Report-2026-10-23-Platform-eVo.md`; `tools/barrymore/README.md`; `tools/barrymore/TASK-PROTOCOL.md`; `tools/barrymore/decisions/DECISION-0001.md`; `tools/barrymore/initiatives/INITIATIVE-0001-live-state-view.md`.
  - `find` по `Docs/`, `Memory/`, `tools/` (список путей); затем по `Notes/`, `Workspace/`; `ls` корня | grep rfc — пусто.
- Результаты: инвентаризация механизмов и пробелов → `FINDINGS.md §1-§3`; выводы приняты пользователем → `FINDINGS.md §2.5`.
- Неудачи и ограничения: содержимое `Notes/*`, `Workspace/*`, `Interface/`, `eVo/`, `Core/` кроме Architecture.md не читалось (только имена); `Memory/Timeline.md` — прочтение вернуло предупреждение о длине, содержимое не зафиксировано; номера строк для непрочитанных файлов не приводятся.
- Git на момент исследования (снимок старта сессии): ветка `release/v1.8.1`, HEAD `1164ed7`, untracked `.graphifyignore`.

### Выполнено сейчас (создание протокола)

- Получены контрольные значения (read-only): `date` → 2026-10-25 14:38:46 +0500; `git branch --show-current` → `release/v1.8.1`; `git log -1` → `1164ed7 add Summary 24.10.2026`; `git status --porcelain` → только `?? .graphifyignore`.
- Проверено отсутствие `Memory/Engineering/` (`test -e`) — не существовал.
- Созданы файлы: `README.md`, `STATE.md`, `LOG.md` (эта запись), `FINDINGS.md`, `PLAN.md`. Коммитов и push не выполнялось; `tools/barrymore/execute.ps1` и иные механизмы сохранения не запускались.
- Ограничения: ничего вне `Memory/Engineering/` не создано и не изменено; `.graphifyignore` и `eVo/graphify-out/` не тронуты (проверка ниже в отчёте о выполнении).
- Открытые вопросы: S-1 (связь с CURRENT.md), S-2 (обновление Map/CHANGELOG) — см. `PLAN.md`.
- Next: ожидание указания пользователя по E-001 или иное распоряжение.
- Git после действий: см. контрольный блок `STATE.md` на момент следующего обновления; сразу после создания файлов — `git status --porcelain` показал `?? .graphifyignore` и `?? Memory/Engineering/` (зафиксировано в отчёте о выполнении, отправленном пользователю 2026-10-25).

---

## E-000-CORR | 2026-10-25 15:08 | Корректирующая запись к E-000

Ссылка: E-000 (2026-10-25 14:38). Текст E-000 не изменялся и не удалялся (append-only).

- Причина: контрольная проверка по указанию пользователя (после обрыва сети во время доставки первоначального отчёта о создании протокола) выявила расхождения записей E-000 / FINDINGS / STATE с фактическим содержимым файлов.
- Расхождение 1 — перекрёстная атрибуция документов. При чтении 2026-10-25 (до создания протокола) содержимое двух файлов зафиксировано перепутанным: «единая сводка» (граф eVo, срез 2026-10-20) ошибочно приписана `SYSTEM_SUMMARY.md`, «Интегрированный отчет» (дата фиксации 2026-10-24) — `Memory/Archive/Reports/Report-2026-10-23-Platform-eVo.md`. Фактически (проверено двумя независимыми способами: `git show HEAD:<path>` и чтение с диска): `SYSTEM_SUMMARY.md:1,3` — «# Проект Platform (eVo): Интегрированный отчет», «**Дата фиксации**: 2026-10-24»; `Report-2026-10-23-Platform-eVo.md:1,3` — «# Platform / eVo — единая сводка», «**Срез:** 20 октября 2026 года». Репозиторий при этом не менялся: `git diff HEAD --stat` пуст, HEAD `1164ed7`, mtime файлов — 23–24.10.2026. Ошибка была в записях журнала, а не в файлах. Примечание: несоответствие имён и содержимого этих двух файлов существует в самом репозитории с коммита `1164ed7` (внесено до текущей работы); сами файлы не исправлялись, не переименовывались и не перемещались.
- Расхождение 2 — неточные номера строк в FINDINGS: формат changelog фактически `CHANGELOG.md:6` (было указано `:5`); раздел RFC фактически `Docs/Architecture/Structure.md:125-141` (было `126-140`).
- Расхождение 3 — фраза E-000 «…в отчёте о выполнении, отправленном пользователю 2026-10-25» преждевременна: первоначальный отчёт НЕ был доставлен пользователю из-за сетевой ошибки; фактически результаты доведены до пользователя позднее, вместе с результатами контрольной проверки.
- Выполнено по разрешению пользователя 2026-10-25: правки `FINDINGS.md` (§1, §2.1, §2.2, §2.4, §3 — атрибуция двух документов и номера строк, каждая с пометкой «Корректировка»), `STATE.md` (контрольный блок, «Статус аудита», «Под вопросом», открытый вопрос №3 о несоответствии имён/содержимого). Другие файлы не изменялись; коммитов и push нет; скрипты не запускались.
- Git (проверено `git status --porcelain` 2026-10-25 15:08, после правок FINDINGS/STATE и до добавления этой записи): ветка `release/v1.8.1`, HEAD `1164ed7`, вывод — `?? .graphifyignore`, `?? Memory/Engineering/`; изменённых tracked-файлов нет.
- Next: ожидание указаний пользователя (в т.ч. решение по аномалии несоответствия имён/содержимого двух файлов, по S-1/S-2 и по запуску E-001).

---

## E-001 | 2026-10-25 15:51 | Полный архитектурный аудит (read-only)

### Исследование (выполнено до записи, 2026-10-25, та же сессия)

Время начала не фиксировалось. Все действия — чтение и read-only диагностика; состояние репозитория не менялось; скрипты проекта и UI не запускались.

- Цель (по указанию пользователя): точки входа и запускаемое; классификация реализовано/частично/заглушки/документы; дублирование и конкурирующие механизмы; связи слоёв; Barrymore реальный vs описанный; противоречия и риски; доказательная база для целевой архитектуры.
- Действия:
  - Структурная съёмка: `find` по всему репозиторию (два первых прогона дали ~490 КБ вывода из-за `Interface/node_modules` и графики — переизданы с фильтрами; сырые выводы сохранены системой во временные логи сессии, в репозиторий не писались).
  - Прочитано ~75 файлов: Core (Principles, Glossary, Identity, Dashboard, ADR-002), Docs/Architecture/Principles, корневые мета-файлы (.gitignore, .gitattributes, .claudeignore, .graphifyignore, skills-lock.json, .vscode/tasks.json, .github/copilot-instructions.md), README.md, eVo/README.md, весь eVo/dashboard (index.html, app.js, workspace.html, history.md, active_project.json, projects/*.json, head languages.js), Interface (package.json, App.vue, main.ts, index.html, README), скрипты (bootstrap.ps1, evo-check.ps1, evo-save.ps1 + diff с .backup, barrymore/execute.ps1), tools/barrymore (tasks 0001–0003, decisions 0001–0003, initiatives 0001), Workspace (CURRENT.md, main.py, EPIC-001, .env — только имена ключей через od/grep), Memory (Solomon, Barrymore/README, Migration, Memos ×3, eVo-SNAPSHOT, CURRENT_11_07_2026, SESSION-2026-07-01, SNAPSHOT-2026-07-24, learning-protocol, gemini-лог, head Genesis/New_ideas/learning-plan/Report-2026-10-20), Notes (Inbox, Questions, evo-test-run), Vision/Local_AI_Agent_Experiment, claude-chief-of-staff/README, .agents/skills/chief-of-staff/SKILL.md.
  - Дубликаты: `diff`/`cmp` по 7 парам (dashboard/Backup ×7 файлов, Handoffs ×2, Archive CURRENT ×2, evo-save ×2, .env ×2).
  - Git (read-only): `log -15`, `ls-files` (206 tracked), `remote -v`, `branch -a`, `git grep 'lsv2_pt'` по HEAD и origin-ссылкам.
- Результаты: → FINDINGS §5–§11. Ключевые: секреты в `Workspace/main.py:16,27` (коммит `1164ed7`, НЕ запушен — проверено git grep по origin); ADR-нумерация в трёх пространствах, ссылки на несуществующие ADR; четыре несогласованные версии системы; два CURRENT; dashboard без связи с Memory; от Barrymore исполняется только execute.ps1.
- Неудачи/ограничения: непрочитанный остаток — FINDINGS §11.3 (Vision/Stories, eVo-2.0-концепты, CLAUDE.md и yaml chief-of-staff, GRAPH_REPORT.md, style.css, хвосты крупных файлов); значения .env сознательно не читались; выводы о поведении — из чтения кода, не из запуска.
- Результаты представлены пользователю в ответе той же сессии; разрешение на запись получено («Разрешаю»).

### Выполнено сейчас (фиксация результатов)

- FINDINGS.md: добавлены §5–§11, указатель актуализации в §4.
- PLAN.md: E-001 → Done; E-002…E-006 → Done (в составе E-001); добавлены S-3 (безопасность) и S-4 (решения пользователя из E-001).
- STATE.md: контроль (15:29), статус аудита (не завершён: E-007/E-008 и решения пользователя ожидаются), подтверждённое, под вопросом, открытые вопросы, следующий шаг.
- Другие файлы не изменялись; коммитов и push нет; скрипты не запускались; `Workspace/main.py` и `.env` не тронуты.
- Git (проверено `git status --porcelain` 2026-10-25 15:51, после правок FINDINGS/PLAN/STATE и до добавления этой записи): `?? .graphifyignore`, `?? Memory/Engineering/`; изменённых tracked-файлов нет.
- Next: решения пользователя — приоритетно безопасность (S-3), затем E-007/E-008.

---

## S-3 | 2026-10-25 16:39 | Устранение секретов из кода и коммита (по разрешению пользователя «лучшие практики»)

- Цель: убрать ключи из `Workspace/main.py` и из локального коммита до первого push. Окно подтверждено: `git branch -r --contains HEAD` пуст (15:59 и 16:38–16:39).
- Действия:
  - `Workspace/.env` (untracked, не в Git): дополнен — `LANGSMITH_API_KEY`, `LANGSMITH_GATEWAY_API_KEY`, `FREE_LLM_API_KEY`, `FREE_LLM_BASE_URL` + несекретные настройки LangSmith; в комментариях — где ротировать.
  - `Workspace/.env.example` (новый, в Git): шаблон с плейсхолдерами и инструкцией.
  - `.gitignore`: `!.env.example` (правило `.env.*` иначе исключало шаблон) и `__pycache__/`.
  - `Workspace/main.py`: секреты заменены на `os.environ.get`; `load_dotenv` с явным путём к `Workspace/.env`; убраны дублирующиеся импорты. Синтаксис проверен `python -m py_compile` (SYNTAX_OK); запуск скрипта не выполнялся.
  - Git: `git add Workspace/main.py Workspace/.env.example .gitignore` → `git commit --amend --no-edit` (дважды: из-за прерывания первой попытки сетью и добавления `__pycache__/`). HEAD: `1164ed7` → `67a84ff` → `709b2c5`. Коммит не запушен; реальных ключей в HEAD нет (`git grep 'lsv2_pt_a\|freellmapi-1' HEAD` — пусто; совпадения только с плейсхолдерами `.env.example`).
  - Удалён артефакт диагностики `Workspace/__pycache__/` (создан `py_compile`).
- Ограничения и остаток за пользователем: ротация ключей LangSmith (smith.langchain.com → Settings → API Keys) и FreeLLMAPI — внешние аккаунты, модели недоступны; старый коммит `1164ed7` остаётся только в локальном reflog (не запушен; параноидальная очистка — `git reflog expire` + `gc` — опциональна); `Workspace/.env.backup` (untracked, копия старого ключа) рекомендована к удалению, не тронута.
- Уведомление пользователя: таблица «ключ / где / зачем / как пользоваться» передана в отчёте (запрос пользователя: всегда извещать о ключах).

---

## E-007 + E-008 | 2026-10-25 16:39 | Синтез, разбор claude-chief-of-staff, итоговый отчёт

- E-007 (синтез): карта компонентов и противоречий сформирована на базе FINDINGS §1–§11; включена в итоговый отчёт.
- Разбор claude-chief-of-staff: прочитаны `claude-chief-of-staff/README.md`, `CLAUDE.md`, `goals.yaml`, `commands/gm.md`; зафиксировано: gitlink mode 160000 без `.gitmodules` (при клоне не скачивается), `CLAUDE.md`/`goals.yaml` — незаполненные шаблоны. Выводы и рекомендация — в отчёте пользователя.
- E-008 (итоговый отчёт с рекомендациями R1–R12 и фазами): передан пользователю в чате 2026-10-25. Постоянная фиксация отчёта — S-5 (предложено `Memory/Archive/Reports/`), запись вне `Memory/Engineering/` — только по разрешению.
- Git: те же контрольные значения, что в S-3 (HEAD `709b2c5`, не запушен).
- Next: решения пользователя (ротация, .env.backup, S-4/S-5), затем — проектирование целевой архитектуры по рекомендациям отчёта.

---

## E-009 | 2026-10-25 18:31 | Реструктуризация контура (пункты 1–9 пользователя)

- Цель: исполнить решения пользователя по итогам аудита: пункты 1–6 приняты как предложено; 7 — переделан в модель веток (develop / feature_X.Y.Z / release_X.Y.Z); 8 — создать RFC-процесс; 9 — зафиксировать отчёт. Указание: сначала запушить текущую ветку, изменения делать в новой локальной ветке.
- Действия:
  - Git: проверка секретов в HEAD (чисто) → `git push origin release/v1.8.1` (`50f80d3..709b2c5`) → создана `feature_1.8.2`.
  - **Коммит `fbffd54`** (пункты 1–5): `claude-chief-of-staff/` → `C:/Work/reference/` (gitlink удалён; mv упёрся в Permission denied → cp+rm); `Backup/` (~30 МБ PNG) → `C:/Work/Platform-archive/`; удалены `eVo/dashboard/Backup/` (побайтовый дубль), `Interface/` (Vue-шаблон), `tools/evo-save.ps1.backup`, `Workspace/.env.backup`, один из идентичных Handoffs (оставлен `-eVo`), один из идентичных Archive CURRENT (оставлен `-before-refactor`: выбор по SNAPSHOT-2026-07-24 — следующим этапом был refactor); `Workspace/CURRENT.md` → `notes-memory-design.md`; `eVo/graphify-out/` исключён из индекса + правило в `.gitignore`.
  - **Коммит `032eb57`** (пункт 6): `Core/Architecture/ADR/`: ADR-001 (UTF-8, перенесён из `Docs/Architecture/Decisions.md` без изменения текста), ADR-003/004/005 (оформлены из heredoc bootstrap.ps1 с пометкой происхождения), `INDEX.md` (единая нумерация + смежные журналы); `Docs/Architecture/Decisions.md` → указатель + история DEC-001; ссылки исправлены: Map.md (ADR-0001/0002 → ADR-003/004), `app.js:227` (ADR-0001 → ADR-003); bootstrap.ps1 больше не создаёт `docs\adr` и ADR-файлы.
  - **Коммит `cdbbebc`** (пункты 7–9): `Memory/Decisions/D-002-branch-and-release-model.md` (модель пользователя; заменяет D-001; противоречие с DECISION-0002 зафиксировано); `RFC/README.md` + Drafts/Accepted/Rejected/Backlog + `RFC/Drafts/RFC-001-platform-contour.md` (Accepted, решения 1–6); отчёт `Memory/Archive/Reports/Report-2026-10-25-audit.md` (E-008: находки, R1–R12 со статусами, фазы); CHANGELOG +5 строк; Map.md обновлён (дата, строки таблицы Interface/Backup/RFC/+Engineering, секция Vue удалена, «Как запускать», bootstrap, graphify); README (убран Interface, добавлен Memory/Engineering).
  - Инженерный журнал: эта запись + STATE + PLAN (коммит 4).
- Неудачи и особенности сессии: 4 обрыва системы; каждый раз фактическое состояние проверялось перед продолжением (стейт-трекер + ls/grep/git status); `git add` на игнорируемый graphify-out дал ошибку pathspec/ignore — учтено (удаления уже были в индексе); CRLF-предупреждения Git (политика `.gitattributes` eol=lf) на правленых файлах.
- Ограничения: ротация ключей — за пользователем; `feature_1.8.2` не запушена (пуш требовался только для release/v1.8.1); старые ветки не тронуты; пустые заглушки (locales, Carrier.md, Timeline.md) и mojibake-файлы — вне этого блока (R7/R12).
- Git (после COMMIT3, до коммита журнала): ветка `feature_1.8.2`, HEAD `cdbbebc`; untracked — `.graphifyignore`, `Memory/Engineering/`.
- Next: по D-002 — слияние `feature_1.8.2` → `develop` → `release_1.8.2` (после указания); продуктовые шаги R3/R4.
