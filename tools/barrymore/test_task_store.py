"""Тесты task_store: чтение карточек и толерантность к терминальному stage="done"
(инцидент 04.11: ручное закрытие мимо mark_done роняло весь /api/tasks)."""

import json
import tempfile
import unittest
from pathlib import Path

import task_store


def _write_card(tmp: Path, task_id: str, **overrides) -> Path:
    card = {
        "id": task_id,
        "title": "Тестовая карточка",
        "source": "test",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-04T00:00:00Z",
        "history": [],
        "stage": "todo",
    }
    card.update(overrides)
    if card["status"] == "done":
        card.setdefault("completedAt", "2026-11-04T00:00:00Z")
    path = tmp / f"{task_id}.json"
    path.write_text(json.dumps(card, ensure_ascii=False), encoding="utf-8")
    return path


class ReadTaskStageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_valid_todo_card_reads(self):
        task = task_store._read_task(_write_card(self.tmp, "t-card-ok"))
        self.assertEqual(task["stage"], "todo")

    def test_done_card_with_stage_done_reads(self):
        # Закрытая карточка со stage="done" — легитимное состояние после ручной правки.
        card = _write_card(self.tmp, "t-card-done", status="done", stage="done")
        task = task_store._read_task(card)
        self.assertEqual(task["status"], "done")
        self.assertEqual(task["stage"], "done")

    def test_active_card_with_stage_done_rejected(self):
        # stage="done" при живой задаче — по-настоящему битое состояние, читатель должен ругаться.
        card = _write_card(self.tmp, "t-card-bad", status="active", stage="done")
        with self.assertRaises(ValueError):
            task_store._read_task(card)

    def test_wrong_stage_value_rejected(self):
        card = _write_card(self.tmp, "t-card-x", stage="alpha")
        with self.assertRaises(ValueError):
            task_store._read_task(card)


if __name__ == "__main__":
    unittest.main()
