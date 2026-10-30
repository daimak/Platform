# -*- coding: utf-8 -*-
"""Статические проверки артефактов: JS дашборда, снапшот аналитики, задачи Barrymore."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # запуск из любого cwd
    sys.path.insert(0, str(ROOT))

DASHBOARD = ROOT / "eVo" / "dashboard"
SNAPSHOT = ROOT / "Workspace" / "analytics" / "2026-10-29"
ACTIVE_TASKS = ROOT / "Memory" / "Engineering" / "Tasks" / "Active"
ALLOWED_CATEGORIES = {"rent", "job", "service", "product", "other"}


def _node_available() -> bool:
    try:
        subprocess.run(["node", "--version"], capture_output=True, timeout=30)
        return True
    except (FileNotFoundError, OSError):
        return False


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@unittest.skipIf(not _node_available(), "node недоступен — проверка синтаксиса JS пропущена")
class TestDashboardJsSyntax(unittest.TestCase):
    """Каждый *.js в eVo/dashboard/ парсится node --check."""

    def test_all_js_parse(self):
        js_files = sorted(DASHBOARD.glob("*.js"))
        self.assertGreater(len(js_files), 0, f"В {DASHBOARD} не найдено *.js")
        for path in js_files:
            with self.subTest(file=path.name):
                proc = subprocess.run(["node", "--check", str(path)],
                                      capture_output=True, text=True, timeout=60)
                self.assertEqual(proc.returncode, 0,
                                 f"node --check провалился для {path.name}:\n{proc.stderr}")


class TestOlxStructured(unittest.TestCase):
    """olx_structured.json: 52 записи, допустимые категории, обязательные поля."""

    def test_records_shape(self):
        data = _load(SNAPSHOT / "olx_structured.json")
        records = data["records"]
        self.assertEqual(len(records), 52)
        for rec in records:
            for key in ("id", "category", "object"):
                self.assertIn(key, rec, f"Нет поля {key}: {rec}")

    def test_categories_whitelist(self):
        data = _load(SNAPSHOT / "olx_structured.json")
        categories = {rec.get("category") for rec in data["records"]}
        self.assertTrue(categories <= ALLOWED_CATEGORIES,
                        f"Недопустимые категории: {categories - ALLOWED_CATEGORIES}")


class TestOlxRaw(unittest.TestCase):
    """raw/olx_autoservices_data.json: 52 записи, title/url/description непустые."""

    def test_raw_records(self):
        records = _load(SNAPSHOT / "raw" / "olx_autoservices_data.json")
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), 52)
        for i, rec in enumerate(records, 1):
            for key in ("title", "url", "description"):
                value = str(rec.get(key, "")).strip()
                self.assertTrue(value, f"Запись #{i}: пустое поле {key}")


class TestActiveTasks(unittest.TestCase):
    """Memory/Engineering/Tasks/Active/*.json валидны по правилам task_store."""

    def test_all_active_tasks_valid(self):
        try:
            from tools.barrymore import task_store
        except ImportError:  # pragma: no cover — модуль всегда должен импортироваться
            self.fail("Не удалось импортировать tools/barrymore/task_store.py")
        files = sorted(ACTIVE_TASKS.glob("*.json"))
        self.assertGreater(len(files), 0, "Нет задач в Active/")
        for path in files:
            with self.subTest(task=path.name):
                try:
                    # _read_task проверяет id==имя файла, статус active/done,
                    # priority urgent/regular, title/createdAt/history (+date для done)
                    task = task_store._read_task(path)
                except (ValueError, KeyError, TypeError) as exc:
                    self.fail(f"Задача {path.name} не проходит валидацию task_store: {exc}")
                # явные инварианты из ТЗ
                self.assertEqual(task["id"], path.stem)
                self.assertIn(task["status"], ("active", "done"))
                self.assertIn(task["priority"], ("urgent", "regular"))


if __name__ == "__main__":
    unittest.main()
