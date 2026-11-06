"""Persistent task lifecycle for Barrymore's dashboard."""

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "Memory" / "Engineering" / "Tasks"
ACTIVE_DIR = TASKS_DIR / "Active"
ARCHIVE_DIR = TASKS_DIR / "Archive"
TASK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
STAGES = ("analysis", "todo", "in-progress", "test")
# Типы сущностей (запрос Sovereign 2026-11-06, ITIL-минимум):
# task = таска, change = ЗНИ (запрос на изменение), epic = эпик.
TASK_TYPES = ("task", "change", "epic")
DONE_RETENTION = timedelta(hours=48)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _read_task(path: Path) -> dict:
    task = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(task, dict)
        or task.get("id") != path.stem
        or not TASK_ID_PATTERN.fullmatch(str(task.get("id", "")))
    ):
        raise ValueError(f"Некорректная запись задачи: {path}")
    if task.get("status") not in ("active", "done"):
        raise ValueError(f"Некорректный статус задачи: {path}")
    if not isinstance(task.get("title"), str) or not task["title"].strip():
        raise ValueError(f"У задачи отсутствует заголовок: {path}")
    if task.get("priority") not in ("urgent", "regular"):
        raise ValueError(f"Некорректный приоритет задачи: {path}")
    if not isinstance(task.get("createdAt"), str):
        raise ValueError(f"У задачи отсутствует дата создания: {path}")
    if not isinstance(task.get("history"), list):
        raise ValueError(f"У задачи отсутствует история переходов: {path}")
    stage_value = task.get("stage")
    # Толерантность: закрытая карточка может нести stage="done" (правка мимо
    # set_stage, который по контракту не трогает stage). Это не повод ронять весь список.
    if (
        stage_value is not None
        and stage_value not in STAGES
        and not (stage_value == "done" and task.get("status") == "done")
    ):
        raise ValueError(f"Некорректная колонка канбана: {path}")
    # Тип сущности: чтение толерантно (нет поля = task; неизвестное значение не
    # роняет доску). Строгий allowlist стоит на записи — set_type, API даёт 400.
    task.setdefault("type", "task")
    if task["status"] == "done":
        try:
            completed_at = _parse_timestamp(task["completedAt"])
            if completed_at.utcoffset() is None:
                raise ValueError("timestamp must include timezone")
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"У завершенной задачи некорректна дата Done: {path}") from error
    return task


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(payload, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


# Л-5 (Docs/DATA-FOUNDATION-PLAN-2026-11-04): подписанные переходы канбана.
# Каждый переход дублируется в машинный журнал (tools/lib/log_event) — внутри
# try/except: падение журнала никогда не ломает drag. Журнал подгружается лениво,
# чтобы импорт task_store не зависел от cwd и наличия корня репо в sys.path.

_JOURNAL_APPEND = None
_JOURNAL_READY = False


def _journal_append():
    """Ленивая загрузка tools.lib.log_event.append_event; None = журнал недоступен."""
    global _JOURNAL_APPEND, _JOURNAL_READY
    if not _JOURNAL_READY:
        _JOURNAL_READY = True
        try:
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))
            from tools.lib.log_event import append_event
            _JOURNAL_APPEND = append_event
        except Exception:
            _JOURNAL_APPEND = None
    return _JOURNAL_APPEND


def _journal_transition(task_id: str, by: str, previous: str | None, next_stage: str) -> None:
    """Дубликат перехода в журнал; любая ошибка глушится (карточка уже записана)."""
    try:
        append_event = _journal_append()
        if append_event is not None:
            append_event("task.stage", by, {"id": task_id, "from": previous, "to": next_stage})
    except Exception:
        pass


# Правило Sovereign (2026-11-06): колонки-врата. Перевод в test/done = заявление
# «работа завершена, прошу приёмки» — его имеет право сделать только владелец
# работы, не случайный прохожий (инцидент: суб-агент соседней сессии двинул
# data-foundation в test посреди чужой ночной смены).
GATE_STAGES = ("test", "done")


def can_transition(task_id: str, by: str, stage: str) -> bool:
    """Разрешён ли автору `by` перевод карточки в колонку `stage`.

    Врата стоят только на GATE_STAGES; рабочие колонки и reopen открыты всем.
    Ошибки чтения карточки не превращаются в 403 — их отработает set_stage.
    """
    if stage not in GATE_STAGES:
        return True
    path = ACTIVE_DIR / f"{task_id}.json"
    if not path.is_file():
        return True
    try:
        task = _read_task(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return True
    allowed = {task.get("source"), task.get("owner"), "Sovereign", "ZCode"}
    return (by or "").strip() in allowed


def _busy_map() -> dict:
    """{task_id: busy-лок} для прикрепления к выдаче /api/tasks; недоступен — пусто."""
    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.lib.task_lock import status_all

        return status_all()
    except Exception:
        return {}


def archive_expired_done(now: datetime | None = None) -> int:
    current_time = now or _now()
    archived = 0
    if not ACTIVE_DIR.exists():
        return archived

    for path in sorted(ACTIVE_DIR.glob("*.json")):
        task = _read_task(path)
        if task["status"] != "done":
            continue
        completed_at = _parse_timestamp(task["completedAt"])
        if current_time - completed_at < DONE_RETENTION:
            continue

        task["archivedAt"] = _timestamp(current_time)
        task["history"].append({
            "status": "archived",
            "at": task["archivedAt"],
        })
        destination = ARCHIVE_DIR / current_time.strftime("%Y") / current_time.strftime("%m") / path.name
        if destination.exists():
            archived_task = _read_task(destination)
            if not archived_task.get("archivedAt"):
                raise FileExistsError(f"Архивная запись уже существует: {destination}")
            path.unlink()
            archived += 1
            continue
        _atomic_write(destination, task)
        path.unlink()
        archived += 1
    return archived


def dashboard_tasks(now: datetime | None = None, archive_expired: bool = True) -> dict:
    if archive_expired:
        archive_expired_done(now)
    result = {"urgent": [], "regular": [], "done": [], "all": []}
    if not ACTIVE_DIR.exists():
        return result

    busy_map = _busy_map()
    for path in sorted(ACTIVE_DIR.glob("*.json")):
        task = _read_task(path)
        task["busy"] = busy_map.get(task["id"])
        result["all"].append(task)
        if task["status"] == "done":
            result["done"].append(task)
        elif task.get("priority") == "urgent":
            result["urgent"].append(task)
        else:
            result["regular"].append(task)
    return result


def mark_done(task_id: str, now: datetime | None = None, by: str = "unknown") -> dict:
    """Закрыть задачу; by — подпись автора перехода (Л-5; по умолчанию "unknown",
    записи без "by" — до эпохи подписей, не мигрируют)."""
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError("Некорректный идентификатор задачи.")

    path = ACTIVE_DIR / f"{task_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Активная задача не найдена: {task_id}")
    task = _read_task(path)
    if task["status"] == "done":
        return task

    completed_at = _timestamp(now or _now())
    task["status"] = "done"
    task["completedAt"] = completed_at
    task["history"].append({
        "status": "done",
        "at": completed_at,
        "by": by,
    })
    _atomic_write(path, task)
    _journal_transition(task_id, by, task.get("stage"), "done")
    return task


def set_stage(task_id: str, stage: str, now: datetime | None = None, by: str = "unknown") -> dict:
    """Канбан: переложить задачу в колонку stage (analysis/todo/in-progress/test/done).

    Колонка хранится в поле stage, терминальность не меняется: "done" = mark_done,
    перенос из Done в рабочую колонку = reopen (status обратно в active).
    Каждый перенос — событие в history с подписью автора "by" (Л-5; по умолчанию
    "unknown", старые записи без "by" не мигрируют)."""
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError("Некорректный идентификатор задачи.")
    if stage != "done" and stage not in STAGES:
        raise ValueError(f"Некорректная колонка канбана: {stage}")

    path = ACTIVE_DIR / f"{task_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Активная задача не найдена: {task_id}")
    task = _read_task(path)
    if stage == "done":
        return mark_done(task_id, now, by)

    previous = task.get("stage")
    # no-op: карточка уже в этой колонке — без дубля в history и без фейкового
    # события движения (fix Д-1 ночной смены 2026-11-05: "test -> test").
    if task["status"] != "done" and previous == stage:
        return task

    event_at = _timestamp(now or _now())
    if task["status"] == "done":
        task["status"] = "active"
        task.pop("completedAt", None)
        task["stage"] = stage
        task["history"].append({"status": "reopened", "stage": stage, "at": event_at, "by": by})
        _atomic_write(path, task)
        _journal_transition(task_id, by, "done", stage)
    else:
        task["stage"] = stage
        task["history"].append({"stage": stage, "at": event_at, "by": by})
        _atomic_write(path, task)
        _journal_transition(task_id, by, previous, stage)
    return task


COMMENT_MAX_LEN = 2000


def add_comment(task_id: str, by: str, text: str, now: datetime | None = None) -> dict:
    """Комментарий к карточке (запрос Sovereign 2026-11-06: «к задачам нельзя
    добавить комментарий»). Хранится в поле comments карточки — история переходов
    (history) остаётся только про движение. Комментарии не мигрируют в старых
    карточках: нет поля = просто пустой список."""
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError("Некорректный идентификатор задачи.")
    author = (by or "").strip()[:100]
    body = (text or "").strip()
    if not body:
        raise ValueError("Комментарий не может быть пустым.")
    if len(body) > COMMENT_MAX_LEN:
        raise ValueError(f"Комментарий длиннее {COMMENT_MAX_LEN} символов.")

    path = ACTIVE_DIR / f"{task_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Активная задача не найдена: {task_id}")
    task = _read_task(path)
    comments = task.get("comments")
    if not isinstance(comments, list):
        comments = []
    comments.append({"by": author or "Sovereign", "text": body,
                     "at": _timestamp(now or _now())})
    task["comments"] = comments
    _atomic_write(path, task)
    return task


def set_type(task_id: str, type_value: str, by: str = "unknown", now: datetime | None = None) -> dict:
    """Тип сущности карточки: task | change (ЗНИ) | epic (запрос Sovereign
    2026-11-06, ITIL-минимум). Allowlist строгий: неизвестное значение =
    ValueError (API отвечает 400, не 500 — урок priority-инцидента).
    Смена типа — запись в history с подписью "by"; смена на тот же тип = no-op."""
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError("Некорректный идентификатор задачи.")
    if type_value not in TASK_TYPES:
        raise ValueError(f"Некорректный тип сущности: {type_value}")

    path = ACTIVE_DIR / f"{task_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Активная задача не найдена: {task_id}")
    task = _read_task(path)
    previous = task.get("type", "task")
    if previous == type_value:
        return task
    task["type"] = type_value
    task["history"].append({"type": type_value, "at": _timestamp(now or _now()), "by": by})
    _atomic_write(path, task)
    return task
