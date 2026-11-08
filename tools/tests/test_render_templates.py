# -*- coding: utf-8 -*-
"""Тесты рендерера шаблонов с приватными переменными (Docs/TEMPLATING.md, E-053)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # запуск из любого cwd
    sys.path.insert(0, str(ROOT))

from tools.render_templates import load_vars, render_string  # noqa: E402


class TestLoadVars(unittest.TestCase):
    """load_vars: слияние JSON-переменных, отсутствие каталога = пустой словарь."""

    def test_missing_dir_is_empty(self):
        self.assertEqual(load_vars(Path(tempfile.mkdtemp()) / "нет-такого"), {})

    def test_merge_sorted_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "a-cloud.json").write_text('{"vm_user": "daimak", "a_only": 1}', encoding="utf-8")
            (d / "b-extra.json").write_text('{"vm_user": "переопределил"}', encoding="utf-8")
            merged = load_vars(d)
        self.assertEqual(merged, {"vm_user": "переопределил", "a_only": 1})

    def test_non_dict_json_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            p.write_text("[1, 2]", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_vars(p.parent)


class TestRenderString(unittest.TestCase):
    """render_string: подстановка, плейсхолдеры отсутствующих, repo-режим."""

    TEMPLATE = "ssh {{ vm_user }}@{{ vm_public_ip }} порт {{ tunnel_local_port }}"

    def test_substitutes_known_vars(self):
        out = render_string(self.TEMPLATE, {"vm_user": "daimak", "vm_public_ip": "203.0.113.7",
                                            "tunnel_local_port": 18765})
        self.assertEqual(out, "ssh daimak@203.0.113.7 порт 18765")

    def test_missing_var_becomes_placeholder(self):
        # отсутствующая переменная = <имя>, а не падение — основа repo-режима
        out = render_string(self.TEMPLATE, {"vm_user": "daimak"})
        self.assertEqual(out, "ssh daimak@<vm_public_ip> порт <tunnel_local_port>")

    def test_repo_mode_ignores_vars(self):
        # даже с полным набором переменных repo-артефакт не раскрывает значений
        full = {"vm_user": "daimak", "vm_public_ip": "203.0.113.7", "tunnel_local_port": 18765}
        out = render_string(self.TEMPLATE, full, repo_mode=True)
        self.assertEqual(out, "ssh <vm_user>@<vm_public_ip> порт <tunnel_local_port>")

    def test_no_secret_leak_in_repo_mode(self):
        # если в значении есть IP-подобная строка, repo-режим обязан её вычистить
        out = render_string("IP: {{ vm_public_ip }}", {"vm_public_ip": "158.160.152.181"}, repo_mode=True)
        self.assertNotIn("158.160", out)
        self.assertIn("<vm_public_ip>", out)

    def test_keep_trailing_newline(self):
        self.assertEqual(render_string("текст\n", {}), "текст\n")


if __name__ == "__main__":
    unittest.main()
