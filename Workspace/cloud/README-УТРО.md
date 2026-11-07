# README-УТРО — чек-лист Дмитрия: регистрация DO + Yandex Cloud и освоение машин

Читается без знания контекста. Цель: за ~30 минут зарегистрироваться на обеих
площадках, поднять по одной машине и выполнить их «освоение» (инициализация +
снимок `probe-machine.sh`). Всё, что делается руками, — помечено **[руки]**;
всё остальное — копипаста команд. Секреты (токены, карты, ключи) через агента
не передаются: команды скриптов уже написаны так, что секретов в них нет —
ключи/токены Дмитрий вставляет сам, только в `Workspace/.env` или в поля UI.

## 0. Подготовка (один раз, до регистрации)

1. **[руки]** Проверить, что есть SSH-ключ:
   ```bash
   ls ~/.ssh/id_ed25519.pub
   ```
   Нет — создать: `ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519`
2. Создать файл `Workspace/.env` (рядом с `Workspace/cloud/`), если его нет, и внести строки-плейсхолдеры:
   ```
   DO_TOKEN=           # вставит Дмитрий после шага DO-3
   YC_OAUTH_TOKEN=     # вставит Дмитрий после шага YC-3 (не обязателен, если всё через yc)
   ```
   Файл НИКОГДА не коммитится (секреты живут только в `Workspace/.env`).
3. Скрипты лежат в `Workspace/cloud/` — они и загружаются на машины целиком
   (скопируете на шагах DO-7 / YC-7).

---

## A. DigitalOcean — 10 шагов

| # | Шаг | Что делать |
|---|-----|-----------|
| DO-1 | **[руки] Регистрация** | digitalocean.com → Sign Up (email + карта). До конца шагов DO-2..DO-10 вход через браузер. |
| DO-2 | **[руки] SSH-ключ в DO** | Console: Settings → Security → **Add SSH Key** → вставить содержимое `~/.ssh/id_ed25519.pub` → имя `dmitriy-laptop`. |
| DO-3 | **[руки] API-токен** | Console: API → **Generate New Token**, название `platform-evo`, права **Full Access** → скопировать строку → вставить в `Workspace/.env` в `DO_TOKEN=...` (не в git!). |
| DO-4 | Создать дроплет (UI) | Create → **Droplets**: Region **Amsterdam (AMS3)** или Frankfurt; Image **Ubuntu 24.04 (LTS) x64**; Size: Shared CPU **Basic**, тариф **Premium/Regular 2 vCPU / 4 GB / 80 GB** (`s-2vcpu-4gb`, ~$24/мес — [руки] выбрать в UI аналогичный); Authentication: **SSH Key** (ключ с DO-2); Hostname: `evo-stand-do`. Quantity: 1. → Create Droplet. |
| DO-5 | Взять IP | Console → Droplets → `evo-stand-do` → скопировать публичный IPv4. Ниже `<DO_IP>` — подставляйте его. |
| DO-6 | Первый вход | ```ssh root@<DO_IP>``` (пароля нет — только ключ; ответить yes на fingerprint). |
| DO-7 | Загрузить скрипты | С ноутбука: ```scp -r Workspace/cloud root@<DO_IP>:/root/``` (или через `doctl compute ssh`, если поставлен doctl — необязательно). |
| DO-8 | Инициализация | На дроплете: ```cd /root/cloud && sudo bash bootstrap.sh do``` (10–15 мин: apt, часовой пояс Ташкент, ufw, fail2ban, ssh-hardening, пользователь `deploy`, docker). Проверка: `ufw status`, `docker --version`. |
| DO-9 | Деплой стендов | Там же: ```sudo bash deploy-polygons.sh all``` (Juice Shop :3000, DVWA :8081, n8n :5678, Uptime-Kuma :3001, WireGuard :51820/udp; пароли сгенерируются в `/opt/polygons/dvwa/.env`). По желанию k3s-мастер: `sudo bash install-k3s.sh`. |
| DO-10 | Снимок машины | Там же: ```sudo bash probe-machine.sh``` → забрать отчёт с ноутбука: ```scp root@<DO_IP>:/root/probe-*.md Workspace/cloud/probes/``` → прогнать чек-лист «Вывод» внутри отчёта. |

Проверка снаружи после DO-9: в браузере `http://<DO_IP>:3000` — Juice Shop отвечает.

---

## B. Yandex Cloud — 10 шагов

| # | Шаг | Что делать |
|---|-----|-----------|
| YC-1 | **[руки] Регистрация** | yandex.cloud → «Подключиться» (Яндекс-аккаунт + карта/телефон). Создать **платёжный аккаунт**, затем облако `platform-evo` и каталог `cloud-lane`. |
| YC-2 | CLI | На ноутбуке: ```curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash``` → перезапустить shell → `yc --version`. |
| YC-3 | **[руки] Токен в CLI** | `yc init` — откроет ссылку OAuth в браузере; Дмитрий подтверждает, токен сам попадёт в профиль `yc` (дополнительно можно продублировать в `Workspace/.env` как `YC_OAUTH_TOKEN=...`). Проверка: `yc config list`. |
| YC-4 | Проверить образ | ```yc compute image list-latest-from-family ubuntu-2404-lts --folder-id standard-images``` — должен вернуть строку с id (семейство Ubuntu 24.04 существует, это его контроль). |
| YC-5 | **[руки] Вставить ключ в user-data** | В файле `Workspace/cloud/cloud-init-yc.yaml` заменить `{{SSH_PUBLIC_KEY}}` на содержимое `~/.ssh/id_ed25519.pub` (одной строкой). Это единственная ручная правка файла. |
| YC-6 | Создать ВМ | В каталоге `Workspace/cloud/`: ```yc compute instance create --name evo-stand-yc --hostname evo-stand-yc --zone ru-central1-a --network-interface subnet-name=default-ru-central1-a,nat-ip-version=ipv4 --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2404-lts,size=40 --cores 2 --memory 4 --metadata-from-file user-data=cloud-init-yc.yaml``` — ВМ рождается уже настроенной (bootstrap не нужен). TODO [руки]: имя тарифа ВМ (2 vCPU/4GB, напр. `s3-c2-m4`) проверить в UI/`yc compute instance create --help` — флаги `--cores/--memory` выше заменяют его. |
| YC-7 | Вход и загрузка скриптов | IP: ```yc compute instance get evo-stand-yc --format 'json(network_interfaces[0].primary_v4_address.one_to_one_nat.address)'``` → `<YC_IP>`. Загрузка: ```tar czf /tmp/cloud.tgz -C Workspace cloud && yc compute scp --user deploy --instance-name evo-stand-yc /tmp/cloud.tgz:/home/deploy/``` → ```ssh deploy@<YC_IP>``` → там: ```tar xzf ~/cloud.tgz```. |
| YC-8 | Инициализация (если ВМ без user-data) | Если ВМ создана с user-data (YC-6) — пропустить. Иначе: ```cd ~/cloud && sudo bash bootstrap.sh yc```. |
| YC-9 | Деплой стендов и k3s-агент | ```sudo bash deploy-polygons.sh all```; для практики мультиоблака: с мастера DO взять токен (`sudo cat /var/lib/rancher/k3s/server/node-token`) и здесь: ```sudo K3S_TOKEN=<токен> bash install-k3s.sh --agent https://<DO_IP>:6443``` |
| YC-10 | Снимок машины | ```sudo bash probe-machine.sh``` → ```exit``` → ```yc compute scp --user deploy --instance-name evo-stand-yc '/home/deploy/probe-*.md':./``` → перенести в `Workspace/cloud/probes/`. |

Проверка снаружи после YC-9: `http://<YC_IP>:3000` — Juice Shop; на мастере DO: `k3s kubectl get nodes` — два узла.

---

## Таблица «что куда деплоим»

| Что | Порт | Машина | Зачем |
|-----|------|--------|-------|
| bootstrap / cloud-init | — | обе | база: apt, TZ Asia/Tashkent, ufw+fail2ban, ssh key-only, deploy, docker |
| **Juice Shop** | 3000 | DO `evo-stand-do` | секьюрити-цель, СВОЯ (легальнее ломать своё) |
| **DVWA** | 8081 | DO | практика эксплойтов с уровнями сложности |
| **n8n** | 5678 | DO | автоматизация (журналы, watchdog-триггеры) |
| **Uptime-Kuma** | 3001 | DO | мониторинг всех стендов и партнёров |
| **WireGuard** | 51820/udp | DO | туннель к домашней лабе (peer `homelab-dmitriy`; конфиг пира: `/opt/polygons/wireguard/config/peer_homelab-dmitriy/` — скачать на ноутбук) |
| **k3s master** | 6443 | DO | практика k8s, база мультиоблака |
| **k3s agent** | — | YC `evo-stand-yc` | вторая машина кластера через границу облаков |
| **probe-machine.sh** | — | обе | «куда мы имеем доступ и что умеет машина» → `probe-<host>.md` в `Workspace/cloud/probes/` |

## Правила безопасности (коротко)

- Токены — только в `Workspace/.env` (НЕ в git). В скриптах секретов нет по построению.
- SSH на обеих машинах key-only, `PermitRootLogin prohibit-password`, root без пароля.
- ufw закрыт по умолчанию; открыто: 22, 80, 443, 3000, 8081, 5678, 3001, 51820/udp, 6443.
- Стенды (Juice Shop, DVWA) — учебные и дырявые НАМЕРЕННО: это цели, не прод. Не держать там ничего настоящего.

## Состав `Workspace/cloud/`

`bootstrap.sh` · `cloud-init-do.yaml` · `cloud-init-yc.yaml` · `install-k3s.sh` ·
`deploy-polygons.sh` · `compose/{juice-shop,dvwa,n8n,uptime-kuma,wireguard}.yml` ·
`probe-machine.sh` · этот README.
