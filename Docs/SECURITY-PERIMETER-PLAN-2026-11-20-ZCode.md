# План периметра перед «открываемся миру» — 20.11.2026 (ZCode)

Цель: к моменту «$100 — открываемся миру» секретный контур чист и ротирован.
Исполнение — по «го» Дмитрия; ротации в консолях провайдеров = руки Дмитрия, остальное — ZCode.
Оценка: ~1 час суммарно, из них рук Дмитрия ~25 минут.

## Инвентарь секретов (фактура 20.11)

| # | Секрет | Где живёт | Статус | Риск |
|---|--------|-----------|--------|------|
| 1 | sk-ant (Anthropic) | `Workspace/main.py:17` | ✅ **снят 20.11**: греп показал заглушку `sk-ant-dummy…` (Холмс был прав, 15.11) | — |
| 2 | FINANCE_TOKEN | `Workspace/.env` | 🔴 значение выведено в чат 08.11 | ротация обязательна до реальных денег |
| 3 | LangSmith + FreeLLMAPI | `Workspace/.env` + след в reflog-коммите `1164ed7` | 🟡 ротация снята с приоритетов 06.11 | reflog локален (не достижим с origin), но перед выходом наружу — ротировать |
| 4 | FREE_LLM_API_KEY (шлюз :31415) | `Workspace/.env` | 🟡 не светился в чате | проверить фактом при Ф-3 |
| 5 | Workspace/.env | вне git (.gitignore:16) | ✅ | ORANGE secret-scan — норма |

Замки уже в бою: pre-commit secret-gate (RED = блок), PUBLISH_BLOCKLIST (private/intel/Dark Watch = RED), `.git/info/exclude` для intel-контуров.

## Ф-0. Статус репозитория — 1 минута, решает объём Ф-4

Открытый вопрос с 09.11: приватный ли github.com/daimak/Platform.
Проверка (Дмитрий): открыть https://github.com/daimak/Platform → Settings → General → внизу «Danger Zone» → «Change repository visibility».
- **Приватный** → история git не публична, rewrite не нужен, Ф-4 сводится к гигиене.
- **Публичный** → Ф-4 полный (rewrite + force-push — решение CEO-0, история `5e09075` несла датасеты orders_board/salary).

## Ф-1. sk-ant — ЗАКРЫТО 20.11 без действий

Греп `Workspace/main.py:17` показал заглушку `sk-ant-dummy…` — живого ключа нет, P1 снят (подтверждение доклада Холмса от 15.11). Остаток: строка в чек-листе критерия №1 сохраняется как регрессионная проверка.

## Ф-2. FINANCE_TOKEN — 10 мин

1. Дмитрий/ZCode: новая случайная строка (32+ hex: `python -c "import secrets;print(secrets.token_hex(24))"`) → заменить строку `FINANCE_TOKEN=` в `Workspace/.env`.
2. Рестарт НЕ нужен (плагин читает на каждый запрос).
3. Дмитрий, 3 движения в UI: открыть штаб → 🏺 Trading Quarter → вкладка «Внутренние расчёты» → вставить новый код в поле токена → «Сохранить токен».
4. Проверка: старый токен → 403; новый → 200 (`curl -H "X-Finance-Token: …" http://127.0.0.1:8765/api/internal/summary`).
5. Касса сейчас чиста от демо (20.11: удалено 4, сохранена 1 реальная запись 200 000 сум).

## Ф-3. LangSmith / FreeLLMAPI — 20 мин (руки Дмитрия в консолях)

1. Консоль LangSmith → API Keys → revoke/создать; консоль/панель FreeLLMAPI (шлюз :31415) → то же.
2. Новые значения → `Workspace/.env` + Vault.
3. Проверка брифа: `python tools/barrymore/morning-brief.ps1` (или дождаться утреннего) — бриф свежий = ключи живы; шлюз :31415 отвечает = FreeLLMAPI жив.
4. Проверка Холмса/Ватсона: POST /api/holmes/run с Origin → 202.

## Ф-4. Git-история

- reflog `1164ed7` (LangSmith/FreeLLMAPI) — локальный объект, недостижим с origin: после ротации Ф-3 ценность утечки = 0. Дополнительно: `git reflog expire --expire=30.days` при санитарии (не срочно).
- `5e09075` (датасеты в истории main): приватный репо → ОК; публичный → rewrite + force-push — отдельное решение Дмитрия (за ним: [[platform-evo-repo-state]] R1).
- Блоклист/гейт уже стоят — коммит-канал защищён.

## Ф-5. Vault — 10 мин (ZCode при «го»)

Все ротированные значения дублируются в KeePassXC `C:/Users/temp/Vault/Platform.kdbx` (без мастер-пароля, доступ локальный). Запись «Platform secrets 20.11».

## Критерий «периметр чист» (чек-лист ≤5)

1. `grep -rn "sk-ant" Workspace/ tools/ eVo/ --include="*.py" --include="*.env"` → 0 живых вхождений
2. `grep -c "FINANCE_TOKEN" Workspace/.env` → 1 строка, значение ≠ утечённому 08.11
3. Тест гейта: `echo "sk-ant-fake" > t.py && git add -f t.py && git commit` → ОТКЛОНЁН; `rm t.py`
4. Старый FINANCE_TOKEN в UI → 403; новый → сводка видна
5. Ф-0 записан в этом файле: «репо = приватный/публичный, решение по Ф-4»

Источники: [[security-vuln-landscape-2026]], [[internal-finance-system]], [[platform-evo-repo-state]] R1, [[auth-gate-platform]].
