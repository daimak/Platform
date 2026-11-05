# -*- coding: utf-8 -*-
"""Мост Л-5 (Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md): подписи "by" канбана.

Сами тесты живут в tools/barrymore/test_task_store_by.py — рядом с task_store.py,
как и основной test_task_store.py. Этот файл не дублирует их, а подключает к
официальному прогону `python -m unittest discover -s tools/tests` (запуск из
любого cwd: корень репо и tools/barrymore добавляются в sys.path).
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BARRYMORE = ROOT / "tools" / "barrymore"
for _path in (str(ROOT), str(BARRYMORE)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from test_task_store_by import BySignatureTests, RealJournalIntegrationTests  # noqa: E402,F401

if __name__ == "__main__":
    unittest.main()
