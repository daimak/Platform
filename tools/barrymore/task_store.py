"""Persistent task lifecycle for Barrymore's dashboard."""

import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "Memory" / "Engineering" / "Tasks"
ACTIVE_DIR = TASKS_DIR / "Active"
ARCHIVE_DIR = TASKS_DIR / "Archive"
TASK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
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
    result = {"urgent": [], "regular": [], "done": []}
    if not ACTIVE_DIR.exists():
        return result

    for path in sorted(ACTIVE_DIR.glob("*.json")):
        task = _read_task(path)
        if task["status"] == "done":
            result["done"].append(task)
        elif task.get("priority") == "urgent":
            result["urgent"].append(task)
        else:
            result["regular"].append(task)
    return result


def mark_done(task_id: str, now: datetime | None = None) -> dict:
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
    })
    _atomic_write(path, task)
    return task
