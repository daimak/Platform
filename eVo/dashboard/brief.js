window.EVO_BRIEF = {
  "generatedAt": "2026-10-30 20:47",
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
    "lastCommit": "b1a9bed Trading Quarter: Vacancies/Orders tabs inside island modal; job_search.py aggregator (hh HTML fallback, FL.ru live gigs) + freelance cheatsheet",
    "dirtyFiles": 17
  },
  "agent": {
    "model": "qwen/qwen3.8-27b",
    "summary": "Дмитрий, данные снимка от 30.10.2026, но контекст CURRENT.md устарел (даты 05.08.2026). Ветка feature_1.8.5 содержит 17 незакоммиченных файлов. Срочные задачи: шум авто-коммитов Холмса (77%), бэкап KeePassXC и ротация ключей LangSmith. Регулярные: слияние D-002, разбор untracked-файлов и актуализация контекста. AI-использование в источниках не указано.",
    "nextStep": "Сверить CURRENT.md с STATE.md и CHANGELOG.md, чтобы устранить расхождение дат и обновить контекст Barrymore."
  },
  "_sourceFingerprint": "b2ffc6c82cf0fc538331b18f680d4fa340860863b4fa5e10466b811c2780d210"
};