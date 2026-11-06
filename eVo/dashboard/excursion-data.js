/* Сгенерировано tools/barrymore/build-excursion.py — не править руками.
   Перегенерация: python tools/barrymore/build-excursion.py
   Источник: Workspace/logs/events.jsonl + карточки Memory/Engineering/Tasks. */
window.EVO_EXCURSION = {
  "generatedAt": "2026-11-07T01:23:38+05:00",
  "journal": "Workspace/logs/events.jsonl",
  "flights": [
    {
      "id": "agents-fleet",
      "title": "«Флот в море» — дашборд запущенных агентов",
      "subtitle": "ночь 05→06.11 · агент «Флот-строитель» · 3 лейна · 1 шторм · 20 тестов",
      "verdict": "принято",
      "nodes": [
        {
          "kind": "idea",
          "label": "Замысел",
          "time": "05.11 05:35",
          "detail": "Идея Sovereign 05.11 в чате. Заложена в Сделать; ждёт сдачи data-foundation.",
          "refs": [
            "Memory/Engineering/Tasks/Active/agents-fleet.json (history)"
          ]
        },
        {
          "kind": "spec",
          "label": "ТЗ",
          "time": "05.11",
          "detail": "Полный план: события evo.agent.event → GET /api/agents/live + agents.html «корабли в море»; метрики лейнов, пульса, штормов, ETA.",
          "refs": [
            "Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md"
          ]
        },
        {
          "kind": "agent",
          "label": "Спавн агента",
          "time": "06.11 01:33",
          "detail": "Дашборд «Флот в море»: API агентов + UI + тесты",
          "refs": [
            "Workspace/logs/events.jsonl (agent.started)"
          ]
        },
        {
          "kind": "lane",
          "label": "Лейны",
          "time": "",
          "chips": [
            {
              "name": "Л-С1 API",
              "detail": "py_compile OK, смоук агрегаторов на живом журнале",
              "refs": [
                "tools/barrymore/dashboard-server.py"
              ]
            },
            {
              "name": "Л-С2 UI",
              "detail": "node --check OK, id/классы сверены скриптом",
              "refs": [
                "eVo/dashboard/agents.html",
                "eVo/dashboard/agents.css",
                "eVo/dashboard/agents.js"
              ]
            },
            {
              "name": "Л-С3 тесты",
              "detail": "unittest 20/20 OK; смежные: test_jobs_registry 10, test_dashboard_static 5 (включая node --check всех *.js), test_log_event 6, test_envelope 14",
              "refs": [
                "tools/tests/test_agents_live.py"
              ]
            }
          ]
        },
        {
          "kind": "storm",
          "label": "Шторм",
          "time": "06.11 01:43",
          "detail": "первый прогон test_agents_live: 3 падения — ETA-считал от старта вместо скорости лейнов (формула ТЗ), синтетика limit-теста была нереалистичной; исправлено, повторный прогон 20/20",
          "refs": [
            "Workspace/logs/events.jsonl (agent.storm)"
          ]
        },
        {
          "kind": "artifact",
          "label": "Артефакты",
          "time": "",
          "files": [
            {
              "path": "eVo/dashboard/agents.html",
              "exists": true,
              "size": 3913
            },
            {
              "path": "eVo/dashboard/agents.css",
              "exists": true,
              "size": 11326
            },
            {
              "path": "eVo/dashboard/agents.js",
              "exists": true,
              "size": 12597
            },
            {
              "path": "tools/tests/test_agents_live.py",
              "exists": true,
              "size": 18133
            }
          ],
          "refs": [
            "tools/barrymore/dashboard-server.py (+/api/agents/*)"
          ]
        },
        {
          "kind": "finish",
          "label": "Финиш рейса",
          "time": "06.11 01:44",
          "detail": "Вердикт: принято",
          "refs": [
            "tools/tests/test_agents_live.py (20/20)"
          ]
        },
        {
          "kind": "accept",
          "label": "Приёмка",
          "time": "06.11 вечер",
          "detail": "Панель agents.html жива после рестарта 8765; принята Sovereign (ночная вахта 06→07.11).",
          "refs": [
            "Memory/Engineering/LOG.md",
            "http://127.0.0.1:8765/agents.html"
          ]
        }
      ]
    },
    {
      "id": "resume-pipeline",
      "title": "«Резюме-конвейер» — фактура для откликов за ночь",
      "subtitle": "ночь 04→05.11 · диспетчер вахты + суб-агент · 5 шагов · 14 файлов",
      "verdict": "принято, 14 файлов, верификация ZCode",
      "nodes": [
        {
          "kind": "idea",
          "label": "Замысел",
          "time": "04.11 вечер",
          "detail": "Санкция Sovereign: «нужны агенты — ночью копают проект, утром я кайфую». Лейн Л-2 ночной вахты: три кейса по шаблону Ситуация→Действие→Результат, факт-чек по LOG E-001…E-046, ничего не выдумывать.",
          "refs": [
            "Workspace/reports/night-2026-11-05/QUEUE.md",
            "Docs/NIGHT-LOG-2026-11-05-ZCode.md"
          ]
        },
        {
          "kind": "agent",
          "label": "Диспетчер вахты",
          "time": "04.11 ~23:58",
          "detail": "Крон-автоматизация ночной вахты берёт лейны из QUEUE.md по порядку; Л-2 отдан суб-агенту с жёстким пайком токенов.",
          "refs": [
            "Workspace/reports/night-2026-11-05/STATE-NIGHT.md"
          ]
        },
        {
          "kind": "lane",
          "label": "Шаги конвейера",
          "time": "05.11 00:40",
          "chips": [
            {
              "name": "1/5 master-profile.json",
              "detail": "status=done; kind=agent.pulse, cases=7, skills=28, todo=11"
            }
          ]
        },
        {
          "kind": "artifact",
          "label": "Артефакты",
          "time": "05.11 ~00:50",
          "files": [
            {
              "path": "Workspace/private/resume/master-profile.json",
              "exists": true,
              "private": true
            },
            {
              "path": "Workspace/private/resume/cases/ (3 кейса RU+EN)",
              "exists": true,
              "private": true
            },
            {
              "path": "Workspace/private/proposals/2026-11-05/ (10 откликов)",
              "exists": true,
              "private": true
            }
          ],
          "detail": "Приватная зона: пути — факт существования, содержимое не читается и не показывается.",
          "refs": [
            "Workspace/reports/night-2026-11-05/QUEUE.md (Л-2)"
          ]
        },
        {
          "kind": "finish",
          "label": "Финиш рейса",
          "time": "06.11 01:46",
          "detail": "Вердикт: принято, 14 файлов, верификация ZCode",
          "refs": [
            "Workspace/logs/events.jsonl (agent.finished)"
          ]
        },
        {
          "kind": "accept",
          "label": "Приёмка",
          "time": "05.11 утро",
          "detail": "Блокер №1 поиска работы снят: 28 навыков, 7 кейсов, 10 откликов готовы; 6 решений за Sovereign — в README зоны.",
          "refs": [
            "Workspace/reports/night-2026-11-05/QUEUE.md"
          ]
        }
      ]
    }
  ]
};
