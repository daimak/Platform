import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import security_contour

SERVER_PATH = Path(__file__).with_name("dashboard-server.py")
SERVER_SPEC = importlib.util.spec_from_file_location("dashboard_server_security", SERVER_PATH)
dashboard_server = importlib.util.module_from_spec(SERVER_SPEC)
SERVER_SPEC.loader.exec_module(dashboard_server)


class SecurityContourTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        security_contour.DATA_DIR = Path(self.temp_dir.name) / "audit"
        security_contour.AUDIT_PATH = security_contour.DATA_DIR / "audit.json"
        security_contour.TARGETS_PATH = Path(self.temp_dir.name) / "targets.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_targets(self, targets, llm_analysis=False):
        security_contour.TARGETS_PATH.write_text(
            json.dumps({"schema_version": 1, "llm_analysis": llm_analysis, "targets": targets}, ensure_ascii=False),
            encoding="utf-8",
        )

    def test_missing_or_empty_allowlist_denies_every_host(self):
        with self.assertRaises(PermissionError):
            security_contour.run_check("example.com")
        self._write_targets([])
        with self.assertRaises(PermissionError):
            security_contour.run_check("example.com")

    def test_config_validation_rejects_bad_entries(self):
        self._write_targets([{"host": "bad host!"}])
        with self.assertRaises(ValueError):
            security_contour.load_config()
        self._write_targets([{"host": "ok.example", "scheme": "ftp"}])
        with self.assertRaises(ValueError):
            security_contour.load_config()

    def test_header_and_cookie_analysis_keeps_values_out(self):
        analysis = security_contour._analyze_headers([
            ("Content-Type", "text/html"),
            ("Strict-Transport-Security", "max-age=63072000"),
            ("Server", "nginx/1.24"),
        ])
        self.assertIn("strict-transport-security", analysis["present"])
        self.assertIn("content-security-policy", analysis["missing"])
        self.assertEqual(analysis["server_banner"], "nginx/1.24")

        cookies = security_contour._analyze_cookies([
            "sid=SECRETVALUE12345; Path=/; HttpOnly",
            "tracker=abc123; Secure; SameSite=Lax",
        ])
        serialized = json.dumps(cookies)
        self.assertNotIn("SECRETVALUE12345", serialized)
        self.assertNotIn("abc123", serialized)
        self.assertTrue(cookies[0]["http_only"])
        self.assertFalse(cookies[0]["secure"])
        self.assertTrue(cookies[1]["secure"])
        self.assertEqual(cookies[1]["same_site"], "lax")

    def test_llm_reply_parsing_variants(self):
        fenced = (
            "```json\n"
            '{"summary": "Ок", "findings": [{"severity": "high", "title": "Нет HSTS", "detail": "d"}], "nextStep": "Включить"}'
            "\n```"
        )
        parsed = security_contour._parse_llm_reply(fenced, "test-model")
        self.assertEqual(parsed["findings"][0]["severity"], "high")
        self.assertEqual(parsed["next_step"], "Включить")

        plain = security_contour._parse_llm_reply("Просто текст без JSON", "test-model")
        self.assertEqual(plain["findings"], [])
        self.assertIn("Просто текст", plain["summary"])

    def test_llm_prompt_is_russian_and_json_only(self):
        self.assertIn("Защищённого контура", security_contour.SECURITY_SYSTEM_PROMPT)
        self.assertIn("СТРОГО в JSON", security_contour.SECURITY_SYSTEM_PROMPT)

    def test_isolation_status_reports_bind_and_probe_mode(self):
        loopback = security_contour.isolation_status(("127.0.0.1", 8765), probe_external=False)
        self.assertTrue(loopback["loopback_only"])
        self.assertIsNone(loopback["external_probe"])

        exposed = security_contour.isolation_status(("0.0.0.0", 8765), probe_external=False)
        self.assertFalse(exposed["loopback_only"])

    def test_audit_events_are_capped_and_summarized(self):
        original_cap = security_contour.MAX_EVENTS
        security_contour.MAX_EVENTS = 3
        try:
            for index in range(5):
                security_contour.audit_event("external-check", {"host": f"host{index}.example", "status": 200})
            summary = security_contour.audit_summary()
        finally:
            security_contour.MAX_EVENTS = original_cap
        self.assertEqual(summary["event_count"], 3)
        self.assertEqual(summary["last"]["host"], "host4.example")

    def test_security_endpoints_local_status_and_manual_check(self):
        server = dashboard_server.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            dashboard_server.DashboardHandler,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        target_host = f"127.0.0.1:{server.server_port}"
        self._write_targets([{"host": target_host, "scheme": "http", "note": "loopback test"}])
        try:
            with urlopen(f"{base_url}/api/security/status") as response:
                status = json.loads(response.read())
            self.assertTrue(status["isolation"]["loopback_only"])
            self.assertEqual(status["targets"][0]["host"], target_host)
            self.assertFalse(status["llm_analysis"])

            denied = Request(
                f"{base_url}/api/security/check",
                data=json.dumps({"host": "example.com"}).encode(),
                headers={"Content-Type": "application/json", "Origin": base_url},
                method="POST",
            )
            with self.assertRaises(HTTPError) as error:
                urlopen(denied)
            self.assertEqual(error.exception.code, 403)

            request = Request(
                f"{base_url}/api/security/check",
                data=json.dumps({"host": target_host}).encode(),
                headers={"Content-Type": "application/json", "Origin": base_url},
                method="POST",
            )
            with urlopen(request) as response:
                payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            facts = payload["facts"]
            self.assertEqual(facts["status"], 200)
            self.assertIsNone(facts["error"])
            self.assertIsNone(payload["llm"])
            self.assertTrue(payload["audit_event_id"].startswith("sec-"))
            self.assertIn("strict-transport-security", facts["headers"]["missing"])

            summary = security_contour.audit_summary()
            self.assertEqual(summary["event_count"], 1)
            self.assertEqual(summary["last"]["host"], target_host)
            self.assertFalse(summary["last"]["llm_used"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_add_target_appends_dedupes_and_validates(self):
        targets = security_contour.add_target({"host": "192.168.1.10:8080", "scheme": "http", "note": "lab"})
        self.assertEqual(targets[0], {"host": "192.168.1.10:8080", "scheme": "http", "note": "lab"})
        with self.assertRaises(ValueError):
            security_contour.add_target({"host": "192.168.1.10:8080", "scheme": "http"})
        with self.assertRaises(ValueError):
            security_contour.add_target({"host": "bad host!"})
        with self.assertRaises(ValueError):
            security_contour.add_target({"host": "example.com:99999"})
        with self.assertRaises(ValueError):
            security_contour.add_target({"host": "example.com", "scheme": "ftp"})
        data = json.loads(security_contour.TARGETS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(data["targets"]), 1)

        security_contour.TARGETS_PATH.unlink()
        security_contour.add_target({"host": "lab.example"})
        data = json.loads(security_contour.TARGETS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(data["targets"]), 1)
        self.assertEqual(data["schema_version"], 1)

    def test_security_targets_endpoint_adds_and_validates(self):
        server = dashboard_server.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            dashboard_server.DashboardHandler,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            request = Request(
                f"{base_url}/api/security/targets",
                data=json.dumps({"host": "127.0.0.1", "scheme": "http", "note": "added via api"}).encode(),
                headers={"Content-Type": "application/json", "Origin": base_url},
                method="POST",
            )
            with urlopen(request) as response:
                self.assertEqual(response.status, 201)
                targets = json.loads(response.read())["targets"]
            self.assertEqual(targets[0]["host"], "127.0.0.1")

            duplicate = Request(
                f"{base_url}/api/security/targets",
                data=json.dumps({"host": "127.0.0.1", "scheme": "http"}).encode(),
                headers={"Content-Type": "application/json", "Origin": base_url},
                method="POST",
            )
            with self.assertRaises(HTTPError) as error:
                urlopen(duplicate)
            self.assertEqual(error.exception.code, 400)

            with urlopen(f"{base_url}/api/security/status") as response:
                status = json.loads(response.read())
            self.assertEqual(status["targets"][0]["note"], "added via api")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
