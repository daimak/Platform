# -*- coding: utf-8 -*-
"""Тесты хвостов ночной смены 05-06.11: no-op переход, врата can_transition,
busy-лок (atomic acquire / TTL-steal / claims). Уроки инцидента
«Резюме-конвейер»: чужой агент двинул data-foundation в test посреди смены."""
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BARRYMORE = ROOT / "tools" / "barrymore"
if str(BARRYMORE) not in sys.path:
    sys.path.insert(0, str(BARRYMORE))

import task_store  # noqa: E402
from tools.lib import task_lock  # noqa: E402


class NoOpTransitionTest(unittest.TestCase):
    """set_stage в ту же колонку — no-op: без дубля history и события."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.active = Path(self.tmp.name) / "Active"
        self.active.mkdir(parents=True)
        self.old_active = task_store.ACTIVE_DIR
        task_store.ACTIVE_DIR = self.active

    def tearDown(self):
        task_store.ACTIVE_DIR = self.old_active

    def _card(self, stage="todo"):
        card = {
            "id": "noop-test", "title": "No-op тест", "source": "Sovereign",
            "priority": "regular", "status": "active", "createdAt": "2026-11-05T00:00:00Z",
            "stage": stage, "history": [{"stage": stage, "at": "2026-11-05T00:00:00Z"}],
        }
        (self.active / "noop-test.json").write_text(
            json.dumps(card, ensure_ascii=False), encoding="utf-8")

    def test_same_stage_is_noop(self):
        self._card(stage="todo")
        result = task_store.set_stage("noop-test", "todo")
        self.assertEqual(result["stage"], "todo")
        self.assertEqual(len(result["history"]), 1, "no-op не должен писать в history")

    def test_real_transition_still_writes(self):
        self._card(stage="todo")
        result = task_store.set_stage("noop-test", "in-progress")
        self.assertEqual(len(result["history"]), 2)

    def test_reopen_from_done_not_noop(self):
        self._card(stage="test")
        card = json.loads((self.active / "noop-test.json").read_text(encoding="utf-8"))
        card["status"] = "done"
        card["completedAt"] = "2026-11-05T01:00:00Z"
        (self.active / "noop-test.json").write_text(json.dumps(card), encoding="utf-8")
        result = task_store.set_stage("noop-test", "test")
        self.assertEqual(result["status"], "active", "из done тот же stage = reopen, не no-op")


class CanTransitionGateTest(unittest.TestCase):
    """Врата: test/done = только source/owner/Sovereign/ZCode."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.active = Path(self.tmp.name) / "Active"
        self.active.mkdir(parents=True)
        self.old_active = task_store.ACTIVE_DIR
        task_store.ACTIVE_DIR = self.active
        card = {
            "id": "gate-test", "title": "Врата", "source": "Sovereign", "owner": "строитель-2",
            "priority": "regular", "status": "active", "createdAt": "2026-11-05T00:00:00Z",
            "stage": "in-progress", "history": [],
        }
        (self.active / "gate-test.json").write_text(
            json.dumps(card, ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        task_store.ACTIVE_DIR = self.old_active

    def test_owner_and_source_allowed(self):
        self.assertTrue(task_store.can_transition("gate-test", "строитель-2", "test"))
        self.assertTrue(task_store.can_transition("gate-test", "Sovereign", "test"))

    def test_watchman_allowed(self):
        self.assertTrue(task_store.can_transition("gate-test", "ZCode", "done"))

    def test_stranger_denied(self):
        self.assertFalse(task_store.can_transition("gate-test", "Резюме-конвейер", "test"))

    def test_working_columns_open_to_all(self):
        self.assertTrue(task_store.can_transition("gate-test", "Резюме-конвейер", "in-progress"))
        self.assertTrue(task_store.can_transition("gate-test", "Резюме-конвейер", "todo"))


class TaskLockTest(unittest.TestCase):
    """busy-лок: атомарный захват, отказ + отклик, TTL-перехват, release."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name) / "Busy"

    def test_acquire_and_conflict(self):
        first = task_lock.acquire("t1", "агент-А", "делаю Л-3", base=self.base)
        self.assertTrue(first["ok"])
        second = task_lock.acquire("t1", "агент-Б", "тоже хочу", base=self.base,
                                   claim_wanted="хотел Л-3")
        self.assertFalse(second["ok"])
        self.assertEqual(second["busy"]["agent"], "агент-А")
        self.assertTrue(second["claimed"], "отказавшийся кладёт отклик")

    def test_release_frees_slot(self):
        task_lock.acquire("t2", "агент-А", base=self.base)
        self.assertTrue(task_lock.release("t2", "агент-А", base=self.base)["ok"])
        self.assertTrue(task_lock.acquire("t2", "агент-Б", base=self.base)["ok"])

    def test_wrong_agent_cannot_release(self):
        task_lock.acquire("t3", "агент-А", base=self.base)
        self.assertFalse(task_lock.release("t3", "агент-Б", base=self.base)["ok"])

    def test_heartbeat_extends_and_updates_doing(self):
        task_lock.acquire("t4", "агент-А", "начал", base=self.base)
        hb = task_lock.heartbeat("t4", "агент-А", doing="почти готово", base=self.base)
        self.assertTrue(hb["ok"])
        self.assertEqual(hb["lock"]["doing"], "почти готово")

    def test_stale_lock_is_stolen(self):
        task_lock.acquire("t5", "агент-мёртвый", base=self.base, ttl_s=1)
        path = self.base / "t5.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["heartbeat"] = "2026-01-01T00:00:00Z"  # руками состарим пульс
        path.write_text(json.dumps(data), encoding="utf-8")
        stolen = task_lock.acquire("t5", "агент-Б", base=self.base)
        self.assertTrue(stolen["ok"])
        self.assertEqual(stolen["lock"].get("stolen_from"), "агент-мёртвый")

    def test_status_and_status_all(self):
        task_lock.acquire("t6", "агент-А", "копаю", base=self.base)
        self.assertEqual(task_lock.status("t6", base=self.base)["agent"], "агент-А")
        self.assertIn("t6", task_lock.status_all(base=self.base))
        self.assertIsNone(task_lock.status("нет-такой", base=self.base))

    def test_claims_listing(self):
        task_lock.acquire("t7", "агент-А", base=self.base)
        task_lock.acquire("t7", "агент-Б", base=self.base, claim_wanted="ревью кода")
        found = task_lock.claims("t7", base=self.base)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["agent"], "агент-Б")
        self.assertEqual(found[0]["wanted"], "ревью кода")


if __name__ == "__main__":
    unittest.main()
