# -*- coding: utf-8 -*-
"""Типы сущностей канбана (запрос Sovereign 2026-11-06, ITIL-минимум):
task | change (ЗНИ) | epic. Чтение толерантно, запись через allowlist."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BARRYMORE = ROOT / "tools" / "barrymore"
if str(BARRYMORE) not in sys.path:
    sys.path.insert(0, str(BARRYMORE))

import task_store  # noqa: E402


class TaskTypesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.active = Path(self.tmp.name) / "Active"
        self.active.mkdir(parents=True)
        self.old_active = task_store.ACTIVE_DIR
        task_store.ACTIVE_DIR = self.active
        card = {
            "id": "type-test", "title": "Типы", "source": "Sovereign",
            "priority": "regular", "status": "active", "createdAt": "2026-11-06T00:00:00Z",
            "stage": "todo", "history": [],
        }
        (self.active / "type-test.json").write_text(
            json.dumps(card, ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        task_store.ACTIVE_DIR = self.old_active

    def _card(self):
        return json.loads(
            (self.active / "type-test.json").read_text(encoding="utf-8"))

    def _read(self):
        return task_store._read_task(self.active / "type-test.json")

    def test_missing_type_defaults_to_task_on_read(self):
        task = self._read()
        self.assertEqual(task["type"], "task")

    def test_set_type_change(self):
        result = task_store.set_type("type-test", "change", by="ZCode")
        self.assertEqual(result["type"], "change")
        entry = self._card()["history"][-1]
        self.assertEqual(entry["type"], "change")
        self.assertEqual(entry["by"], "ZCode")

    def test_set_type_epic(self):
        task_store.set_type("type-test", "epic", by="Sovereign")
        self.assertEqual(self._card()["type"], "epic")

    def test_unknown_type_rejected(self):
        with self.assertRaises(ValueError):
            task_store.set_type("type-test", "incident")
        # файл не тронут
        self.assertNotIn("type", self._card())

    def test_same_type_noop(self):
        task_store.set_type("type-test", "change", by="ZCode")
        task_store.set_type("type-test", "change", by="ZCode")
        type_entries = [h for h in self._card()["history"] if "type" in h]
        self.assertEqual(len(type_entries), 1)

    def test_unknown_type_in_file_tolerated_on_read(self):
        card = self._card()
        card["type"] = "incident"  # чужое значение не должно ронять доску
        (self.active / "type-test.json").write_text(
            json.dumps(card, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(self._read()["type"], "incident")

    def test_bad_task_id_rejected(self):
        with self.assertRaises(ValueError):
            task_store.set_type("../evil", "task")


if __name__ == "__main__":
    unittest.main()
