# Higgsfield AI — полная документация для Platform Evo

**Составлено:** Хиггсфилд-пилот-2 (рейс 2), 2026-11-05/06
**Версия SDK:** higgsfield-client 0.2.0 (Python 3.8+, сверен локально в `Workspace/higgsfield-pilot/.venv`)
**Base URL:** `https://api.higgsfield.ai`
**Статус документа:** сверено с живыми доками docs.higgsfield.ai (индекс `llms.txt` от 2026-11-06) и прайсингом open.higgsfield.ai/pricing + blog higgsfield-api. SDK-факты сверены напрямую с исходниками установленного пакета.
**Платная генерация в ходе подготовки НЕ выполнялась.** Единственный реальный вызов API — бесплатный auth-check (HTTP 401 без ключа, задокументирован ниже).

---

## Оглавление

1. [Как получить ключ и где его хранить](#1-ключ)
2. [Авторизация](#2-авторизация)
3. [Общая модель: асинхронный цикл и статусы](#3-асинхронный-цикл)
4. [Soul 2: кадр от submit до fetch (главный сценарий)](#4-soul-2)
5. [Soul ID: тренировка персонажа](#5-soul-id)
6. [Marketing Studio: товар → кампания](#6-marketing-studio)
7. [Стили Soul, оценки стоимости, учёт расходов](#7-стили-и-деньги)
8. [Загрузка входных файлов](#8-файлы)
9. [Вебхуки](#9-вебхуки)
10. [DoP и другие «фишки»](#10-фишки)
11. [Agent API](#11-agent-api)
12. [Ошибки и их разбор (с живым примером)](#12-ошибки)
13. [Лимиты](#13-лимиты)
14. [Retention (хранение данных)](#14-retention)
15. [Прайсинг и смета тестового прогона](#15-прайсинг-и-смета)
16. [Интеграция в Platform Evo](#16-интеграция)
17. [Чек-лист: что нужно от Sovereign для живого прогона](#17-чек-лист)
18. [Источники и степень достоверности](#18-источники)

---

## 1. Ключ {#1-ключ}

### Где получить

1. Зарегистрироваться: **[console.higgsfield.ai](https://console.higgsfield.ai)** (для API-разработки портал — **[open.higgsfield.ai](https://open.higgsfield.ai)**, ключи создаются там же/в консоли по руководству help-center «What Is the Higgsfield API»).
2. Создать API-креденшел: пара **Key ID + Secret** (это НЕ один токен — именно пара).
3. Пополнить баланс (платёж — только для живого прогона; см. раздел 17).

### Где хранить (правило Platform Evo)

Ключ кладём в **`Workspace/.env`**, переменная:

```
HIGGSFIELD_API_KEY="<key_id>:<key_secret>"
```

Формат значения — «id:secret» одной строкой (SDK принимает либо это, либо пару HF_API_KEY/HF_API_SECRET; см. раздел 2).

**Железные правила:**
- Никогда не коммитить (`.env` вне git; в репо попадает только формат без значений).
- Никогда не выводить в логи/отчёты (пилотный скрипт печатает только `HF_***:ab***`-маску).
- Только server-side код: ключ в браузере/мобильном приложении = компрометация аккаунта (доки прямо запрещают).
- Отдельные креденшелы для dev и prod; при подозрении на утечку — немедленная ротация в консоли.

### Переменные окружения, которые понимает SDK 0.2.0

| Переменная | Значение | Кем используется |
|---|---|---|
| `HF_KEY` | `"<id>:<secret>"` одной строкой | Python SDK (основная) |
| `HF_API_KEY` + `HF_API_SECRET` | пара отдельно | Python SDK (альтернатива) |
| `HF_CREDENTIALS` | `"<id>:<secret>"` | TypeScript SDK (`@higgsfield/client`) |
| `HIGGSFIELD_API_KEY` | `"<id>:<secret>"` | Стандарт Platform Evo; скрипты Platform сами мапят на `HF_KEY` |

SDK-факт (сверено с исходниками 0.2.0): при отсутствии всех перечисленных `higgsfield_client.auth.get_credential_key()` бросает `CredentialsMissedError: Higgsfield API credentials missing. Please set HF_KEY, or alternatively set HF_API_KEY and HF_API_SECRET.`

---

## 2. Авторизация {#2-авторизация}

Каждый запрос к API требует заголовок:

```
Authorization: Key <API_KEY_ID>:<API_KEY_SECRET>
```

```bash
curl https://api.higgsfield.ai/requests/REQUEST_ID/status \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}"
```

- Заголовок общий для всех эндпоинтов (generation, status, cancel, delete, files, custom-references, presets, usage).
- **Legacy-заголовки** `hf-api-key` + `hf-secret` ещё принимаются, но для новых интеграций доки требуют `Authorization`.
- Неверные/отсутствующие креды → **HTTP 401**, тело `{"detail": "Invalid credentials"}` (см. живой пример в разделе 12).
- Аутентификация определяет аккаунт; доступ к конкретной модели может дополнительно ограничиваться (тогда 404/423/503).
- Пресайнд-URL хранилища (загрузка файлов) — единственное место, куда креденшелы отправлять НЕ нужно (раздел 8).

### Python SDK 0.2.0

```python
import os
import higgsfield_client

# SDK сам читает HF_KEY (или HF_API_KEY+HF_API_SECRET) из окружения.
# Для Platform: загрузчик .env ставит HIGGSFIELD_API_KEY — мапим:
os.environ.setdefault("HF_KEY", os.environ.get("HIGGSFIELD_API_KEY", ""))

client = higgsfield_client.Client()   # base_url по умолчанию https://api.higgsfield.ai
```

---

## 3. Асинхронный цикл {#3-асинхронный-цикл}

Генерация асинхронна у всех моделей:

1. `POST /<model-endpoint>` c JSON-параметрами → мгновенный ответ с `request_id`.
2. Сохранить `request_id` (стабильный идентификатор для poll/cancel/webhook-dedup/поддержки).
3. Опрашивать `status_url` (GET) или ждать вебхук.
4. По `completed` — скачать `images`/`video`/`audio` URL.

### Первичный ответ (queued)

```json
{
  "status": "queued",
  "request_id": "d7e6c0f3-6699-4f6c-bb45-2ad7fd9158ff",
  "status_url": "https://api.higgsfield.ai/requests/d7e6c0f3-.../status",
  "cancel_url": "https://api.higgsfield.ai/requests/d7e6c0f3-.../cancel",
  "expires_after": 604800
}
```

`expires_after` — сколько секунд (604800 = 7 суток) хранятся данные запроса после завершения.

### Статусы

| Статус | Терминальный | Смысл |
|---|:-:|---|
| `queued` | нет | В очереди, ещё можно отменить |
| `in_progress` | нет | Генерация пошла, отменить нельзя |
| `completed` | да | Есть выходные URL (`images[]` / `video` / `audio`) |
| `failed` | да | Ошибка, возможен `error`; не тарифицируется |
| `nsfw` | да | Отклонено модерацией; не тарифицируется |
| `canceled` | да | Отменено до начала обработки |

В SDK 0.2.0 статусы — классы-синглтоны, терминальные собраны в константу:

```python
from higgsfield_client import DONE_STATUSES   # == (Completed, NSFW, Cancelled, Failed)
```

### Завершённый ответ (image)

```json
{
  "status": "completed",
  "request_id": "...",
  "expires_at": "2026-10-31T12:05:12.481Z",
  "images": [{ "url": "https://cdn.example.com/image-1.jpg" }]
}
```

Видео — `"video": {"url": ...}`, аудио — `audio`/`audios`; некоторые video/3D-операции отдают `zip`, `mov`, `jsx`, `fbx`, `ply`. `expires_at` появляется в момент завершения: после него файлы удаляются и URL перестают работать → **скачивать сразу**.

### Cancel и Delete

```bash
# Отмена — только пока всё ещё queued:
POST /requests/{request_id}/cancel      # 202 Accepted, пустое тело; если пошло — 400
# Немедленное удаление данных завершённого запроса:
DELETE /requests/{request_id}           # 200 {"request_id":"...","status":"deleted"};
                                        # 409 если ещё queued/in_progress; идемпотентно
```

Платёжные записи сохраняются после delete. Отмена успешно отменённого queued-запроса возвращает зарезервированные средства.

---

## 4. Soul 2 {#4-soul-2} — главный сценарий

**Endpoint:** `POST https://api.higgsfield.ai/higgsfield-ai/soul/v2/standard`
**Endpoint ID:** `higgsfield-ai/soul/v2/standard`
**Задача:** text-to-image — портреты, fashion, editorial-фотографии с SOUL-стилями.

### Схема запроса (актуальная, сверено 2026-11-06)

> ВАЖНО: схема изменилась относительно того, что предполагал рейс-1 в `pilot.py`. Ниже — точные поля с workflow-страницы SOUL V2 generate.

| Поле | Тип | Default | Обяз. | Ограничения |
|---|---|---|:-:|---|
| `prompt` | string | — | **да** | единственное обязательное |
| `aspect_ratio` | string | `1:1` | нет | `9:16, 16:9, 4:3, 3:4, 1:1, 2:3, 3:2` |
| `resolution` | string | `720p` | нет | `720p` \| `1080p` (НЕ 2K/4K!) |
| `enhance_prompt` | boolean | `false` | нет | авто-улучшение промпта |
| `custom_reference_id` | string\|null (uuid) | null | нет | завершённый персонаж Soul ID вашего аккаунта (раздел 5) |
| `custom_reference_strength` | number | 1.0 | нет | 0..1; с персонажем 0 невалиден в рантайме, нужен >0 |
| `style_id` | string (uuid) | `3db34ab5-3439-4317-9e03-08dc30852e69` | нет | из GET /v1/text2image/soul-styles/v2 (раздел 7) |
| `style_strength` | number | 1.0 | нет | 0..1; **сейчас не влияет на генерацию** (заявлено в доках) |
| `seed` | integer | random | нет | 1..1000000; явный `null` невалиден |
| `batch_size` | integer | 1 | нет | только `1` или `4` |

Поля `num_images` у Soul 2 **не существует** (это поле старого Soul v1 standard: `/higgsfield-ai/soul/standard`, где enum resolution 2K/4K и aspect_ratio до 21:9). Вебхук передаётся query-параметром `?hf_webhook=...` (раздел 9), параметра `webhook` в теле нет.

### Полный пример под SDK 0.2.0: submit → poll → fetch

```python
"""Soul 2: один кадр от submit до скачивания. Платный при живом ключе!"""
import os, time, random

os.environ.setdefault("HF_KEY", os.environ.get("HIGGSFIELD_API_KEY", ""))
import higgsfield_client
from higgsfield_client import DONE_STATUSES

APP = "higgsfield-ai/soul/v2/standard"

arguments = {
    "prompt": (
        "Editorial fashion photo, a mid-30s woman in a charcoal wool coat, "
        "rain-wet Tokyo street at dusk, neon reflections, 85mm lens"
    ),
    "aspect_ratio": "3:4",
    "resolution": "1080p",
    "batch_size": 1,
    "enhance_prompt": False,
}

# Вариант A: submit + ручной цикл poll (контроль статусов для events.jsonl)
controller = higgsfield_client.submit(APP, arguments=arguments)
print("request_id:", controller.request_id)

delay = 2.0
deadline = time.monotonic() + 300            # app-level таймаут под модель
last = None
while time.monotonic() < deadline:
    st = controller.status()
    name = type(st).__name__                 # Queued / InProgress / ...
    if name != last:
        print("status:", name)
        last = name
    if isinstance(st, DONE_STATUSES):
        break
    time.sleep(delay + random.uniform(0, 0.5))
    delay = min(delay * 1.5, 10.0)           # backoff 2с -> 10с, jitter

result = controller.get()                    # финальный словарь ответа
if result["status"] == "completed":
    for img in result["images"]:
        print("URL:", img["url"])            # скачать СРАЗУ (retention 7 дней)
else:
    print("терминальный статус:", result["status"], result.get("error"))
```

```python
# Вариант B: subscribe — SDK сам опрашивает до терминального статуса
import os
os.environ.setdefault("HF_KEY", os.environ.get("HIGGSFIELD_API_KEY", ""))
import higgsfield_client

result = higgsfield_client.subscribe(
    "higgsfield-ai/soul/v2/standard",
    arguments={
        "prompt": "Editorial portrait in soft daylight",
    },
)
print(result["images"][0]["url"])
```

Есть также `subscribe_async` / `submit_async` (asyncio-версии тех же вызовов).

### cURL (REST, как в доках)

```bash
export IDEMPOTENCY_KEY=$(uuidgen | tr '[:upper:]' '[:lower:]')

curl --request POST \
  --url https://api.higgsfield.ai/higgsfield-ai/soul/v2/standard \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
  --header "Content-Type: application/json" \
  --header "Idempotency-Key: ${IDEMPOTENCY_KEY}" \
  --data '{
    "prompt": "A quiet alpine lake at sunrise, editorial photography",
    "resolution": "720p",
    "aspect_ratio": "1:1",
    "enhance_prompt": true,
    "batch_size": 1
  }'
```

`Idempotency-Key` — UUID, который вы генерируете сами. Если submit завис и ответ не пришёл — повторить с ТЕМ ЖЕ ключом: дубликат-запрос не создастся. Повторное использование того же ключа с другим телом → 422.

Нюанс из доков: короткие промпты общего стиля могут быть авто-улучшены даже при `enhance_prompt=false`.

---

## 5. Soul ID {#5-soul-id} — тренировка персонажа

**Что это:** workflow тренировки персонажа-референса из ваших фото. Результат (`id`) подставляется в Soul-генерации как `custom_reference_id`.

### Создание (тренировка)

**Endpoint:** `POST https://api.higgsfield.ai/v1/custom-references`
**Catalog ID:** `soul-id` (это НЕ image-эндпоинт — POST на /soul-id делать не нужно).

| Поле | Тип | Обяз. | Ограничения |
|---|---|:-:|---|
| `name` | string | да | ≤ 100 символов |
| `model_version` | string | нет (default `v1`) | `v1` \| `v2` \| `cinema` — должен совпадать с семейством генерации |
| `input_images` | array | да | 1–100 штук, каждая `{"type": "image_url", "image_url": "<публичный URL ≤2083>"}` |

```bash
curl --request POST \
  --url https://api.higgsfield.ai/v1/custom-references \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
  --header "Content-Type: application/json" \
  --data '{
  "name": "Island host",
  "model_version": "v2",
  "input_images": [
    { "type": "image_url", "image_url": "https://example.com/host-front.jpg" },
    { "type": "image_url", "image_url": "https://example.com/host-side.jpg" },
    { "type": "image_url", "image_url": "https://example.com/host-outdoors.jpg" }
  ]
}'
```

Ответ — объект персонажа: `id`, `name`, `model_version`, `status`, `thumbnail_url`, `created_at`, `in_progress_at`, `fail_reason`. **У тренировки нет request_id и нет images.**

### Опрос тренировки

`GET /v1/custom-references/{id}` — статусы: `not_ready`, `queued`, `in_progress`, `completed`, `failed`.

### Лимиты и деньги

- 1–100 входных изображений; референсы привязаны к аккаунту.
- Если у аккаунта уже максимум одновременных тренировок → `429` c `Retry-After` (в доках пример: «Maximum number of concurrent requests (2) has been reached»); отклонённый запрос ничего не стоит.

### Использование с Soul 2

Когда статус `completed` — передать `id` как `custom_reference_id` ( Soul 2 v2, Soul v1 — v1, Soul Cinema — cinema):

```python
arguments = {
    "prompt": "The host standing on a wooden pier at sunrise, editorial photo",
    "custom_reference_id": "<character-uuid>",
    "custom_reference_strength": 0.85,
    "aspect_ratio": "3:4",
    "resolution": "1080p",
}
controller = higgsfield_client.submit("higgsfield-ai/soul/v2/standard", arguments=arguments)
```

---

## 6. Marketing Studio {#6-marketing-studio} — товар → кампания

**Что это:** генерация и редактирование рекламных/кампейных изображений с опциональным preset-улучшением промпта. Это тот блок, где «товар → кампания» есть в API напрямую.

### Воркфлоу (3 шт.)

| Воркфлоу | Endpoint | Endpoint ID |
|---|---|---|
| 2.0 Alpha (generate-and-edit) | `POST /marketing-studio/image` | `marketing-studio/image` |
| 2.5 Flare | `POST /marketing-studio/image/flare` | `marketing-studio/image/flare` |
| 2.5 Sunburst | `POST /marketing-studio/image/sunburst` | `marketing-studio/image/sunburst` |

### Схема 2.0 Alpha (`marketing-studio/image`)

| Поле | Тип | Default | Обяз. | Ограничения |
|---|---|---|:-:|---|
| `prompt` | string | — | **да** | 1–5000 символов |
| `quality` | string | `high` | нет | `low` \| `medium` \| `high` |
| `preset_id` | string (uuid) | — | условно | из GET /marketing-studio/image/presets |
| `image_urls` | array of URI | — | условно | 0–16 публичных URL; порядок значим |
| `moderation` | string | `auto` | нет | `auto` \| `low` |
| `resolution` | string | `2k` | нет | `1k` \| `2k` \| `4k` |
| `aspect_ratio` | string | `auto` | нет | `auto, 1:1, 3:2, 2:3, 4:3, 3:4, 16:9, 9:16, 21:9` |
| `enhance_prompt` | boolean | `false` | нет | см. условие ниже |

**Условное правило схемы:** при `enhance_prompt=true` поля `preset_id` и `image_urls` становятся обязательными, `quality` обязан быть `high`, а `image_urls` ограничивается 1–2 элементами (первый — товар, второй опционально человек/модель).

- Text-to-image: `image_urls` не передаём. Редактирование: до 16 URL с `enhance_prompt=false`.
- Референс-изображения: JPEG, PNG, WebP; слишком большие нормализуются.
- `auto` в aspect_ratio: с enhance — соотношение пресета; без enhance — квадрат.
- 1k/2k/4k — тире; точные пиксели зависят от соотношения сторон.

### Пресеты

`GET https://api.higgsfield.ai/marketing-studio/image/presets` (authorized).
Query: `search` (строка), `size` (default 50), `cursor` (default 0).
Ответ: список пресетов (`id`, `name`, `type`, `group`, `aspect_ratio`, …) + `total`. Пример из доков: `{"name": "Editorial product portrait", "type": "ads", "group": "Editorial", "aspect_ratio": "3:4"}`, всего `total: 120`.

### Пример (товар → кампания-кадр)

```bash
curl --request POST \
  --url https://api.higgsfield.ai/marketing-studio/image \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
  --header "Content-Type: application/json" \
  --header "Idempotency-Key: ${IDEMPOTENCY_KEY}" \
  --data '{
  "prompt": "A ceramic vase on a wooden table beside a sunlit window, soft natural shadows, editorial photograph.",
  "resolution": "2k",
  "aspect_ratio": "1:1",
  "quality": "high",
  "enhance_prompt": false
}'
```

Ответ — тот же queued-конверт с `request_id`/`status_url`/`cancel_url`; в `completed` — `images[]`. Дальше — как в разделе 4.

SDK:

```python
controller = higgsfield_client.submit("marketing-studio/image", arguments={
    "prompt": "Our island-house product on a sunset terrace, lifestyle shot",
    "image_urls": [product_public_url],          # из раздела 8
    "enhance_prompt": True,                      # потянет за собой preset_id+quality=high
    "preset_id": "<uuid из /marketing-studio/image/presets>",
    "resolution": "2k",
})
```

Рядом существует **Ads Studio** (текстовый бриф + опциональные референсы товара → 1–8 рекламных концептов через GPT Image 2.5 Flare, `ads-studio.md`) — отдельный высокоуровневый генератор кампаний; в прайс-листе блога не фигурирует, цену брать из estimate-эндпоинта.

---

## 7. Стили и деньги {#7-стили-и-деньги}

### Стили Soul (для Soul 2)

`GET https://api.higgsfield.ai/v1/text2image/soul-styles/v2` (authorized) → список стилей: `id`, `name`, `description`, `preview_url`. Выбранный `id` подставляется в `style_id` запроса Soul 2. Default-стиль: `3db34ab5-3439-4317-9e03-08dc30852e69`.

### Оценка стоимости ДО генерации (estimate)

**Endpoint:** `POST https://api.higgsfield.ai/estimate/<endpoint-id>` — принимает то же тело, что и генерация, возвращает USD за запрос:

```bash
curl --request POST \
  --url https://api.higgsfield.ai/estimate/higgsfield-ai/soul/v2/standard \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
  --header "Content-Type: application/json" \
  --data '{ "prompt": "Editorial portrait in soft daylight" }'
# {"usd": "0.094"}   <- доки помечают значение ИЛЛЮСТРАТИВНЫМ; авторитетна оценка вашего аккаунта
```

Для Platform: estimate вызывать перед каждым живым submit и писать в events.jsonl — так смета сверяется с фактом.

### Учёт расходов (usage)

`GET https://api.higgsfield.ai/models/usage` (authorized)
Параметры: `start`/`end` (ISO 8601, окно ≤31 день), `timeframe` (`hour|day|week|month`), `bound_to_timeframe`, `model`, `expand=time_series` / `expand=auth_method`, `page`/`limit` (limit ≤100).
Ответ: bucket-записи `model`, `unit` (`generation`), `quantity`, `unit_price`, `cost`, `currency` (`USD`), плюс `total`. Пример значений в доках: `"unit_price": "0.0940"`, `"cost": "11.2800"`.
Предупреждение доков: «Usage analytics is not a billing record» — сверять итоги по инвойсам; неоплачиваются failed/nsfw/canceled-запросы.

### Денежные правила

- Pay-as-you-go: предоплаченный USD-баланс, без подписки и per-seat. «Spending stops at zero» — при нуле запросы ставятся на паузу до пополнения (есть auto top-up).
- **Средства на балансе истекают через 1 год после внесения.**
- Тарифицируются только успешные (`completed`) генерации; failed/nsfw не списываются, зарезервированное возвращается автоматически; отменённый до обработки queued-запрос возвращается.
- Enterprise: инвойсная оплата по контракту (open.higgsfield.ai/contact-sales).

---

## 8. Файлы {#8-файлы} — загрузка входных медиа

Если вход не доступен по публичному HTTPS-URL — пресайнд-загрузка:

### 1) Получить upload URL

```bash
curl --request POST \
  --url https://api.higgsfield.ai/files/generate-upload-url \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
  --header "Content-Type: application/json" \
  --data '{"content_type":"image/jpeg"}'
```

```json
{
  "public_url": "https://cdn.example.com/input/example.jpeg",
  "upload_url": "https://storage.example.com/presigned-upload-url",
  "content_type": "image/jpeg",
  "upload_headers": { "Content-Type": "image/jpeg", "x-amz-tagging": "retention=temporary" }
}
```

Upload URL живёт **1 час**.

### 2) Залить файл

PUT на `upload_url` со ВСЕМИ заголовками из `upload_headers` (креденшелы Higgsfield на storage-URL не отправлять).

### 3) Использовать `public_url`

Подставить в параметры модели: `image_url` / `video_url` / `audio_url`, `input_images[].image_url`, `image_urls[]`.

**Поддерживаемые content-type:** `image/jpeg`, `image/jpg`, `image/png`, `image/webp`, `image/gif`; `audio/wav`, `audio/x-wav`; `video/mp4`. Content-type при создании и при загрузке должен совпадать.

### SDK 0.2.0 (сверено с исходниками)

```python
os.environ.setdefault("HF_KEY", os.environ.get("HIGGSFIELD_API_KEY", ""))
import higgsfield_client
client = higgsfield_client.Client()

url = client.upload(b"<bytes>", "image/jpeg")     # всё в одном: presign + PUT -> public_url
url = client.upload_file("C:/Work/Platform/Workspace/assets/host.jpg")
url = client.upload_image(pil_image, format="jpeg")
```

Внутри SDK это `POST /files/generate-upload-url` + PUT на пресайнд-URL.

---

## 9. Вебхуки {#9-вебхуки}

Альтернатива опросу: передать в submit query-параметр `hf_webhook` (HTTPS-URL), Higgsfield сделает `POST` на него при `completed` / `failed` / `nsfw`.

```bash
curl --request POST \
  --url "https://api.higgsfield.ai/higgsfield-ai/soul/v2/standard?hf_webhook=https%3A%2F%2Fexample.com%2Fwebhooks%2Fhiggsfield" \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
  --header "Content-Type: application/json" \
  --data '{ "prompt": "Editorial portrait in soft daylight" }'
```

Требования к эндпоинту: публичный HTTPS, JSON-body, ответ ≤10 секунд.

### Конверт доставки

```json
{
  "request_id": "9417a243-...",
  "status": "completed",
  "error": null,
  "expires_at": "2026-10-31T12:05:12.481Z",
  "payload": { "images": [{ "url": "https://cdn.example.com/generated-image.jpg", "content_type": "image/jpeg" }] }
}
```

(`payload.video` для видео; `payload: null` при failed/nsfw; `error` — строка при failed.)

### Подписи (обязательно проверять)

Спецификация **Standard Webhooks**. Заголовки: `webhook-id`, `webhook-timestamp`, `webhook-signature` (`v1,<base64>`, через пробел при нескольких). Секрет: **Settings в консоли**, начинается с `whsec_`, создаётся при первом reveal (до этого доставки не подписаны). Один секрет на все ключи аккаунта; ротация — старый живёт 24 часа (до двух секретов одновременно).

```python
import os
from standardwebhooks import Webhook, WebhookVerificationError

webhook = Webhook(os.environ["HF_WEBHOOK_SECRET"])
try:
    event = webhook.verify(raw_body, headers)   # проверять ДО json.loads, raw body!
except WebhookVerificationError:
    return Response(status=400)
```

(`pip install standardwebhooks`.)

### Доставки и ретраи

- Ответить `2xx` после надёжной записи события; сетевые ошибки и `5xx` ретраятся до 2 часов; `4xx` — постоянный отказ, без ретрая.
- Возможны дубликаты → дедуп по `webhook-id` (или `request_id` + terminal status).
- Если доставка не удалась навсегда — забрать результат авторизованным GET status.
- После delete запроса доставки прекращаются; при retention короче окна ретраев держать polling как fallback.

Для Platform: вебхук — опционально; MVP-цикл может жить на polling (раздел 4).

---

## 10. Фишки {#10-фишки}

### DoP (Director of Photography) — видеомодель камеры

- Имитация реального поведения камеры/объектива: control-пресеты движения камеры и оптики (motion/lens presets).
- В API-каталоге числится **видео**-моделью, но тарифицируется **за генерацию**, не за секунду: **$0.125/generation** (стартовый тариф из блога Higgsfield API).
- Тиры (по сторонним справочникам): `dop-lite` (быстро/дёшево), `dop-preview` (стандарт), `dop-turbo` (качество/латентность) — в официальных доках-индексе страницы DoP сейчас нет; перед использованием проверить схему через estimate/консоль.
- Официальный Node-SDK (github.com/higgsfield-ai/higgsfield-js) содержит примеры image-to-video c DoP.

### Soul ID

Тренировка постоянного персонажа (раздел 5) — «лицо острова-дома» во всех Soul-кадрах; согласованность бренда без повторных промпт-трюков.

### Пресеты Marketing Studio

120 готовых пресетов (Editorial, ads-группы…) с фиксированным соотношением сторон — «товар → кампания» одной строкой (раздел 6).

### Прочее, что стоит знать

- `style_id`/`style_strength` Soul 2: библиотека стилей через soul-styles/v2; `style_strength` сейчас не влияет (доки честно предупреждают).
- `seed` 1..1M — воспроизводимость кадров.
- `enhance_prompt` — авто-улучшение промпта (Soul 2) / пресетное усиление (Marketing Studio).
- Старый Soul v1 (`higgsfield-ai/soul/standard`) жив: `num_images` 1–4, resolution 2K/4K, aspect_ratio вплоть до 21:9 — полезен, если нужны 4K-стоп-кадры.
- Каталог вообще: 17 image-воркфлоу (SOUL, SOUL V2, SOUL Cinema, Soul ID, Marketing Studio x3, Ads Studio, Grok Image 2.0, Recraft V4.1 x4, Qwen Image 3 x2, Ideogram 4.0, Z-Image Turbo) и 67 video-воркфлоу (Genjutsu, Seedance, Kling, Wan, Happy Horse, Cinema Studio 4.0, LTX, MiniMax, PixVerse, Grok…). Доступность меняется — проверять в консоли.

---

## 11. Agent API {#11-agent-api}

В SDK 0.2.0 есть ресурс агента (сверено с исходниками): base `https://api.higgsfield.ai/v1/agent`.

```python
os.environ.setdefault("HF_KEY", os.environ.get("HIGGSFIELD_API_KEY", ""))
import higgsfield_client
client = higgsfield_client.Client()

session = client.agents.sessions.create(config={...})            # POST /v1/agent/sessions {"config": {...}}
client.agents.sessions.send_message(session_id, message=...)     # POST /v1/agent/sessions/{id}/messages
messages = client.agents.sessions.list_messages(session_id)      # GET  /v1/agent/sessions/{id}/messages
client.agents.sessions.interrupt(session_id)                     # POST /v1/agent/sessions/{id}/interrupt
media = client.agents.media.slots(...)                           # POST /v1/agent/media, POST /v1/agent/media/{id}/confirm
```

Типы: `AgentSession`, `AgentMessage` (части с `type == "text"`, `asset_urls` — ссылки на сгенерированные ассеты). Ошибки: `AgentError`, `AgentAccessDeniedError`, `AgentBackendError`, `AgentTimeoutError`.
Синхронные и async-версии (`AsyncAgentsResource`). Документация на Agent API в публичном llms.txt-индексе не публикуется — факты взяты из исходников SDK; это помечено в разделе 18 как «по SDK, не по докам».

---

## 12. Ошибки {#12-ошибки}

### Конверт ошибок

FastAPI-стиль: `{"detail": "<строка>"}`; при валидации `detail` может быть списком. Доки запрещают парсить человеко-читаемые сообщения для бизнес-логики — только HTTP-коды.

### Таблица кодов

| Код | Смысл | Что делать |
|---|---|---|
| 400 | Плохие параметры / отклонён ввод | Исправить запрос |
| 401 | Креденшелы отсутствуют/неверны | Не ретраить; чинить ключ |
| 403 | **Insufficient balance** | Пополнить баланс |
| 404 | Request/модель не найдены для аккаунта | Проверить ID/доступ к модели |
| 409 | Запрос ещё исполняется (например delete по in_progress) | Ждать завершения |
| 422 | Валидация; повторное использование Idempotency-Key с другим телом; плохой `Hf-Expires-After` | Не ретраить |
| 423 | **Model is temporarily blocked** | Позже |
| 429 | Очередь аккаунта полна (`account_queue_full`) или лимит эндпоинта | Ждать `Retry-After`, повторить с тем же Idempotency-Key |
| 500 | Серверная ошибка | Ретрай с экспоненциальным backoff |
| 503 | Модель отключена/не готова; `admission_control_unavailable` | Позже, с backoff |

### Живой пример 401 (из нашего dry-run, рейс 1)

```
GET https://api.higgsfield.ai/requests/5142fdaf-d8d3-45f3-b185-76bf3b8cfb33/status
Authorization: (отсутствует)

HTTP 401 Unauthorized
{"detail": "Invalid credentials"}
```

Точная тройка «нет заголовка → 401 → {"detail": "Invalid credentials"}» — воспроизведена реальным бесплатным вызовом; SDK без ключа даже не доходит до сети: локально бросает `CredentialsMissedError` (см. раздел 1). Оба факта вошли в `pilot-report.json`.

### 429 account_queue_full (форма из доков rate-limits)

```json
{
  "detail": {
    "code": "account_queue_full",
    "message": "Too many queued generations for this account",
    "retryable": true,
    "limit": 40,
    "retry_after_seconds": 30
  }
}
```

(Т.е. `detail` бывает строкой, списком или объектом — парсить по коду ответа, не по форме.)

### Терминальный failed

```json
{ "status": "failed", "request_id": "...", "error": "Generation failed" }
```

Failed и NSFW не тарифицируются; зарезервированное возвращается.

### Политика ретраев (сжатая из доков)

- GET status: ретраить после сетевых ошибок и 5xx.
- 401/422 (и 400 без изменений) — НЕ ретраить.
- Экспоненциальный backoff с jitter, cap попыток, общий дедлайн.
- Submit всегда с `Idempotency-Key`; при неоднозначном таймауте/5xx — повторить с тем же ключом.
- Каждый ответ несёт `X-Correlation-ID` — логировать вместе с `request_id` для поддержки.

---

## 13. Лимиты {#13-лимиты}

- Главный лимит — **конкурентность** (число одновременно исполняемых запросов), зависит от аккаунта и модели; точные значения — в консоли (доки: значения дашборда авторитетны, rate-limit заголовков в ответах нет).
- **Запросы сверх лимита не отклоняются**: принимаются со статусом `queued` и стартуют автоматически, когда освободится слот.
- **Очередь** ограничена кратным лимиту конкурентности (каждый элемент batch считается отдельно). Полная очередь → `429` `account_queue_full` c `Retry-After`, ничего не создаётся и не списывается.
- Эндпоинтные лимиты на НЕ-generation эндпоинты (например `POST /v1/custom-references` — лимит одновременных тренировок Soul ID, по докам 2) отклоняются `429` сразу.
- `503 admission_control_unavailable` при кратком сбое admission control — ретрай с backoff, ничего не списано.
- Тиры конкурентности (open.higgsfield.ai/pricing): **2** concurrent у новых аккаунтов; **10** при балансе ≥$25; **20** при ≥$100; **40** при ≥$1000 — «считаются только средства, внесённые за последние 28 дней». Блог API говорит «создание ключа разблокирует 20 concurrent» — ориентир: тир растёт с пополнениями; авторитетны значения консоли.
- При плановом всплеске трафика — предупредить в Discord заранее.

### Стратегия poll (из доков)

1. Стартовый интервал 2 сек; 2. наращивать до 10 сек; 3. jitter при многих воркерах; 4. стоп на терминальных статусах; 5. app-level таймаут под модель. Решения по ответам: 200 не-терминальный → продолжать; 401 → стоп и чинить ключ; 404 → стоп, проверить request_id/аккаунт; 5xx/сеть → ретрай backoff. Для прод-нагрузки — вебхуки, polling как recovery-путь.

---

## 14. Retention {#14-retention}

- **Выходные файлы хранятся 7 суток** после завершения запроса (фактура «7 дней» подтверждена), затем удаляются; URL перестают работать.
- Точный момент удаления — `expires_at` в завершённом ответе и вебхуке; первичный ответ даёт `expires_after` в секундах (604800 = 7 дней).
- **Сократить retention:** заголовок `Hf-Expires-After` (минимум 1 час) на submit; аккаунт-уровневый срок — по договорённости.
- **Удалить немедленно:** `DELETE /requests/{request_id}` (данные, промпт, параметры; 409 пока queued/in_progress; идемпотентно; платёжные записи остаются).
- Для Platform: скачанные кадры сразу копируются в своё хранилище — API-URL не как долгосрочное хранилище.

---

## 15. Прайсинг и смета {#15-прайсинг-и-смета}

### Тарифы (официальный блог Higgsfield API + open.higgsfield.ai/pricing, USD)

**Изображения (за изображение):**

| Модель | Стартовый тариф |
|---|---|
| **Soul 2** | **$0.0032 / image** |
| Soul Cinema | $0.0032 / image |
| Marketing Studio Image | $0.0059 / image |

**Видео (за секунду, кроме DoP):** Genjutsu Light от $0.050/s; Wan 3.0 от $0.050/s (pr.) — $0.20/s (блог); Kling 2.5 $0.042/s; Kling 2.6 $0.070/s; Kling 3.0 $0.084–0.112/s; Seedance 2.5 $0.0738–0.206/s; Seedance 2.0 $0.141–0.9332/s; PixVerse 6 $0.115/s; MiniMax H3 $0.13/s; LTX 2.5 Pro $0.17/s; **DoP $0.125/generation**. Полный каталог и точные тиры: open.higgsfield.ai/pricing (34 позиции).

**Подтверждение фактуры от 04.11 (~$0.0032/кадр): ПОДТВЕРЖДЕНО** — «Soul 2 Image $0.0032/image» в официальном посте Higgsfield. Оговорка: это стартовый тариф (низкое разрешение/базовый конфиг); 1080p и batch_size=4 стоят дороже — точную сумму на конкретный конфиг даёт **estimate-эндпоинт** (раздел 7), который и считать авторитетом. Иллюстративный `{"usd": "0.094"}` из доков — формат-пример, не прайс Soul 2.

### Смета одного тестового прогона Platform

| Сценарий | Расчёт | Сумма |
|---|---|---|
| **Минимальный smoke-тест** | 1 кадр Soul 2, 720p, batch_size=1 × $0.0032 | **$0.0032** (~0,26 ₽ при ~81 ₽/$) |
| Короткий тест серии | 4 кадра (2 submit'а по batch=1 или 1 submit batch=4*) × $0.0032 | $0.0128 (~1,04 ₽) |
| Серия «день острова» | 16 кадров × $0.0032 | $0.0512 (~4,2 ₽) |
| Персонаж + серия | 1 тренировка Soul ID (цена тренировки в прайсе не публикуется — взять estimate) + 16 кадров × $0.0032 | $0.0512 + estimate(Soul ID) |
| Кампания Marketing Studio | 8 кадров × $0.0059 | $0.0472 (~3,8 ₽) |

\* batch_size=4 в estimate вернёт суммарную стоимость пакета — сместить перед submit, чтобы не гадать.

**Резерв под живой прогон: $5–10 на балансе покрывает сотни кадров и всё тестирование интеграции с запасом; минимальный осмысленный порог тиры конкурентности — $25 (10 concurrent), но для пилота это не требуется.**

### Как платится

Предоплаченный USD-баланс (top-up), списание за успешные генерации, failed/nsfw/canceled не стоят ничего, средства истекают через 1 год, авто-пополнение опционально.

---

## 16. Интеграция в Platform Evo {#16-интеграция}

### Архитектурное место

- Модуль-генератор «остров-дом»: сценарии дня (рассвет/день/вечер/ночь) → кадры Soul 2 с постоянным персонажем (Soul ID) и пресетами Marketing Studio для товарных кампаний.
- DoP — будущий видеослой (движение камеры по острову) — после проверки схемы на живом аккаунте.

### События в events.jsonl (через tools/lib/log_event.py)

```python
import sys
sys.path.insert(0, "tools/lib")
from log_event import append_event

append_event("higgsfield.submit", "Платформа-остров", {
    "model": "higgsfield-ai/soul/v2/standard",
    "request_id": controller.request_id,
    "estimate_usd": est_usd,          # из POST /estimate/... перед submit
})
append_event("higgsfield.completed", "Платформа-остров", {
    "request_id": rid, "frames": len(result["images"]),
    "cost_usd": usage_cost,           # сверка с GET /models/usage
})
append_event("higgsfield.failed", "Платформа-остров", {"request_id": rid, "error": err})
```

Рекомендуемые kind'ы: `higgsfield.submit`, `higgsfield.status`, `higgsfield.completed`, `higgsfield.failed`, `higgsfield.nsfw`, `higgsfield.cancel`, `higgsfield.estimate`.

### Цикл воркера Platform (конспект)

1. Перед submit: `POST /estimate/<model>` → `estimate_usd`; логировать.
2. Submit c `Idempotency-Key` (uuid4, хранить рядом с request_id) и `?hf_webhook=` при наличии HTTPS-эндпоинта.
3. Poll 2→10 c + jitter; каждый переход статуса → `higgsfield.status` в events.jsonl.
4. `completed` → скачать все URL в `Workspace/assets/higgsfield/<request_id>/` немедленно (retention 7 дней).
5. Раз в сутки: `GET /models/usage` → сверка смета/факт → `higgsfield.usage` событие.
6. Ошибки: 401/403/404/422 — стоп и сигнал Sovereign; 429/503/5xx — backoff по Retry-After; 423 — модель временно недоступна, снять задачу с очереди.
7. Ключи: только server-side, из `Workspace/.env` (`HIGGSFIELD_API_KEY`), маскировать в логах.

### Готовые артефакты пилота

- `Workspace/higgsfield-pilot/pilot.py` — auth-check + submit-скелет (константа `REAL_PAYMENT_SANCTIONED=False`; до санкции живых списаний нет). Внимание: `build_soul2_payload` в нём использует устаревшую схему (`num_images`, `2K`) — при живом прогоне заменить на схему раздела 4 (`batch_size`, `720p/1080p`).
- `Workspace/higgsfield-pilot/pilot-report.json` — зафиксированное поведение без ключа.
- `Workspace/higgsfield-pilot/dry-run-log.txt` — лог dry-run.

---

## 17. Чек-лист {#17-чек-лист} — что нужно от Sovereign для живого прогона

1. **Регистрация:** аккаунт на open.higgsfield.ai / console.higgsfield.ai (email).
2. **Ключ:** создать API-креденшел (Key ID + Secret) в консоли; передать значения в `Workspace/.env` как `HIGGSFIELD_API_KEY="<id>:<secret>"` (или самому поставить; значения в чат/отчёты не пересылать).
3. **Пополнение:** минимально достаточная сумма для пилота — **$10** (сотни кадров Soul 2; при желании тиры конкурентности — $25, но пилоту не обязательно). Учесть: средства истекают через 1 год.
4. **(Опционально) Вебхук-секрет:** Settings → reveal `whsec_...` — если хотим event-driven цикл; для MVP хватит polling.
5. **Санкция:** явное подтверждение платного прогона (сейчас в `pilot.py` `REAL_PAYMENT_SANCTIONED=False`); при санкции — правка константы + запуск `pilot.py --live` с ключом в окружении.
6. **Бюджетная рамка:** согласовать потолок прогона (рекомендация: смета раздела 15 — smoke-тест $0.0032, серия 16 кадров $0.0512; потолок $1 на первый живой цикл).

Что НЕ нужно от Sovereign: организация, invoice-контракт, Discord-согласование лимитов — всё это для прод-масштаба, не для пилота.

---

## 18. Источники и степень достоверности {#18-источники}

**Проверено руками (реальные вызовы/инспекция):**
- HTTP 401 `{"detail":"Invalid credentials"}` на api.higgsfield.ai без Authorization (бесплатный вызов, рейс 1, `pilot-report.json`).
- SDK `CredentialsMissedError` без ключа (рейс 1).
- Исходники higgsfield-client 0.2.0 в `.venv`: submit/subscribe/submit_async/subscribe_async, upload/upload_file/upload_image, `POST /files/generate-upload-url`, `DONE_STATUSES=(Completed, NSFW, Cancelled, Failed)`, Agent API `/v1/agent/sessions`, `/sessions/{id}/messages`, `/interrupt`, `/v1/agent/media` (+`/confirm`), ошибки `Agent*`, base URL.

**По официальным докам (docs.higgsfield.ai, индекс llms.txt, прочитано 2026-11-06):**
- authentication, quickstart, concepts/requests, polling, file-uploads, webhooks, errors, rate-limits, billing-and-retention, enterprise/usage-and-billing, how-to/sdk, models/soul-2(+generate), soul-id(+create-character), marketing-studio-image(+generate-and-edit), models/image-generation, models/video-generation.

**По официальным промо-источникам (менее формальные, но публичные):**
- Прайсы: higgsfield.ai/blog/higgsfield-api («Soul 2 Image $0.0032/image», Marketing Studio $0.0059, Soul Cinema $0.0032, DoP $0.125/generation) и open.higgsfield.ai/pricing (видео per-second, тиры конкурентности 2/10/20/40, «funds past 28 days counted»).
- DoP-тиры (dop-lite/preview/turbo) — сторонние справочники (Pixazo/APIFrame/Withone) — экстраполяция, требует проверки на живом аккаунте.

**Экстраполяция / требует живой проверки:**
- Agent API (нет в публичных доках; взят из SDK) — не тестировался без ключа.
- Точная цена 1080p-кадра и batch_size=4 (стартовый тариф $0.0032 подтверждён; конкретный конфиг — только через estimate на аккаунте).
- Цена тренировки Soul ID (в прайс-листе не публиковалась).
- Минимальная сумма пополнения и способы оплаты (доки не публикуют; консоль покажет при первом топ-апе).
- Свежесть бесплатных кредитов/launch-offer для новых аккаунтов (на pricing-странице упоминается, деталей не раскрыто).

**Изменения относительно кэша рейса-1 (docs-cache/ + openapi.json):**
1. Схема Soul 2: `num_images` → `batch_size` (только 1|4); `resolution` теперь `720p|1080p` (не 2K|4K — 2K/4K остались у Soul v1); aspect_ratio default `1:1`, enum 7 значений (убраны 5:4, 4:5, 21:9); добавлены `enhance_prompt`, `custom_reference_id(+strength)`, `style_id(+strength)`, `seed`.
2. Появились новые страницы доков: errors, rate-limits (форма 429 c `detail`-объектом), billing-and-retention (estimate-эндпоинт, expire 1 год), enterprise/usage-and-billing (`GET /models/usage`).
3. Retention: 7 дней подтверждён + появился `Hf-Expires-After` (сокращение, минимум 1 час) и `DELETE /requests/{id}`.
4. Прайсинг: фактура $0.0032/кадр подтверждена официально; concurrency-тиры опубликованы (2/10/20/40).
5. openapi.json (кэш рейса-1) — частичный supplementary-спек; в нём Soul v2 отсутствует (только soul/standard v1), поэтому схема бралась со workflow-страниц доков.
