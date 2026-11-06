# evofind — мгновенный поиск по Platform Evo (Golang)

Написан по заказу Sovereign 06.11 (ночь, ZCode). Цель: агентам и человеку — найти
любой файл/строку в репо за миллисекунды, вместо того чтобы жечь токены на ручной
обход каталогов. Тянет на скрап-пул следующий шаг: та же механика горутин.

## Что умеет

- **Параллельная индексация** репо горутинами (4×CPU воркеров), тексты в памяти.
- **Приватность зашита в код**: `Workspace/private/`, `.env`, `node_modules`, `.git`,
  `graphify-out` не индексируются никогда (см. `skipDirs`/`skipFiles` в indexer.go).
- **Поиск всех слов запроса** в одной строке, ранжирование по частоте + свежесть.
- **HTTP API** (только loopback): `GET /search?q=&limit=&ext=`, `GET /stats`,
  `POST /reindex` — индекс пересобирается на лету без перезапуска.
- **CLI**: `index`, `search -q`, `serve`.
- **Машинный журнал**: каждый HTTP-поиск пишется в `Workspace/logs/events.jsonl`
  конвертом `evo.tools.evofind` (тот самый фундамент data-foundation Л-1/Л-2).

## Запуск (portable Go в C:\Work\go-portable)

```
set PATH=C:\Work\go-portable\go\bin;%PATH%
cd C:\Work\Platform\golang_test
go build -o evofind.exe .
evofind.exe index
evofind.exe -q "jobs.json" -limit 10 search
evofind.exe serve -port 8973
curl "http://127.0.0.1:8973/search?q=fundament&limit=5"
```

ГОЧА Go-flag: флаги (`-q`, `-limit`, `-root`, `-port`) пишутся ДО позиционного режима (`index`/`search`/`serve`).

## Тесты

```
go test ./... -v
```

## Ограничения честности

- Индекс в памяти: корень платформы ~N МБ текста — живут в RAM до перезапуска.
- Поиск substring-овый, без морфологии и регулярных выражений (для скорости).
- Единственный бинарник — `evofind.exe`; в git не брать (правило бинарников).
