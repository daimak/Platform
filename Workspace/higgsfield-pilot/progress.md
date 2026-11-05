# Прогресс Хиггсфилд-пилота (лог для Sovereign)

Формат: HH:MM — шаг — результат

00:20 — рабочий каталог создан — Workspace/higgsfield-pilot/ готов; tools/lib/log_event.py отсутствует, маяк append_event не ставится; Python 3.13.15
00:45 — SDK изучен — higgsfield-client 0.2.0: base https://api.higgsfield.ai, auth "Authorization: Key <id>:<secret>", env HF_KEY/HF_API_KEY+HF_API_SECRET, submit(application=<путь>, arguments), статусы queued/in_progress/completed/failed/nsfw/canceled, вебхук ?hf_webhook=, retry 3x backoff, Agent API /v1/agent/sessions, файлы /files/generate-upload-url
00:52 — pilot.py написан — auth-check (SDK+raw HTTP) + submit-скелет Soul 2, LIVE заблокирован константой REAL_PAYMENT_SANCTIONED=False, отчёт в pilot-report.json
00:55 — DRY-RUN прогнан — без ключа SDK локально даёт CredentialsMissedError; сервер api.higgsfield.ai на запрос без Authorization: HTTP 401 {"detail":"Invalid credentials"} (бесплатный вызов, реальный). Платных вызовов 0. Лог: dry-run-log.txt, отчёт: pilot-report.json
