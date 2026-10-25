# Индекс архитектурных решений (ADR)

Единое место архитектурных ADR — этот каталог. Нумерация сквозная, без пересечений.
Создан при консолидации 2026-10-25 (аудит E-001, решение пользователя п.6).

| ADR | Тема | Статус | Дата |
|---|---|---|---|
| [ADR-001](ADR-001-Encoding-Policy-UTF-8.md) | Единая политика кодировки UTF-8 | Принято | 12.07.2026 |
| [ADR-002](ADR-002-Island-Architecture-Model.md) | Island Architecture Model (остров = автономная система) | Accepted | 05.08.2026 |
| [ADR-003](ADR-003-Barrymore-Is-ReadOnly.md) | Barrymore работает в режиме read-only | Accepted | 25.10.2026 (оформлен) |
| [ADR-004](ADR-004-Agents-Never-Access-OS.md) | Агенты не обращаются к ОС напрямую | Accepted | 25.10.2026 (оформлен) |
| [ADR-005](ADR-005-Everything-Is-A-Tool.md) | Всё есть инструмент | Accepted | 25.10.2026 (оформлен) |

## Смежные, но не архитектурные ADR

- **Операционные решения Barrymore**: `tools/barrymore/decisions/` (DECISION-0001…0003) — журнал исполнителя, остаётся на месте.
- **Системные решения Platform**: `Memory/Decisions/` (D-001, D-002…) — журнал решений системы.
- **История подтверждений** (DEC-001, тест evo-save): `Docs/Architecture/Decisions.md`.

## Примечание

ADR-003…005 до 25.10.2026 существовали только как heredoc-строки внутри `eVo/scripts/bootstrap.ps1`
(bootstrap не запускался, файлов не было). Ссылки на них в `Docs/Map.md` и `eVo/dashboard/app.js`
тогда указывали на несуществующие документы — исправлены 25.10.2026 на ADR-003/ADR-004.
