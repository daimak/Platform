import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import hunter_store

SERVER_PATH = Path(__file__).with_name("dashboard-server.py")
SERVER_SPEC = importlib.util.spec_from_file_location("dashboard_server_hunter", SERVER_PATH)
dashboard_server = importlib.util.module_from_spec(SERVER_SPEC)
SERVER_SPEC.loader.exec_module(dashboard_server)


class HunterStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.inbox_path = Path(self.temp_dir.name) / "assignments.json"
        self.path_patch = patch.object(hunter_store, "INBOX_PATH", self.inbox_path)
        self.path_patch.start()

    def tearDown(self):
        self.path_patch.stop()
        self.temp_dir.cleanup()

    def test_create_assignment_persists_and_orders_latest_first(self):
        first = hunter_store.create_assignment({
            "category": "employment",
            "title": " Вакансии с быстрым выходом ",
            "details": "Удалённо",
        })
        second = hunter_store.create_assignment({
            "category": "quick-income",
            "title": "Разовые заказы",
        })

        self.assertEqual(first["title"], "Вакансии с быстрым выходом")
        self.assertEqual(second["category_label"], "Быстрый заработок")
        self.assertEqual(hunter_store.list_assignments(), [second, first])
        self.assertEqual(json.loads(self.inbox_path.read_text(encoding="utf-8")), [second, first])

    def test_assignment_validation_rejects_invalid_fields(self):
        for payload in (
            {"category": "unknown", "title": "Задача"},
            {"category": "employment", "title": " "},
            {"category": "employment", "title": "x" * 121},
            {"category": "employment", "title": "Задача", "details": 5},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                hunter_store.create_assignment(payload)

    def test_local_api_accepts_and_lists_assignments(self):
        server = dashboard_server.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            dashboard_server.DashboardHandler,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            request = Request(
                f"{base_url}/api/hunter/tasks",
                data=json.dumps({
                    "category": "organize",
                    "title": "Систематизировать вакансии",
                    "details": "Срок до первой выплаты и сложность",
                }).encode("utf-8"),
                headers={"Content-Type": "application/json", "Origin": base_url},
                method="POST",
            )
            with urlopen(request) as response:
                self.assertEqual(response.status, 201)
                created = json.loads(response.read())["task"]
            with urlopen(f"{base_url}/api/hunter/tasks") as response:
                listed = json.loads(response.read())["tasks"]
            self.assertEqual(listed, [created])

            invalid = Request(
                f"{base_url}/api/hunter/tasks",
                data=b'{"category":"invalid","title":"Bad"}',
                headers={"Content-Type": "application/json", "Origin": base_url},
                method="POST",
            )
            with self.assertRaises(HTTPError) as error:
                urlopen(invalid)
            self.assertEqual(error.exception.code, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
