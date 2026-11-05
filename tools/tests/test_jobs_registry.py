# -*- coding: utf-8 -*-
"""Тесты реестра джобов (Лейн Л-3): валидация jobs.json и функций состояния.

Живой сервер 8765 не поднимается (рестарт — только с санкции Sovereign):
обработчики проверяются unittest-уровнем через вызов модульных функций.
"""
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # запуск из любого cwd
    sys.path.insert(0, str(ROOT))

from tools.lib.envelope import validate_envelope  # noqa: E402

SERVER_PATH = ROOT / "tools" / "barrymore" / "dashboard-server.py"
JOBS_JSON = ROOT / "tools" / "ops" / "jobs.json"

_SERVER_MODULE = None


def _server_module():
    """Ленивая одноразовая загрузка dashboard-server.py (имя с дефисом — через importlib)."""
    global _SERVER_MODULE
    if _SERVER_MODULE is None:
        barrymore = ROOT / "tools" / "barrymore"
        if str(barrymore) not in sys.path:
            sys.path.insert(0, str(barrymore))
        spec = importlib.util.spec_from_file_location("dashboard_server_testee", SERVER_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _SERVER_MODULE = module
    return _SERVER_MODULE


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _patch_paths(self, module, registry=None, state=None):
        if registry is not None:
            original = module.JOBS_REGISTRY_PATH
            module.JOBS_REGISTRY_PATH = registry
            self.addCleanup(setattr, module, "JOBS_REGISTRY_PATH", original)
        if state is not None:
            original = module.JOBS_STATE_PATH
            module.JOBS_STATE_PATH = state
            self.addCleanup(setattr, module, "JOBS_STATE_PATH", original)


class TestJobsJson(TempDirTest):
    """jobs.json: 3 записи, уникальные id, обязательные поля, корректные типы."""

    def test_registry_shape(self):
        raw = json.loads(JOBS_JSON.read_text(encoding="utf-8"))
        self.assertIsInstance(raw, list)
        self.assertEqual(len(raw), 3, "по ТЗ Л-3 в реестре три джоба")
        ids = [job.get("id") for job in raw]
        self.assertEqual(len(set(ids)), len(ids), f"id должны быть уникальны: {ids}")
        for job in raw:
            with self.subTest(job=job.get("id")):
                for field in ("id", "title", "owner", "cmd", "cwd", "timeout_s", "report_hint", "enabled"):
                    self.assertIn(field, job)
                self.assertIsInstance(job["cmd"], list)
                self.assertTrue(all(isinstance(arg, str) and arg for arg in job["cmd"]))
                self.assertIsInstance(job["enabled"], bool)
                self.assertIsInstance(job["timeout_s"], int)
                self.assertGreater(job["timeout_s"], 0)

    def test_expected_jobs_present(self):
        raw = json.loads(JOBS_JSON.read_text(encoding="utf-8"))
        ids = {job["id"] for job in raw}
        self.assertEqual(ids, {"analytics-snapshot", "token-meter", "healthcheck"})
        by_id = {job["id"]: job for job in raw}
        # фактические пути сверены с файлами: token_meter.py и healthcheck.py запускаются без аргументов
        self.assertEqual(by_id["analytics-snapshot"]["cmd"], ["python", "tools/analytics_snapshot.py"])
        self.assertEqual(by_id["token-meter"]["cmd"], ["python", "tools/ops/token_meter.py"])
        self.assertEqual(by_id["healthcheck"]["cmd"], ["python", "tools/ops/healthcheck.py"])
        self.assertTrue(all(job["enabled"] for job in raw))

    def test_registry_commands_point_to_existing_files(self):
        raw = json.loads(JOBS_JSON.read_text(encoding="utf-8"))
        for job in raw:
            script = ROOT / job["cmd"][1]
            self.assertTrue(script.is_file(), f"{job['id']}: файл не найден: {script}")


class TestJobStateFunctions(TempDirTest):
    """Функции состояния: конверт evo.ops.job_state, маркер «джоб уже запущен»."""

    def test_job_is_running_marker(self):
        module = _server_module()
        self.assertFalse(module._job_is_running(None))
        self.assertFalse(module._job_is_running({}))
        self.assertFalse(module._job_is_running({"started_at": None, "finished_at": None}))
        self.assertTrue(module._job_is_running({"started_at": "2026-11-05T00:00:00Z", "finished_at": None}))
        self.assertFalse(
            module._job_is_running({"started_at": "2026-11-05T00:00:00Z", "finished_at": "2026-11-05T00:01:00Z"})
        )

    def test_state_roundtrip_envelope(self):
        module = _server_module()
        state_path = self.tmp / "jobs_state.json"
        self._patch_paths(module, state=state_path)
        self.assertEqual(module._load_jobs_state(), {})
        module._save_jobs_state({"analytics-snapshot": {"started_at": "2026-11-05T00:00:00Z"}})
        on_disk = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["schema_id"], "evo.ops.job_state")
        self.assertEqual(validate_envelope(on_disk), [], on_disk)
        self.assertEqual(
            module._load_jobs_state(),
            {"analytics-snapshot": {"started_at": "2026-11-05T00:00:00Z"}},
        )

    def test_broken_state_file_is_empty(self):
        module = _server_module()
        state_path = self.tmp / "jobs_state.json"
        state_path.write_text("{битый json", encoding="utf-8")
        self._patch_paths(module, state=state_path)
        self.assertEqual(module._load_jobs_state(), {})

    def test_snapshot_filters_and_attaches_last_run(self):
        module = _server_module()
        registry = self.tmp / "jobs.json"
        registry.write_text(json.dumps([
            {"id": "job-on", "title": "Вкл", "owner": "Sovereign", "cmd": ["python", "-c", "print()"],
             "cwd": ".", "timeout_s": 60, "report_hint": "-", "enabled": True},
            {"id": "job-off", "title": "Выкл", "owner": "Sovereign", "cmd": ["python", "-c", "print()"],
             "cwd": ".", "timeout_s": 60, "report_hint": "-", "enabled": False},
        ], ensure_ascii=False), encoding="utf-8")
        state_path = self.tmp / "jobs_state.json"
        envelope = {
            "schema_id": "evo.ops.job_state", "schema_version": 1, "produced_by": "test",
            "produced_at": "2026-11-05T00:00:00Z",
            "payload": {"job-on": {"started_at": "2026-11-05T00:00:00Z", "finished_at": "2026-11-05T00:01:00Z",
                                   "exit_code": 0, "duration_s": 60.0}},
            "refs": {},
        }
        state_path.write_text(json.dumps(envelope), encoding="utf-8")
        self._patch_paths(module, registry=registry, state=state_path)

        default_view = module.jobs_snapshot(include_all=False)
        self.assertEqual([j["id"] for j in default_view["jobs"]], ["job-on"])
        self.assertEqual(default_view["jobs"][0]["last_run"]["exit_code"], 0)
        self.assertFalse(default_view["jobs"][0]["running"])

        full_view = module.jobs_snapshot(include_all=True)
        self.assertEqual([j["id"] for j in full_view["jobs"]], ["job-on", "job-off"])
        self.assertIsNone(full_view["jobs"][1]["last_run"])


class TestStartJob(TempDirTest):
    """start_job: 404 на неизвестный id, 409 на уже идущий, 202 + финальный state на запуск."""

    def test_unknown_job_404(self):
        module = _server_module()
        status, response = module.start_job("no-such-job")
        self.assertEqual(status, 404)
        self.assertIn("no-such-job", response["error"])

    def test_running_job_409(self):
        module = _server_module()
        state_path = self.tmp / "jobs_state.json"
        envelope = {
            "schema_id": "evo.ops.job_state", "schema_version": 1, "produced_by": "test",
            "produced_at": "2026-11-05T00:00:00Z",
            "payload": {"analytics-snapshot": {"started_at": "2026-11-05T00:00:00Z",
                                               "finished_at": None, "exit_code": None, "duration_s": None}},
            "refs": {},
        }
        state_path.write_text(json.dumps(envelope), encoding="utf-8")
        self._patch_paths(module, state=state_path)
        status, response = module.start_job("analytics-snapshot")
        self.assertEqual(status, 409)
        self.assertIn("уже выполняется", response["error"])

    def test_start_real_process_finishes(self):
        module = _server_module()
        registry = self.tmp / "jobs.json"
        registry.write_text(json.dumps([
            {"id": "echo-job", "title": "Эхо", "owner": "test", "timeout_s": 60,
             "cmd": [sys.executable, "-c", "print('ok')"], "cwd": ".",
             "report_hint": "-", "enabled": True},
        ], ensure_ascii=False), encoding="utf-8")
        state_path = self.tmp / "jobs_state.json"
        self._patch_paths(module, registry=registry, state=state_path)

        status, response = module.start_job("echo-job")
        self.assertEqual(status, 202)
        self.assertTrue(response["started"])
        self.assertTrue(response["started_at"].endswith("Z"))

        deadline = time.monotonic() + 15
        payload = module._load_jobs_state()
        while time.monotonic() < deadline and not (payload.get("echo-job") or {}).get("finished_at"):
            time.sleep(0.1)
            payload = module._load_jobs_state()
        entry = payload.get("echo-job")
        self.assertIsNotNone(entry, "поток-наблюдатель не записал финальный state за 15 с")
        self.assertEqual(entry["exit_code"], 0)
        self.assertTrue(entry["finished_at"].endswith("Z"))
        self.assertIsInstance(entry["duration_s"], float)
        self.assertEqual(entry["started_at"], response["started_at"])

        # после завершения маркер «уже запущен» снят
        self.assertFalse(module._job_is_running(entry))


if __name__ == "__main__":
    unittest.main()
