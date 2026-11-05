# -*- coding: utf-8 -*-
"""Тесты подписанных переходов канбана (Лейн Л-5): by в history + дубликат в журнал.

Активные карточки подменяются на tmp (MODULE-константы task_store), журнал — на
рекордер или на tmp-файл через tools.lib.log_event.DEFAULT_LOG_PATH. Реальные
Memory/Engineering/Tasks и Workspace/logs не затрагиваются.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # запуск из любого cwd (например, из tools/barrymore)
    sys.path.insert(0, str(ROOT))

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
    path = tmp / f"{task_id}.json"
    path.write_text(json.dumps(card, ensure_ascii=False), encoding="utf-8")
    return path


class BySignatureTests(unittest.TestCase):
    """set_stage/mark_done принимают by; каждая новая запись history получает "by"."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self._original_active = task_store.ACTIVE_DIR
        task_store.ACTIVE_DIR = self.tmp
        self.addCleanup(setattr, task_store, "ACTIVE_DIR", self._original_active)
        # журнал глушим по умолчанию: рекордер ставится в конкретных тестах
        self.events = []
        self._original_append = task_store._JOURNAL_APPEND
        self._original_ready = task_store._JOURNAL_READY
        task_store._JOURNAL_APPEND = lambda kind, source, payload=None, log_path=None: (
            self.events.append({"kind": kind, "source": source, **(payload or {})}) or {"ok": True}
        )
        task_store._JOURNAL_READY = True
        self.addCleanup(setattr, task_store, "_JOURNAL_APPEND", self._original_append)
        self.addCleanup(setattr, task_store, "_JOURNAL_READY", self._original_ready)

    def _last_history(self, task_id: str) -> dict:
        task = json.loads((self.tmp / f"{task_id}.json").read_text(encoding="utf-8"))
        return task["history"][-1]

    def test_set_stage_signs_history(self):
        _write_card(self.tmp, "t-by-stage", stage="todo")
        task = task_store.set_stage("t-by-stage", "in-progress", by="ZCode")
        last = task["history"][-1]
        self.assertEqual(last["stage"], "in-progress")
        self.assertEqual(last["by"], "ZCode")
        self.assertTrue(last["at"].endswith("Z"))

    def test_set_stage_default_by_unknown(self):
        _write_card(self.tmp, "t-by-default")
        task = task_store.set_stage("t-by-default", "test")
        self.assertEqual(task["history"][-1]["by"], "unknown")

    def test_mark_done_signs_history(self):
        _write_card(self.tmp, "t-by-done", stage="in-progress")
        task = task_store.mark_done("t-by-done", by="Sovereign")
        last = task["history"][-1]
        self.assertEqual(last["status"], "done")
        self.assertEqual(last["by"], "Sovereign")

    def test_stage_done_delegates_by_to_mark_done(self):
        _write_card(self.tmp, "t-by-delegate", stage="test")
        task = task_store.set_stage("t-by-delegate", "done", by="Watson")
        last = task["history"][-1]
        self.assertEqual(last["status"], "done")
        self.assertEqual(last["by"], "Watson")

    def test_reopen_signs_history(self):
        _write_card(self.tmp, "t-by-reopen", status="done",
                    completedAt="2026-11-04T00:00:00Z", stage="done")
        task = task_store.set_stage("t-by-reopen", "todo", by="ZCode")
        last = task["history"][-1]
        self.assertEqual(last["status"], "reopened")
        self.assertEqual(last["by"], "ZCode")
        self.assertEqual(task["status"], "active")

    def test_journal_duplicate_on_stage_move(self):
        _write_card(self.tmp, "t-jr-stage", stage="todo")
        task_store.set_stage("t-jr-stage", "in-progress", by="Sovereign")
        self.assertEqual(len(self.events), 1)
        event = self.events[0]
        self.assertEqual(event["kind"], "task.stage")
        self.assertEqual(event["source"], "Sovereign")
        self.assertEqual(event["id"], "t-jr-stage")
        self.assertEqual(event["from"], "todo")
        self.assertEqual(event["to"], "in-progress")

    def test_journal_duplicate_on_reopen_and_done(self):
        _write_card(self.tmp, "t-jr-reopen", status="done",
                    completedAt="2026-11-04T00:00:00Z", stage="done")
        task_store.set_stage("t-jr-reopen", "todo", by="ZCode")
        self.assertEqual(self.events[0]["from"], "done")
        self.assertEqual(self.events[0]["to"], "todo")

        _write_card(self.tmp, "t-jr-done", stage="test")
        task_store.mark_done("t-jr-done", by="Sovereign")
        self.assertEqual(self.events[1]["kind"], "task.stage")
        self.assertEqual(self.events[1]["from"], "test")
        self.assertEqual(self.events[1]["to"], "done")

        # set_stage("done") не дублирует запись дважды: делегирует в mark_done
        self.events.clear()
        _write_card(self.tmp, "t-jr-once", stage="test")
        task_store.set_stage("t-jr-once", "done", by="Sovereign")
        self.assertEqual(len(self.events), 1)

    def test_journal_failure_does_not_break_move(self):
        def broken_append(*args, **kwargs):
            raise OSError("журнал недоступен")
        task_store._JOURNAL_APPEND = broken_append
        _write_card(self.tmp, "t-jr-broken")
        task = task_store.set_stage("t-jr-broken", "in-progress", by="Sovereign")
        self.assertEqual(task["stage"], "in-progress")  # переход состоялся despite журнал

    def test_old_history_without_by_still_reads(self):
        # записи до эпохи подписей не мигрируют и не ломают чтение
        card_path = _write_card(self.tmp, "t-legacy", history=[{"stage": "todo", "at": "2026-10-01T00:00:00Z"}])
        task = task_store._read_task(card_path)
        self.assertNotIn("by", task["history"][0])


class RealJournalIntegrationTests(unittest.TestCase):
    """Интеграция с настоящим tools.lib.log_event (ленивая загрузка), путь — tmp."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_stage_move_writes_real_event_line(self):
        from tools.lib import log_event

        active = self.tmp / "Active"
        active.mkdir()
        journal = self.tmp / "logs" / "events.jsonl"
        card = {
            "id": "t-real-jr", "title": "Реальный журнал", "source": "test",
            "priority": "regular", "status": "active",
            "createdAt": "2026-11-04T00:00:00Z", "history": [], "stage": "todo",
        }
        (active / "t-real-jr.json").write_text(json.dumps(card, ensure_ascii=False), encoding="utf-8")

        original_active = task_store.ACTIVE_DIR
        original_log = log_event.DEFAULT_LOG_PATH
        original_append = task_store._JOURNAL_APPEND
        original_ready = task_store._JOURNAL_READY
        task_store.ACTIVE_DIR = active
        log_event.DEFAULT_LOG_PATH = journal
        task_store._JOURNAL_APPEND = None
        task_store._JOURNAL_READY = False  # форсируем ленивую загрузку настоящего append_event
        try:
            task_store.set_stage("t-real-jr", "in-progress", by="Sovereign")
        finally:
            task_store.ACTIVE_DIR = original_active
            log_event.DEFAULT_LOG_PATH = original_log
            task_store._JOURNAL_APPEND = original_append
            task_store._JOURNAL_READY = original_ready

        lines = [line for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])
        self.assertEqual(event["schema_id"], "evo.log.event")
        self.assertEqual(event["payload"], {"kind": "task.stage", "id": "t-real-jr",
                                            "from": "todo", "to": "in-progress"})
        self.assertEqual(event["produced_by"], "Sovereign")


if __name__ == "__main__":
    unittest.main()
