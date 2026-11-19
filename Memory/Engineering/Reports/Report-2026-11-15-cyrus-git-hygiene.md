# Отчёт: Git-гигиена Platform — разбор незакоммиченного хвоста

- **Кто:** Сайрус Смит, мастерская eVo Workshop (первый прогон после оживления)
- **Когда:** 15.11.2026; **ночная ревизия 15→16.11** — секция 0 ниже (актуальный план пакетов)
- **Режим:** только чтение; ничего не коммитилось, не пушилось, код не трогался
- **Команда-заказ:** руководитель проекта (после стендапа Холмса 15.11)

---

## 0. Ночь 15→16.11: пересборка пакетов (финальный план)

**Когда:** ночь 15→16.11, CEO спит. Канал «коммит» утром откроет только руководитель (первая запись журнала после молчания с 08.11 — E-060); порядок пакетов ниже согласован с этим.

### 0.1 Фактура (ветка `main`, `4395fe1` Release 1.8.9, локально)

Хвост вырос против вечернего прогона: было 15 путей в ~19:45, стало **41 путь** (17 изменённых, 24 неотслеженных файла после раскрытия директорий `Memory/Council/` и `scratch/`). После релиза 1.8.9 (74 файла) вечер добавил стендап-страницы и табель, ночь — контур **Правления** (бэкенд +321 строка, зал, диспетчер), штат v6 и чек-лист публикаций Рокфеллера. Отдельный факт: **`main` опережает `origin/main` на 8 коммитов** — Release 1.8.9 физически ещё не на origin; пуш — слово руководителя.

```
 M Memory/Agents/README.md                      M eVo/dashboard/maelstorm.html
 M Memory/Agents/estate-staff.json              M eVo/dashboard/money-map.html
 M eVo/dashboard/agents.html                    M eVo/dashboard/nav-dock.js
 M eVo/dashboard/brief.js                       M eVo/dashboard/solomon.html
 M eVo/dashboard/chronicle.html                 M eVo/dashboard/world-map.html
 M eVo/dashboard/command-center.html            M tools/barrymore/dashboard-server.py
 M eVo/dashboard/engine-core.html               (17-й: eVo/dashboard/holmes.html)
 M eVo/dashboard/index.html
 M eVo/dashboard/kanban.html                   ?? Memory/Agents/Analyst.md
 M eVo/dashboard/maelstorm-observatory.html    ?? Memory/Agents/STAFF-TABLE.md
                                               ?? Memory/Council/ (board.json, meetings/2026-11-15-1.json)
                                               ?? Memory/Engineering/Reports/Report-2026-11-15-cyrus-git-hygiene.md
                                               ?? Workspace/cloud/nginx-auth-gate.conf
                                               ?? Workspace/sales-lane/PUBLICATION-CHECKLIST.md
                                               ?? Workspace/sales-lane/ping-vitrina.log
                                               ?? Workspace/sales-lane/vitrina-build/deploy-188.tar.gz
                                               ?? eVo/dashboard/council.html, council.js, darkwatch.html,
                                                  login.html, staff-table.html, staff-table.md,
                                                  standup.html, standup-data.json
                                               ?? scratch/migrate-staff-ranks.py
                                               ?? tools/agents/council_dispatch.py
                                               ?? tools/barrymore/auth-admin.py, auth-gate.service.template,
                                                  auth_gate.py, make-demo-api.py
                                               ?? tools/job_search_results_salary.json
```

**Секреты (grep по всем дифф-кускам и новым файлам: ключи/токены/пароли/private key):** RED-находок нет. Совпадения — ложные (поля `type="password"` в login.html, PBKDF2-код, роль «secretary», условные цифры демо-стабов). `AUTH_SECRET` читается из `Workspace/.env` (gitignored); ключ шлюза :31415 в `council_dispatch.py` берётся из env через реестр. VM-IP витрины в `PUBLICATION-CHECKLIST.md` — тот же уровень, что уже в tracked `sales-lane/STATUS.md`/`channels.md`/`outreach/base` (нового раскрытия нет); личные контакты заменены плейсхолдерами `TODO_username`/`TODO@example.com`.

### 0.2 Статус P0: auth_gate.py — по-прежнему В ДЕРЕВЕ, не в git

Проверка ночью: `git ls-files --error-unmatch tools/barrymore/auth_gate.py` → pathspec not known to git (exit 1) — **никто не закоммитил, пакет 1 открыт**. Файл на диске (22,7 КБ, 534 строки, mtime 02:08 15.11); фикс на месте — строки 446–450:

```python
# гость: только плоские имена демо-API, без ../, \ и дисков
if (not rel or '..' in rel.split('/')
        or '\\' in rel or ':' in rel):
    self._json({'ok': False, 'error': 'not-in-demo'}, 404)
    return
```

Единственные живые копии P0-фикса — диск и ВМ; любой git-риск (чистка, сбой диска) его теряет. Коммитить первым.

### 0.3 Финальные пакеты — порядок коммита (утро, E-060)

**Пакет 1 (P0) — Входная дверь: auth-gate контур.** `tools/barrymore/auth_gate.py`, `auth-admin.py`, `auth-gate.service.template`, `make-demo-api.py`, `eVo/dashboard/login.html`, `Workspace/cloud/nginx-auth-gate.conf` — без изменений против вечернего плана.
> Входная дверь v1: auth-gate (роли admin/agent/member/guest, сессии, инвайты, PBKDF2/HMAC), P0-фикс traversal-гейта гостя (../ \\ : → 404, return на месте; перепроверен ночью 15→16), CLI учёток, systemd-юнит + nginx 443→8767 (деплой 14.11), гостевые демо-стабы — Dark Watch стаб не светится

**Пакет 2 (P1) — Штат v6 + табель о рангах.** `Memory/Agents/estate-staff.json` (v4→v6: поле rank CEO-0..CEO-5 вместо L0..L5, Соломон поднят на CEO-1, +10 строк смотрителей/капитанов/специалистов, стендап 15.11 в last_pocket_result), `Memory/Agents/README.md` (+секция «Команда eVo»), `Memory/Agents/STAFF-TABLE.md`, `Memory/Agents/Analyst.md` (новый паспорт, кандидат), `eVo/dashboard/staff-table.html` + `eVo/dashboard/staff-table.md`. Хвост важен: html в рантайме делает `fetch("staff-table.md")` (строка 571) — md-копия обязана уехать тем же коммитом, байт-в-байт совпадает с STAFF-TABLE.md.
> Штат v6: табель о рангах CEO-0..CEO-5 (переезд с L0..L5 по слову Дмитрия, Соломон — CEO-1) + 10 строк смотрителей и Сайруса Смита; паспорт Аналитика (кандидат); живая оргсхема staff-table.html + md-копия для её рантайма; стендап 15.11 в last_pocket_result

**Пакет 3 (P1) — Правление Estate (новый контур ночи).** `tools/barrymore/dashboard-server.py` (+321: GET /api/council, /api/council/<id>, POST convene/report/summary/edit/verdict/status/run, диспетчер в фоне), `tools/agents/council_dispatch.py` (диспут через шлюз :31415, план-токены CEO не тратит; секретов нет — ключ из env), `eVo/dashboard/council.html` + `council.js`, `Memory/Council/board.json` + `meetings/2026-11-15-1.json`, `eVo/dashboard/nav-dock.js` (+дверь «🏛 Правление»), бамп `nav-dock.js?v=7` в 10 страницах (agents, chronicle, engine-core, holmes, kanban, maelstorm-observatory, maelstorm, money-map, solomon, world-map).
> Правление Estate: зал совета управляющих (council.html/js, /api/council*, диспетчер диспута через шлюз :31415 — «рука Бэрримова»), протоколы в Memory/Council/, дверь в nav-dock v7 (бамп 10 страниц); собрание 2026-11-15-1 «Деньги к дедлайну 04.12» — снапшот фазы «созвано»

**Пакет 4 (P2) — Стендап + двери.** `eVo/dashboard/standup.html`, `standup-data.json` (стендап 15.11, 7 докладов, закрыт 19:25), `index.html` (двери 🎩/👥), `command-center.html` (меню: Зал заседаний, Команда eVo, Правление), `eVo/dashboard/brief.js` (автоген, регенерирован 20:35 — руками не правится, едет как снапшот). **Строго после пакетов 2–3:** эти модифицированные страницы ссылаются на новые untracked — при обратном порядке ссылки уходят в 404.
> Дашборд: зал заседаний (стендап 15.11, семь докладов, резолюция), двери Зала и Команды в Estate и меню штаба, регенерация Morning Brief

**Пакет 5 (P2, только после явного слова Дмитрия) — Тёмный радар.** `eVo/dashboard/darkwatch.html` — как вечером: вне блоклиста формально, но по ассоциации с Dark Watch и после утечки-rewrite 09.11 — отдельно и после санкции (в релизе 1.8.9 помечен «(visibility rule)»).

**Пакет 6 (P3, решение руководителя) — Чек-лист часа публикаций.** `Workspace/sales-lane/PUBLICATION-CHECKLIST.md` (48 КБ, Рокфеллер, ночь 15→16.11, по санкции ночного цикла: «Ничего не публиковалось, не отправлялось, не коммитилось»). Коммитить МОЖНО (контакты — уровень уже-tracked outreach/base; плейсхолдеры вместо личных данных; секретов нет), но это одноразовый операционный документ утра 16.11 — пусть руководитель решит: в git как протокол лейна или на стол без коммита.

**Пакет 7 — НЕ КОММИТИТЬ никогда + .gitignore.** Вечерний список подтверждён и расширен:
- `Workspace/sales-lane/ping-vitrina.log` — живой лог пинг-сторожки (runtime);
- `Workspace/sales-lane/vitrina-build/deploy-188.tar.gz` — deploy-тарбол (двоичный дамп);
- `tools/job_search_results_salary.json` — снапшот 08.11, регенерится `tools/job_search.py`;
- **новое:** `scratch/migrate-staff-ranks.py` — разовая миграция v5→v6; `scratch/` никогда не был в git (история пуста) — архивировать/удалять вне git, при необходимости переотдать в `tools/` отдельной задачей.
`git check-ignore` подтверждает: ping-лог и tarball сейчас НЕ покрыты .gitignore — пополнить (раздел runtime-хвостов: `Workspace/sales-lane/ping-vitrina.log`, `Workspace/sales-lane/vitrina-build/`, `tools/job_search_results_salary.json`) отдельным мелким коммитом.

### 0.4 Красные флаги на утро (для E-060)

1. **P0 всё ещё вне git** — фикс существует на диске и ВМ, один коммит от потери. Пакет 1 — первым, до любых чисток.
2. **main ahead 8 от origin** — 1.8.9 и хвост локальны; пушить только по слову руководителя, после пакетов 1–4.
3. **Порядок 2→3→4 обязателен** — модифицированные tracked-страницы (index, command-center, nav-dock) ссылаются на untracked-страницы; частичный/перепутанный порядок коммитов даёт живые 404 в дашборде.
4. **Собрание правления живое** — `meetings/2026-11-15-1.json` в фазе «созвано» (5 пунктов, 7 участников); если утром диспут запустят до коммитов, протокол уедет дальше снапшота. Протоколы append-only — коммит снапшота корректен, следующий догонит, но коммитить пакет 3 лучше до запуска диспута.
5. **Журнал молчит с 08.11 (E-059)** — E-060 станет первой записью за 8 дней; в неё — ссылки на пакеты 1–4.
6. Косметика: в estate-staff.json v6 две строки приглашённого CLI-штата остались с `rank: "L5"` (переезд на CEO-* их не задел) — не блокер.

*Ночь 15→16.11: git не тронут (0 коммитов, 0 пушей), сервер не перезапускался, код не правился; единственная запись за ночь — эта секция. Вечерний разбор (секции 1–5) сохранён ниже как снимок ~19:45.*

---

## 1. Фактура git (снимок вечера ~19:45, ветка `main`)

**Сверка с ревизором.** Холмс на стендапе назвал 34 файла (+791/−1351). Расхождение объяснимо и не подозрительно: в 19:26 ушёл коммит `4395fe1` «Release 1.8.9» — 74 файла (+9762/−1352), в него попали и «важное» из жалобы (в т.ч. `eVo/dashboard/assets/logo-core.png`). В сообщении релиза прямо перечислен остаток: *«Вне релиза оставлены: auth-gate контур (auth_gate.py, login.html, nginx conf), standup, darkwatch.html (visibility rule), job_search_results_salary.json, лог+tar.gz — разобрать на „полочках“ перед 1.9.0»*. Текущий хвост — **15 путей**: 2 изменённых, 13 неотслеженных.

```
 M Memory/Agents/README.md
 M Memory/Agents/estate-staff.json
?? Memory/Agents/STAFF-TABLE.md
?? Workspace/cloud/nginx-auth-gate.conf
?? Workspace/sales-lane/ping-vitrina.log
?? Workspace/sales-lane/vitrina-build/deploy-188.tar.gz
?? eVo/dashboard/darkwatch.html
?? eVo/dashboard/login.html
?? eVo/dashboard/standup-data.json
?? eVo/dashboard/standup.html
?? tools/barrymore/auth-admin.py
?? tools/barrymore/auth-gate.service.template
?? tools/barrymore/auth_gate.py
?? tools/barrymore/make-demo-api.py
?? tools/job_search_results_salary.json
```

`git diff --stat` (только отслеживаемое): `Memory/Agents/README.md +6`, `Memory/Agents/estate-staff.json +143/−14` (итого +157/−14).

---

## 2. Разбор каждого файла

| # | Файл | Что это | Почему в изменённых |
|---|------|---------|---------------------|
| 1 | `tools/barrymore/auth_gate.py` | Входная дверь eVo (22,7 КБ, фаза 1): роли admin/agent/member/guest, сессии, инвайты, PBKDF2, HMAC-инвайт-токены. **Содержит P0-фикс**: traversal-гейт гостевого профиля (строки 446–450: `..`, `\`, `:` → 404 + return на месте) | Новый файл контура auth-gate; деплой на ВМ 14.11, код дожил до коммита только сейчас |
| 2 | `tools/barrymore/auth-admin.py` | CLI управления учётками/заявками/инвайтами auth-gate | Комплект к auth_gate.py |
| 3 | `tools/barrymore/auth-gate.service.template` | systemd-юнит входной двери (User=daimak, порт 8767, пути ВМ) | Комплект |
| 4 | `tools/barrymore/make-demo-api.py` | Генератор санитизированных демо-стабов /api/* для гостя; Dark Watch стаб не получает никогда (RED) | Комплект |
| 5 | `eVo/dashboard/login.html` | Страница входа/регистрации auth-gate (AUTH_LOGIN_HTML юнита) | Комплект |
| 6 | `Workspace/cloud/nginx-auth-gate.conf` | nginx 443 → gate 127.0.0.1:8767; само-подписанный серт; деплой 14.11 по санкции Дмитрия | Конфиг деплоя |
| 7 | `Memory/Agents/estate-staff.json` | Штат v4→v5: поле `rank` L0..L5, +9 строк смотрителей (Бендер, Гефест, Немо, Магеллан, Синдбад, Паганель, Леонардо, Maelstorm, Сайрус Смит), стендап 15.11 в last_pocket_result | Стендап 15.11 обновил кадры |
| 8 | `Memory/Agents/STAFF-TABLE.md` | Новый: ASCII-оргсхема штата (табель о рангах), утренний брифинг Бэрримора | Создан 15.11, 19:38 |
| 9 | `Memory/Agents/README.md` | +6 строк: ссылка на STAFF-TABLE.md в шапке | Комплект к табелю |
| 10 | `eVo/dashboard/standup.html` | Дашборд-страница стендапа штата 15.11 | Протокол стендапа в UI |
| 11 | `eVo/dashboard/standup-data.json` | Данные стендапа 15.11 (7 докладов, резолюция, закрыт в 19:25) | Комплект |
| 12 | `eVo/dashboard/darkwatch.html` | «Тёмный радар»: подробности darkwatch — публичные каналы, безличная агрегация, noindex. **Уже отсылается из закоммиченного command-center.html:193** (ссылка сейчас висит в 404) | Страница не попала в 1.8.9 — в сообщении релиза помечена «(visibility rule)» |
| 13 | `Workspace/sales-lane/ping-vitrina.log` | Живой лог пинг-сторожки витрины: 109 строк, 30 сбоев code=000 | Runtime-лог, должен жить вне git |
| 14 | `Workspace/sales-lane/vitrina-build/deploy-188.tar.gz` | Артефакт сборки витрины, 285 КБ (дамп дашборда) | Сборочный хвост |
| 15 | `tools/job_search_results_salary.json` | Снапшот job-search от 08.11: 51 вакансия (hh.uz, hh.ru, FL.ru, OLX, RemoteOK, Remotive) | Фактура Хантера «волна 1»; регенерится `tools/job_search.py` |

**Проверка на секреты** (grep по ключам/токенам/приватным ключам по всем 13 новым файлам): RED-находок нет. `auth_gate.py` секрет из env не хранит (`AUTH_SECRET` читается из `Workspace/.env`, который в `.gitignore`); в `standup-data.json` и STAFF-TABLE токен FINANCE_TOKEN упомянут только словами; `make-demo-api.py` — условные цифры. Уровень ORANGE: `auth-gate.service.template` и nginx-конфиг раскрывают имя VM-юзера `daimak` и внутренние пути — не секрет, но внутренний контур (репо уже пушится на `origin https://github.com/daimak/Platform.git`).

---

## 3. Пакеты коммитов (5 штук)

### Пакет 1 (P0) — Входная дверь: auth-gate контур
- **Файлы:** `tools/barrymore/auth_gate.py`, `tools/barrymore/auth-admin.py`, `tools/barrymore/auth-gate.service.template`, `tools/barrymore/make-demo-api.py`, `eVo/dashboard/login.html`, `Workspace/cloud/nginx-auth-gate.conf`
- **Черновик сообщения:**
  > Входная дверь v1: auth-gate (роли admin/agent/member/guest, сессии, инвайты, PBKDF2/HMAC), P0-фикс traversal-гейта гостя (../ \\ : → 404, return на месте), CLI учёток, systemd-юнит + nginx 443→8767 (деплой 14.11, «го деплой»), гостевые демо-стабы — Dark Watch стаб не светится
- **Приоритет:** P0 (жалоба Холмса; код реально работает в проде на ВМ, а в git его нет — коммит может потерять P0-фикс при любой чистке)
- **Риски:** секретов нет (проверено); ORANGE — юнит/конфиг раскрывают VM-пути и юзера. `Workspace/.env` с AUTH_SECRET в git не входит и не должен.

### Пакет 2 (P1) — Штат v5: табель о рангах
- **Файлы:** `Memory/Agents/estate-staff.json`, `Memory/Agents/STAFF-TABLE.md`, `Memory/Agents/README.md`
- **Черновик сообщения:**
  > Штат v5: табель о рангах (L0..L5) + 9 строк смотрителей островов и Сайруса Смита («кандидат», без рантайма); стендап 15.11 в last_pocket_result; Рокфеллер сдал пилот-дайджест казны, Соломон — вердикт «фокус-копьё»; брифинг Бэрримора
- **Приоритет:** P1 (протокол; ссылки estate-staff.json на паспорта все валидны — Bender.md, CyrusSmith.md, Solomon.md отслежены)
- **Риски:** секретов нет; финансовые цифры (топливо 372,7/500 млн) — того же уровня, что уже в git (money-map, штат v4).

### Пакет 3 (P2) — Дашборд: стендап 15.11
- **Файлы:** `eVo/dashboard/standup.html`, `eVo/dashboard/standup-data.json`
- **Черновик сообщения:**
  > Дашборд: стенд-страница штата 15.11 (семь докладов, резолюция, карточки агентов) — протокол живёт в UI, рядом с хроникой
- **Приоритет:** P2
- **Риски:** секретов нет (токены упомянуты словами, значений нет); внутренняя финансовая кухня — тот же уровень открытости, что уже в git.

### Пакет 4 (P2, осторожно) — Тёмный радар: darkwatch.html
- **Файлы:** `eVo/dashboard/darkwatch.html`
- **Черновик сообщения:**
  > Дашборд: Тёмный радар — подробности darkwatch (лента вымогателей, реестр групп-ботов; публичные каналы, безличная агрегация, noindex); закрывает ссылку command-center
- **Приоритет:** P2, **но только после явного слова Дмитрия**
- **Риски:** НЕ покрыт pre-commit блоклистом (тот ловит только `Workspace/private/`, `Workspace/intel/`, `tools/intel/`, `Docs/.*DARK-WATCH`). Слово Дмитрия 09.11 касалось «план, intel-картотека, darkwatch-инструменты» — страница формально не в запретной зоне, но по ассоциации с Dark Watch (и с учётом утечки-rewrite 09.11) — коммитить отдельно от прочего и после санкции. В сообщении Release 1.8.9 она помечена «(visibility rule)».

### Пакет 5 — НЕ КОММИТИТЬ: runtime-хвосты витрины и снапшоты
- **Файлы:** `Workspace/sales-lane/ping-vitrina.log` (живой лог, 30 сбоев), `Workspace/sales-lane/vitrina-build/deploy-188.tar.gz` (сборочный артефакт), `tools/job_search_results_salary.json` (снапшот 08.11, регенерится `tools/job_search.py`)
- **Действие:** в git не брать; пополнить `.gitignore` (раздел «Runtime logs and data snapshots»): `*.log` для sales-lane или точечные пути, `Workspace/sales-lane/vitrina-build/`, `tools/job_search_results_salary.json`. Если Хантеру нужна фактура «волны 1» — переотдать в `Workspace/analytics/` по прецеденту 2026-10-29, отдельным коммитом и явно.
- **Риски:** секретов нет, но это мусор в истории: логи растут, tar.gz — двоичный дамп.

---

## 4. P0-фикс auth_gate.py — куда входит

**Пакет 1 «Входная дверь»**, первым файлом. Суть фикса (факт из кода, строки 446–450): гостевой профиль на /api/* отсекает `..`, `\`, `:` — выдаёт 404, и после 404 стоит потерянный ранее `return`. Вместе с ним в пакет идут admin-CLI, systemd-юнит, nginx-конфиг, login.html и генератор демо-стабов. Внимание на открытые P1 (не в этом файле, не в этом пакете): (1) POST за дверью мёртв — gate вырезает Origin, канбан-приёмка ловит 403; варианты фикса ждут решения; (2) гостю светит настоящий brief.js. Оба — из доклада Холмса на стендапе 15.11.

---

## 5. Рекомендованный порядок

1. **Пакет 1 (P0)** — коммитить первым, немедленно: единственное место, где физически живёт P0-фикс.
2. **Пакет 2 (Штат v5)** — протокол за 15.11, пока стендап не разошёлся с git-фактами.
3. **Пакет 3 (Стендап-страница)** — комплект к протоколу.
4. **Пакет 4 (darkwatch.html)** — после явного «да» Дмитрия (visibility rule), отдельно от прочих дашборд-страниц.
5. **Пакет 5** — не коммитить; `.gitignore`-пополнение отдельным мелким коммитом.

После пакетов 1–3 хвост закрывается, журнал Engineering получает E-060 (первый прогон Сайруса Смита — этот отчёт), и путь к 1.9.0 чист.

---

*Сайрус Смит, мастерская eVo Workshop. Проверено рифлением собственных рук: git не тронут, отчёт — единственная новая запись.*
