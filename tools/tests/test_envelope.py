# -*- coding: utf-8 -*-
"""Тесты конверта артефактов (Лейн Л-1, Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md)."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # запуск из любого cwd
    sys.path.insert(0, str(ROOT))

from tools.lib.envelope import make_envelope, validate_envelope  # noqa: E402


class TestMakeEnvelope(unittest.TestCase):
    """make_envelope: happy-path, автоматический produced_at в UTC, passthrough полей."""

    def test_happy_path(self):
        env = make_envelope("evo.demo.x", "test", {"a": 1})
        self.assertEqual(env["schema_id"], "evo.demo.x")
        self.assertEqual(env["schema_version"], 1)
        self.assertEqual(env["produced_by"], "test")
        self.assertEqual(env["payload"], {"a": 1})
        self.assertEqual(env["refs"], {})
        self.assertEqual(validate_envelope(env), [])

    def test_payload_any_json_type(self):
        # payload может быть любым JSON-типом, кроме отсутствия (None)
        for payload in ([1, 2], "текст", 0, False, 3.14, {"кириллица": "ў, қ, ҳ"}):
            with self.subTest(payload=payload):
                env = make_envelope("evo.demo.x", "test", payload)
                self.assertEqual(validate_envelope(env), [])

    def test_produced_at_auto_and_utc(self):
        # produced_at пишется с точностью до секунд — границы тоже усекаем до секунд
        before = datetime.now(timezone.utc).replace(microsecond=0)
        env = make_envelope("evo.demo.x", "test", 1)
        after = datetime.now(timezone.utc)
        raw = env["produced_at"]
        self.assertTrue(raw.endswith("Z"), f"produced_at должен заканчиваться на Z: {raw}")
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        self.assertEqual(parsed.utcoffset().total_seconds(), 0, "produced_at должен быть UTC")
        self.assertTrue(before <= parsed <= after, "produced_at — из системных часов, между до/после")

    def test_refs_passthrough(self):
        refs = {"source": "tools/lib/envelope.py", "job": "analytics-snapshot"}
        env = make_envelope("evo.demo.x", "test", {}, refs=refs)
        self.assertEqual(env["refs"], refs)

    def test_version_passthrough(self):
        env = make_envelope("evo.demo.x", "test", {}, version=2)
        self.assertEqual(env["schema_version"], 2)
        self.assertEqual(validate_envelope(env), [])


class TestValidateEnvelope(unittest.TestCase):
    """validate_envelope: формат schema_id, битый produced_at, отсутствующий payload."""

    def test_schema_id_without_dot_is_error(self):
        env = make_envelope("nodot", "test", 1)
        errors = validate_envelope(env)
        self.assertTrue(any("schema_id" in e for e in errors), errors)

    def test_schema_id_two_segments_ok(self):
        env = make_envelope("evo.demo", "test", 1)
        self.assertEqual(validate_envelope(env), [])

    def test_schema_id_four_segments_is_error(self):
        env = make_envelope("evo.a.b.c", "test", 1)
        self.assertTrue(any("schema_id" in e for e in validate_envelope(env)))

    def test_schema_id_non_ascii_is_error(self):
        env = make_envelope("evo.демо.x", "test", 1)
        self.assertTrue(any("schema_id" in e for e in validate_envelope(env)))

    def test_bad_produced_at_is_error(self):
        env = make_envelope("evo.demo.x", "test", 1)
        env["produced_at"] = "не-время"
        errors = validate_envelope(env)
        self.assertTrue(any("produced_at" in e for e in errors), errors)

    def test_missing_fields_reported(self):
        errors = validate_envelope({})
        self.assertTrue(any("schema_id" in e for e in errors), errors)
        self.assertTrue(any("payload" in e for e in errors), errors)
        self.assertTrue(any("produced_at" in e for e in errors), errors)
        self.assertTrue(any("produced_by" in e for e in errors), errors)
        self.assertTrue(any("schema_version" in e for e in errors), errors)

    def test_payload_none_is_missing(self):
        env = make_envelope("evo.demo.x", "test", None)
        errors = validate_envelope(env)
        self.assertTrue(any("payload" in e for e in errors), errors)

    def test_refs_must_be_dict(self):
        env = make_envelope("evo.demo.x", "test", 1, refs="не-словарь")
        self.assertTrue(any("refs" in e for e in validate_envelope(env)))

    def test_not_a_dict(self):
        self.assertNotEqual(validate_envelope([1, 2]), [])


if __name__ == "__main__":
    unittest.main()
