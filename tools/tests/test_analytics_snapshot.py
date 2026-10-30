# -*- coding: utf-8 -*-
"""Тесты tools/analytics_snapshot.py (stdlib-only). Фикстуры — только во временных каталогах."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # запуск из любого cwd
    sys.path.insert(0, str(ROOT))

from tools import analytics_snapshot as m  # noqa: E402

BOM = b"\xef\xbb\xbf"


class TempDirTest(unittest.TestCase):
    """Базовый класс: временный каталог, автоматически удаляемый после теста."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)


class TestParseK(unittest.TestCase):
    """parse_k: «38.2K» -> 38200, «1,5K» -> 1500, «700» -> 700."""

    def test_k_with_dot(self):
        self.assertEqual(int(m.parse_k("38.2K")), 38200)

    def test_k_with_comma(self):
        # запятая как десятичный разделитель
        self.assertEqual(int(m.parse_k("1,5K")), 1500)

    def test_plain_number(self):
        self.assertEqual(int(m.parse_k("700")), 700)


class TestBuildJobs(TempDirTest):
    """build_jobs: CSV с header + BOM utf-8-sig, чанки заданного размера."""

    SAMPLE = [
        {"source": "hh", "title": "Python-разработчик", "company": "ООО «Ромашка»",
         "location": "Ташкент", "salary": "2000 у.е.", "date": "2026-10-29",
         "url": "https://example.com/1", "snippet": "Знание Django, FastAPI; юникод: ў, ҳ, қ"},
        {"source": "olx", "title": "Backend engineer", "company": None,
         "location": "", "salary": None, "date": "2026-10-28",
         "url": "https://example.com/2", "snippet": ""},
        {"source": "hh", "title": "Data Analyst", "company": "Acme",
         "location": "Ташкент", "salary": None, "date": None,
         "url": "https://example.com/3", "snippet": "SQL и аналитика"},
    ]

    def setUp(self):
        super().setUp()
        self.day = self.tmp / "snap"
        # snapshot_dir() в реальном прогоне создаёт raw/ и chunks/ до build_jobs
        (self.day / "raw").mkdir(parents=True)
        (self.day / "chunks").mkdir()
        # маленький фиктивный JSON с юникодом — вместо реального job_search_results.json
        (self.day / "raw" / "job_search_results.json").write_text(
            json.dumps(self.SAMPLE, ensure_ascii=False), encoding="utf-8")

    def test_build_jobs(self):
        old_chunk = m.JOBS_CHUNK_SIZE
        m.JOBS_CHUNK_SIZE = 2  # переопределяем размер чанка через атрибут модуля
        try:
            info = m.build_jobs(self.day)
        finally:
            m.JOBS_CHUNK_SIZE = old_chunk

        self.assertEqual(info["count"], 3)
        self.assertEqual(info["unique_urls"], 3)

        # CSV: BOM utf-8-sig, 4 строки (header + 3 записи), юникод сохранён
        raw_bytes = (self.day / "jobs.csv").read_bytes()
        self.assertTrue(raw_bytes.startswith(BOM), "CSV должен начинаться с BOM utf-8-sig")
        with open(self.day / "jobs.csv", newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0][:3], ["idx", "source", "title"])
        self.assertEqual(rows[1][0], "1")
        self.assertEqual(rows[1][2], "Python-разработчик")
        self.assertEqual(rows[1][8], self.SAMPLE[0]["snippet"])

        # чанки: 3 записи при размере 2 -> 2 файла (2 + 1 запись)
        self.assertEqual(info["chunks"], ["jobs-01.md", "jobs-02.md"])
        sizes = []
        for name in info["chunks"]:
            text = (self.day / "chunks" / name).read_text(encoding="utf-8")
            sizes.append(sum(1 for ln in text.splitlines() if ln.startswith("## #")))
        self.assertEqual(sizes, [2, 1])


class TestBuildTokens(TempDirTest):
    """build_tokens: фиктивный TOKEN_USAGE_LOG.md во временном каталоге,
    TOKEN_LOG подменяется; 2 ответа + 2 запроса FreeLLMAPI -> 4 строки данных."""

    LOG = (
        "# Логирование использования токенов\n\n"
        "### Ответ 1\n"
        "- **Дата и время**: 29.10.2026, 18:06\n"
        "- **Расход токенов**: 1500\n"
        "- **Контекст**: Анализ файлов Barrymore.md; юникод: ў, қ.\n\n"
        "### Ответ 2\n"
        "- **Дата и время**: 29.10.2026, 18:11\n"
        "- **Расход токенов**: 136\n"
        "- **Контекст**: Проверка формата лога.\n\n"
        "### Запросы FreeLLMAPI (детализация по обращениям)\n\n"
        "#### Запрос: 18:35:32\n"
        "- **Модель**: mistral-code-latest\n"
        "- **Входной контекст (Prompt)**: 38.2K токенов\n"
        "- **Выходные токены (Completion)**: 536 токенов\n"
        "- **Время ответа**: 5900 мс\n\n"
        "#### Запрос: 18:37:00\n"
        "- **Модель**: mistral-code-latest\n"
        "- **Входной контекст (Prompt)**: 1,5K токенов\n"
        "- **Выходные токены (Completion)**: 35 токенов\n"
        "- **Время ответа**: 4082 мс\n"
    )

    def setUp(self):
        super().setUp()
        self.day = self.tmp / "snap"
        self.day.mkdir()
        fake_log = self.tmp / "TOKEN_USAGE_LOG.md"
        fake_log.write_text(self.LOG, encoding="utf-8")

    def test_build_tokens(self):
        old_log = m.TOKEN_LOG
        m.TOKEN_LOG = self.tmp / "TOKEN_USAGE_LOG.md"  # monkeypatch модульной константы
        try:
            info = m.build_tokens(self.day)
        finally:
            m.TOKEN_LOG = old_log

        # счётчики: 2 ответа codex + 2 вызова FreeLLMAPI
        self.assertEqual(info, {"codex_answers": 2, "freellm_calls": 2})

        # CSV: BOM utf-8-sig, header + 4 строки данных; раскладка 8 колонок
        # (после фикса: kind, item, time, model, prompt, completion, latency, context)
        raw_bytes = (self.day / "token_usage.csv").read_bytes()
        self.assertTrue(raw_bytes.startswith(BOM), "CSV должен начинаться с BOM utf-8-sig")
        with open(self.day / "token_usage.csv", newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        header = ["kind", "item", "time", "model", "prompt_tokens",
                  "completion_tokens", "latency_ms", "context"]
        self.assertEqual(rows[0], header)
        self.assertEqual(len(rows), 5, "header + 4 строки данных")
        self.assertTrue(all(len(r) == len(header) for r in rows),
                        "все строки выровнены по заголовку")
        kinds = [r[0] for r in rows[1:]]
        self.assertEqual(kinds, ["codex-tui", "codex-tui", "freellm-api", "freellm-api"])

        # ответ codex: item, время, токены, контекст на своих местах
        self.assertEqual(rows[1][1], "ответ 1")
        self.assertEqual(rows[1][2], "29.10.2026, 18:06")
        self.assertEqual(rows[1][5], "1500")
        self.assertIn("ў, қ", rows[1][7])

        # freellm-строка: время, модель, prompt (38.2K -> 38200), completion, latency
        self.assertEqual(rows[3][2], "18:35:32")
        self.assertEqual(rows[3][3], "mistral-code-latest")
        self.assertEqual(rows[3][4], "38200")   # «38.2K токенов» -> 38200
        self.assertEqual(rows[3][5], "536")
        self.assertEqual(rows[3][6], "5900 мс")
        self.assertEqual(rows[4][3], "mistral-code-latest")
        self.assertEqual(rows[4][4], "1500")    # «1,5K токенов» -> 1500


class TestSnapshotDir(TempDirTest):
    """snapshot_dir: создаёт папку дня с raw/ и chunks/ (Workspace-путь подменяем)."""

    def test_snapshot_dir(self):
        old_analytics = m.ANALYTICS
        m.ANALYTICS = self.tmp / "analytics"  # подмена Workspace-пути на временный каталог
        try:
            d = m.snapshot_dir("2099-01-02")
            self.assertEqual(d.parent, self.tmp / "analytics")
            self.assertEqual(d.name, "2099-01-02")
            self.assertTrue((d / "raw").is_dir())
            self.assertTrue((d / "chunks").is_dir())
            # повторный вызов не падает (exist_ok=True); тоже под патчем,
            # чтобы не создавать каталоги в реальном Workspace/
            d2 = m.snapshot_dir("2099-01-02")
            self.assertEqual(d2, d)
        finally:
            m.ANALYTICS = old_analytics


if __name__ == "__main__":
    unittest.main()
