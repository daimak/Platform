/* Сгенерировано tools/barrymore/build-excursion.py — не править руками.
   Перегенерация: python tools/barrymore/build-excursion.py
   Источники: events.jsonl, карточки задач, git show --stat, Docs/NIGHT-LOG. */
window.EVO_EXCURSION = {
  "generatedAt": "2026-11-07T09:12:21+05:00",
  "journal": "Workspace/logs/events.jsonl",
  "summary": "За ночь 05.11 задокументировано 3 рейсов, суммарно ~11.5M токенов — все приняты.",
  "flights": [
    {
      "id": "agents-fleet",
      "title": "«Флот в море» — дашборд запущенных агентов",
      "subtitle": "ночь 06→07.11 · вахта 8 · коммит d271fd5",
      "verdict": "принято Sovereign",
      "metrics": [
        {
          "value": "+1572",
          "label": "строк кода в 6 файлах"
        },
        {
          "value": "20/20",
          "label": "тестов живой панели"
        },
        {
          "value": "10 мин 40 с",
          "label": "от спавна до финиша"
        }
      ],
      "reportRows": [
        {
          "label": "Работали",
          "value": "агент «Флот-строитель» (суб-агент ZCode), рейс ночной вахты 06→07.11"
        },
        {
          "label": "Задача",
          "value": "панель запущенных агентов по ТЗ, лейны Л-С1 API → Л-С2 UI → Л-С3 тесты"
        },
        {
          "label": "Результат",
          "value": "+1572 строк кода в 6 файлах (коммит d271fd5): интерфейс 909 строк (agents.html 83 + agents.css 544 + agents.js 282), API +318 строк в dashboard-server.py (GET /api/agents/live + /history, шторм = storm без finished ИЛИ тишина >30 мин), 339 строк тестов"
        },
        {
          "label": "Инцидент",
          "value": "1 шторм: первый прогон test_agents_live: 3 падения — ETA-считал от старта вместо скорости лейнов (формула ТЗ), синтетика limit-теста была нереалистичной; исправлено, повторный прогон 20/20"
        },
        {
          "label": "Эксплуатация",
          "value": "сервер 8765 перезапущен, панель отвечает 200, автообновление 15 с"
        },
        {
          "label": "Вердикт",
          "value": "принято Sovereign 06.11; панель в бою — http://127.0.0.1:8765/agents.html"
        }
      ],
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
            }
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
            "Memory/Engineering/LOG.md"
          ]
        }
      ]
    },
    {
      "id": "resume-pipeline",
      "title": "«Резюме-конвейер» — фактура для откликов за ночь",
      "subtitle": "ночь 04→05.11 · рейс 2 ночной вахты · 14 файлов",
      "verdict": "принято, верифицировано",
      "metrics": [
        {
          "value": "3.34M",
          "label": "токенов суб-контекста"
        },
        {
          "value": "14",
          "label": "файлов в резюме-зоне"
        },
        {
          "value": "216 → 10",
          "label": "позиций рынка → откликов"
        }
      ],
      "reportRows": [
        {
          "label": "Работали",
          "value": "суб-агент ZCode под диспетчером ночной вахты: 67 вызовов инструментов, ~21 мин, 3.34M токенов суб-контекста"
        },
        {
          "label": "Задача",
          "value": "лейн Л-2 ночной вахты 04→05.11 — фактура резюме для откликов (QUEUE.md, шаблон «Ситуация → Действие → Результат», ничего не выдумывать)"
        },
        {
          "label": "Результат",
          "value": "7 кейсов в профиле (28 навыков, 11 честных todo), 3 полных кейса в двух языках (RU 171–200, EN 205–232 слов), рынок: 216 свежих позиций, 10 отобрано (6 RU + 4 EN), 10 черновиков откликов по 120-141 слов + README-указатель — 14 файлов"
        },
        {
          "label": "Приватная зона",
          "value": "резюме-артефакты в Workspace/private/ — показаны путями, содержимое не читается"
        },
        {
          "label": "Вердикт",
          "value": "принято, верификация ZCode; блокер №1 поиска работы снят (отклики готовы к отправке)"
        }
      ],
      "nodes": [
        {
          "kind": "idea",
          "label": "Замысел",
          "time": "04.11 вечер",
          "detail": "Санкция Sovereign: «нужны агенты — ночью копают проект, утром я кайфую». Л-2: три кейса по шаблону, факт-чек по LOG E-001…E-046.",
          "refs": [
            "Workspace/reports/night-2026-11-05/QUEUE.md",
            "Docs/NIGHT-LOG-2026-11-05-ZCode.md"
          ]
        },
        {
          "kind": "agent",
          "label": "Диспетчер вахты",
          "time": "04.11 ~23:58",
          "detail": "Крон-автоматизация ночной вахты берёт лейны из QUEUE.md по порядку; Л-2 отдан суб-агенту с пайком токенов.",
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
              "detail": "kind=agent.pulse, cases=7, skills=28, todo=11"
            },
            {
              "name": "2/5 cases",
              "detail": "kind=agent.pulse, files=3, ru_words=[188, 171, 200], en_words=[215, 205, 232]"
            },
            {
              "name": "3/5 job_search+top10",
              "detail": "kind=agent.pulse, fresh_total=216, selected=10, en=4, ru=6"
            },
            {
              "name": "4/5 proposals-2026-11-05",
              "detail": "kind=agent.pulse, files=10, word_range=120-141"
            },
            {
              "name": "5/5 README",
              "detail": "kind=agent.pulse, pipeline=complete"
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
