# -*- coding: utf-8 -*-
"""Тесты машинного журнала (Лейн Л-2): envelope-строки, дозапись, живучесть при битом пути."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # запуск из любого cwd
    sys.path.insert(0, str(ROOT))

from tools.lib import log_event  # noqa: E402
from tools.lib.envelope import validate_envelope  # noqa: E402
from tools.lib.log_event import append_event  # noqa: E402


class TempDirTest(unittest.TestCase):
    """Базовый класс: временный каталог, автоматически удаляемый после теста."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _records(self, path: Path) -> list:
        """Все валидные JSON-записи журнала (пустые строки формата "\n"+line пропускаются)."""
        text = path.read_text(encoding="utf-8")
        return [json.loads(line) for line in text.splitlines() if line.strip()]


class TestAppendEvent(TempDirTest):
    """append_event: валидный конверт, дозапись, кириллица, живучесть."""

    def test_line_is_valid_envelope(self):
        log = self.tmp / "events.jsonl"
        result = append_event(
            "snapshot.completed", "analytics_snapshot", {"dir": "2026-11-05"}, log_path=log
        )
        self.assertTrue(result["ok"], result)
        records = self._records(log)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(validate_envelope(record), [], record)
        self.assertEqual(record["schema_id"], "evo.log.event")
        self.assertEqual(record["produced_by"], "analytics_snapshot")
        self.assertEqual(record["payload"]["kind"], "snapshot.completed")
        self.assertEqual(record["payload"]["dir"], "2026-11-05")
        self.assertIn("ts", record)
        self.assertTrue(record["ts"].endswith("Z"), record["ts"])
        self.assertEqual(record["ts"], record["produced_at"])

    def test_cyrillic_payload_roundtrip(self):
        log = self.tmp / "events.jsonl"
        result = append_event("test.kind", "тест-источник", {"заметка": "привет, ўқҳ"}, log_path=log)
        self.assertTrue(result["ok"], result)
        record = self._records(log)[0]
        self.assertEqual(record["produced_by"], "тест-источник")
        self.assertEqual(record["payload"]["заметка"], "привет, ўқҳ")

    def test_three_calls_three_lines(self):
        log = self.tmp / "events.jsonl"
        for i in range(3):
            result = append_event("test.kind", "test", {"n": i}, log_path=log)
            self.assertTrue(result["ok"], result)
        records = self._records(log)
        self.assertEqual(len(records), 3)
        self.assertEqual([r["payload"]["n"] for r in records], [0, 1, 2])

    def test_broken_path_no_raise(self):
        # родительский «каталог» — существующий файл: запись невозможна,
        # но append_event возвращает {"ok": False}, а не raise
        blocker = self.tmp / "blocked.txt"
        blocker.write_text("это файл, а не каталог", encoding="utf-8")
        log = blocker / "events.jsonl"
        result = append_event("test.kind", "test", None, log_path=log)
        self.assertFalse(result["ok"], result)
        self.assertIn("error", result)

    def test_payload_none_keeps_kind_only(self):
        log = self.tmp / "events.jsonl"
        self.assertTrue(append_event("test.kind", "test", None, log_path=log)["ok"])
        record = self._records(log)[0]
        self.assertEqual(record["payload"], {"kind": "test.kind"})

    def test_default_path_redirectable(self):
        # путь по умолчанию = Workspace/logs/events.jsonl; для теста подменяем на tmp
        original = log_event.DEFAULT_LOG_PATH
        redirected = self.tmp / "logs" / "events.jsonl"
        log_event.DEFAULT_LOG_PATH = redirected
        try:
            result = append_event("test.kind", "test", None)
        finally:
            log_event.DEFAULT_LOG_PATH = original
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(self._records(redirected)), 1)


if __name__ == "__main__":
    unittest.main()
