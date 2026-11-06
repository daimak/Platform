# -*- coding: utf-8 -*-
"""Комментарии к карточкам (запрос Sovereign 2026-11-06: «к задачам нельзя
добавить комментарий»). Поле comments карточки; history остаётся про движение."""
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


class AddCommentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.active = Path(self.tmp.name) / "Active"
        self.active.mkdir(parents=True)
        self.old_active = task_store.ACTIVE_DIR
        task_store.ACTIVE_DIR = self.active
        card = {
            "id": "comment-test", "title": "Комментарии", "source": "Sovereign",
            "priority": "regular", "status": "active", "createdAt": "2026-11-06T00:00:00Z",
            "stage": "in-progress", "history": [],
        }
        (self.active / "comment-test.json").write_text(
            json.dumps(card, ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        task_store.ACTIVE_DIR = self.old_active

    def _card(self):
        return json.loads(
            (self.active / "comment-test.json").read_text(encoding="utf-8"))

    def test_happy_path(self):
        result = task_store.add_comment("comment-test", "Sovereign", "Принято, работаем дальше")
        self.assertEqual(len(result["comments"]), 1)
        stored = result["comments"][0]
        self.assertEqual(stored["by"], "Sovereign")
        self.assertEqual(stored["text"], "Принято, работаем дальше")
        self.assertTrue(stored["at"].endswith("Z"))
        # history не тронут — комментарии не движения
        self.assertEqual(self._card()["history"], [])

    def test_appends_sequentially(self):
        task_store.add_comment("comment-test", "ZCode", "первый")
        task_store.add_comment("comment-test", "Sovereign", "второй")
        comments = self._card()["comments"]
        self.assertEqual([c["text"] for c in comments], ["первый", "второй"])

    def test_empty_text_rejected(self):
        with self.assertRaises(ValueError):
            task_store.add_comment("comment-test", "Sovereign", "   ")

    def test_too_long_rejected(self):
        with self.assertRaises(ValueError):
            task_store.add_comment("comment-test", "Sovereign", "х" * 2001)

    def test_missing_task(self):
        with self.assertRaises(FileNotFoundError):
            task_store.add_comment("no-such-task", "Sovereign", "текст")

    def test_cyrillic_and_limit_by(self):
        result = task_store.add_comment("comment-test", "S", "кириллица ✔")
        self.assertEqual(result["comments"][0]["text"], "кириллица ✔")


if __name__ == "__main__":
    unittest.main()
