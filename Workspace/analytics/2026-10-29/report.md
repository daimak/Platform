# Аналитика поиска работы — снапшот 2026-10-29

*Сгенерировано tools/analytics_report.py; предыдущий снапшот: — (это первый)*

## Сводка

- Вакансий всего: **213** (уникальных URL: 213)
- Предыдущего снапшота нет — дифф появится со второго прогона
- Свежих (≤14 дней): 19; без разборной даты: 123; старше: 71

## Зарплаты (USD/месяц)

- **С зарплатой (✓ has_salary=yes): 16** из 213; без вилки: 197 — не брак, вилку спрашиваем при первом контакте
- Фильтрация: `salary_extracted.csv`, колонка `has_salary` (yes/no); пересчитано в USD/мес: 8
- По всей выборке: медиана **14,584**, p25 12,084, p75 17,084

| Сегмент | n | медиана | min–max |
|---|---|---|---|
| remote-intl (HN/RemoteOK/Remotive) | 7 | 16,250 | 1,380–18,666 |
| tg-ru (@remote_jobs_ru) | 1 | 10,792 | 10,792–10,792 |

*Внимание: UZS пересчитан по фиксированному курсу из флага --uzs-rate экстрактора — приближение.*

## Источники

| Источник | всего | свежих ≤14д | с ЗП ✓ |
|---|---|---|---|
| hh (hh.uz, html) | 60 | 0 | 0 |
| hh (hh.ru, html) | 60 | 0 | 0 |
| HN (Ask HN: Who is hiring? (October 2026)) | 34 | 1 | 7 |
| Telegram @devops_vacancies | 20 | 0 | 0 |
| RemoteOK | 17 | 11 | 5 |
| Telegram @remote_jobs_ru | 14 | 4 | 1 |
| Remotive | 5 | 3 | 2 |
| OLX.uz | 3 | 0 | 1 |

## Топ-10 «скорость до денег» (эвристика)

| балл | вакансия | источник | дата | USD/мес |
|---|---|---|---|---|
| 2 | 💻 Front‑End AI‑инженер 🏢 Accenture • 🌍 Remote 💰 $54K - $205K/год 🛠 Сте | Telegram @remote_jobs_ru | 2026-10-26 | 4,500.0 |
| 0 | Ask HN: Who is hiring? (October 2026) | HN (Ask HN: Who is hiring? (October 2026)) | 2026-10-12 | 1,160.0 |
| 0 | Ask HN: Who is hiring? (October 2026) | HN (Ask HN: Who is hiring? (October 2026)) | 2026-10-10 | 14,583.0 |
| 0 | Ask HN: Who is hiring? (October 2026) | HN (Ask HN: Who is hiring? (October 2026)) | 2026-10-03 | 11,667.0 |
| 0 | Ask HN: Who is hiring? (October 2026) | HN (Ask HN: Who is hiring? (October 2026)) | 2026-10-02 | 12,500.0 |
| 0 | Ask HN: Who is hiring? (October 2026) | HN (Ask HN: Who is hiring? (October 2026)) | 2026-10-02 | 10,000.0 |
| 0 | Ask HN: Who is hiring? (October 2026) | HN (Ask HN: Who is hiring? (October 2026)) | 2026-10-02 | 9,417.0 |
| 0 | Ask HN: Who is hiring? (October 2026) | HN (Ask HN: Who is hiring? (October 2026)) | 2026-10-01 | 16,583.0 |

## Свежие без вилки — спросить ЗП при контакте (has_salary=no, не брак)

| вакансия | источник | дата | возраст, дн |
|---|---|---|---|
| Senior Back-end Developer | Remotive | 2026-10-27 | 1 |
| 🖥️ Senior Java‑разработчик 🏢 pathway solutions gmbh • 🌍 Remote 💰 По до | Telegram @remote_jobs_ru | 2026-10-20 | 8 |
| Risk Analyst | RemoteOK | 2026-10-20 | 8 |
| ⚙️ Azure DevOps инженер 🏢 Coopers Group AG • 🌍 Remote 💰 По договорённо | Telegram @remote_jobs_ru | 2026-10-19 | 9 |
| Technical Account Manager | RemoteOK | 2026-10-17 | 11 |
| APAC Python | RemoteOK | 2026-10-16 | 12 |
| Associate Data Scientist | RemoteOK | 2026-10-16 | 12 |
| Director of IT and Workplace | RemoteOK | 2026-10-16 | 12 |
| Senior Software Engineer II Applied AI | RemoteOK | 2026-10-15 | 13 |
| 🤖 Инженер по внедрению ИИ 🏢 Neurawork GmbH & Co. KG • 🌍 Remote 💰 По до | Telegram @remote_jobs_ru | 2026-10-15 | 13 |
*…и ещё 2 — фильтруй в `salary_extracted.csv` по has_salary=no*

## OLX автосервисы (быстрый доход)

- Объявлений: 52; категории: {'job': 38, 'rent': 8, 'service': 4, 'product': 1, 'other': 1}
- Вакансий: 38, из них с жильём: 16
- С явной ценой: 6 из 52 (цена в отдельном поле выдачи — парсер её пока не берёт)

## Ограничения данных

- Без даты: 123; без вилки (has_salary=no — спросить при контакте): 197; location — свободный текст (не нормализован)
- Даты старше месяца — вероятно кэш прошлых прогонов; в трендах фильтровать

## Выводы

- Записываем всё: отсутствие вилки — не красный флаг; ✗ = спросить ЗП при первом контакте.
- Рынок по вашей выборке: медиана 14,584 USD/мес (n=8). Сравнивайте с целью ~2500 USD/мес и своей специализацией.
- Источники со свежими записями (см. таблицу «Источники») — там стоит смотреть в первую очередь.
