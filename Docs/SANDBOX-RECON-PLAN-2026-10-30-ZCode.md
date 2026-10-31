# План: Sandbox Recon — парсер + AI-оценка (декомпозиция под параллельную сборку)

> Автор и координатор сборки: ZCode, 2026-10-30. Цель документа: 5–7 параллельных
> ИИ-сессий собирают пакеты независимо, без конфликтов файлов, по замороженным
> контрактам ниже. Правила: protocol-first, files+git as truth, чужие файлы не
> трогать, коммитить только свои файлы с префиксом `Sandbox recon (З-N): …`.

## Цель (одним предложением)

Python-краулер на stdlib «бродит» только по доменам из allowlist, собирает
простую информацию о страницах; лёгкая LLM-модель триажит находки, ценные
эскалируются на более мощную модель; результаты хранятся в
`Workspace/sandbox/crawls/` и видны в AI Sandbox на дашборде.

## Замороженные контракты (на них собираем всё)

1. **Прогон** = каталог `Workspace/sandbox/crawls/YYYY-MM-DD_HHMM/`.
2. **`pages.json`** (выход З-1, вход З-2/З-5):
   ```json
   {
     "crawl": {"tool": "webcrawler.py v1", "startedAt": "ISO-8601 Z",
                "params": {"start": ["https://…"], "maxPages": 15, "maxDepth": 2,
                            "timeoutSec": 10, "delayMs": 1500}},
     "pages": [{"url": "…", "host": "…", "fetchedAt": "ISO Z", "status": 200,
                 "elapsedMs": 0, "depth": 0, "title": "…", "description": "…",
                 "headings": {"h1": [], "h2": []},
                 "emails": [], "phones": [],
                 "links": [{"url": "…", "text": "…"}],
                 "textSample": "≤1200 символов очищенного текста",
                 "wordCount": 0, "error": null}]
   }
   ```
   Ошибки сети не прерывают прогон — страница получает `"error"`. `links` —
   только те же хосты, не более 50 на страницу.
3. **`evaluations.json`** (выход З-2, вход З-4/З-5):
   ```json
   {"evaluatedAt": "ISO Z", "crawlDir": "…", "fastModel": "…", "deepModel": "…",
    "items": [{"url": "…",
       "triage": {"model": "…", "value": 0, "category": "…", "reason": "…",
                   "escalate": false},
       "deep": null}]
   }
   ```
   `deep` (только если триаж решил эскалировать: `value >= 7` или
   `escalate: true`): `{"model": "…", "verdict": "ценное|спорно|мусор",
   "summary": "…", "tags": ["…"]}`.
4. **Модели и режимы оценки** (правило от Sovereign, 30.10): пока активен план
   z.ai (много токенов, ограниченное время) — оценку находок делают **сами
   z.ai-сессии** (параллельные чаты читают `pages.json` и пишут
   `evaluations.json` по контракту 3). Локальный шлюз FreeLLMAPI (:31415,
   ключи `FREE_LLM_API_KEY`/`FREE_LLM_BASE_URL` в `Workspace/.env`) — **запасной
   режим**: evaluate.py через `/chat/completions` для автоматизации и после
   истечения плана. Тиры шлюза: триаж — `FREE_LLM_FAST_MODEL` или
   `gpt-oss-20b`; эскалация — `FREE_LLM_DEEP_MODEL` или `gpt-oss-120b`
   (на шлюзе есть и `claude-sonnet-4-5`, `deepseek-v4-pro`, `glm-5.3`).
   Формат ответа LLM строго JSON (срезать ```-заборы, как в
   tools/agents/run_agent.py). Оба режима обязаны выдавать идентичный JSON.
5. **Allowlist**: `tools/sandbox/webcrawler-allowlist.json` —
   `{"comment": "…", "hosts": ["testphp.vulnweb.com", "httpbin.org"]}` —
   хосты без схемы и без www. Вне списка краулер отказывается идти
   (ADR-004: сеть — только через инструмент с явными разрешениями).
   Пополнение списка — осознанная правка файла человеком.
6. **Вежливость**: robots.txt через urllib.robotparser (нет robots/ошибка
   получения — разрешить с пометкой), задержка между запросами к одному хосту
   ≥1500 мс, таймаут 10 с, только http/https, без выполнения скриптов.

## Пакеты (файлы не пересекаются — можно параллельно)

| ID | Пакет | Файлы (единоличное владение) | Зависит от | Готово, когда |
|---|---|---|---|---|
| **З-1** | Ядро-краулер | `tools/sandbox/webcrawler.py` | контракт 2, 5, 6 | CLI `python tools/sandbox/webcrawler.py --start https://httpbin.org/ --max-pages 5 --depth 1` создаёт `pages.json` по схеме |
| **З-2** | Оценочный контур (режим шлюза — резерв/автоматизация; при активном плане z.ai оценку делают сами сессии) | `tools/sandbox/evaluate.py` | контракт 3, 4; вход — готовый `pages.json` | CLI `python tools/sandbox/evaluate.py <crawl-dir>` создаёт `evaluations.json`; двухуровневая логика и дайджест в консоли |
| **З-3** | Allowlist-файл + правила пополнения | `tools/sandbox/webcrawler-allowlist.json`, `tools/sandbox/ALLOWLIST.md` | контракт 5 | файл создан, семя из `tools/barrymore/security-targets.json` (testphp.vulnweb.com, httpbin.org), правила пополнения описаны |
| **З-4** | Агент Синдбад: реестр v5 + ветка в рантайме + паспорт | `tools/agents/registry.json`, `tools/agents/run_agent.py`, `Memory/Agents/Sinbad.md` | З-1, З-2 (вызывает их subprocess-ом) | `python tools/agents/run_agent.py --agent Sinbad` делает: crawl → evaluate → канонический отчёт «Вывод/Факты/Варианты/Риски/Рекомендация» + `report.write` |
| **З-5** | UI-вкладка «Разведка» в AI Sandbox | `eVo/dashboard/sandbox-recon.js`, `eVo/dashboard/sandbox-recon.css` | контракты 2, 3; API-маршруты (см. ниже) | форма запуска прогона (start, maxPages), список прогонов, таблица находок с оценками |
| **З-6** | Тесты (offline) | `tools/sandbox/test_webcrawler.py`, `tools/sandbox/test_evaluate.py` | З-1, З-2 | `python -m unittest discover -s tools/sandbox -p "test_*.py"` зелёный без сети: парсер HTML на fixture-файлах, схема JSON, эскалация на фейковом шлюзе |
| **З-7** | Документация | `tools/sandbox/README.md` | всё выше | README: запуск, схема данных, лимиты, как добавить домен |

**Интеграционные точки — только координатор (ZCode), не параллельным сессиям:**
`tools/barrymore/dashboard-server.py` (маршруты `POST /api/sandbox/crawl` —
запуск прогона в фоновом потоке, `GET /api/sandbox/runs` — список прогонов и
оценок; контракт совпадает с п. 2–3), строки подключения `sandbox-recon.js` в
`eVo/dashboard/index.html`, точечный хук в `app.js`/`languages.js` (заголовок
вкладки RU/EN), паспорт и реестр (З-4).

## Зоны конфликта

Общие файлы (`registry.json`, `run_agent.py`, `dashboard-server.py`, `app.js`,
`languages.js`, `index.html`) параллельным сессиям НЕ трогать — писать только
в файлы из колонки «Файлы» своего пакета. Второй AI ведёт `eVo/dashboard/brief.js`
и журнал `Memory/Engineering/LOG.md` — тем более не трогать.

## Метрика прогона (правило «агент = паспорт + инструмент + метрика»)

`pagesFetched / pagesEvaluated / escalations / valuableConfirmed` (verdict
«ценное») — печатается evaluate.py и отображается в UI; после стабилизации —
строка в Morning Brief.

## Порядок сборки

1. Параллельно: З-1, З-2, З-3, З-5 (UI против контрактов), З-6 (по мере
   появления соседей), З-7.
2. Координатор по готовности З-1/З-2: З-4 (Синдбад) + серверные маршруты +
   хуки UI.
3. Сквозной прогон: allowlist → crawl httpbin.org → evaluate → отчёт Синдбада
   → UI. Затем выбор первых «настоящих» целей и их внесение в allowlist
   человеком.
