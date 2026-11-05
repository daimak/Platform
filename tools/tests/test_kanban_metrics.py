# -*- coding: utf-8 -*-
"""Тесты метрик конвейера канбана (Лейн Л-5): 4 блока по карточкам и журналу событий."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # запуск из любого cwd
    sys.path.insert(0, str(ROOT))

from tools.lib.envelope import validate_envelope  # noqa: E402
from tools.ops import kanban_metrics  # noqa: E402
from tools.ops.kanban_metrics import build_envelope, build_metrics, render_text  # noqa: E402

NOW = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def _card(task_id: str, *, status="active", stage="todo", created_days_ago=0, done_days_ago=None, title="Карточка"):
    card = {
        "id": task_id,
        "title": f"{title} {task_id}",
        "priority": "regular",
        "status": status,
        "createdAt": _iso(NOW - timedelta(days=created_days_ago)),
        "history": [],
        "stage": stage,
    }
    if status == "done":
        card["completedAt"] = _iso(NOW - timedelta(days=done_days_ago if done_days_ago is not None else 0))
    return card


def _stage_event(ts: datetime, author: str, task_id="t-1", frm="todo", to="in-progress") -> dict:
    return {
        "schema_id": "evo.log.event",
        "schema_version": 1,
        "produced_by": author,
        "produced_at": _iso(ts),
        "payload": {"kind": "task.stage", "id": task_id, "from": frm, "to": to},
        "refs": {},
        "ts": _iso(ts),
    }


class MetricsFixturesTest(unittest.TestCase):
    """Фикстуры во временном каталоге: карточки Active/*.json + events.jsonl."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.active = self.tmp / "Active"
        self.active.mkdir()
        self.events = self.tmp / "events.jsonl"

    def write_cards(self, *cards):
        for card in cards:
            (self.active / f"{card['id']}.json").write_text(
                json.dumps(card, ensure_ascii=False), encoding="utf-8")

    def write_events(self, *events, raw_prefix=""):
        # raw_prefix имитирует ведущий "\n" формата записи Л-2 (write("\n"+line))
        lines = raw_prefix + "\n".join(json.dumps(e, ensure_ascii=False) for e in events)
        self.events.write_text(lines + "\n", encoding="utf-8")

    def test_block_1_done_last_7d(self):
        self.write_cards(
            _card("t-done-fresh", status="done", done_days_ago=2, created_days_ago=10),
            _card("t-done-old", status="done", done_days_ago=20, created_days_ago=30),
            _card("t-active", stage="todo", created_days_ago=1),
        )
        metrics = build_metrics(self.active, self.events, now=NOW)
        ids = [c["id"] for c in metrics["block_1_done_last_7d"]]
        self.assertEqual(ids, ["t-done-fresh"])

    def test_block_2_avg_age_in_progress(self):
        self.write_cards(
            _card("t-ip-10", stage="in-progress", created_days_ago=10),
            _card("t-ip-1", stage="in-progress", created_days_ago=1),
            _card("t-todo", stage="todo", created_days_ago=10),
        )
        metrics = build_metrics(self.active, self.events, now=NOW)
        self.assertEqual(metrics["block_2_in_progress_count"], 2)
        self.assertEqual(metrics["block_2_in_progress_avg_age_days"], 5.5)

    def test_block_3_older_than_7d(self):
        self.write_cards(
            _card("t-old-ip", stage="in-progress", created_days_ago=10),
            _card("t-old-todo", stage="todo", created_days_ago=8),
            _card("t-fresh", stage="test", created_days_ago=3),
            _card("t-done-long-ago", status="done", done_days_ago=15, created_days_ago=40),
        )
        metrics = build_metrics(self.active, self.events, now=NOW)
        ids = [c["id"] for c in metrics["block_3_older_than_7d"]]
        # закрытые карточки не считаются «старше 7 дней» — это блок только по активным
        self.assertEqual(ids, ["t-old-ip", "t-old-todo"])

    def test_block_4_transitions_by_author(self):
        fresh = NOW - timedelta(days=1)
        old = NOW - timedelta(days=10)
        self.write_events(
            _stage_event(fresh, "Sovereign", "t-1", "todo", "in-progress"),
            _stage_event(fresh, "Sovereign", "t-1", "in-progress", "test"),
            _stage_event(fresh, "ZCode", "t-2", "todo", "test"),
            _stage_event(old, "Sovereign", "t-3", "todo", "done"),  # вне окна — не считается
            _stage_event(fresh, "Sovereign", "t-4", "todo", "in-progress"),
            {"schema_id": "evo.log.event", "produced_by": "analytics_snapshot",
             "produced_at": _iso(fresh), "payload": {"kind": "snapshot.completed", "dir": "x"},
             "refs": {}, "ts": _iso(fresh)},  # другой kind — не переход
            {"schema_id": "evo.log.event", "produced_by": "x", "produced_at": _iso(fresh),
             "payload": {"kind": "task.stage", "id": "t-5", "from": "a", "to": "b"},
             "refs": {}, "ts": _iso(fresh)},
        )
        metrics = build_metrics(self.active, self.events, now=NOW)
        self.assertEqual(metrics["block_4_transitions_by_author"], {"Sovereign": 3, "ZCode": 1, "x": 1})
        self.assertEqual(metrics["block_4_transitions_total"], 5)
        last = metrics["block_4_transitions_log"][-1]
        self.assertEqual((last["id"], last["by"]), ("t-5", "x"))

    def test_block_4_history_fallback_without_journal(self):
        # журнал отсутствует: переходы считаются по fallбэку history[].by карточек
        card = _card("t-fb", stage="in-progress", created_days_ago=2)
        card["history"] = [
            {"stage": "todo", "at": _iso(NOW - timedelta(days=3)), "by": "Sovereign"},
            {"stage": "in-progress", "at": _iso(NOW - timedelta(days=1)), "by": "ZCode"},
            {"status": "done", "at": _iso(NOW - timedelta(hours=12)), "by": "Sovereign"},
            {"stage": "test", "at": _iso(NOW - timedelta(days=10)), "by": "Sovereign"},  # вне окна
            {"stage": "todo", "at": _iso(NOW - timedelta(days=1))},  # до эпохи подписей
            {"status": "archived", "at": _iso(NOW - timedelta(days=1))},  # не переход
        ]
        self.write_cards(card)
        metrics = build_metrics(self.active, self.tmp / "нет-журнала.jsonl", now=NOW)
        self.assertEqual(metrics["block_4_transitions_by_author"], {"Sovereign": 2, "ZCode": 1})
        self.assertEqual(metrics["block_4_transitions_total"], 3)
        self.assertEqual(metrics["block_4_fallback_count"], 3)
        self.assertEqual(metrics["block_4_transitions_log"][-1]["source"], "history")

    def test_block_4_fallback_dedupes_with_journal(self):
        # один и тот же переход есть и в журнале, и в history — считается один раз
        at = NOW - timedelta(days=1)
        card = _card("t-dup", stage="in-progress", created_days_ago=2)
        card["history"] = [{"stage": "in-progress", "at": _iso(at), "by": "Sovereign"}]
        self.write_cards(card)
        self.write_events(_stage_event(at, "Sovereign", "t-dup", "todo", "in-progress"))
        metrics = build_metrics(self.active, self.events, now=NOW)
        self.assertEqual(metrics["block_4_transitions_by_author"], {"Sovereign": 1})
        self.assertEqual(metrics["block_4_transitions_total"], 1)
        self.assertEqual(metrics["block_4_fallback_count"], 0)

    def test_tolerates_empty_journal_and_blank_lines(self):
        # ведущая пустая строка — норма формата записи Л-2 (write("\n"+line))
        self.write_events(_stage_event(NOW - timedelta(days=1), "Sovereign"), raw_prefix="\n")
        self.write_cards(_card("t-x", stage="in-progress", created_days_ago=2))
        metrics = build_metrics(self.active, self.events, now=NOW)
        self.assertEqual(metrics["block_4_transitions_by_author"], {"Sovereign": 1})
        # журнал вообще отсутствует — блок 4 пустой, падения нет
        metrics_no_log = build_metrics(self.active, self.tmp / "нет-такого.jsonl", now=NOW)
        self.assertEqual(metrics_no_log["block_4_transitions_by_author"], {})

    def test_envelope_valid_and_text_has_4_blocks(self):
        self.write_cards(
            _card("t-done", status="done", done_days_ago=1, created_days_ago=5),
            _card("t-ip", stage="in-progress", created_days_ago=9),
        )
        self.write_events(_stage_event(NOW - timedelta(days=1), "Sovereign"))
        metrics = build_metrics(self.active, self.events, now=NOW)
        envelope = build_envelope(metrics, self.active, self.events)
        self.assertEqual(envelope["schema_id"], "evo.kanban.metrics")
        self.assertEqual(validate_envelope(envelope), [], envelope)
        self.assertEqual(envelope["payload"], metrics)

        text = render_text(metrics)
        self.assertIn("1) Закрыто за 7 дней: 1", text)
        self.assertIn("2) Средний возраст карточек в in-progress: 9.0 дн.", text)
        self.assertIn("3) Карточки старше 7 дней: 1", text)
        self.assertIn("4) Переходы по авторам за 7 дней (всего 1):", text)
        self.assertIn("- Sovereign: 1", text)

    def test_real_active_dir_smoke(self):
        # на настоящих данных платформы: ничего не падает, все 4 блока присутствуют
        metrics = build_metrics(ROOT / "Memory" / "Engineering" / "Tasks" / "Active",
                                ROOT / "Workspace" / "logs" / "events.jsonl", now=NOW)
        for key in ("block_1_done_last_7d", "block_2_in_progress_avg_age_days",
                    "block_3_older_than_7d", "block_4_transitions_by_author"):
            self.assertIn(key, metrics)


if __name__ == "__main__":
    unittest.main()
