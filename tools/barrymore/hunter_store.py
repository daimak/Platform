"""Persistent local inbox for Hunter assignments."""

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Platform" / "Hunter"
INBOX_PATH = DATA_DIR / "assignments.json"
CATEGORIES = {
    "employment": "Работа по найму",
    "quick-income": "Быстрый заработок",
    "organize": "Систематизация и актуализация",
    "other": "Другое",
}
MAX_TITLE_LENGTH = 120
MAX_DETAILS_LENGTH = 3000


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def list_assignments() -> list[dict]:
    if not INBOX_PATH.exists():
        return []
    assignments = json.loads(INBOX_PATH.read_text(encoding="utf-8"))
    if not isinstance(assignments, list):
        raise ValueError(f"Некорректный формат очереди Hunter: {INBOX_PATH}")
    return assignments


def create_assignment(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Ожидался объект поручения.")
    category = payload.get("category")
    title = payload.get("title")
    details = payload.get("details", "")
    if category not in CATEGORIES:
        raise ValueError("Выберите допустимое направление поручения.")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Укажите краткое описание поручения.")
    title = title.strip()
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"Заголовок не должен превышать {MAX_TITLE_LENGTH} символов.")
    if not isinstance(details, str):
        raise ValueError("Уточнения должны быть текстом.")
    details = details.strip()
    if len(details) > MAX_DETAILS_LENGTH:
        raise ValueError(f"Уточнения не должны превышать {MAX_DETAILS_LENGTH} символов.")

    created_at = _timestamp()
    assignment = {
        "id": uuid.uuid4().hex,
        "category": category,
        "category_label": CATEGORIES[category],
        "title": title,
        "details": details,
        "status": "queued",
        "created_at": created_at,
    }
    assignments = list_assignments()
    assignments.insert(0, assignment)
    INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=INBOX_PATH.parent,
            prefix=".hunter-assignments-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(assignments, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        os.replace(temporary_path, INBOX_PATH)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
    return assignment
