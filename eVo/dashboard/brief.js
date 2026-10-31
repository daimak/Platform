window.EVO_BRIEF = {
  "generatedAt": "2026-10-30 23:56",
  "sources": [
    "Memory/Context/CURRENT.md",
    "Memory/Engineering/STATE.md",
    "CHANGELOG.md",
    "git"
  ],
  "current": {
    "date": "2026-08-05",
    "nextAction": "Актуализировать контекст Barrymore:\n- сверить CURRENT.md с STATE.md, LOG.md и CHANGELOG.md;\n- устранить устаревшие указания на создание Morning Brief;\n- проверить качество доклада после обновления контекста;\n- отдельно разобраться с неотслеживаемым tools/barrymore/logger.py.\n\nНе выполнять merge, commit или удаление файлов без отдельного решения Sovereign."
  },
  "state": {
    "nextStep": "По указанию пользователя: слияние веток по D-002 (после проверки) либо продуктовые шаги (R4 — Morning Brief read-only MVP)."
  },
  "changes": [
    "2026-10-29 | Barrymore brief refresh button in dashboard; loopback-only local server runs the existing generator and returns the fresh report to the open modal | refresh Morning Brief on demand | —",
    "2026-10-29 | Barrymore dashboard starts at Windows logon; source fingerprints avoid unchanged LLM runs; explicit Done tasks retain history for 48h before archival | persistent brief and task lifecycle | —",
    "2026-10-29 | Platform v1.8.3: Tashkent time, silent Windows startup, cached Morning Brief, durable Barrymore task history and Graphify project report | on-demand, low-noise project overview | —",
    "2026-10-29 | Maelstorm research beacons and translucent island markers | clarify island roles and reduce map clutter until hover | —",
    "2026-10-29 | Platform v1.8.4: AI Sandbox usage ledger and security contour, Hunter cabinet in Core Citadel, project onboarding and context handoff | improve AI visibility, controlled safety checks, and continuity between sessions | —"
  ],
  "tasks": {
    "urgent": [
      {
        "id": "holmes-host-noise",
        "title": "Холмс: шум авто-коммитов агент-хоста в истории",
        "source": "Holmes",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-29T19:34:08Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T19:34:08Z",
            "by": "Holmes",
            "note": "Шум истории: 104 авто-коммитов агент-хоста из 134 за 7 дней (77%)."
          }
        ]
      },
      {
        "id": "kali-pentest-lab",
        "title": "Kali Linux лаборатория: VMware Workstation Pro + белый пентест",
        "source": "user",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-30T17:58:29Z",
        "description": "Задача Дмитрия (30.10, 23:00, «вопрос важный, займусь утром»): поднять спец-систему для сбора, анализа и проверки информации, защиты и анализа угроз, поиска уязвимостей — в рамках БЕЛОГО пентеста. Форма: VMware Workstation Pro (бесплатен для личного использования с мая 2024, после ухода VMware под Broadcom) + готовый образ Kali. Затем ZCode запускается из виртуалки, и работа идёт по доктрине платформы. Ориентир по времени: 1–1,5 часа суммарно.",
        "steps": [
          {
            "n": 1,
            "do": "Проверить виртуализацию: Диспетчер задач → Производительность → ЦП → «Виртуализация: Включено» (иначе включить VT-x/SVM в BIOS). Решить конфликт с Hyper-V: «Изоляция ядра / Целостность памяти» (Безопасность Windows → Безопасность устройства) тормозит VMware на −20–30%; выключать её только если WSL2 и Android-эмуляторы не нужны (bcdedit /set hypervisorlaunchtype off ломает WSL2).",
            "dod": "Виртуализация включена, решение по Hyper-V-слою принято и осознано."
          },
          {
            "n": 2,
            "do": "Установить VMware Workstation Pro 17 (НЕ Player, он больше не существует отдельно): бесплатный аккаунт на support.broadcom.com → Downloads → VMware Cloud Foundation → Workstation Pro (17.6.x) для Windows. Папку VM указать C:\\VM (без кириллицы/пробелов). План Б при капризах Broadcom-портала: VirtualBox (тот же подход, образ для VBox рядом на get-kali).",
            "dod": "Workstation открывается, вкладка создания VM доступна."
          },
          {
            "n": 3,
            "do": "Скачать ГОТОВЫЙ образ Kali (не ISO!): kali.org/get-kali → Virtual Machines → VMware 64-bit (.7z, ~3–4 ГБ) → распаковать 7-Zip → Workstation: Open → .vmx → на вопрос «I moved it / I copied it» ответить «I Copied It». Вход kali/kali. Сразу: sudo apt update && sudo apt full-upgrade -y, passwd. Настройки VM: 2–4 vCPU, RAM 4–8 ГБ, диск тонкий, сеть NAT.",
            "dod": "Kali загружается, апдейты прошли, пароль сменён."
          },
          {
            "n": 4,
            "do": "Снять снапшот «clean» (VM → Snapshot → Take Snapshot) — золотое правило лаборатории: откат к чистому состоянию за секунды после любых экспериментов. Настроить обмен с хостом: Shared Folders → C:\\Work (в госте /mnt/hgfs/Work) или чисто через git.",
            "dod": "Снапшот существует, обмен хост↔гость проверен."
          },
          {
            "n": 5,
            "do": "Поднять легальные мишени и полигоны: локально — Metasploitable 3, DVWA, OWASP Juice Shop (уязвимые приложения в соседнюю VM); онлайн с легальным полигоном — TryHackMe (с нуля, бесплатные комнаты), HackTheBox, PortSwigger Web Security Academy (бесплатно, лучшая по web-безопасности).",
            "dod": "Одна локальная мишень поднята и видна из Kali."
          },
          {
            "n": 6,
            "do": "Запустить ZCode внутри VM: git clone репо (git/Python/Node в Kali из коробки), вход по канону Docs/Map.md → Memory/Engineering/STATE.md → LOG.md. Написать «Протокол лаборатории» в доктрине платформы: цель → разрешение → инструменты → лог → отчёт; стыковать с security-контуром Platform (allowlist security-targets.json).",
            "dod": "ZCode в VM отвечает на канонические входы; протокол-документ в репо."
          }
        ],
        "constraints": [
          "БЕЛЫЙ пентест: активное сканирование и эксплуатация — ТОЛЬКО свои системы, локальные учебные мишени или платформы с явным разрешением (TryHackMe/HTB/PortSwigger). Чужие системы без письменного разрешения — за гранью, и по доктрине платформы тоже.",
          "Каждая сессия: снапшот до экспериментов, лог действий, отчёт по формату «Вывод/Факты/Варианты/Риски/Рекомендация».",
          "Секреты и личные данные хоста (Workspace/.env, vault, ключи) в VM НЕ переносить; лаборатория изолирована.",
          "USB Wi-Fi адаптер с режимом монитора (Alfa AWUS036ACH и подобные) — отдельная будущая глава, не блокирует эту задачу."
        ],
        "links": [
          "https://www.kali.org/get-kali/",
          "https://support.broadcom.com/",
          "Docs/ASSESSMENT-2026-10-30-ZCode.md (раздел «Безопасность»)",
          "Memory/Engineering/Tasks/Active/study-ai-agents.json (агентность — смежный трек)"
        ],
        "history": [
          {
            "status": "active",
            "at": "2026-10-30T17:58:29Z",
            "note": "Создана ZCode по прямому указанию Дмитрия («сохрани как важную ToDo, займусь утром»); полный план установки + границы белого пентеста заложены в JSON."
          }
        ]
      },
      {
        "id": "keepass-master-password-backup",
        "title": "Мастер-пароль KeePassXC + бэкап хранилища",
        "source": "S-4",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          }
        ]
      },
      {
        "id": "money-radar-orders",
        "title": "Радар денег: всесторонний разбор заказов и перспективных направлений заработка",
        "source": "Sovereign",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-29T20:45:00Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T20:45:00Z",
            "note": "Приоритет Sovereign: реальные деньги любой ценой. Вести всесторонне: (1) триаж-доска Workspace/analytics/orders_board.json + orders_report.md (tools/orders_triage.py) — перспективные/основной/отсев, ручная сортировка сохраняется; (2) подключить к агрегатору биржи заказов (fl.ru, kwork — функции уже есть в tools/job_search.py, в снапшот 29.10 не попали); (3) подтягивать has_salary и свежесть; (4) готовить первые отклики на перспективные заказы (скраперы/парсеры/боты/LLM/DevOps); (5) задействовать все ресурсы платформы: агрегатор, экстракция зарплат, дашборд Trading Quarter, агенты. MVP уже стоит, работаем итерациями."
          }
        ]
      },
      {
        "id": "rotate-langsmith-freellmapi",
        "title": "Ротация ключей LangSmith/FreeLLMAPI",
        "source": "S-1",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          }
        ]
      }
    ],
    "regular": [
      {
        "id": "clean-empty-stubs",
        "title": "Чистка пустых заглушек (locales, Carrier, Timeline)",
        "source": "R7",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          }
        ]
      },
      {
        "id": "holmes-uncommitted-edits",
        "title": "Холмс: незакоммиченные правки в рабочем дереве",
        "source": "Holmes",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-10-29T19:34:08Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T19:34:08Z",
            "by": "Holmes",
            "note": "Незакоммиченные правки: tools/agents/registry.json, tools/agents/run_agent.py"
          }
        ]
      },
      {
        "id": "holmes-untracked-files",
        "title": "Холмс: разобрать untracked-файлы (коммит или .gitignore)",
        "source": "Holmes",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-10-29T19:34:08Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T19:34:08Z",
            "by": "Holmes",
            "note": "Untracked-файлов: 13: Workspace/analytics/2026-10-29/report.md, Workspace/analytics/2026-10-29/salary_extract_cache.json, Workspace/analytics/2026-10-29/salary_extracted.csv, tools/analytics_report.py"
          }
        ]
      },
      {
        "id": "merge-branches-d002",
        "title": "Слияние веток по D-002",
        "source": "R9",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          }
        ]
      },
      {
        "id": "study-ai-agents",
        "title": "Изучение агентов: декомпозиция, лаборатории, запуск в работу",
        "source": "user",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-10-30T16:33:00Z",
        "description": "Задача от Дмитрия (30.10, поздний вечер): «Меня этот вопрос уже напрягает — вопрос надо декомпозировать, собрать максимум информации, подготовить исследовательские лаборатории и начать использовать». Контекст: Дмитрий параллелит три потока — ZCode (платформа/агенты), ChatGPT (вопросы переезда), codex (фриланс и свои проекты); агентные навыки — рыночный товар, связка с потоком заработка. Действующая доктрина не отменяется (см. constraints): сначала учёба и лаборатории, развёртывание нового штата — только по слову Sovereign.",
        "goal": "От «напрягает» к «использую»: конспект ландшафта агентов, инвентаризация своих рантаймов, 1-2 готовые лаборатории для безопасных экспериментов и первый полезный агент, отработавший реальную задачу с зафиксированной метрикой.",
        "steps": [
          {
            "n": 1,
            "do": "Собрать входы: прочитать Docs/AGENTS-LANDSCAPE-2026-10-30-ZCode.md (справка второго AI), паспорта Memory/Agents/, рантайм tools/agents/ (Холмс), TASK-PROTOCOL.md; снаружи — протоколы и фреймворки (MCP, agent SDK, оркестраторы).",
            "dod": "Одностраничный конспект «анатомия агента»: каркас / инструменты / память / верификация / метрика / стоимость."
          },
          {
            "n": 2,
            "do": "Инвентаризация своих: Barrymore, Holmes, Hunter — что из паспорта/инструмента/метрики есть, чего нет.",
            "dod": "Таблица «агент → паспорт? инструмент? метрика?» с пробелами."
          },
          {
            "n": 3,
            "do": "Декомпозировать «изучение агентов» на учебные вопросы: агент vs скрипт; оркестрация и циклы; MCP и протоколы; память и контекст; безопасность (верификация dangerous-действий как у Холмса); экономика токенов.",
            "dod": "Список вопросов, отсортированный по «ценность для заработка и платформы / усилия»."
          },
          {
            "n": 4,
            "do": "Подготовить лаборатории: (а) sandbox-режим tools/agents/ + scratch-каталог вне git; (б) изолированный ключ/шлюз для экспериментов (FreeLLMAPI :31415 уже есть); (в) шаблон паспорта + строка метрики.",
            "dod": "Чек-лист «поднять лабораторию за 5 минут», опробованный один раз."
          },
          {
            "n": 5,
            "do": "Начать использовать: первый практический агент на реальной задаче. Кандидаты: Researcher по вакансиям (питается снапшотами Workspace/analytics — прямая связь с заработком) или рутинный агент над дневным снапшотом.",
            "dod": "Агент отработал одну реальную задачу; метрика зафиксирована в журнале; паспорт обновлён по факту."
          },
          {
            "n": 6,
            "do": "Ревизия доктрины: доложить Sovereign, что изменилось; предложить, кто следующий в штат после Холмса (или почему никого).",
            "dod": "Решение Sovereign записано в Memory/Agents/README.md."
          }
        ],
        "constraints": [
          "Правило «агент = паспорт + инструмент + метрика» (Memory/Agents/README.md) — без метрики агент не считается активным.",
          "ADR-003/004: агенты read-only по умолчанию, ОС не трогают; расширение полномочий — только явным решением Sovereign.",
          "«Других агентов не разворачивать» действует до шага 6; попытка с chief-of-staff вне доктрины — известный прецедент, не повторять.",
          "Два AI работают в одном чекауте: задачу ведёт один исполнитель (назначить при старте), чужие незакоммиченные файлы не трогать."
        ],
        "links": [
          "Docs/AGENTS-LANDSCAPE-2026-10-30-ZCode.md",
          "Memory/Agents/",
          "tools/agents/",
          "tools/barrymore/TASK-PROTOCOL.md",
          "Core/Architecture/ADR/ (ADR-003, ADR-004)",
          "Workspace/analytics/2026-10-29/README.md (данные для агента-Researcher)"
        ],
        "economics": "Агентные навыки сейчас покупают: связка «парсер данных + агент-обработчик + метрика» = готовый фриланс-продукт (пересекается с потоком codex по фрилансу). Учебный результат шага 5 оформлять как кейс/памятку — двойное использование: платформа + портфолио.",
        "history": [
          {
            "status": "active",
            "at": "2026-10-30T16:33:00Z",
            "note": "Создана ZCode по прямому указанию Дмитрия («создай в AI задачу — изучение агентов»); декомпозиция заложена в JSON. 30.10 ~21:33 local (UTC+5)."
          }
        ]
      },
      {
        "id": "update-current-context",
        "title": "Актуализация Memory/Context/CURRENT.md",
        "source": "R3",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          }
        ]
      }
    ],
    "done": []
  },
  "git": {
    "branch": "feature_1.8.5",
    "lastCommit": "115ea76 Fill sanctioned empty stubs (clean-empty-stubs): Timeline chronology, Carrier honest passport, callouts draft spec",
    "dirtyFiles": 31
  },
  "agent": {
    "model": "qwen/qwen3.8-27b",
    "summary": "Дмитрий, утро. Снимок данных от 30.10.2026 23:56. Ветка feature_1.8.5, 31 незакоммиченный файл. Срочные задачи: лаборатория Kali Linux (план на 1-1.5 часа, старт с проверки виртуализации), разбор заказов на заработок, ротация ключей и бэкап KeePass. Также активен трек по изучению AI-агентов. Внимание: в CURRENT.md указана дата 05.08.2026, данные устарели, требуется сверка с STATE.md. Не выполнять merge/commit без твоего решения.",
    "nextStep": "Начать с шага 1 задачи kali-pentest-lab: проверить статус виртуализации в Диспетчере задач и принять решение по конфликту с Hyper-V."
  },
  "_sourceFingerprint": "15cf147913bd7b5a79a961a39b6c2f74e1d6f56aa5605c72cb656c1f7b724f9e"
};