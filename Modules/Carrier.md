# Carrier — паспорт модуля (честный)

**СТАТУС: не реализован как модуль.** До 2026-10-30 файл был заглушкой в 1 байт
(аудит R7: `Memory/Archive/Reports/Report-2026-10-25-audit.md`); заполнение — задача
`clean-empty-stubs` из лиджера `Memory/Engineering/Tasks/`. Реализации в коде нет:
единственные упоминания Carrier — `Docs/Map.md` («`Modules/` — почти пусто (`Carrier.md`)»)
и метка «Carrier Module Placeholder» в `graphify-out/GRAPH_REPORT.md`.

## Задумка

`Modules/` по `Docs/Map.md` и `README.md` — «предметные домены». Carrier — предполагаемый
домен-перевозчик: **транспорт данных между агентами и дашбордом Estate** (задачи, отчёты,
снапшоты, статусы — от тех, кто работает, к тому, что показывает).

## Факт на сегодня: транспорт существует, но не как модуль

Перевозку выполняют разрозненные механизмы, нигде не описанные как единый Carrier:

- **JSON-файлы как сообщения:** задачи лиджера `Memory/Engineering/Tasks/` (active/done),
  `eVo/dashboard/active_project.json`, доска `Workspace/analytics/orders_board.json`,
  снапшоты `Workspace/analytics/<дата>/`, задачи Холмса/Хантера, отчёты Холмса.
- **Локальный HTTP API:** `tools/barrymore/dashboard-server.py` (только loopback,
  `http://127.0.0.1:8765`, старт при логоне Windows). GET: `/api/tasks`, `/api/hunter/tasks`,
  `/api/ai-usage`, `/api/security/status`, `/api/holmes/reports`; POST: `/api/tasks/{id}/done`,
  `/api/refresh-brief`, `/api/ai-usage/snapshots`, `/api/ai-usage/settings`,
  `/api/ai-usage/ask-barrymore`, `/api/security/check`, `/api/security/targets`,
  `/api/hunter/tasks`, `/api/holmes/implement`.

## Что должно появиться, чтобы Carrier стал реальным модулем

1. Реестр каналов и форматов: какой файл/API для какого сообщения, кто публикует, кто читает.
2. Контракты сообщений в духе ADR-005 «Всё есть инструмент» — каждое действие агента
   через описанный инструмент, никаких приватных каналов; аудит по реестру.
3. Границы безопасности по ADR-003/004 (агенты read-only, без прямого доступа к ОС) —
   в т.ч. решение, остаётся ли сервер loopback-only.
4. Единая точка правды вместо дублирования (сейчас часть данных живёт и в файлах, и в API).
5. Решение Sovereign: нужен ли Carrier как отдельный модуль, или честнее задокументировать
   текущие каналы в `Docs/Ops.md` и закрыть вопрос.

## Связи

- `Core/Architecture/ADR/ADR-005-Everything-Is-A-Tool.md` — принцип, по которому только и имеет смысл строить транспорт
- `Core/Architecture/ADR/ADR-003-Barrymore-Is-ReadOnly.md`, `ADR-004-Agents-Never-Access-OS.md` — ограничения
- `eVo/dashboard/` — потребитель; `tools/barrymore/dashboard-server.py` — фактический «порт»
- `Memory/Agents/` — отправители сообщений (Бэрримор, Холмс, Хантер)
