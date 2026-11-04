# Миры (архипелаги) Platform — канонический реестр

> Единственное место, где описаны все архипелаги. Правило: **«Кто живёт — Memory/Agents, где живут — Memory/Worlds»**.
> Обновлять при появлении нового мира или переименовании островов. Последняя проверка: 2026-11-04.

## Три архипелага

| # | Мир | Файл | Суть |
|---|-----|------|------|
| 1 | **Estate** (World & Command Center) | `eVo/dashboard/index.html` | Центр власти: острова Trading Quarter, Harbor, Navigation Observatory (Магеллан, Хантер), Memory Library, AI Sandbox, Workshop, Study, Sinbad Market. Данные островов — ключи в `eVo/dashboard/languages.js`, логика — `app.js` |
| 2 | **Engine Core Atoll** (Engineering Archipelago) | `eVo/dashboard/engine-core.html` | Инженерный архипелаг. Список островов — `ENGINE_ISLANDS` в `engine-core.js` |
| 3 | **Maelstorm** (Research Archipelago) | `eVo/dashboard/maelstorm.html` | Исследовательский архипелаг Мэлшторма (Мэлшторм — житель 3 островов) |

Навигация между мирами — карта `eVo/dashboard/world-map.html` (+ review-версия `world-map-review.html`), кнопка «🗺» в HUD каждого мира, маршрут корабля — `ROUTE_PX` в `eVo/dashboard/harbor-ship.js`.

## Где лежат заготовки и исходники (карта источников)

- **Концепция архипелага и агентов** (21.10.2026): `Memory/New_ideas/estate_archipelago_agents.md` — Sovereign/Бэрримор/Соломон/Рокфеллер, таблица островов, внешние исполнители.
- **Паспорта жителей**: `Memory/Agents/*.md` (штат v4, коммит 833ea24, E-042).
- **Скины-темы** (заготовки июля 2026, статус: не подключены к мирам): `eVo/dashboard/projects/{marvel_v, minimalism, organica}/project.json` — палитра/шрифт/mood; активный — `eVo/dashboard/active_project.json` (marvel_v; логотип используется в HUD Estate).
- **Стори и визуальные принципы**: `Vision/Stories/The_Citadel_and_Roads.md`, `Vision/Stories/The_Kingdom_Map_Principle.md`, `Vision/Future/eVo-2.0-Visual-Direction.md`, `Vision/Estate/Decomposition/`.
- **Сводка проекта для быстрой адаптации агентов**: `SYSTEM_SUMMARY.md`.
- **Актуальный контекст**: `Memory/Context/CURRENT.md`.

## Что есть что (кратко, из концепции)

- **Sovereign** — верховный правитель (Дмитрий). Бэрримор — операционный контур, Соломон — ценность/приоритеты, Рокфеллер — капитал.
- Архипелаг = способ визуализации и управления доменными областями; остров = домен, хозяин = агент с мандатом.
