# Быстрый вход в Platform / eVo

Карта для ИИ-ассистента, которому нужно продолжить работу без повторного
полного аудита. Снимок структуры: 2026-11-06. Это указатель на источники,
а не замена им: перед изменениями сверяйся с текущими файлами и Git.

## Первые минуты

1. Прочитай `README.md`, затем `Docs/Map.md` (актуализирован 06.11) и `VERSION`
   — учти, что `VERSION` (1.8.4) может отставать от ветки: активна
   `release/1.8.6`, HEAD — `a3ca29e develop/v1.8.6`.
2. Проверь `git status --short`, ветку и последние коммиты. В рабочем дереве
   могут одновременно находиться изменения нескольких параллельных сессий.
   Не сбрасывай, не перезаписывай и не коммитай чужое вслепую.
3. Прочитай хвост `Memory/Engineering/LOG.md` (журнал E-NNN) — там последние
   зафиксированные итоги; затем проверь `Memory/Engineering/PLAN.md` и
   task-лиджер `Memory/Engineering/Tasks/Active/`. `Memory/Context/CURRENT.md`
   и `Memory/Engineering/STATE.md` — не гарантированно живое состояние,
   сведения в них отстают от кода и Git.
4. Для навигации по связям используй `graphify query "<вопрос>"`, если
   `graphify-out/graph.json` существует. Граф — подсказка; конкретный факт
   подтверждай первичным файлом.
5. Не читай и не выводи секреты из `Workspace/.env`, локальных журналов или
   данных использования. Не открывай `Workspace/private/` — это приватная зона
   данных Sovereign (gitignored): в картах только факт её существования.
   Не запускай установщики и скрипты с побочными эффектами без необходимости.

## Что это за проект

Platform — персональная система управления контекстом и развитием, построенная
вокруг обычных файлов. eVo — её интерфейс и концептуальная модель. Основной
живой UI — статические HTML/CSS/JavaScript-страницы дашборда (три мира:
Estate, Engine Core Atoll, Maelstorm — см. `Memory/Worlds/README.md`); Barrymore
и его локальный HTTP-сервер добавляют генерацию доклада, канбан-лиджер,
ограниченные локальные API и машинный журнал событий
(`Workspace/logs/events.jsonl`, пишется `tools/lib/log_event.py`).
В репозитории также присутствует отдельный шаблон Vue/Vite в `Interface/`;
не считай его runtime основного Estate dashboard без проверки связей и задачи.

## Карта каталогов

| Путь | Назначение и точка входа |
|---|---|
| `Core/` | Принципы, глоссарий и ADR. Начни с `Core/Principles.md` и `Core/Architecture/ADR/INDEX.md`. |
| `eVo/dashboard/` | Основной UI: миры Estate (`index.html`), Engine Core (`engine-core.html`), Maelstorm (`maelstorm.html`); карта мира (`world-map.html`), канбан лиджера (`kanban.html`), кабинет Холмса (`holmes.html`), AI Sandbox с вкладкой «Инструменты». Общие стили и интерактивность — `style.css`, `app.js`, `languages.js`. |
| `eVo/dashboard/brief.js` | Сгенерированный снимок `window.EVO_BRIEF`, который читает интерфейс. Генератор доклада — `tools/barrymore/morning-brief-agent.py`; не путай данные с источником/логикой генерации. |
| `tools/barrymore/` | Локальный сервер, генератор Morning Brief, AI usage, task-лиджер (`task_store.py` — переходы с подписью `by`) и обслуживание. Начни с `README.md`, затем `dashboard-server.py`, `morning-brief-agent.py`, `ai_usage.py`, `task_store.py`. |
| `tools/lib/` | Фундамент данных: конверт артефактов (`envelope.py`, `evo.*`-схемы) и машинный журнал (`log_event.py` → `Workspace/logs/events.jsonl`). |
| `tools/ops/` | Оперативные скрипты: `backup_workspace.py`, `healthcheck.py`, `token_meter.py`, реестр джобов `jobs.json` (API `/api/jobs`), метрики канбана `kanban_metrics.py`; план — в `README.md`. |
| `tools/security/` | Прототипы безопасности (`vuln_radar.py`, `port_audit.py`, `secret_scan.py`, `nmap_probe.py`); кнопки во вкладке «Инструменты» AI Sandbox, отчёты в `%LOCALAPPDATA%`, вне git. |
| `tools/agents/` | Агентный рантайм: `registry.json` (v5 — контракты и права агентов), `run_agent.py`. Паспорта — `Memory/Agents/`, миры — `Memory/Worlds/README.md`. |
| `Memory/Context/` | Текущий контекст и handoff-файлы. Сверяй даты и подтверждай утверждения в живых исходниках. |
| `Memory/Engineering/` | Инженерные состояние, план, журнал и результаты: `STATE.md`, `PLAN.md`, `LOG.md` (E-NNN), `FINDINGS.md`, `Tasks/` (лиджер канбана). |
| `Docs/` | Инструкции, архитектурные указатели, карта (`Map.md`), операции, планы смен и заметки релизов. |
| `RFC/` | Предложения и решения по изменению контура проекта. |
| `Vision/` | Концепты, истории и визуальные референсы; не считать каждую идею реализованной. |
| `Workspace/` | Материалы и проекты пользователя: аналитический контур `analytics/`, машинный журнал `logs/`, пилоты (`higgsfield-pilot/`). `Workspace/private/` — приватная зона, не открывать; `.env` может содержать секреты — не открывать и не включать в отчёты. |
| `Modules/`, `Notes/` | Предметные заметки и входящий поток вопросов/идей. |
| `Interface/` | Отдельный Vue 3 + TypeScript + Vite каркас; собственные `package.json` и команды сборки. |
| `graphify-out/`, `eVo/graphify-out/` | Сгенерированные графы/кэши для навигации, не исходники приложения. |

## Запуск и данные

- Обычный вход в Estate: `http://127.0.0.1:8765/` после установки
  автозапуска через `tools/barrymore/install-dashboard.ps1`.
- Сервер `tools/barrymore/dashboard-server.py` раздаёт `eVo/dashboard/`,
  ограничивает доступ loopback и обслуживает локальные API: задачи (включая
  канбан-переходы `POST /api/tasks/<id>/stage/<колонка>` с подписью `by`),
  агенты (`/api/holmes/*`, `/api/watson/*`, `/api/riskscan/*`), песочница
  (`/api/sandbox/*`), реестр джобов (`/api/jobs`, запуск — `POST /api/jobs/<id>/run`).
  Все POST-эндпоинты требуют заголовок `Origin: http://127.0.0.1:8765`
  (curl без него получает 403).
- Канбан-переходы выполняются только через `task_store` / API — не правь
  `stage` в JSON-карточках руками: каждая запись history должна нести подпись
  `by`, переход дублируется в машинный журнал событием `task.stage`.
- Машинный журнал `Workspace/logs/events.jsonl` — только дозапись через
  `from tools.lib.log_event import append_event; append_event(kind, source, payload)`
  внутри try/except (падение журнала не должно ломать вызывающий код).
  Пульсы агентов: `append_event("agent.pulse", source="<имя>", payload={...})`.
- `morning-brief-agent.py` собирает локальные источники и при доступности
  настроенного шлюза может запрашивать LLM; `morning-brief.ps1` — вариант
  генерации данных без LLM.
- AI-журнал хранится вне репозитория в `%LOCALAPPDATA%\Platform\AI-Usage\`.
  Неизвестные значения не равны нулю; стоимость не следует выводить из числа
  токенов (замер расхода z.ai — `tools/ops/token_meter.py` →
  `Workspace/analytics/token-spend/ledger.jsonl`).
- Перед работой с локальным сервером, установкой или задачами Barrymore
  прочитай `Docs/Barrymore.md`.

## Проверки и рабочие правила

- Два сьюта: `python -m unittest discover -s tools/tests` (48 тестов —
  аналитика, lib, jobs, kanban metrics, task by) и
  `python -m unittest discover -s tools/barrymore -p "test_*.py"` (35 тестов).
- Для `Interface/` команды определены в `Interface/package.json`; это отдельная
  сборка и не проверка статического dashboard.
- У дашборда нет общего npm build. Проверяй изменённые JS через `node --check`,
  затем проверяй соответствующие страницы/сценарии в браузере. При правке JS
  поднимай `?v=` в подключении (`app.js?v=12`, `kanban.js?v=6` и т.п.).
- Архитектурные ограничения Barrymore описаны в ADR-003 и ADR-004:
  Barrymore read-only по отношению к решениям/состоянию, действия выполняются
  через инструменты. Перед запуском файловых или системных операций изучи
  соответствующий скрипт и его эффекты.
- Правила веток и релизов: `Memory/Decisions/D-002-branch-and-release-model.md`
  (слияние в main выполнено 04.11, E-046). Текущая версия хранится в `VERSION`;
  заметки — в `Docs/Releases/` и `CHANGELOG.md`.

## Устаревшие ориентиры

`Docs/Map.md` актуализирован 2026-11-06 (фундамент данных, канбан, миры,
итоги ночной смены 05.11) — можно опираться на него, но он фиксирует состояние
на дату съёмки. Сверяйся с `README.md`, живыми файлами, хвостом
`Memory/Engineering/LOG.md` и текущим Git-состоянием; исправляй карту, если
задача включает актуализацию документации.
