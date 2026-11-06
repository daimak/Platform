# -*- coding: utf-8 -*-
"""Тесты агрегации «Флот в море» (ТЗ Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md).

Живой сервер 8765 не поднимается (рестарт — только с санкции Sovereign):
агрегаты GET /api/agents/live и /api/agents/history проверяются unittest-уровнем
через вызов модульных функций на синтетическом events.jsonl.
"""
import importlib.util
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # запуск из любого cwd
    sys.path.insert(0, str(ROOT))

SERVER_PATH = ROOT / "tools" / "barrymore" / "dashboard-server.py"

_SERVER_MODULE = None


def _server_module():
    """Ленивая одноразовая загрузка dashboard-server.py (имя с дефисом — через importlib)."""
    global _SERVER_MODULE
    if _SERVER_MODULE is None:
        barrymore = ROOT / "tools" / "barrymore"
        if str(barrymore) not in sys.path:
            sys.path.insert(0, str(barrymore))
        spec = importlib.util.spec_from_file_location("dashboard_server_testee_agents", SERVER_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _SERVER_MODULE = module
    return _SERVER_MODULE


def _ts(minute: int, second: int = 0) -> str:
    """Фиксированный момент журнала: 2026-11-05T10:MM:SSZ (синтетика, не системные часы)."""
    return f"2026-11-05T10:{minute:02d}:{second:02d}Z"


def _envelope(produced_by: str, minute: int, kind: str, second: int = 0, **payload) -> dict:
    """Конверт журнала в формате tools/lib/log_event.py (schema evo.log.event)."""
    return {
        "schema_id": "evo.log.event",
        "schema_version": 1,
        "produced_by": produced_by,
        "produced_at": _ts(minute, second),
        "payload": {"kind": kind, **payload},
        "refs": {},
        "ts": _ts(minute, second),
    }


def _moment(minute: int, second: int = 0) -> datetime:
    return datetime(2026, 11, 5, 10, minute, second, tzinfo=timezone.utc)


class AgentsLogTestBase(unittest.TestCase):
    """Базовый класс: временный журнал + ленивый модуль сервера."""

    def setUp(self):
        self._tmp_import = _server_module()
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.log = self.tmp / "events.jsonl"

    def write_log(self, envelopes: list, extra_lines: list | None = None) -> None:
        """Записать синтетический журнал (+ произвольные чужие строки, если заданы)."""
        lines = [json.dumps(envelope, ensure_ascii=False) for envelope in envelopes]
        lines.extend(extra_lines or [])
        self.log.write_text("\n".join(lines), encoding="utf-8")

    def live(self, minute: int, second: int = 0) -> dict:
        module = _server_module()
        return module.agents_live_snapshot(log_path=self.log, now=_moment(minute, second))

    def history(self, limit: int = 20) -> dict:
        module = _server_module()
        return module.agents_history_snapshot(limit=limit, log_path=self.log)


class TestAgentsLive(AgentsLogTestBase):
    """GET /api/agents/live: агрегат активных рейсов."""

    def test_ship_in_sea_with_lanes(self):
        """Море: started + 2 лейна из 4 + свежий пульс; лейны, ETA, пульс, лента."""
        self.write_log([
            _envelope("Строитель-1", 0, "agent.started", task="Построить док",
                      lanes_total=4, spec="Docs/plan.md"),
            _envelope("Строитель-1", 5, "agent.lane", lane="Л-1", files=["a.py"]),
            _envelope("Строитель-1", 10, "agent.lane", lane="Л-2", files=["b.py"]),
            _envelope("Строитель-1", 15, "agent.pulse", step="половина доков"),
        ])
        snapshot = self.live(minute=17, second=0)
        ships = snapshot["ships"]
        self.assertEqual(len(ships), 1)
        ship = ships[0]
        self.assertEqual(ship["by"], "Строитель-1")
        self.assertEqual(ship["task"], "Построить док")
        self.assertEqual(ship["status"], "море")
        self.assertEqual(ship["lanes"], {"done": 2, "total": 4})
        self.assertEqual(ship["storms"], 0)
        self.assertEqual(ship["started_at"], _ts(0))
        self.assertAlmostEqual(ship["pulse_min"], 2.0, delta=0.01)
        self.assertAlmostEqual(ship["elapsed_min"], 17.0, delta=0.01)
        self.assertEqual(ship["pulse_status"], "идёт")
        # ETA-оценка по фактической скорости лейнов: лейны закрыты на 5-й и 10-й
        # минуте → 5 мин/лейн → на 2 оставшихся ~10 мин (значок «~» рисует UI)
        self.assertAlmostEqual(ship["eta_min"], 10.0, delta=0.01)
        self.assertEqual([event["kind"] for event in ship["events_recent"]],
                         ["agent.started", "agent.lane", "agent.lane", "agent.pulse"])

    def test_storm_by_storm_event_without_finished(self):
        """Шторм: storm-событие в незавершённом рейсе — статус шторм, счётчик растёт."""
        self.write_log([
            _envelope("Буре-1", 0, "agent.started", task="Рейскан"),
            _envelope("Буре-1", 5, "agent.storm", reason="concurrency-лимит"),
            _envelope("Буре-1", 6, "agent.pulse", step="после шторма"),
        ])
        ship = self.live(minute=7)["ships"][0]
        self.assertEqual(ship["status"], "шторм")
        self.assertEqual(ship["pulse_status"], "шторм")
        self.assertEqual(ship["storms"], 1)

    def test_storm_by_silence_over_30_min(self):
        """Шторм: тишина >30 минут без storm-событий."""
        self.write_log([
            _envelope("Тихоня", 0, "agent.started", task="Копилот"),
            _envelope("Тихоня", 1, "agent.pulse", step="ушёл в море"),
        ])
        ship = self.live(minute=45)["ships"][0]
        self.assertEqual(ship["status"], "шторм")
        self.assertEqual(ship["pulse_status"], "шторм")
        self.assertEqual(ship["storms"], 0)
        self.assertAlmostEqual(ship["pulse_min"], 44.0, delta=0.01)

    def test_pulse_statuses_go_calm_storm(self):
        """Статусы пульса ТЗ: <10 мин «идёт», 10–30 «тихо», >30 «шторм»."""
        self.write_log([
            _envelope("Дозорный", 0, "agent.pulse", step="только маячок"),
        ])
        self.assertEqual(self.live(minute=5)["ships"][0]["pulse_status"], "идёт")
        self.assertEqual(self.live(minute=20)["ships"][0]["pulse_status"], "тихо")
        self.assertEqual(self.live(minute=40)["ships"][0]["pulse_status"], "шторм")

    def test_finished_ship_leaves_live(self):
        """Корабль с завершённым последним рейсом не в live (уходит в history)."""
        self.write_log([
            _envelope("Портовый", 0, "agent.started", task="Смета"),
            _envelope("Портовый", 30, "agent.finished", verdict="принято"),
        ])
        self.assertEqual(self.live(minute=31)["ships"], [])

    def test_new_voyage_reopens_ship(self):
        """Новый agent.started после finished снова поднимает корабль в море."""
        self.write_log([
            _envelope("Маяк", 0, "agent.started", task="Рейс один"),
            _envelope("Маяк", 10, "agent.finished", verdict="принято"),
            _envelope("Маяк", 20, "agent.started", task="Рейс два", lanes_total=2),
            _envelope("Маяк", 22, "agent.pulse", step="опять в море"),
        ])
        ships = self.live(minute=23)["ships"]
        self.assertEqual(len(ships), 1)
        self.assertEqual(ships[0]["task"], "Рейс два")
        self.assertEqual(ships[0]["started_at"], _ts(20))
        self.assertEqual(ships[0]["lanes"], {"done": 0, "total": 2})
        self.assertIsNone(ships[0]["eta_min"], "ETA при нуля закрытых лейнов не считается")

    def test_ship_name_prefers_payload_by(self):
        """Поле by payload-а (схема evo.agent.event) сильнее produced_by (фаза 1)."""
        self.write_log([
            _envelope("ZCode", 0, "agent.started", by="Верификатор", task="Проверка"),
            _envelope("ZCode", 1, "agent.pulse", by="Верификатор", step="маячок"),
        ])
        ship = self.live(minute=2)["ships"][0]
        self.assertEqual(ship["by"], "Верификатор")

    def test_ship_without_started_event_kept_by_produced_by(self):
        """Писателей started нет (фаза 1): рейс собирается из любых agent.* по produced_by."""
        self.write_log([
            _envelope("Резюме-конвейер", 0, "agent.pulse", step="шаг 1/5"),
            _envelope("Резюме-конвейер", 4, "agent.pulse", step="шаг 2/5"),
        ])
        ship = self.live(minute=6)["ships"][0]
        self.assertEqual(ship["by"], "Резюме-конвейер")
        self.assertEqual(ship["task"], "задача не объявлена")
        self.assertEqual(ship["started_at"], _ts(0))
        self.assertEqual(ship["lanes"], {"done": 0, "total": None})

    def test_eta_none_until_any_lane_done(self):
        """ETA-оценка не врёт при нулевой скорости: done=0 → None (UI покажет «—»)."""
        self.write_log([
            _envelope("Медленный", 0, "agent.started", task="Долгий рейс", lanes_total=3),
        ])
        self.assertIsNone(self.live(minute=10)["ships"][0]["eta_min"])

    def test_events_recent_capped_at_five(self):
        """Лента карточки — последние 5 событий (AGENTS_RECENT_LIMIT)."""
        envelopes = [_envelope("Лентяй", 0, "agent.started", task="Ленты")]
        for i in range(1, 9):
            envelopes.append(_envelope("Лентяй", i, "agent.pulse", step=f"шаг {i}"))
        self.write_log(envelopes)
        ship = self.live(minute=9)["ships"][0]
        self.assertEqual(len(ship["events_recent"]), 5)
        self.assertEqual(ship["events_recent"][-1]["text"], "шаг 8")

    def test_non_agent_events_ignored_and_broken_lines_skipped(self):
        """Чужие kinds и битые строки журнал не ломают; панель читает только agent.*."""
        self.write_log(
            [
                _envelope("evofind", 0, "evofind.query", q="test"),
                _envelope("Пираты", 1, "agent.started", task="Настоящий рейс"),
            ],
            extra_lines=["{битая json-строка", "", "не json вовсе"],
        )
        ships = self.live(minute=2)["ships"]
        self.assertEqual([ship["by"] for ship in ships], ["Пираты"])

    def test_empty_and_missing_log(self):
        """Нет журнала / пустой журнал → пустой флот без исключений."""
        self.assertEqual(self.live(minute=1)["ships"], [])
        self.log.write_text("", encoding="utf-8")
        self.assertEqual(self.live(minute=1)["ships"], [])

    def test_lanes_total_from_list(self):
        """lanes как список в started → total = длина списка (готовность ТЗ)."""
        self.write_log([
            _envelope("Списочник", 0, "agent.started", task="План",
                      lanes=["Л-1", "Л-2", "Л-3"]),
            _envelope("Списочник", 2, "agent.lane", lane="Л-1"),
        ])
        ship = self.live(minute=3)["ships"][0]
        self.assertEqual(ship["lanes"], {"done": 1, "total": 3})
        self.assertAlmostEqual(ship["eta_min"], 4.0, delta=0.01)


class TestAgentsHistory(AgentsLogTestBase):
    """GET /api/agents/history: завершённые рейсы с итогами."""

    def _full_voyage_log(self):
        self.write_log([
            _envelope("Строитель-1", 0, "agent.started", task="Построить док", lanes_total=2),
            _envelope("Строитель-1", 5, "agent.lane", lane="Л-1"),
            _envelope("Строитель-1", 8, "agent.storm", reason="retry"),
            _envelope("Строитель-1", 10, "agent.lane", lane="Л-2"),
            _envelope("Строитель-1", 12, "agent.finished", verdict="принято",
                      files=["dock.py", "dock.css"], tests="unittest OK", tokens=12345),
            _envelope("Строитель-2", 15, "agent.started", task="Ремонт"),
            _envelope("Строитель-2", 20, "agent.finished", verdict="доработка"),
        ])

    def test_finished_voyages_with_outcomes(self):
        self._full_voyage_log()
        voyages = self.history()["voyages"]
        self.assertEqual(len(voyages), 2)
        # новые сверху: рейс Строителя-2 закончился позже
        self.assertEqual([voyage["by"] for voyage in voyages], ["Строитель-2", "Строитель-1"])
        first = voyages[1]
        self.assertEqual(first["verdict"], "принято")
        self.assertEqual(first["files"], ["dock.py", "dock.css"])
        self.assertEqual(first["tests"], "unittest OK")
        self.assertEqual(first["tokens"], 12345)
        self.assertEqual(first["storms"], 1)
        self.assertEqual(first["lanes"], {"done": 2, "total": 2})
        # минуты факта нет в payload → считаем от started/finished
        self.assertAlmostEqual(first["minutes"], 12.0, delta=0.01)

    def test_chain_roles_order(self):
        """Цепочка ТЗ: начальные → промежуточные → итоговые, порядок хронологический."""
        self._full_voyage_log()
        voyage = self.history()["voyages"][1]
        roles = [step["role"] for step in voyage["chain"]]
        self.assertEqual(roles[0], "initial")
        self.assertEqual(roles[-1], "final")
        self.assertEqual(roles.count("intermediate"), 3)  # лейн, шторм, лейн
        self.assertEqual([step["kind"] for step in voyage["chain"]],
                         ["agent.started", "agent.lane", "agent.storm", "agent.lane", "agent.finished"])

    def test_limit_clamped(self):
        """limit обрезает выдачу и зажимается в 1..100."""
        envelopes = []
        for i in range(5):  # рейсы по 10 минут: старт i*10, финиш i*10+5
            envelopes.append(_envelope("Челнок", i * 10, "agent.started", task=f"рейс {i + 1}"))
            envelopes.append(_envelope("Челнок", i * 10 + 5, "agent.finished", verdict="принято"))
        self.write_log(envelopes)
        self.assertEqual(len(self.history(limit=3)["voyages"]), 3)
        self.assertEqual(len(self.history(limit=0)["voyages"]), 1)
        self.assertEqual(len(self.history(limit=999)["voyages"]), 5)
        # пять finished → самый свежий первым
        voyages = self.history(limit=1)["voyages"]
        self.assertEqual(voyages[0]["task"], "рейс 5")

    def test_unfinished_voyages_not_in_history(self):
        """Незавершённые рейсы — не история (они в live)."""
        self.write_log([
            _envelope("Бродяга", 0, "agent.started", task="Без финиша"),
            _envelope("Бродяга", 5, "agent.pulse", step="всё ещё в море"),
        ])
        self.assertEqual(self.history()["voyages"], [])

    def test_missing_log_empty_history(self):
        self.assertEqual(self.history()["voyages"], [])


class TestVoyageSplitting(AgentsLogTestBase):
    """Разбиение на рейсы и сортировка: хаос в журнале не должен путать панель."""

    def test_events_out_of_order_sorted_by_ts(self):
        """Журнал с событиями не по времени: агрегат сортирует по ts перед разбиением."""
        self.write_log([
            _envelope("Штормовой", 10, "agent.lane", lane="Л-1"),
            _envelope("Штормовой", 0, "agent.started", task="Порядок", lanes_total=2),
            _envelope("Штормовой", 20, "agent.finished", verdict="принято"),
        ])
        live_ships = self.live(minute=21)["ships"]
        self.assertEqual(live_ships, [], "finished после сортировки должен увести корабль из live")
        voyages = self.history()["voyages"]
        self.assertEqual(len(voyages), 1)
        self.assertEqual([step["kind"] for step in voyages[0]["chain"]],
                         ["agent.started", "agent.lane", "agent.finished"])

    def test_multiple_ships_independent(self):
        """Корабли независимы: finished одного не топит другого."""
        self.write_log([
            _envelope("А", 0, "agent.started", task="Рейс А"),
            _envelope("Б", 0, "agent.started", task="Рейс Б"),
            _envelope("А", 5, "agent.finished", verdict="принято"),
        ])
        ships = self.live(minute=6)["ships"]
        self.assertEqual([ship["by"] for ship in ships], ["Б"])
        self.assertEqual(len(self.history()["voyages"]), 1)


if __name__ == "__main__":
    unittest.main()
