# Скраперы: ландшафт и план hh-скрапера

Дата: 2026-10-30 (~22:00 Тшк) · Автор: ZCode · Статус: план, ждёт санкции Sovereign (Дмитрий)
Контекст: [[scrapers-top-priority]] — «скраперы, парсеры и подобные инструменты — в огромном приоритете».
Цель: стабильный поток вакансий с зарплатами (hh.ru/hh.uz — главный пробел, E-018/E-020) в дневной аналитический ритм и на остров Trading Quarter.

---

## 1. Живые факты (пробы 30.10 с этой машины, Ташкент)

| Слой | Проверка | Результат |
|---|---|---|
| Официальный API | `api.hh.ru/vacancies?text=DevOps`, `api.hh.uz/...` | **403 forbidden** (оба хоста, чистый urllib, браузерный UA). С этой сети официальный API закрыт. |
| HTML выдача | `GET /search/vacancy?text=DevOps` | **200**, серверный рендер (~1.8 МБ), карточки в DOM, пагинация `?page=N` — обычные HTML-страницы. Редирект `hh.uz → tashkent.hh.uz`. |
| Web-API сайта | `GET /shards/vacancies?text=DevOps&page=…` | **406** (XML `<doc/>`) на hh.ru, hh.uz и tashkent.hh.uz — **даже** с: куками сессии (`hhtoken`, `_xsrf`, `hhuid`, `__ddg*`), полным набором браузерных заголовков (Sec-Fetch-*, sec-ch-ua, priority), TLS-имперсонацией Chrome (curl_cffi). |
| TLS-защита | curl_cffi `impersonate="chrome"` | HTML проходит (значит DDoS-Guard-фингерпринт TLS обходится), но shards всё равно 406 — стена не в TLS. |
| Перехват живого XHR | headless Chrome → mitmproxy 12.3.1 | Стартовая страница рендерится **без XHR к shards** (SSR). Рецепт shards требует интеракции (клик пагинации) — следующий эксперимент. |
| Зарплаты на карточках hh.uz | grep DOM | Спаны `vacancy-serp__vacancy-compensation` есть, но для DevOps это плашки «Выплаты: два раза в месяц», сумм почти нет. Суммы — на детальных страницах (`data-qa="vacancy-salary"`) и в карточках hh.ru. |

Вывод: **HTML-слой работает сегодня** и отдаёт всё, кроме сумм зарплат по uz-карточкам; shards-API — красивый, но охраняемый путь; официальный API закрыт по IP.

## 2. Слои доступа к данным hh (лестница)

- **L0 — официальный API** (`api.hh.ru`, OpenAPI: github.com/hhru/api): структурные зарплаты, лимит 2000 вакансий/запрос. Здесь: 403. Обход: авторизация (access token работодателя/соискателя), либо вынесение пуллера на VPS/прокси. Самый честный путь, если появится токен или IP.
- **L1 — web-API сайта** (`/shards/vacancies` — тот же JSON, что видит браузер): 406. Рецепт недодобран: нужен перехват XHR с реальным кликом пагинации (browser-use/DevTools/mitmproxy — раз, и рецепт у нас в руках) или итерация rae с сохранением HAR. Приоритет эксперимента — средний: HTML даёт те же данные.
- **L2 — HTML выдача** (SSR): работает сейчас. Карточки: `data-qa="serp-item__title-text"`, ссылка `data-qa="serp-item__title"`, зарплатный спан `vacancy-serp__vacancy-compensation`, работодатель `vacancy-serp__vacancy-employer`. Пагинация — `?page=N`. Для зарплат: догрузка детальных страниц вакансии (блок `data-qa="vacancy-salary"`), rate-limit вежливый.
- **L3 — мобильный/внутренний API** (`apiver.hh.ru` и мобильные клиенты): недоразведано; реверс через rae/mitmproxy — «ламповый» резерв.

## 3. Готовые скраперы с просторов (разбор)

| Проект | Подход | Выхлоп | Живость | Что берём |
|---|---|---|---|---|
| [strpc/parse-vacancy-from-hh_ru](https://github.com/strpc/parse-vacancy-from-hh_ru) | async aiohttp + BS4/lxml, **HTML-выдача**, data-qa селекторы | CSV: title, salary, company, url, description; 1945 вакансий за 8.4 c | Мал, 9 коммитов, 1 звезда — учебный | Селекторы data-qa (подтверждены нашими пробами), паттерн пагинации по `data-page` |
| [qdimka/headhunter-scraper](https://github.com/qdimka/headhunter-scraper) | CLI, экспортёры | вакансии по запросу/городу | Py2-эпоха, мёртв | Ничего, кроме идеи фильтров CLI |
| [Apify hh.ru Scraper](https://apify.com/haketa/hh-scraper/api/python) (hosted) | облако, готовый actor «Jobs, Salaries & Skills» | JSON с зарплатами и навыками | Поддерживается автором | Альтернатива «без инфраструктуры», но платно и данные уходят в облако — против нашего контура |
| Темы [hh-ru-scraper](https://github.com/topics/hh-ru-scraper), [vacancy-parser](https://github.com/topics/vacancy-parser) | в основном учебные парсеры **официального API** | CSV/DB | разные | Подтверждение: официальное API — стандарт индустрии; 403 с наших IP — наш частный случай |
| наш `tools/job_search.py` | stdlib-HTTP, HTML-фолбэк hh + 5 других источников | `job_search_results.json` + `vacancies.js` | живой, наш | База: новый hh-скрапер = апгрейд его hh-фильтера, не отдельный зоопарк |

Общий вывод: готового «серебряного» скрапера нет — живые проекты либо учебные (официальный API), либо хостед-платные. **Пишем свой тонкий слой поверх HTML + curl_cffi**, схемы данных уже у нас.

## 4. Рекомендуемый стек (одна рекомендация)

- **Ядро: Python 3.13 + curl_cffi** (`impersonate="chrome"`) — проходит DDoS-Guard-фингерпринт; `requests`-совместимый API. Fallback: stdlib urllib (как сейчас) и playwright только там, где нужен JS.
- **Парсер: BS4/lxml по data-qa** (не по классам-простыням) — селекторы стабильны годами, подтверждены пробами и strpc.
- **Вежливость: пауза 2–5 с между страницами**, браузерный UA, без логинов, только публичные данные; детект 406/403 → фолбэк и пропуск, никаких агрессивных ретраев.
- **Схема записи: как в `job_search_results.json`** (source/title/company/location/salary/date/url/snippet) + `has_salary` (правило E-020) — скрапер становится ещё одним фильтром агрегатора, дневной ритм snapshot → extract → report не меняется.
- **Оркестрация: не заводить** — рядом уже живут schtasks-задачи и автоматизации ZCode; скраперу достаточно CLI-точки входа.

## 5. Тяжёлая артиллерия (установлено и проверено 30.10)

- **mitmproxy 12.3.1** — установлен (`uv tool install mitmproxy`). Рабочий сценарий перехвата (проверен): аддон-логгер `~/rae-work/hh-mitm/hh_capture.py` → `mitmdump -q -p 8899 -s <addon>` → headless Chrome с `--proxy-server=127.0.0.1:8899 --ignore-certificate-errors` → потоки в `flows.jsonl`. Порт 8080 на машине занят (PID 5104) — не трогать.
- **curl_cffi** — установлен в системный Python; TLS-имперсонация Chrome.
- **reverse-api-engineer** — см. отдельный вердикт (дорого: ~$8.5/прогон на sonnet; для рутины haiku).
- **Wireshark** — НЕ установлен (тяжёлый; ставить через `winget install Wireshark` по желанию). Ламповый трюк на будущее: `SSLKEYLOGFILE=C:\temp\sslkeys.log` в окружении Chrome + в Wireshark `Preferences → Protocols → TLS → (Pre)-Master-Secret log filename` — расшифровка своего же TLS-трафика; для HTTP(S)-API mitmproxy удобнее, Wireshark — для нижних уровней (TCP-ретрансмиты, QUIC, DNS).

## 6. Риски и границы

- Защита hh: DDoS-Guard (TLS/JS), 406-стена на shards, 403 на официальный API. Всё наблюдали руками. Не дёргать: паузы, один запрос за раз, кэш уже есть (E-016/E-020).
- ToS hh: публичные данные, без логинов, без репоста «как есть» наружу; данные только в наш приватный контур.
- Хрупкость селекторов: data-qa меняется редко, но парсер должен молча деградировать (0 карточек → алерт в журнал, не падение).
- Компетенция: hh.uz — региональный редирект (`tashkent.hh.uz`); хардкодить host нельзя.

## 7. Roadmap (оценка времени)

1. **Апгрейд hh-парсера в `tools/job_search.py`** (curl_cffi + data-qa + пагинация `page=0..2` + has_salary): ~1 вечер. Выигрыш сразу: свежесть и полнота hh в дайджесте.
2. **Зарплатная догрузка**: топ-N детальных страниц (data-qa="vacancy-salary") с паузами: ~1 вечер. Закрывает E-018 по uz.
3. **Эксперимент «рецепт shards»**: перехват XHR с кликом пагинации (browser-use skill или rae-итерация с HAR): 1 экспериментальный вечер, результат — либо JSON-клиент ( best), либо честное «HTML достаточно».
4. **Опционально**: api.hh.ru через VPS/токен — только если лимиты HTML станут тесны.

## 8. Источники

- Пробы этой машины 30.10 (сценарии в журнале E-022-наследнике и командной истории)
- [strpc/parse-vacancy-from-hh_ru](https://github.com/strpc/parse-vacancy-from-hh_ru) · [qdimka/headhunter-scraper](https://github.com/qdimka/headhunter-scraper) · [Apify hh.ru Scraper](https://apify.com/haketa/hh-scraper/api/python) · [topic: hh-ru-scraper](https://github.com/topics/hh-ru-scraper) · [topic: vacancy-parser](https://github.com/topics/vacancy-parser) · [topic: headhunter](https://github.com/topics/headhunter)
- [curl_cffi](https://github.com/lexiforest/curl_cffi) · [mitmproxy](https://mitmproxy.org) · официальный OpenAPI hh: [github.com/hhru/api](https://github.com/hhru/api)
