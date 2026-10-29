window.EVO_BRIEF = {
  "generatedAt": "2026-10-29 17:23",
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
    "2026-10-26 | new island \"Holmes Study\" on the map (beacon + modal + RU/EN), sidebars toggle; all 10 modals verified clickable | co-worked with second AI | —",
    "2026-10-29 | Barrymore brief refresh button in dashboard; loopback-only local server runs the existing generator and returns the fresh report to the open modal | refresh Morning Brief on demand | —",
    "2026-10-29 | Barrymore dashboard starts at Windows logon; source fingerprints avoid unchanged LLM runs; explicit Done tasks retain history for 48h before archival | persistent brief and task lifecycle | —",
    "2026-10-29 | Platform v1.8.3: Tashkent time, silent Windows startup, cached Morning Brief, durable Barrymore task history and Graphify project report | on-demand, low-noise project overview | —",
    "2026-10-29 | Maelstorm research beacons and translucent island markers | clarify island roles and reduce map clutter until hover | —"
  ],
  "tasks": {
    "urgent": [
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
    "branch": "feature_1.8.2",
    "lastCommit": "ddd621b Add Maelstorm research beacons and subtle icons",
    "dirtyFiles": 197
  },
  "agent": {
    "model": "openai/gpt-oss-20b",
    "summary": "Дата отчёта: 2026‑10‑29 (генерация). Дата в CURRENT.md – 2026‑08‑05, следовательно, контекст устарел.\n\nВажные обновления: добавлен остров Holmes Study, кнопка обновления Morning Brief в Dashboard, запуск Barrymore при логине Windows, кэширование Brief.\n\nВерсия платформы v1.8.3: поддержка Tashkent time, silent startup, Graphify project report.\n\nПриоритетные задачи: резервирование мастер‑пароля KeePassXC и ротация ключей LangSmith/FreeLLMAPI.\n\nРегулярные задачи: очистка пустых заглушек, слияние веток D‑002, актуализация CURRENT.md.\n\nGit‑статус: ветка feature_1.8.2, последний коммит ddd621b, 197 грязных файлов.\n\nСледующий шаг: выполнить актуализацию контекста Barrymore и проверить качество отчёта после обновления.",
    "nextStep": "Выполнить актуализацию контекста Barrymore и проверить качество отчёта после обновления."
  },
  "_sourceFingerprint": "23fba76c8663f6ee194074638ed1d15b654830419cb3b91bf19a844b35341255"
};