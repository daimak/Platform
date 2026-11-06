window.EVO_BRIEF = {
  "generatedAt": "2026-11-06 12:10",
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
          },
          {
            "stage": "analysis",
            "at": "2026-11-01T08:56:15Z"
          }
        ],
        "stage": "analysis",
        "busy": null
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
          },
          {
            "n": 7,
            "do": "СПЕЦ-УЧЁТКА (поручение Дмитрия 01.11 ~10:40, вход kali/kali несекьюрен): 1) написать инструкцию — создать отдельного пользователя с рутовыми правами через sudo (например `adduser ops` + `usermod -aG sudo ops`, проверка `sudo -v`; пароль НЕ совпадающий с kali; sshd ограничить AllowUsers на новую учётку); 2) применить в VM после снапшота clean-baseline; 3) ZCode/агенты ходят в VM только под спец-учёткой; вход под kali парализовать (passwd -l kali или AllowUsers).",
            "dod": "Инструкция записана (Workspace/pentest/, в git НЕ брать); в VM есть sudo-учётка, sshd пускает только её, kali/kali отключён."
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
          "Docs/KALI-PENTEST-PLAN-2026-10-31-ZCode.md (план фаз П-1…П-7, 31.10: Juice Shop как мишень, отчёты «атака/защита», локально-first)",
          "Docs/ASSESSMENT-2026-10-30-ZCode.md (раздел «Безопасность»)",
          "Memory/Engineering/Tasks/Active/study-ai-agents.json (агентность — смежный трек)"
        ],
        "history": [
          {
            "status": "active",
            "at": "2026-10-30T17:58:29Z",
            "note": "Создана ZCode по прямому указанию Дмитрия («сохрани как важную ToDo, займусь утром»); полный план установки + границы белого пентеста заложены в JSON."
          },
          {
            "status": "active",
            "at": "2026-10-31T17:20:13Z",
            "by": "ZCode",
            "note": "По команде Sovereign «сливай»: сюда слит дубль kali-pentest-lab-setup (31.10 17:14 Тшк — флаг «высочайший приоритет наравне с поиском работы» + план П-1…П-7); дубль перенесён в Tasks/Archive/. Приоритет urgent в силе. Шаги 1-4 (Фаза 0) — за Дмитрием; после снапшота clean-baseline стартуют П-1/П-4/П-5, хостовые П-2/П-3/П-6/П-7 можно вести уже сейчас."
          },
          {
            "status": "active",
            "at": "2026-11-01T10:15:00Z",
            "by": "ZCode",
            "note": "Шаги 1-3 ЗАКРЫТЫ Дмитрием 01.11: Kali поднят и обновлён (образ он скачал сам через торрент за 4 мин — ZCode качал HTTPS-ом ~час, не предложив торрент; урок в памяти big-downloads-torrent-first). НОВАЯ ПОДЗАДАЧА НА 01.11 (слово Дмитрия): ZCode подключается к VM и «чутка похозяйничает» — лёгкое хозяйство (среда, инструменты, shared folder, Juice Shop) по согласованию с Дмитрием; снапшот перед изменениями обязателен. Способ подключения уточнить у Дмитрия."
          },
          {
            "status": "active",
            "at": "2026-11-01T10:47:00+05:00",
            "by": "ZCode",
            "note": "Развёртка Дмитрия 01.11 ~10:40: Kali-хозяйство начнём ПОЗЖЕ (жена спит), пока записаны стартовые шаги. СТАРТОВЫЕ ШАГИ ХОЗЯЙСТВА (порядок, каждый — с отчётом): 0) Дмитрий запускает VM или даёт .vmx → ZCode запускает через vmrun; 1) снапшот clean-baseline через vmrun; 2) ШАГ 7: спец-учётка с sudo (подзадача в steps, вход kali/kali — закрыть); 3) sshd + ключ с хоста (пароли выключить); 4) docker + OWASP Juice Shop; 5) portproxy шлюза LLM :31415 в VM; 6) инструменты фаз П-1/П-4/П-5. Гипервизор подтверждён: VMware Workstation на хосте, VM 01.11 ~10:30 не запущена, .vmx в типичных местах не найден — путь спросить у Дмитрия. Развёртка по бюджету: 12 рабочих часов до сна, расход следит token_meter.py."
          },
          {
            "status": "done",
            "at": "2026-11-01T09:02:00Z"
          },
          {
            "status": "reopened",
            "stage": "todo",
            "at": "2026-11-01T09:02:33Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-01T09:03:21Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-01T09:03:47Z"
          },
          {
            "stage": "analysis",
            "at": "2026-11-03T08:57:26Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-03T08:57:27Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-04T06:13:19Z"
          },
          {
            "stage": "test",
            "at": "2026-11-04T06:13:35Z"
          }
        ],
        "stage": "test",
        "busy": null
      },
      {
        "id": "keepass-master-password-backup",
        "title": "Мастер-пароль KeePassXC + бэкап хранилища",
        "source": "S4",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          },
          {
            "stage": "analysis",
            "at": "2026-11-04T06:13:39Z"
          }
        ],
        "stage": "analysis",
        "busy": null
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
        ],
        "busy": null
      },
      {
        "id": "rotate-langsmith-freellmapi",
        "title": "Ротация ключей LangSmith/FreeLLMAPI",
        "source": "S1",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          },
          {
            "stage": "in-progress",
            "at": "2026-11-04T06:13:34Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-04T06:28:13Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-04T18:20:23Z",
            "note": "Аудит секретов 04.11 (E-046): реальные LangSmith и FreeLLMAPI ключи были в Workspace/main.py коммита 1164ed7 — он НЕ достижим из веток, держится в reflog, на origin не запушен (ключи не покидали хост). sk-ant в истории — только dummy-заглушка, не секрет. Срочность низкая. Ротация для Sovereign: 1) smith.langchain.com → Settings → API Keys → Create key → вписать в Workspace/.env (строки 11-12); 2) FreeLLMAPI-ключ перевыпустить в шлюзе :31415 → вписать в Workspace/.env:13. После ротации опционально: git reflog expire --expire-unreachable=now --all && git gc --prune=now — сотрёт 1164ed7 из локальной базы (осторожно: убьёт и чужие висячие объекты)."
          }
        ],
        "stage": "todo",
        "description": "Ротация LangSmith + FreeLLMAPI ключей (аудит 04.11: ключи в локальном reflog-коммите 1164ed7, origin чист; sk-ant — dummy)",
        "busy": null
      },
      {
        "id": "sec-todo-2026-11-05",
        "title": "Утро 05.11 — контур безопасности: выжимка дня и ToDo (ZCode)",
        "source": "ZCode/E-047",
        "priority": "urgent",
        "status": "active",
        "stage": "todo",
        "due": "2026-11-05",
        "createdAt": "2026-11-04T23:51:15+05:00",
        "history": [
          {
            "status": "active",
            "at": "2026-11-04T23:51:15+05:00",
            "by": "ZCode (E-047, выжимка по просьбе Sovereign)",
            "note": "ГОТОВО 04.11: (1) «Целевой стенд» в AI Sandbox → Инструменты — цели-чипы + галочки проверок → nmap_probe, прогон и скриншот ок (app.js?v=12, languages.js?v=3); (2) найден и закрыт routing-drift баг /api/sandbox/run (V-06), сервер 8765 перезапущен — ожили и эндпоинты E-046; (3) VULN-PROGRAM.md в Workspace/pentest/2026-11-04-vuln-program/ (вне git): 12 уязвимостей Platform + 12 индустриальных классов + фазы Ф-1..Ф-5; (4) Kali: VM headless 192.168.238.128, снапшот pre-pentest-2026-11-04, консоль-блок для шага 7 сохранён Дмитрием. || НА 05.11: [1] Ротация sk-ant руками Sovereign (V-01, P1, ~10 мин: панель Anthropic → новый ключ → Vault → правка Workspace/main.py:17) — критерий: secret_scan RED=0. [2] Консоль-блок Kali (учётка watson) → ZCode поднимает Juice Shop (target-server.sh) → скан 192.168.238.128 через стенд → фазовый отчёт в Workspace/pentest/2026-11-04-juiceshop/. [3] После ротации: слово на вычистку git-истории (filter-repo/BFG по sk-ant, 709b2c5). [4] Ф-1 остаток: rae-work HAR/chrome-profile под пароль/удалить (куки hh!), мастер-пароль на Vault, pre-commit hook secret_scan. [5] Коммит кода стенда — когда разобраны чужие правки в app.js/dashboard-server (сейчас не смешивать)."
          }
        ],
        "busy": null
      },
      {
        "id": "staff-hh-dashboard-loss",
        "title": "Штат/Code Reviewer: hh-вакансии не доходят до дашборда (пустая дата → вырезает [:60])",
        "source": "Staff/Code Reviewer",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-31T12:28:00Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-31T12:28:00Z",
            "by": "Code Reviewer (пилот штата, E-023)",
            "note": "P1: карточки hh из HTML-фолбэка получают date=''; parse_date даёт datetime.min; сортировка уносит их в хвост, слайс [:60] вырезает первыми. Верифицировано: results.json — 60 hh-записей, все с пустой датой; vacancies.js — 0 записей hh. Фикс: пустую дату подставлять временем запуска (hh-выдача отсортирована по свежести) или трактовать пустую дату как now в ключе сортировки. Файл: tools/job_search.py:133, 388, 400."
          }
        ],
        "busy": null
      }
    ],
    "regular": [
      {
        "id": "agents-fleet",
        "title": "«Флот в море» — дашборд запущенных агентов",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-05T00:35:00Z",
        "description": "Панель рейсов: события evo.agent.event в events.jsonl → GET /api/agents/live + agents.html «корабли в море». Метрики: лейны, пульс, штормы, ETA (~), итоги. Полное ТЗ: Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md. Старт: после сдачи data-foundation (нужен events.jsonl).",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T00:35:00Z",
            "by": "ZCode",
            "note": "Идея Sovereign 05.11 в чате. Заложена в Сделать; ждёт сдачи data-foundation."
          },
          {
            "stage": "test",
            "at": "2026-11-05T20:46:01Z",
            "by": "ZCode"
          }
        ],
        "stage": "test",
        "busy": null
      },
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
          },
          {
            "stage": "analysis",
            "at": "2026-11-01T06:49:12Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-01T06:49:41Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-01T08:56:07Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-01T08:56:08Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-01T09:06:57Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-01T09:07:02Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-01T09:07:06Z"
          },
          {
            "stage": "analysis",
            "at": "2026-11-01T09:07:07Z"
          },
          {
            "stage": "test",
            "at": "2026-11-01T09:07:08Z"
          },
          {
            "status": "done",
            "at": "2026-11-01T09:07:08Z"
          },
          {
            "status": "reopened",
            "stage": "test",
            "at": "2026-11-01T09:07:11Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-01T09:07:30Z"
          },
          {
            "stage": "test",
            "at": "2026-11-01T09:07:31Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-01T09:07:37Z"
          },
          {
            "stage": "analysis",
            "at": "2026-11-04T06:14:12Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-04T06:14:13Z"
          },
          {
            "stage": "analysis",
            "at": "2026-11-04T06:14:14Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-04T06:14:15Z"
          }
        ],
        "stage": "todo",
        "busy": null
      },
      {
        "id": "data-foundation",
        "title": "Фундамент данных: конверт артефактов + events.jsonl + реестр джобов + мастер-профиль",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-04T18:33:13Z",
        "description": "5 лейнов: Л-1 конверт артефактов (tools/lib/envelope.py), Л-2 машинный журнал событий (events.jsonl), Л-3 реестр джобов + API (ops/jobs.json), Л-4 мастер-профиль откликов (private/resume), Л-5 подписанные переходы канбана + метрики (by в history, kanban_metrics.py). Полное ТЗ: Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md. Исполнитель: суб-агент ZCode — берётся сразу при переводе в in-progress, по лейнам последовательно, git агенту запрещён, верификация ZCode.",
        "history": [
          {
            "status": "active",
            "at": "2026-11-04T18:33:13Z",
            "note": "Создана ZCode по слову Sovereign 04.11. Анализ выполнен (зачем и почему — в ТЗ). Агент-исполнитель стартует при переводе в in-progress."
          },
          {
            "stage": "in-progress",
            "at": "2026-11-04T18:56:24Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-05T00:17:00Z",
            "by": "ZCode",
            "note": "Исполнитель назначен: суб-агент ZCode. Прогресс лейнов см. Workspace/logs/events.jsonl после Л-2 и отчёт ZCode по завершении."
          },
          {
            "stage": "test",
            "at": "2026-11-04T19:45:08Z",
            "by": "ZCode"
          },
          {
            "stage": "test",
            "at": "2026-11-04T19:52:07Z",
            "by": "ZCode"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-05T19:47:33Z",
            "by": "ZCode"
          },
          {
            "stage": "test",
            "at": "2026-11-05T19:47:53Z",
            "by": "ZCode"
          }
        ],
        "stage": "test",
        "owner": "агент-строитель ZCode (Л-1…Л-5, старт 23:58)",
        "comments": [
          {
            "by": "Sovereign",
            "text": "Night shift accepted: envelope, journal, gates, busy-lock.",
            "at": "2026-11-05T20:06:23Z"
          },
          {
            "by": "Sovereign",
            "text": "Ночная смена принята: конверт, журнал, врата, busy-лок. ✅",
            "at": "2026-11-05T20:06:32Z"
          }
        ],
        "busy": null
      },
      {
        "id": "higgsfield-pilot-test",
        "title": "Higgsfield AI: пилотный тест «товар → ролик» (05.11.2026)",
        "source": "user",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-04T17:54:38Z",
        "dueNote": "Запланировано Дмитрием на 05.11.2026 («зафиксируй эту задачу на завтра»)",
        "description": "Контекст (исследование 04.11.2026, полное — в чате сессии ZCode; в репо Higgsfield НЕ внедрён, проверено grep): Higgsfield — AI-студия видео/изображений с API; главный рыночный сценарий — AI UGC-реклама для малого бизнеса (Upwork-категория «Higgsfield AI experts», $50–200/ролик, топ-исполнители $90K+). Marketing Studio: ссылка на товар → кампания из 1500+ шаблонов. Цель пилота: за один вечер проверить, может ли сервис стать производственным станком монетизации (рекламные креативы перекупам/СТО с OLX, витрина будущего OLX-подписного продукта, канал растра Soul 2 для будущих арт-задач). Регистрация и генерация — руками Дмитрия (ZCode аккаунты не регистрирует).",
        "steps": [
          {
            "n": 1,
            "do": "Дмитрий регистрируется на higgsfield.ai (Free-план; из сети хоста сервис доступен — проверено 04.11, гео-блока не видно; оплата не тестировалась — это Free, не нужна).",
            "dod": "Аккаунт создан, Marketing Studio открывается."
          },
          {
            "n": 2,
            "do": "Берём один реальный товар (например, с OLX или товар жены-художницы). Дмитрий делает 5–6 вариантов ролика в Marketing Studio, отбирает 1–2 лучших. Ожидание: качество нестабильное, отбор — обязательный шаг (рынок советует перебор вариантов).",
            "dod": "Есть 1–2 ролика, субъективно пригодных для показа."
          },
          {
            "n": 3,
            "do": "Показать ролик 2–3 потенциальным заказчикам (перекупы/СТО/знакомые малые бизнесы). Вопрос один: заплатили бы за такой $50–100? Сценарий ролика перед генерацией может писать ZCode (связка «LLM сценарий → Higgsfield видео» — стандарт агентств).",
            "dod": "Минимум один честный ответ потенциального платящего."
          },
          {
            "n": 4,
            "do": "Критерий решения: ≥1 платящий/горячий интерес → берем Plus $49/мес (1000 кредитов ≈ 28 клипов) и строим конвейер «товар → сценарий (ZCode) → генерация → отбор → клиент»; ноль интереса за 2–3 показа → тема закрывается дёшево, Higgsfield остаётся только как возможный растровый канал (Soul 2 API, $0.0032/кадр) на будущее.",
            "dod": "Решение Дмитрия зафиксировано в history карточки."
          }
        ],
        "constraints": [
          "Ничего не интегрировать в Platform до положительного исхода пилота: без tools/, без ключей в vault, без коммитов.",
          "API у Higgsfield живёт на отдельном долларовом балансе от кредитов сайта; кредиты/Unlimited-планы сайта в API не переносятся.",
          "Результаты API живут 7 дней — скачивать сразу (актуально при будущем внедрении).",
          "Кредиты на Free/платных тарифах горят быстро — перебор вариантов ограничивать, генерить пакетами.",
          "Коммерческое использование разрешено с платных планов; на Free — нет (учитывать при показе заказчикам: показ можно, продажа ролика — уже после Plus)."
        ],
        "links": [
          "https://higgsfield.ai/marketing-studio-intro (Marketing Studio: товар → кампания)",
          "https://www.upwork.com/hire/higgsfield-ai (рынок: категория исполнителей)",
          "https://www.wireflow.ai/blog/how-much-to-charge-clients-for-ai-ugc-ads (тарифы $50–200/ролик)",
          "https://higgsfield.ai/blog/higgsfield-pricing-explained (тарифы, проверено окт 2026: Free/Starter $15/Plus $49/Ultra $129)",
          "https://docs.higgsfield.ai (API-доки — для этапа внедрения, ЕСЛИ пилот успешен)"
        ],
        "history": [
          {
            "status": "active",
            "at": "2026-11-04T17:54:38Z",
            "by": "ZCode",
            "note": "Создана по команде Дмитрия 04.11 (~17:54 Тшк): «Зафиксируй эту задачу на завтра» — пилотный тест Higgsfield назначен на 05.11.2026. Дмитрий: «сейчас нам нужны более масштабные вещи» — т.е. пилот не в текущем фокусе. Полное исследование 04.11 (возможности, API, тарифы, права, доступность, альтернативы fal.ai/Runway, рыночный контекст UGC-хастла) — в чате сессии ZCode; в репо внедрений нет (grep 04.11 чист)."
          },
          {
            "stage": "in-progress",
            "at": "2026-11-05T01:00:00Z",
            "by": "ZCode",
            "note": "Старт агента-пилота: SDK-осмотр, один безопасный прогон (auth-check/dry-run, БЕЗ платных вызовов), полная документация. Живой кадр — после ключа от Sovereign."
          },
          {
            "stage": "test",
            "at": "2026-11-05T19:39:58Z",
            "by": "ZCode"
          }
        ],
        "stage": "test",
        "owner": "агент-пилот ZCode (Higgsfield SDK+docs, старт 05.11)",
        "busy": null
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
          },
          {
            "stage": "in-progress",
            "at": "2026-11-03T06:51:12Z"
          }
        ],
        "stage": "in-progress",
        "busy": null
      },
      {
        "id": "jobs-registry-hardening",
        "title": "Тех-долг реестра джобов: stale-running и типы полей (P2 ревизора)",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-05T20:07:02Z",
        "description": "Отчёт ревизора ночи: (1) dashboard-server.py:1148-1177 — running-статус джоба зависает навечно после краха сервера (daemon-поток умер, в jobs_state.json остался started_at без finished_at → вечный 409). Чинить: при старте сервера/чтении state считать запись мёртвой если started_at старше timeout_s+запас. (2) int(timeout_s) вне try + _load_jobs_registry не проверяет типы (timeout_s строка → 500). Чинить: валидация типов в загрузчике (timeout_s int>0, enabled bool). ПРАВИЛА: git запрещён, малые вставки, unittest зелёный (80 тестов), сервер 8765 не рестартовать (сделает вахтёр).",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T20:07:02Z",
            "by": "ZCode",
            "note": "Создана ZCode по задаче Sovereign (раздача на 4 ч, ночь 06.11)"
          }
        ],
        "stage": "todo",
        "busy": null
      },
      {
        "id": "master-profile-gaps",
        "title": "Заполнить 6 пробелов фактуры master-profile.json (конвейер откликов)",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-05T20:07:02Z",
        "description": "Файл: Workspace/private/resume/master-profile.json (зона данных Sovereign, вне git). Пробелы из todo-поля: (1) реальные цифры в 3 кейсах proposals/2026-11-04/ — помечены TODO; (2) ссылки-доказательства (репо, HAR, runbook); (3) preferences.rate/hours — своя ставка; (4) links: портфолио/GitHub/профили; (5) подтвердить «8+ лет» и уровень Kubernetes (противоречие откликов 03/07/09 vs 12); (6) какие навыки из «предлагаемого подхода» считать реальными. ПРАВИЛА: git запрещён; не выдумывать факты — только из существующих материалов Workspace/private/proposals/; чего нет — остаётся null/TODO с пометкой. Кейсы править в 2026-11-04/*.md синхронно с профилем.",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T20:07:02Z",
            "by": "ZCode",
            "note": "Создана ZCode по задаче Sovereign (раздача на 4 ч, ночь 06.11)"
          }
        ],
        "stage": "todo",
        "busy": null
      },
      {
        "id": "money-lanes-2026-11-05",
        "title": "Денежные лейны 05.11: выбор направления и MVP",
        "source": "user",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-04T19:35:00Z",
        "description": "Каталог монетизации IT-навыков Дмитрия (исследование ZCode 04.11.2026, интернет-проверка). Классы: A-услуги (A1 AI-автоматизации n8n/агенты — билд $1K-12K + ретейнер; A2 нишевые AI-агенты $199-799/мес; A3 скрапинг/лид-ген; A4 UGC-креативы Higgsfield $50-200/ролик), B-подписки (B1 AI-voice приёмка звонков SMB — себестоимость $0.01-0.10/мин, продажа $50-300/мес, маржа-спред; B2 OLX-мониторинг подпиской; B3 DevOps-абонентка $100-300/мес), C-физ+AI гибрид (AI-видеонаблюдение Frigate NVR: монтаж + edge-аналитика абоненткой $10-30/камера/мес — рынок $7B→$27B 2034), D-консалтинг (приватные LLM on-prem — 31% энтерпрайза ставят приватность №1; AI workflow-консалтинг $100+/час). Топ-3 ZCode: B1 voice-агенты, A1/A2 агенты-автоматизации, C камеры+Frigate. Связка: OLX-парсер приводит клиента → ему продаёшь voice-агента/камеры/креативы.",
        "steps": [
          {
            "n": 1,
            "do": "Дмитрий выбирает основной лейн (рекомендация: B1 voice-агент — маржа, масштаб, канал = OLX-клиенты).",
            "dod": "Лейн выбран, зафиксирован в history."
          },
          {
            "n": 2,
            "do": "ZCode расписывает MVP выбранного лейна: что берём готового, что дописываем, часы, чековая модель, первый клиент.",
            "dod": "MVP-план оформлен, первый шаг запущен."
          },
          {
            "n": 3,
            "do": "Первый платящий/проявленный клиент — критерий жизнеспособности лейна.",
            "dod": "Клиент есть или лейн закрыт с выводом."
          }
        ],
        "constraints": [
          "Higgsfield-пилот (карточка higgsfield-pilot-test) — отдельный лейн A4, не смешивать.",
          "УЗ-цены (камеры, монтаж, голос-минуты) не подтверждены поиском — только западные ориентиры, помечать как оценку."
        ],
        "links": [
          "https://zapsstudio.com/resources/best-workflow-agencies-2026",
          "https://pickaxe.co/post/monetize-ai-agents-2026",
          "https://www.fortunebusinessinsights.com/ai-video-surveillance-market-106741",
          "https://www.dreamfactory.com/hub/on-premise-llm-deployment-statistics",
          "Memory/Engineering/Tasks/Active/higgsfield-pilot-test.json (лейн A4)"
        ],
        "history": [
          {
            "status": "active",
            "at": "2026-11-04T19:35:00Z",
            "by": "ZCode",
            "note": "Создана по команде Дмитрия 04.11 ~19:35 Тшк («запиши все это в задачу на завтра») — каталог денежных лейнов из интернет-исследования «как зарабатывают AI-айтишники 2026»."
          },
          {
            "status": "active",
            "at": "2026-11-06T00:40:00Z",
            "by": "ZCode",
            "note": "Ночная «десятка агентов» исполнена 10/10 по команде Дмитрия («запустить десяток агентов, чтобы жрали токены с пользой»): ресёрч R1 voice (Vapi+свой шлюз, себест. $0.02-0.09/мин, узкое место UZ-номера — Telnyx от $50/мес, узб. язык не готов → MVP на русском), R2 Frigate (N100 тянет 6-8 камер, LPR встроен 0.16, демо $560-1150, RMR $15-40/объект, аргумент ЗРУ-547), R3 прайс-карта (Kwork демпинг 500₽, Upwork n8n+AI $100-180/ч, OLX УЗ живой 135+ объявлений, вход: парсер 5-8K₽/бот 12-18K₽/AI-автоматизация 25-50K₽), R4 n8n-пакеты («Заявка под контролем» 45-70K₽, «Репутация» 60-90K₽, «Цифровой офис» 90-150K₽ + абонентка), R5 приватные LLM (Qwen3+vLLM, MoE на CPU €45-90/мес, ВАЖНО: УЗ отменил локализацию персданных 03.2026 — продавать через ТКО и коммерч. тайну), C1 объявления 4 площадок, C2 сценарии звонков СТО/клиника, C3 кейсы+резюме RU/EN, K1 код-скелет voice-агента (FastAPI+Vapi Custom LLM+Telegram), K2 план Frigate-стенда (демо без железа на mp4-цикле). Артефакты: Workspace/analytics/research/_agents-2026-11-04/ (сводка SUMMARY-utro-2026-11-05.md). Расход ~6.87M. Гочи: спавн только последовательно (пары рвёт concurrency), сон хоста убивает фон."
          }
        ],
        "stage": "analysis",
        "busy": null
      },
      {
        "id": "morning-review-agent-diagnostics",
        "title": "Утро: ознакомиться с диагностикой параллельных агентов (04.11)",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "stage": "todo",
        "createdAt": "2026-11-04T18:53:39Z",
        "description": "Результат диагностики 04.11 ~23:45 (вопрос Дмитрия «у нас запущены параллельные агенты?»). ВЕРДИКТ: работающих агентов НЕТ, кроме одной параллельной ZCode-сессии (sess_d092a1db, активна — E-045, app.js v12).\n\nПо слоям:\n1. Платформенные рантаймы: Holmes/Watson/RiskScan — running:false у всех; последний прогон RiskScan 23:40:17→23:40:36, код 0.\n2. Python-процессы: только dashboard-server.py (норма) + hermes_cli.main gateway run (PID 2972, порт 45616) — не наш агент, локальный шлюз инструментария.\n3. Планировщик ОС: одна запись «Barrymore Dashboard Server» (триггер на логон). Risk-крона в системе нет.\n4. ZCode-автоматизации: обе enabled=false — ночной насос-сторож (failed, ночь 01→02.11 кончилась) и «проверка знаний 20:30» (paused). Поводок подтверждён.\n5. Свежая фактура C:/Users/temp/.zcode/cli/rollout/model-io-*.jsonl (mtime <30 мин): наша сессия, суб-агент, параллельная сессия d092a1db.\n\nШпаргалка самопроверки (описана Дмитрию в чате 04.11): curl /api/<holmes|watson|riskscan>/run-status; лог %LOCALAPPDATA%/Platform/Barrymore/dashboard-server.log; Get-CimInstance Win32_Process (python%); schtasks; sqlite tasks-index.sqlite → automations.enabled; mtime model-io-*.jsonl.\n\nСвязь: утром — сверить, что картина не изменилась, и решить вопрос «почему агенты не работают сами» (обсуждение 04.11: снятие поводка ступенями).",
        "history": [
          {
            "stage": "todo",
            "at": "2026-11-04T18:53:39Z",
            "by": "Sovereign",
            "note": "Создано по просьбе Дмитрия «запиши результат и оставь на утро задачу — еще раз ознакомиться»"
          }
        ],
        "busy": null
      },
      {
        "id": "resume-pipeline-collision",
        "title": "Коллизия двойного исполнения: найти профиль «Резюме-конвейера»",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-05T20:07:02Z",
        "description": "Контекст: ночью суб-агент «Резюме-конвейер» соседней сессии Sovereign исполнял (вероятно) лейн Л-4 параллельно с ночным писарем — возможен второй master-profile.json или черновики вне канона. ЗАДАЧА: обследовать Workspace/private/resume/ и workspace-черновики параллельных сессий; найти артефакты «Резюме-конвейера»; свести в один канон (канон = Workspace/private/resume/master-profile.json от ночного писаря, 27 навыков/5 кейсов); чужие черновики — не удалить, а влить недостающее и пометить merged. ОТЧЁТ: список найденных артефактов + что влито. Git запрещён; приватную зону наружу не выносить.",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T20:07:02Z",
            "by": "ZCode",
            "note": "Создана ZCode по задаче Sovereign (раздача на 4 ч, ночь 06.11)"
          }
        ],
        "stage": "todo",
        "busy": null
      },
      {
        "id": "staff-agents-2026-11-05",
        "title": "Личный штат +2: DevOps Automator и Technical Writer — разбор для Sovereign",
        "source": "ZCode/санкция Sovereign «Поставь парочку полезных агентов»",
        "priority": "regular",
        "status": "active",
        "stage": "todo",
        "due": "2026-11-05",
        "createdAt": "2026-11-05T00:19:59+05:00",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T00:19:59+05:00",
            "by": "ZCode",
            "note": "Установлены в ~/.zcode/agents/ из каталога agency-agents (230+): engineering-devops-automator.md и engineering-technical-writer.md. Штат: 8 ролей. Зачем: (1) DevOps Automator — инфраструктурная автоматизация, CI/CD, операции: родная стихия Дмитрия, усилит tools/ops (бэкап/healthcheck), переезд Platform на хостинг (план fffc974), рутину вакансий DevOps; (2) Technical Writer — документация, README, гайды: закрывает БЛОКЕР №1 поиска работы (3 кейса для резюме + визитка в Workspace/private/resume/), описания услуг/откликов, устаревшие README Platform. Как работают: как остальные 6 — вызов в ZCode-окне (агент = роль с промптом; рантайма как у Холмса/Хантера нет и не нужно), привязка к задаче → прогон → отчёт. НОВЫЕ ТИПЫ УЖЕ ВИДНЫ СИСТЕМЕ БЕЗ ПЕРЕЗАПУСКА (хост подхватил живьём). Смоук 05.11 00:2x: Technical Writer живой — микрозадача справки за 88 сек / ~22k токенов, чистый русский текст + «СМОУК ОК»; первая попытка упёрлась в «user concurrency limit» (слот соседнего чата) — повтор через 45 с прошёл. Утром: демонстрация по живой задаче (кейс №1 для резюме техписателем, healthcheck-скрипт девопсом)."
          }
        ],
        "busy": null
      },
      {
        "id": "staff-secrets-rotation",
        "title": "Штат/Secrets Engineer: копии ключей в артефактах ZCode-сессии → ротация",
        "source": "Staff/Secrets Engineer",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-10-31T12:28:00Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-31T12:28:00Z",
            "by": "Secrets & Credential Hygiene Engineer (пилот штата, E-023)",
            "note": "P1: реальные LANGSMITH_API_KEY и FREE_LLM_API_KEY лежат plaintext в C:/Users/temp/.zcode/cli/artifacts/session_c87212841fb8241f72e3dd5a6f5e7333/ (call_99ddca97… — эхо .env, call_fcdf812e…). Git-история чиста (P0 нет, 262 коммита). Действия по санкции Sovereign: (1) удалить два artifact-файла; (2) ротировать LANGSMITH_API_KEY (smith.langchain.com) и FREE_LLM_API_KEY (шлюз :31415); (3) обновить Workspace/.env и KeePassXC. P2: pre-commit сканер (gitleaks); заглушку sk-… из Workspace/main.py:17 убрать из tracked-кода."
          }
        ],
        "busy": null
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
        ],
        "busy": null
      },
      {
        "id": "task-lock-hardening",
        "title": "Тех-долг task_lock: валидация task_id, докстринг журнала, кран тестов (P2 ревизора)",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-05T20:07:02Z",
        "description": "Отчёт ревизора ночи: (1) tools/lib/task_lock.py — task_id нигде не валидируется: путь-траверсал ../.. и glob-инъекция *?[ в acquire/heartbeat/release/status/claims. Чинить: отклонять task_id с /, \\, .., glob-метасимволами (по образцу TASK_ID_PATTERN из task_store). (2) tools/lib/log_event.py:8-10 — докстринг противоречит фиксу Д-2 (обновить, оговорка про многопроцессную запись). (3) тесты TaskLockTest пишут в ПРОДОВЫЙ events.jsonl — завести кран (параметр journal_path/монки-патч). ПРАВИЛА: git запрещён, unittest зелёный, сервер не трогать.",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T20:07:02Z",
            "by": "ZCode",
            "note": "Создана ZCode по задаче Sovereign (раздача на 4 ч, ночь 06.11)"
          }
        ],
        "stage": "todo",
        "busy": null
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
          },
          {
            "stage": "in-progress",
            "at": "2026-11-04T06:28:17Z"
          }
        ],
        "stage": "in-progress",
        "busy": null
      }
    ],
    "done": [
      {
        "id": "merge-branches-d002",
        "title": "Слияние веток по D-002",
        "source": "R9",
        "priority": "regular",
        "status": "done",
        "completedAt": "2026-11-04T18:36:05Z",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          },
          {
            "stage": "in-progress",
            "at": "2026-11-03T06:36:52Z"
          },
          {
            "stage": "test",
            "at": "2026-11-03T06:43:22Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-03T06:43:24Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-03T06:51:13Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-04T06:13:21Z"
          },
          {
            "stage": "done",
            "at": "2026-11-04T18:36:05Z",
            "by": "Sovereign",
            "note": "Закрыто 04.11 (E-046): merge origin/main (PR #2) в feature_1.8.6 → push origin/main (5057dcb), локальная main создана, ветки feature_1.8.6/1.8.5/1.8.2 удалены локально и на origin. Работа продолжается на main."
          }
        ],
        "stage": "in-progress",
        "busy": null
      }
    ],
    "all": [
      {
        "id": "agents-fleet",
        "title": "«Флот в море» — дашборд запущенных агентов",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-05T00:35:00Z",
        "description": "Панель рейсов: события evo.agent.event в events.jsonl → GET /api/agents/live + agents.html «корабли в море». Метрики: лейны, пульс, штормы, ETA (~), итоги. Полное ТЗ: Docs/AGENT-FLEET-PLAN-2026-11-05-ZCode.md. Старт: после сдачи data-foundation (нужен events.jsonl).",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T00:35:00Z",
            "by": "ZCode",
            "note": "Идея Sovereign 05.11 в чате. Заложена в Сделать; ждёт сдачи data-foundation."
          },
          {
            "stage": "test",
            "at": "2026-11-05T20:46:01Z",
            "by": "ZCode"
          }
        ],
        "stage": "test",
        "busy": null
      },
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
          },
          {
            "stage": "analysis",
            "at": "2026-11-01T06:49:12Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-01T06:49:41Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-01T08:56:07Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-01T08:56:08Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-01T09:06:57Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-01T09:07:02Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-01T09:07:06Z"
          },
          {
            "stage": "analysis",
            "at": "2026-11-01T09:07:07Z"
          },
          {
            "stage": "test",
            "at": "2026-11-01T09:07:08Z"
          },
          {
            "status": "done",
            "at": "2026-11-01T09:07:08Z"
          },
          {
            "status": "reopened",
            "stage": "test",
            "at": "2026-11-01T09:07:11Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-01T09:07:30Z"
          },
          {
            "stage": "test",
            "at": "2026-11-01T09:07:31Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-01T09:07:37Z"
          },
          {
            "stage": "analysis",
            "at": "2026-11-04T06:14:12Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-04T06:14:13Z"
          },
          {
            "stage": "analysis",
            "at": "2026-11-04T06:14:14Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-04T06:14:15Z"
          }
        ],
        "stage": "todo",
        "busy": null
      },
      {
        "id": "data-foundation",
        "title": "Фундамент данных: конверт артефактов + events.jsonl + реестр джобов + мастер-профиль",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-04T18:33:13Z",
        "description": "5 лейнов: Л-1 конверт артефактов (tools/lib/envelope.py), Л-2 машинный журнал событий (events.jsonl), Л-3 реестр джобов + API (ops/jobs.json), Л-4 мастер-профиль откликов (private/resume), Л-5 подписанные переходы канбана + метрики (by в history, kanban_metrics.py). Полное ТЗ: Docs/DATA-FOUNDATION-PLAN-2026-11-04-ZCode.md. Исполнитель: суб-агент ZCode — берётся сразу при переводе в in-progress, по лейнам последовательно, git агенту запрещён, верификация ZCode.",
        "history": [
          {
            "status": "active",
            "at": "2026-11-04T18:33:13Z",
            "note": "Создана ZCode по слову Sovereign 04.11. Анализ выполнен (зачем и почему — в ТЗ). Агент-исполнитель стартует при переводе в in-progress."
          },
          {
            "stage": "in-progress",
            "at": "2026-11-04T18:56:24Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-05T00:17:00Z",
            "by": "ZCode",
            "note": "Исполнитель назначен: суб-агент ZCode. Прогресс лейнов см. Workspace/logs/events.jsonl после Л-2 и отчёт ZCode по завершении."
          },
          {
            "stage": "test",
            "at": "2026-11-04T19:45:08Z",
            "by": "ZCode"
          },
          {
            "stage": "test",
            "at": "2026-11-04T19:52:07Z",
            "by": "ZCode"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-05T19:47:33Z",
            "by": "ZCode"
          },
          {
            "stage": "test",
            "at": "2026-11-05T19:47:53Z",
            "by": "ZCode"
          }
        ],
        "stage": "test",
        "owner": "агент-строитель ZCode (Л-1…Л-5, старт 23:58)",
        "comments": [
          {
            "by": "Sovereign",
            "text": "Night shift accepted: envelope, journal, gates, busy-lock.",
            "at": "2026-11-05T20:06:23Z"
          },
          {
            "by": "Sovereign",
            "text": "Ночная смена принята: конверт, журнал, врата, busy-лок. ✅",
            "at": "2026-11-05T20:06:32Z"
          }
        ],
        "busy": null
      },
      {
        "id": "higgsfield-pilot-test",
        "title": "Higgsfield AI: пилотный тест «товар → ролик» (05.11.2026)",
        "source": "user",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-04T17:54:38Z",
        "dueNote": "Запланировано Дмитрием на 05.11.2026 («зафиксируй эту задачу на завтра»)",
        "description": "Контекст (исследование 04.11.2026, полное — в чате сессии ZCode; в репо Higgsfield НЕ внедрён, проверено grep): Higgsfield — AI-студия видео/изображений с API; главный рыночный сценарий — AI UGC-реклама для малого бизнеса (Upwork-категория «Higgsfield AI experts», $50–200/ролик, топ-исполнители $90K+). Marketing Studio: ссылка на товар → кампания из 1500+ шаблонов. Цель пилота: за один вечер проверить, может ли сервис стать производственным станком монетизации (рекламные креативы перекупам/СТО с OLX, витрина будущего OLX-подписного продукта, канал растра Soul 2 для будущих арт-задач). Регистрация и генерация — руками Дмитрия (ZCode аккаунты не регистрирует).",
        "steps": [
          {
            "n": 1,
            "do": "Дмитрий регистрируется на higgsfield.ai (Free-план; из сети хоста сервис доступен — проверено 04.11, гео-блока не видно; оплата не тестировалась — это Free, не нужна).",
            "dod": "Аккаунт создан, Marketing Studio открывается."
          },
          {
            "n": 2,
            "do": "Берём один реальный товар (например, с OLX или товар жены-художницы). Дмитрий делает 5–6 вариантов ролика в Marketing Studio, отбирает 1–2 лучших. Ожидание: качество нестабильное, отбор — обязательный шаг (рынок советует перебор вариантов).",
            "dod": "Есть 1–2 ролика, субъективно пригодных для показа."
          },
          {
            "n": 3,
            "do": "Показать ролик 2–3 потенциальным заказчикам (перекупы/СТО/знакомые малые бизнесы). Вопрос один: заплатили бы за такой $50–100? Сценарий ролика перед генерацией может писать ZCode (связка «LLM сценарий → Higgsfield видео» — стандарт агентств).",
            "dod": "Минимум один честный ответ потенциального платящего."
          },
          {
            "n": 4,
            "do": "Критерий решения: ≥1 платящий/горячий интерес → берем Plus $49/мес (1000 кредитов ≈ 28 клипов) и строим конвейер «товар → сценарий (ZCode) → генерация → отбор → клиент»; ноль интереса за 2–3 показа → тема закрывается дёшево, Higgsfield остаётся только как возможный растровый канал (Soul 2 API, $0.0032/кадр) на будущее.",
            "dod": "Решение Дмитрия зафиксировано в history карточки."
          }
        ],
        "constraints": [
          "Ничего не интегрировать в Platform до положительного исхода пилота: без tools/, без ключей в vault, без коммитов.",
          "API у Higgsfield живёт на отдельном долларовом балансе от кредитов сайта; кредиты/Unlimited-планы сайта в API не переносятся.",
          "Результаты API живут 7 дней — скачивать сразу (актуально при будущем внедрении).",
          "Кредиты на Free/платных тарифах горят быстро — перебор вариантов ограничивать, генерить пакетами.",
          "Коммерческое использование разрешено с платных планов; на Free — нет (учитывать при показе заказчикам: показ можно, продажа ролика — уже после Plus)."
        ],
        "links": [
          "https://higgsfield.ai/marketing-studio-intro (Marketing Studio: товар → кампания)",
          "https://www.upwork.com/hire/higgsfield-ai (рынок: категория исполнителей)",
          "https://www.wireflow.ai/blog/how-much-to-charge-clients-for-ai-ugc-ads (тарифы $50–200/ролик)",
          "https://higgsfield.ai/blog/higgsfield-pricing-explained (тарифы, проверено окт 2026: Free/Starter $15/Plus $49/Ultra $129)",
          "https://docs.higgsfield.ai (API-доки — для этапа внедрения, ЕСЛИ пилот успешен)"
        ],
        "history": [
          {
            "status": "active",
            "at": "2026-11-04T17:54:38Z",
            "by": "ZCode",
            "note": "Создана по команде Дмитрия 04.11 (~17:54 Тшк): «Зафиксируй эту задачу на завтра» — пилотный тест Higgsfield назначен на 05.11.2026. Дмитрий: «сейчас нам нужны более масштабные вещи» — т.е. пилот не в текущем фокусе. Полное исследование 04.11 (возможности, API, тарифы, права, доступность, альтернативы fal.ai/Runway, рыночный контекст UGC-хастла) — в чате сессии ZCode; в репо внедрений нет (grep 04.11 чист)."
          },
          {
            "stage": "in-progress",
            "at": "2026-11-05T01:00:00Z",
            "by": "ZCode",
            "note": "Старт агента-пилота: SDK-осмотр, один безопасный прогон (auth-check/dry-run, БЕЗ платных вызовов), полная документация. Живой кадр — после ключа от Sovereign."
          },
          {
            "stage": "test",
            "at": "2026-11-05T19:39:58Z",
            "by": "ZCode"
          }
        ],
        "stage": "test",
        "owner": "агент-пилот ZCode (Higgsfield SDK+docs, старт 05.11)",
        "busy": null
      },
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
          },
          {
            "stage": "analysis",
            "at": "2026-11-01T08:56:15Z"
          }
        ],
        "stage": "analysis",
        "busy": null
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
          },
          {
            "stage": "in-progress",
            "at": "2026-11-03T06:51:12Z"
          }
        ],
        "stage": "in-progress",
        "busy": null
      },
      {
        "id": "jobs-registry-hardening",
        "title": "Тех-долг реестра джобов: stale-running и типы полей (P2 ревизора)",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-05T20:07:02Z",
        "description": "Отчёт ревизора ночи: (1) dashboard-server.py:1148-1177 — running-статус джоба зависает навечно после краха сервера (daemon-поток умер, в jobs_state.json остался started_at без finished_at → вечный 409). Чинить: при старте сервера/чтении state считать запись мёртвой если started_at старше timeout_s+запас. (2) int(timeout_s) вне try + _load_jobs_registry не проверяет типы (timeout_s строка → 500). Чинить: валидация типов в загрузчике (timeout_s int>0, enabled bool). ПРАВИЛА: git запрещён, малые вставки, unittest зелёный (80 тестов), сервер 8765 не рестартовать (сделает вахтёр).",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T20:07:02Z",
            "by": "ZCode",
            "note": "Создана ZCode по задаче Sovereign (раздача на 4 ч, ночь 06.11)"
          }
        ],
        "stage": "todo",
        "busy": null
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
          },
          {
            "n": 7,
            "do": "СПЕЦ-УЧЁТКА (поручение Дмитрия 01.11 ~10:40, вход kali/kali несекьюрен): 1) написать инструкцию — создать отдельного пользователя с рутовыми правами через sudo (например `adduser ops` + `usermod -aG sudo ops`, проверка `sudo -v`; пароль НЕ совпадающий с kali; sshd ограничить AllowUsers на новую учётку); 2) применить в VM после снапшота clean-baseline; 3) ZCode/агенты ходят в VM только под спец-учёткой; вход под kali парализовать (passwd -l kali или AllowUsers).",
            "dod": "Инструкция записана (Workspace/pentest/, в git НЕ брать); в VM есть sudo-учётка, sshd пускает только её, kali/kali отключён."
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
          "Docs/KALI-PENTEST-PLAN-2026-10-31-ZCode.md (план фаз П-1…П-7, 31.10: Juice Shop как мишень, отчёты «атака/защита», локально-first)",
          "Docs/ASSESSMENT-2026-10-30-ZCode.md (раздел «Безопасность»)",
          "Memory/Engineering/Tasks/Active/study-ai-agents.json (агентность — смежный трек)"
        ],
        "history": [
          {
            "status": "active",
            "at": "2026-10-30T17:58:29Z",
            "note": "Создана ZCode по прямому указанию Дмитрия («сохрани как важную ToDo, займусь утром»); полный план установки + границы белого пентеста заложены в JSON."
          },
          {
            "status": "active",
            "at": "2026-10-31T17:20:13Z",
            "by": "ZCode",
            "note": "По команде Sovereign «сливай»: сюда слит дубль kali-pentest-lab-setup (31.10 17:14 Тшк — флаг «высочайший приоритет наравне с поиском работы» + план П-1…П-7); дубль перенесён в Tasks/Archive/. Приоритет urgent в силе. Шаги 1-4 (Фаза 0) — за Дмитрием; после снапшота clean-baseline стартуют П-1/П-4/П-5, хостовые П-2/П-3/П-6/П-7 можно вести уже сейчас."
          },
          {
            "status": "active",
            "at": "2026-11-01T10:15:00Z",
            "by": "ZCode",
            "note": "Шаги 1-3 ЗАКРЫТЫ Дмитрием 01.11: Kali поднят и обновлён (образ он скачал сам через торрент за 4 мин — ZCode качал HTTPS-ом ~час, не предложив торрент; урок в памяти big-downloads-torrent-first). НОВАЯ ПОДЗАДАЧА НА 01.11 (слово Дмитрия): ZCode подключается к VM и «чутка похозяйничает» — лёгкое хозяйство (среда, инструменты, shared folder, Juice Shop) по согласованию с Дмитрием; снапшот перед изменениями обязателен. Способ подключения уточнить у Дмитрия."
          },
          {
            "status": "active",
            "at": "2026-11-01T10:47:00+05:00",
            "by": "ZCode",
            "note": "Развёртка Дмитрия 01.11 ~10:40: Kali-хозяйство начнём ПОЗЖЕ (жена спит), пока записаны стартовые шаги. СТАРТОВЫЕ ШАГИ ХОЗЯЙСТВА (порядок, каждый — с отчётом): 0) Дмитрий запускает VM или даёт .vmx → ZCode запускает через vmrun; 1) снапшот clean-baseline через vmrun; 2) ШАГ 7: спец-учётка с sudo (подзадача в steps, вход kali/kali — закрыть); 3) sshd + ключ с хоста (пароли выключить); 4) docker + OWASP Juice Shop; 5) portproxy шлюза LLM :31415 в VM; 6) инструменты фаз П-1/П-4/П-5. Гипервизор подтверждён: VMware Workstation на хосте, VM 01.11 ~10:30 не запущена, .vmx в типичных местах не найден — путь спросить у Дмитрия. Развёртка по бюджету: 12 рабочих часов до сна, расход следит token_meter.py."
          },
          {
            "status": "done",
            "at": "2026-11-01T09:02:00Z"
          },
          {
            "status": "reopened",
            "stage": "todo",
            "at": "2026-11-01T09:02:33Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-01T09:03:21Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-01T09:03:47Z"
          },
          {
            "stage": "analysis",
            "at": "2026-11-03T08:57:26Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-03T08:57:27Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-04T06:13:19Z"
          },
          {
            "stage": "test",
            "at": "2026-11-04T06:13:35Z"
          }
        ],
        "stage": "test",
        "busy": null
      },
      {
        "id": "keepass-master-password-backup",
        "title": "Мастер-пароль KeePassXC + бэкап хранилища",
        "source": "S4",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          },
          {
            "stage": "analysis",
            "at": "2026-11-04T06:13:39Z"
          }
        ],
        "stage": "analysis",
        "busy": null
      },
      {
        "id": "master-profile-gaps",
        "title": "Заполнить 6 пробелов фактуры master-profile.json (конвейер откликов)",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-05T20:07:02Z",
        "description": "Файл: Workspace/private/resume/master-profile.json (зона данных Sovereign, вне git). Пробелы из todo-поля: (1) реальные цифры в 3 кейсах proposals/2026-11-04/ — помечены TODO; (2) ссылки-доказательства (репо, HAR, runbook); (3) preferences.rate/hours — своя ставка; (4) links: портфолио/GitHub/профили; (5) подтвердить «8+ лет» и уровень Kubernetes (противоречие откликов 03/07/09 vs 12); (6) какие навыки из «предлагаемого подхода» считать реальными. ПРАВИЛА: git запрещён; не выдумывать факты — только из существующих материалов Workspace/private/proposals/; чего нет — остаётся null/TODO с пометкой. Кейсы править в 2026-11-04/*.md синхронно с профилем.",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T20:07:02Z",
            "by": "ZCode",
            "note": "Создана ZCode по задаче Sovereign (раздача на 4 ч, ночь 06.11)"
          }
        ],
        "stage": "todo",
        "busy": null
      },
      {
        "id": "merge-branches-d002",
        "title": "Слияние веток по D-002",
        "source": "R9",
        "priority": "regular",
        "status": "done",
        "completedAt": "2026-11-04T18:36:05Z",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          },
          {
            "stage": "in-progress",
            "at": "2026-11-03T06:36:52Z"
          },
          {
            "stage": "test",
            "at": "2026-11-03T06:43:22Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-03T06:43:24Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-03T06:51:13Z"
          },
          {
            "stage": "in-progress",
            "at": "2026-11-04T06:13:21Z"
          },
          {
            "stage": "done",
            "at": "2026-11-04T18:36:05Z",
            "by": "Sovereign",
            "note": "Закрыто 04.11 (E-046): merge origin/main (PR #2) в feature_1.8.6 → push origin/main (5057dcb), локальная main создана, ветки feature_1.8.6/1.8.5/1.8.2 удалены локально и на origin. Работа продолжается на main."
          }
        ],
        "stage": "in-progress",
        "busy": null
      },
      {
        "id": "money-lanes-2026-11-05",
        "title": "Денежные лейны 05.11: выбор направления и MVP",
        "source": "user",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-04T19:35:00Z",
        "description": "Каталог монетизации IT-навыков Дмитрия (исследование ZCode 04.11.2026, интернет-проверка). Классы: A-услуги (A1 AI-автоматизации n8n/агенты — билд $1K-12K + ретейнер; A2 нишевые AI-агенты $199-799/мес; A3 скрапинг/лид-ген; A4 UGC-креативы Higgsfield $50-200/ролик), B-подписки (B1 AI-voice приёмка звонков SMB — себестоимость $0.01-0.10/мин, продажа $50-300/мес, маржа-спред; B2 OLX-мониторинг подпиской; B3 DevOps-абонентка $100-300/мес), C-физ+AI гибрид (AI-видеонаблюдение Frigate NVR: монтаж + edge-аналитика абоненткой $10-30/камера/мес — рынок $7B→$27B 2034), D-консалтинг (приватные LLM on-prem — 31% энтерпрайза ставят приватность №1; AI workflow-консалтинг $100+/час). Топ-3 ZCode: B1 voice-агенты, A1/A2 агенты-автоматизации, C камеры+Frigate. Связка: OLX-парсер приводит клиента → ему продаёшь voice-агента/камеры/креативы.",
        "steps": [
          {
            "n": 1,
            "do": "Дмитрий выбирает основной лейн (рекомендация: B1 voice-агент — маржа, масштаб, канал = OLX-клиенты).",
            "dod": "Лейн выбран, зафиксирован в history."
          },
          {
            "n": 2,
            "do": "ZCode расписывает MVP выбранного лейна: что берём готового, что дописываем, часы, чековая модель, первый клиент.",
            "dod": "MVP-план оформлен, первый шаг запущен."
          },
          {
            "n": 3,
            "do": "Первый платящий/проявленный клиент — критерий жизнеспособности лейна.",
            "dod": "Клиент есть или лейн закрыт с выводом."
          }
        ],
        "constraints": [
          "Higgsfield-пилот (карточка higgsfield-pilot-test) — отдельный лейн A4, не смешивать.",
          "УЗ-цены (камеры, монтаж, голос-минуты) не подтверждены поиском — только западные ориентиры, помечать как оценку."
        ],
        "links": [
          "https://zapsstudio.com/resources/best-workflow-agencies-2026",
          "https://pickaxe.co/post/monetize-ai-agents-2026",
          "https://www.fortunebusinessinsights.com/ai-video-surveillance-market-106741",
          "https://www.dreamfactory.com/hub/on-premise-llm-deployment-statistics",
          "Memory/Engineering/Tasks/Active/higgsfield-pilot-test.json (лейн A4)"
        ],
        "history": [
          {
            "status": "active",
            "at": "2026-11-04T19:35:00Z",
            "by": "ZCode",
            "note": "Создана по команде Дмитрия 04.11 ~19:35 Тшк («запиши все это в задачу на завтра») — каталог денежных лейнов из интернет-исследования «как зарабатывают AI-айтишники 2026»."
          },
          {
            "status": "active",
            "at": "2026-11-06T00:40:00Z",
            "by": "ZCode",
            "note": "Ночная «десятка агентов» исполнена 10/10 по команде Дмитрия («запустить десяток агентов, чтобы жрали токены с пользой»): ресёрч R1 voice (Vapi+свой шлюз, себест. $0.02-0.09/мин, узкое место UZ-номера — Telnyx от $50/мес, узб. язык не готов → MVP на русском), R2 Frigate (N100 тянет 6-8 камер, LPR встроен 0.16, демо $560-1150, RMR $15-40/объект, аргумент ЗРУ-547), R3 прайс-карта (Kwork демпинг 500₽, Upwork n8n+AI $100-180/ч, OLX УЗ живой 135+ объявлений, вход: парсер 5-8K₽/бот 12-18K₽/AI-автоматизация 25-50K₽), R4 n8n-пакеты («Заявка под контролем» 45-70K₽, «Репутация» 60-90K₽, «Цифровой офис» 90-150K₽ + абонентка), R5 приватные LLM (Qwen3+vLLM, MoE на CPU €45-90/мес, ВАЖНО: УЗ отменил локализацию персданных 03.2026 — продавать через ТКО и коммерч. тайну), C1 объявления 4 площадок, C2 сценарии звонков СТО/клиника, C3 кейсы+резюме RU/EN, K1 код-скелет voice-агента (FastAPI+Vapi Custom LLM+Telegram), K2 план Frigate-стенда (демо без железа на mp4-цикле). Артефакты: Workspace/analytics/research/_agents-2026-11-04/ (сводка SUMMARY-utro-2026-11-05.md). Расход ~6.87M. Гочи: спавн только последовательно (пары рвёт concurrency), сон хоста убивает фон."
          }
        ],
        "stage": "analysis",
        "busy": null
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
        ],
        "busy": null
      },
      {
        "id": "morning-review-agent-diagnostics",
        "title": "Утро: ознакомиться с диагностикой параллельных агентов (04.11)",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "stage": "todo",
        "createdAt": "2026-11-04T18:53:39Z",
        "description": "Результат диагностики 04.11 ~23:45 (вопрос Дмитрия «у нас запущены параллельные агенты?»). ВЕРДИКТ: работающих агентов НЕТ, кроме одной параллельной ZCode-сессии (sess_d092a1db, активна — E-045, app.js v12).\n\nПо слоям:\n1. Платформенные рантаймы: Holmes/Watson/RiskScan — running:false у всех; последний прогон RiskScan 23:40:17→23:40:36, код 0.\n2. Python-процессы: только dashboard-server.py (норма) + hermes_cli.main gateway run (PID 2972, порт 45616) — не наш агент, локальный шлюз инструментария.\n3. Планировщик ОС: одна запись «Barrymore Dashboard Server» (триггер на логон). Risk-крона в системе нет.\n4. ZCode-автоматизации: обе enabled=false — ночной насос-сторож (failed, ночь 01→02.11 кончилась) и «проверка знаний 20:30» (paused). Поводок подтверждён.\n5. Свежая фактура C:/Users/temp/.zcode/cli/rollout/model-io-*.jsonl (mtime <30 мин): наша сессия, суб-агент, параллельная сессия d092a1db.\n\nШпаргалка самопроверки (описана Дмитрию в чате 04.11): curl /api/<holmes|watson|riskscan>/run-status; лог %LOCALAPPDATA%/Platform/Barrymore/dashboard-server.log; Get-CimInstance Win32_Process (python%); schtasks; sqlite tasks-index.sqlite → automations.enabled; mtime model-io-*.jsonl.\n\nСвязь: утром — сверить, что картина не изменилась, и решить вопрос «почему агенты не работают сами» (обсуждение 04.11: снятие поводка ступенями).",
        "history": [
          {
            "stage": "todo",
            "at": "2026-11-04T18:53:39Z",
            "by": "Sovereign",
            "note": "Создано по просьбе Дмитрия «запиши результат и оставь на утро задачу — еще раз ознакомиться»"
          }
        ],
        "busy": null
      },
      {
        "id": "resume-pipeline-collision",
        "title": "Коллизия двойного исполнения: найти профиль «Резюме-конвейера»",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-05T20:07:02Z",
        "description": "Контекст: ночью суб-агент «Резюме-конвейер» соседней сессии Sovereign исполнял (вероятно) лейн Л-4 параллельно с ночным писарем — возможен второй master-profile.json или черновики вне канона. ЗАДАЧА: обследовать Workspace/private/resume/ и workspace-черновики параллельных сессий; найти артефакты «Резюме-конвейера»; свести в один канон (канон = Workspace/private/resume/master-profile.json от ночного писаря, 27 навыков/5 кейсов); чужие черновики — не удалить, а влить недостающее и пометить merged. ОТЧЁТ: список найденных артефактов + что влито. Git запрещён; приватную зону наружу не выносить.",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T20:07:02Z",
            "by": "ZCode",
            "note": "Создана ZCode по задаче Sovereign (раздача на 4 ч, ночь 06.11)"
          }
        ],
        "stage": "todo",
        "busy": null
      },
      {
        "id": "rotate-langsmith-freellmapi",
        "title": "Ротация ключей LangSmith/FreeLLMAPI",
        "source": "S1",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-29T04:26:16Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-29T04:26:16Z",
            "note": "Перенесено из текущего списка задач дашборда."
          },
          {
            "stage": "in-progress",
            "at": "2026-11-04T06:13:34Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-04T06:28:13Z"
          },
          {
            "stage": "todo",
            "at": "2026-11-04T18:20:23Z",
            "note": "Аудит секретов 04.11 (E-046): реальные LangSmith и FreeLLMAPI ключи были в Workspace/main.py коммита 1164ed7 — он НЕ достижим из веток, держится в reflog, на origin не запушен (ключи не покидали хост). sk-ant в истории — только dummy-заглушка, не секрет. Срочность низкая. Ротация для Sovereign: 1) smith.langchain.com → Settings → API Keys → Create key → вписать в Workspace/.env (строки 11-12); 2) FreeLLMAPI-ключ перевыпустить в шлюзе :31415 → вписать в Workspace/.env:13. После ротации опционально: git reflog expire --expire-unreachable=now --all && git gc --prune=now — сотрёт 1164ed7 из локальной базы (осторожно: убьёт и чужие висячие объекты)."
          }
        ],
        "stage": "todo",
        "description": "Ротация LangSmith + FreeLLMAPI ключей (аудит 04.11: ключи в локальном reflog-коммите 1164ed7, origin чист; sk-ant — dummy)",
        "busy": null
      },
      {
        "id": "sec-todo-2026-11-05",
        "title": "Утро 05.11 — контур безопасности: выжимка дня и ToDo (ZCode)",
        "source": "ZCode/E-047",
        "priority": "urgent",
        "status": "active",
        "stage": "todo",
        "due": "2026-11-05",
        "createdAt": "2026-11-04T23:51:15+05:00",
        "history": [
          {
            "status": "active",
            "at": "2026-11-04T23:51:15+05:00",
            "by": "ZCode (E-047, выжимка по просьбе Sovereign)",
            "note": "ГОТОВО 04.11: (1) «Целевой стенд» в AI Sandbox → Инструменты — цели-чипы + галочки проверок → nmap_probe, прогон и скриншот ок (app.js?v=12, languages.js?v=3); (2) найден и закрыт routing-drift баг /api/sandbox/run (V-06), сервер 8765 перезапущен — ожили и эндпоинты E-046; (3) VULN-PROGRAM.md в Workspace/pentest/2026-11-04-vuln-program/ (вне git): 12 уязвимостей Platform + 12 индустриальных классов + фазы Ф-1..Ф-5; (4) Kali: VM headless 192.168.238.128, снапшот pre-pentest-2026-11-04, консоль-блок для шага 7 сохранён Дмитрием. || НА 05.11: [1] Ротация sk-ant руками Sovereign (V-01, P1, ~10 мин: панель Anthropic → новый ключ → Vault → правка Workspace/main.py:17) — критерий: secret_scan RED=0. [2] Консоль-блок Kali (учётка watson) → ZCode поднимает Juice Shop (target-server.sh) → скан 192.168.238.128 через стенд → фазовый отчёт в Workspace/pentest/2026-11-04-juiceshop/. [3] После ротации: слово на вычистку git-истории (filter-repo/BFG по sk-ant, 709b2c5). [4] Ф-1 остаток: rae-work HAR/chrome-profile под пароль/удалить (куки hh!), мастер-пароль на Vault, pre-commit hook secret_scan. [5] Коммит кода стенда — когда разобраны чужие правки в app.js/dashboard-server (сейчас не смешивать)."
          }
        ],
        "busy": null
      },
      {
        "id": "staff-agents-2026-11-05",
        "title": "Личный штат +2: DevOps Automator и Technical Writer — разбор для Sovereign",
        "source": "ZCode/санкция Sovereign «Поставь парочку полезных агентов»",
        "priority": "regular",
        "status": "active",
        "stage": "todo",
        "due": "2026-11-05",
        "createdAt": "2026-11-05T00:19:59+05:00",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T00:19:59+05:00",
            "by": "ZCode",
            "note": "Установлены в ~/.zcode/agents/ из каталога agency-agents (230+): engineering-devops-automator.md и engineering-technical-writer.md. Штат: 8 ролей. Зачем: (1) DevOps Automator — инфраструктурная автоматизация, CI/CD, операции: родная стихия Дмитрия, усилит tools/ops (бэкап/healthcheck), переезд Platform на хостинг (план fffc974), рутину вакансий DevOps; (2) Technical Writer — документация, README, гайды: закрывает БЛОКЕР №1 поиска работы (3 кейса для резюме + визитка в Workspace/private/resume/), описания услуг/откликов, устаревшие README Platform. Как работают: как остальные 6 — вызов в ZCode-окне (агент = роль с промптом; рантайма как у Холмса/Хантера нет и не нужно), привязка к задаче → прогон → отчёт. НОВЫЕ ТИПЫ УЖЕ ВИДНЫ СИСТЕМЕ БЕЗ ПЕРЕЗАПУСКА (хост подхватил живьём). Смоук 05.11 00:2x: Technical Writer живой — микрозадача справки за 88 сек / ~22k токенов, чистый русский текст + «СМОУК ОК»; первая попытка упёрлась в «user concurrency limit» (слот соседнего чата) — повтор через 45 с прошёл. Утром: демонстрация по живой задаче (кейс №1 для резюме техписателем, healthcheck-скрипт девопсом)."
          }
        ],
        "busy": null
      },
      {
        "id": "staff-hh-dashboard-loss",
        "title": "Штат/Code Reviewer: hh-вакансии не доходят до дашборда (пустая дата → вырезает [:60])",
        "source": "Staff/Code Reviewer",
        "priority": "urgent",
        "status": "active",
        "createdAt": "2026-10-31T12:28:00Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-31T12:28:00Z",
            "by": "Code Reviewer (пилот штата, E-023)",
            "note": "P1: карточки hh из HTML-фолбэка получают date=''; parse_date даёт datetime.min; сортировка уносит их в хвост, слайс [:60] вырезает первыми. Верифицировано: results.json — 60 hh-записей, все с пустой датой; vacancies.js — 0 записей hh. Фикс: пустую дату подставлять временем запуска (hh-выдача отсортирована по свежести) или трактовать пустую дату как now в ключе сортировки. Файл: tools/job_search.py:133, 388, 400."
          }
        ],
        "busy": null
      },
      {
        "id": "staff-secrets-rotation",
        "title": "Штат/Secrets Engineer: копии ключей в артефактах ZCode-сессии → ротация",
        "source": "Staff/Secrets Engineer",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-10-31T12:28:00Z",
        "history": [
          {
            "status": "active",
            "at": "2026-10-31T12:28:00Z",
            "by": "Secrets & Credential Hygiene Engineer (пилот штата, E-023)",
            "note": "P1: реальные LANGSMITH_API_KEY и FREE_LLM_API_KEY лежат plaintext в C:/Users/temp/.zcode/cli/artifacts/session_c87212841fb8241f72e3dd5a6f5e7333/ (call_99ddca97… — эхо .env, call_fcdf812e…). Git-история чиста (P0 нет, 262 коммита). Действия по санкции Sovereign: (1) удалить два artifact-файла; (2) ротировать LANGSMITH_API_KEY (smith.langchain.com) и FREE_LLM_API_KEY (шлюз :31415); (3) обновить Workspace/.env и KeePassXC. P2: pre-commit сканер (gitleaks); заглушку sk-… из Workspace/main.py:17 убрать из tracked-кода."
          }
        ],
        "busy": null
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
        ],
        "busy": null
      },
      {
        "id": "task-lock-hardening",
        "title": "Тех-долг task_lock: валидация task_id, докстринг журнала, кран тестов (P2 ревизора)",
        "source": "Sovereign",
        "priority": "regular",
        "status": "active",
        "createdAt": "2026-11-05T20:07:02Z",
        "description": "Отчёт ревизора ночи: (1) tools/lib/task_lock.py — task_id нигде не валидируется: путь-траверсал ../.. и glob-инъекция *?[ в acquire/heartbeat/release/status/claims. Чинить: отклонять task_id с /, \\, .., glob-метасимволами (по образцу TASK_ID_PATTERN из task_store). (2) tools/lib/log_event.py:8-10 — докстринг противоречит фиксу Д-2 (обновить, оговорка про многопроцессную запись). (3) тесты TaskLockTest пишут в ПРОДОВЫЙ events.jsonl — завести кран (параметр journal_path/монки-патч). ПРАВИЛА: git запрещён, unittest зелёный, сервер не трогать.",
        "history": [
          {
            "status": "active",
            "at": "2026-11-05T20:07:02Z",
            "by": "ZCode",
            "note": "Создана ZCode по задаче Sovereign (раздача на 4 ч, ночь 06.11)"
          }
        ],
        "stage": "todo",
        "busy": null
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
          },
          {
            "stage": "in-progress",
            "at": "2026-11-04T06:28:17Z"
          }
        ],
        "stage": "in-progress",
        "busy": null
      }
    ]
  },
  "hunter": {
    "generatedAt": "2026-11-06T00:17:08+05:00",
    "headline": "Доска: 125 перспективных + 32 основных (снимок 2026-11-06); находок с вилкой: 19; OLX-находки: 253 (2026-10-31); очередь поручений: 0.",
    "top": [
      {
        "title": "💻 Front‑End AI‑инженер 🏢 Accenture • 🌍 Remote 💰 $54K - $205K/год 🛠 Стек: JavaScript, TypeS",
        "url": "https://t.me/remote_jobs_ru/444",
        "source": "Telegram @remote_jobs_ru",
        "date": "2026-10-26",
        "category": "сайты/вёрстка",
        "status": "perspective",
        "salary": "$4500–17083/мес"
      },
      {
        "title": "Ask HN: Who is hiring? (October 2026)",
        "url": "https://news.ycombinator.com/item?id=50059584",
        "source": "HN (Ask HN: Who is hiring? (October 2026))",
        "date": "2026-10-12",
        "category": "AI/LLM",
        "status": "perspective",
        "salary": "$1160–1600/мес"
      },
      {
        "title": "Ask HN: Who is hiring? (October 2026)",
        "url": "https://news.ycombinator.com/item?id=49940381",
        "source": "HN (Ask HN: Who is hiring? (October 2026))",
        "date": "2026-10-03",
        "category": "",
        "status": "main",
        "salary": "$11667–22000/мес"
      },
      {
        "title": "Ask HN: Who is hiring? (October 2026)",
        "url": "https://news.ycombinator.com/item?id=49934530",
        "source": "HN (Ask HN: Who is hiring? (October 2026))",
        "date": "2026-10-02",
        "category": "AI/LLM",
        "status": "perspective",
        "salary": "$12500–21667/мес"
      },
      {
        "title": "Ask HN: Who is hiring? (October 2026)",
        "url": "https://news.ycombinator.com/item?id=49929553",
        "source": "HN (Ask HN: Who is hiring? (October 2026))",
        "date": "2026-10-02",
        "category": "",
        "status": "main",
        "salary": "$9417–16417/мес"
      }
    ],
    "full": "Workspace/analytics/hunter/digest.json"
  },
  "git": {
    "branch": "release/1.8.6",
    "lastCommit": "dd4113c Security fixes from AI-code audit (A-01..A-04): per-tool args allowlist on /api/sandbox/run (CWE-88, PoC-verified 400), safeUrl scheme check for external feed hrefs (CWE-79), escapeHtml in estate-staff and Holmes branch renders; pre-commit secret gate hooks (tools/security/hooks, install after key rotation)",
    "dirtyFiles": 35
  },
  "agent": {
    "error": "LLM gateway HTTP 502 {\"error\":{\"message\":\"All 3 routed attempt(s) failed with upstream provider errors (error ×3). This is a provider-side failure, not a problem with your request; retry, or check provider status. Attempt"
  },
  "_sourceFingerprint": "c82155afc264c24cab9a082704b1656493f3a3e3e39b6ca2931717d2287fadbb"
};