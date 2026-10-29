import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import ai_usage

AGENT_PATH = Path(__file__).with_name("morning-brief-agent.py")
AGENT_SPEC = importlib.util.spec_from_file_location("morning_brief_agent", AGENT_PATH)
morning_brief_agent = importlib.util.module_from_spec(AGENT_SPEC)
AGENT_SPEC.loader.exec_module(morning_brief_agent)
SERVER_PATH = Path(__file__).with_name("dashboard-server.py")
SERVER_SPEC = importlib.util.spec_from_file_location("dashboard_server", SERVER_PATH)
dashboard_server = importlib.util.module_from_spec(SERVER_SPEC)
SERVER_SPEC.loader.exec_module(dashboard_server)


class AiUsageLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        ai_usage.DATA_DIR = Path(self.temp_dir.name)
        ai_usage.LEDGER_PATH = ai_usage.DATA_DIR / "usage.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ai_usage_review_prompt_requires_russian(self):
        self.assertIn("Пиши кратко по-русски", morning_brief_agent.AI_USAGE_SYSTEM_PROMPT)

    def test_records_provider_usage_and_unknown_cost_without_guessing(self):
        ai_usage.record_request(
            "freellmapi",
            "model-x",
            {"prompt_tokens": 12, "completion_tokens": 7, "total_tokens": 19},
            {},
            "Morning Brief",
            "Доклад по адресу user@example.com",
        )

        report = ai_usage.dashboard_data()
        request = report["requests"][0]
        self.assertEqual(request["total_tokens"], 19)
        self.assertIsNone(request["cost_amount"])
        self.assertEqual(request["cost_source"], "unavailable")
        self.assertNotIn("user@example.com", request["result_summary"])
        self.assertEqual(report["summary"]["total_tokens"], 19)
        self.assertEqual(report["summary"]["costs"], [])

    def test_openai_compatible_gateway_usage_is_recorded_without_prompt_content(self):
        response_data = {
            "model": "actual-model",
            "choices": [{"message": {"content": '{"summary":"Safe summary","nextStep":"Next"}'}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 7, "total_tokens": 19},
            "cost": {"amount": 0.0012, "currency": "USD"},
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps(response_data).encode()

        with patch.object(morning_brief_agent.urllib.request, "urlopen", return_value=FakeResponse()):
            result = morning_brief_agent.ask_brain(
                {"private_source": "this content must not be stored"},
                {"FREE_LLM_BASE_URL": "http://127.0.0.1:1/v1"},
            )

        record = ai_usage.dashboard_data()["requests"][0]
        self.assertEqual(result["model"], "actual-model")
        self.assertEqual(record["total_tokens"], 19)
        self.assertEqual(record["cost_amount"], 0.0012)
        self.assertEqual(record["cost_source"], "provider_response")
        self.assertNotIn("private_source", json.dumps(record))
        self.assertEqual(record["result_summary"], "Доклад сформирован")

    def test_manual_snapshot_and_provider_adapter_extensibility(self):
        snapshot = ai_usage.add_snapshot({
            "provider_id": "new-model-service",
            "provider_name": "New Model Service",
            "credits_used_percent": 51,
            "period": "October",
            "note": "User-reported snapshot",
        })

        report = ai_usage.dashboard_data()
        self.assertEqual(snapshot["source"], "manual")
        self.assertEqual(report["snapshots"][0]["provider_name"], "New Model Service")
        self.assertIn(
            ("new-model-service", "New Model Service"),
            report["custom_providers"],
        )

    def test_barrymore_summary_excludes_its_own_calls_to_keep_fingerprint_stable(self):
        ai_usage.record_request("freellmapi", "model-x", {}, {}, "Morning Brief", "ok")
        ai_usage.record_request("freellmapi", "model-x", {}, {}, "AI usage review", "ok")
        ai_usage.record_request("freellmapi", "model-x", {}, {}, "Other task", "ok")

        self.assertEqual(ai_usage.data_for_barrymore()["request_count"], 1)

    def test_opt_in_is_persisted_and_input_is_validated(self):
        self.assertFalse(ai_usage.settings()["include_in_morning_brief"])
        ai_usage.set_include_in_morning_brief(True)
        self.assertTrue(ai_usage.settings()["include_in_morning_brief"])
        with self.assertRaises(ValueError):
            ai_usage.set_include_in_morning_brief("yes")
        with self.assertRaises(ValueError):
            ai_usage.add_snapshot({"provider_id": "github-copilot", "credits_used_percent": 101})

    def test_dashboard_api_and_page_are_local_and_accept_manual_snapshot(self):
        server = dashboard_server.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            dashboard_server.DashboardHandler,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(f"{base_url}/ai-usage.html") as response:
                self.assertEqual(response.status, 200)
                self.assertIn("ПЕСОЧНИЦА ИИ".encode("utf-8"), response.read())

            with urlopen(f"{base_url}/AI-SANDBOX-HISTORY.md") as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.geturl(), f"{base_url}/ai-sandbox-history.html")
                self.assertIn("charset=utf-8", response.headers["Content-Type"])
                self.assertIn("СВЕДЕНИЯ ОБ АВТОРСТВЕ".encode("utf-8"), response.read())

            with urlopen(f"{base_url}/ai-sandbox-history.html") as response:
                self.assertEqual(response.status, 200)
                self.assertIn("text/html", response.headers["Content-Type"])
                self.assertIn("charset=utf-8", response.headers["Content-Type"])
                self.assertIn("История участия ИИ".encode("utf-8"), response.read())

            payload = {
                "provider_id": "github-copilot",
                "credits_used_percent": 51,
                "period": "October 2026",
            }
            request = Request(
                f"{base_url}/api/ai-usage/snapshots",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Origin": base_url,
                },
                method="POST",
            )
            with urlopen(request) as response:
                self.assertEqual(response.status, 201)

            with urlopen(f"{base_url}/api/ai-usage") as response:
                report = json.loads(response.read())
            self.assertEqual(report["snapshots"][0]["credits_used_percent"], 51)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_usage_write_rejects_non_dashboard_origin(self):
        server = dashboard_server.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            dashboard_server.DashboardHandler,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            request = Request(
                f"{base_url}/api/ai-usage/settings",
                data=b'{"include_in_morning_brief":true}',
                headers={
                    "Content-Type": "application/json",
                    "Origin": "http://example.invalid",
                },
                method="POST",
            )
            with self.assertRaises(HTTPError) as error:
                urlopen(request)
            self.assertEqual(error.exception.code, 403)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
