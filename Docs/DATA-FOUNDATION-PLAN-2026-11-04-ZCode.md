# ТЗ: Фундамент данных Platform Evo

Создано: 2026-11-04 ZCode · Задача: канбан `data-foundation` (Memory/Engineering/Tasks/Active/)
Статус: ждёт перевода в `in-progress` Sovereign → после этого берётся суб-агентом.

## Зачем это

Проект умеет делать всё больше (снапшоты, Хантер, Холмс, security, token-meter, канбан), но не умеет складывать сделанное в один ящик: у каждого модуля свой формат отчёта, свои пути, свои кнопки. Каждый новый житель платформы будет изобретать это заново. Это фундамент под будущее расширение: **единый формат фактуры + единый журнал + единый диспетчер** + (отдельно) мастер-данные конвейера откликов.

## Правила исполнителя (обязательны)

1. **git запрещён полностью**: никаких add/commit/stash/branch. Только правки рабочего дерева. Коммитит ZCode после верификации.
2. **stdlib-only Python** (ADR-003/004): без pip-зависимостей.
3. После каждого лейна: `python -m unittest discover -s tools/tests` остаётся зелёным (новые тесты добавляются, ничего существующего не ломать).
4. Не трогать: `brief.js`, `vacancies.js`, `languages.js`, `app.js` (автогенерация/фронт), существующие форматы данных не мигрировать.
5. `tools/barrymore/dashboard-server.py` уже содержит чужие незакоммиченные правки — править ТОЛЬКО малыми вставками рядом с существующими `@do_.../api`-обработчиками, не переформатировать файл.
6. Новые файлы — только по списку лейнов ниже. Ничего не удалять.
7. Кириллица в строках приветствуется (кодировка UTF-8).

## Лейн Л-1: Конверт артефактов

Файлы: `tools/lib/__init__.py`, `tools/lib/envelope.py`, `tools/tests/test_envelope.py`

- `make_envelope(schema_id, produced_by, payload, version=1, refs=None) -> dict` возвращает:
  `{"schema_id": "evo.<домен>.<имя>", "schema_version": version, "produced_by": str, "produced_at": UTC ISO-8601 "Z", "payload": <как передали>, "refs": dict|{}}`
- `validate_envelope(env) -> list[str]` — список ошибок (пустой = ок): обязательные поля, формат schema_id (два-три сегмента через точку, ascii), produced_at парсится, payload присутствует (может быть любым JSON-типом, включая None → считать ошибкой отсутствия).
- Тесты: happy-path; schema_id без точки → ошибка; produced_at устанавливается автоматически и в UTC.

## Лейн Л-2: Машинный журнал событий

Файлы: `tools/lib/log_event.py`, `tools/tests/test_log_event.py`, точечная правка `tools/analytics_snapshot.py`

- `append_event(kind, source, payload=None, log_path=None) -> dict`: дозапись одной JSON-строки в JSONL (по умолчанию `Workspace/logs/events.jsonl`; путь можно переопределить — тесты пишут во tmp). Каждая строка = envelope: `schema_id="evo.log.event"`, produced_by=source, payload={"kind": kind, **(payload or {})}, плюс `"ts"` записи.
- Атомарность: запись целиком одной операцией `open(...,"a", encoding="utf-8") + write("\n"+line)`; исключение при записи НЕ должно ронять вызывающий код — `append_event` возвращает `{"ok": False, "error": ...}` вместо raise.
- Врезка-доказательство: в конце успешного прогона `analytics_snapshot.py` одна строка `append_event("snapshot.completed", "analytics_snapshot", {"dir": <имя папки>})` внутри try/except (падение журнала не должно ломать снапшот).
- `Workspace/logs/` добавить в `.gitignore` (если там уже есть похожее — не дублировать).
- Тесты: строка валидна как envelope; три вызова подряд = 3 строки; битый путь → ok:False, не raise.

## Лейн Л-3: Реестр джобов + API

Файлы: `tools/ops/jobs.json`, правка `tools/barrymore/dashboard-server.py` (малые вставки), `tools/tests/test_jobs_registry.py`

- `jobs.json` — реестр: `[{"id": "...", "title": "...", "owner": "<паспорт/имя>", "cmd": ["python", "tools/..."], "cwd": "<корень репо>", "timeout_s": 600, "report_hint": "<куда смотрит человек>", "enabled": true}]`.
  Заложить 3 записи: `analytics-snapshot` (`python tools/analytics_snapshot.py`), `token-meter` (`python tools/ops/token_meter.py` — сверить фактический путь и аргументы в файле перед записью), `healthcheck` (`python tools/ops/healthcheck.py` — так же сверить). Если команды/пути отличаются — записать фактические, ничего не переименовывать.
- Сервер: `GET /api/jobs` → реестр (только enabled по умолчанию, `?all=1` — все) + статус последнего запуска из `Workspace/logs/jobs_state.json`; `POST /api/jobs/<id>/run` → запуск через `subprocess.Popen` c таймаутом, ответ немедленный `{"started": true}`, по завершении (поток-наблюдатель) обновляет jobs_state.json (`{id: {started_at, finished_at, exit_code, duration_s}}`, envelope `schema_id="evo.ops.job_state"`). Одновременно один и тот же джоб не запускать (проверка started_at без finished_at → 409). Origin-проверка как у остальных POST (см. рядом в файле).
- Без UI-кнопок — только API. UI позже.
- Тесты: валидация jobs.json (уникальные id, обязательные поля); функции состояния (маркер «джоб уже запущен»).

## Лейн Л-4: Мастер-профиль конвейера откликов (денежный, не код)

Файлы: `Workspace/private/resume/master-profile.json` (+ gitignore для `Workspace/private/`, если ещё не закрыт)

- Скелет: `{"schema_id": "evo.resume.master", "skills": [], "cases": [{"id", "title", "period", "facts": [], "metrics": {}, "proof": null}], "preferences": {"roles": [], "rate": null, "hours": null}, "links": {}}`.
- Наполнить черновик из уже существующих материалов: `Workspace/private/proposals/2026-11-02/` (12 откликов RU+EN) и `proposals/2026-11-04/` (3 кейса-скелета) — вытащить навыки, кейсы, цифры, вилки. Не выдумывать факты; чего нет — оставить null с пометкой в `"todo"`-поле уровня корня.
- Это ЗОНА ДАННЫХ ДМИТРИЯ: файл не показывать в UI, не копировать в публичные data-файлы, в git не брать.

## Лейн Л-5: Подписанные переходы канбана + метрики конвейера

Мотивация (01:1-тимлид, 04.11): в history нет автора перехода («кто закрыл?») и нет метрик конвейера («покажи цифры»). Решение — одно: каждое движение карточки = подписанное событие, метрики = выборка по событиям.

Файлы: правка `tools/barrymore/task_store.py`, малая вставка в `tools/barrymore/dashboard-server.py`, правка `eVo/dashboard/kanban.js` (+ поднять `?v=` в подключении `kanban.html`), новый `tools/ops/kanban_metrics.py`, тесты.

- `set_stage()` и `mark_done()` принимают `by: str = "unknown"`; каждая новая запись history получает `"by": by`. Старые записи не мигрировать (нет `by` = «до эпохи подписей»).
- `POST /api/tasks/<id>/stage/<col>` читает `by` из JSON-body (дефолт "Sovereign").
- `kanban.js` шлёт `by: "Sovereign"` в теле обоих fetch (drag и статус-кнопки). Без логинов и ролей: loopback, один хозяин, автор декларирует сам — для сырого теста честно.
- Каждый переход дублируется в журнал: `append_event("task.stage", source=by, payload={"id": ..., "from": <пред. колонка>, "to": ...})` — внутри try/except, падение журнала не ломает drag.
- `tools/ops/kanban_metrics.py` (stdlib-only): читает `Active/*.json` + `events.jsonl`, печатает 4 блока: (1) закрыто за 7 дней; (2) средний возраст карточек в in-progress; (3) карточки старше 7 дней; (4) переходы по авторам за 7 дней. Вывод: человекочитаемый текст + JSON-envelope `schema_id="evo.kanban.metrics"`. Без UI.
- НЕ делать: логины, роли, графики, миграции старых карточек.

## Критерии приёмки (чек-лист Sovereign/ZCode)

1. `python -m unittest discover -s tools/tests` зелёный, включая новые тесты (≥3 новых файла тестов).
2. `python -c "from tools.lib.envelope import make_envelope, validate_envelope; e=make_envelope('evo.demo.x','test',{'a':1}); assert not validate_envelope(e)"` проходит из корня репо.
3. Прогон `python tools/analytics_snapshot.py` создаёт строку-событие в `Workspace/logs/events.jsonl`.
4. `GET /api/jobs` отдаёт 3 джоба; `POST /api/jobs/analytics-snapshot/run` запускает и через время пишет state (проверка curl с Origin-заголовком `http://127.0.0.1:8765`; сервер перезапускать только с санкции Sovereign — если рестарт невозможен, допустимо `unittest`-проверка обработчиков без живого сервера, пометить в отчёте).
5. `master-profile.json` существует, валиден как JSON, в git не попал.
6. Отчёт исполнителя: список созданных/правленных файлов, вывод тестов, что НЕ сделано и почему.
7. (Л-5) Drag карточки в UI пишет в её history запись с `"by"`; после прогона `kanban_metrics.py` видно 4 блока цифр.
