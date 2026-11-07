#!/usr/bin/env bash
# probe-machine.sh — «освоение удалённой машины»: снимок добычи с любой свежей ВМ
# (Ubuntu 24.04) в markdown-отчёт probe-<host>.md. Полностью read-only: ничего не
# ставит, не меняет, не трогает — поэтому без аргументов сразу снимает отчёт.
#
# Собирает: ОС/ядро, CPU/RAM/диск, внутренние/внешний IP, открытые порты (ss),
# гео-IP (бесплатный сервис без ключа), docker/k3s версии, cloud-метаданные DO/YC,
# пинг и трассировку до узла-ориентира.
#
# Usage:
#   sudo bash probe-machine.sh                 # отчёт ./probe-<host>.md
#   sudo bash probe-machine.sh --out /tmp      # отчёт в другой каталог
#   PROBE_TARGET=1.1.1.1 sudo bash probe-machine.sh   # свой узел-ориентир
#   sudo bash probe-machine.sh --help
# Секретов НЕТ: сервисы гео/метаданных — без ключей. Токены не читаются никогда.

set -u

OUT_DIR="."
PROBE_TARGET="${PROBE_TARGET:-1.1.1.1}"

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --out) OUT_DIR="${2:-.}"; shift 2 ;;
    *) printf '[ОШИБКА] неизвестный аргумент: %s (см. --help)\n' "$1" >&2; exit 1 ;;
  esac
done

mkdir -p "$OUT_DIR" 2>/dev/null
HOSTNAME_NOW="$(hostname 2>/dev/null || echo unknown-host)"
SANITIZED="$(printf '%s' "$HOSTNAME_NOW" | tr -c 'A-Za-z0-9._-' '_')"
REPORT="$OUT_DIR/probe-$SANITIZED.md"

# утилита есть → вывод, нет → заглушка (probe не должен падать на свежей машине)
have() { command -v "$1" >/dev/null 2>&1; }

run_or_na() { # run_or_na <команда...>
  local cmd="$1"; shift
  if have "$cmd"; then "$cmd" "$@" 2>/dev/null || echo "(ошибка выполнения)"
  else echo "(не установлено: $cmd)"; fi
}

log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" >&2; }

log "снимаю машину: $HOSTNAME_NOW → $REPORT"

# --- сеть: внутренние IP ------------------------------------------------------
INT_IPS="$(ip -4 -br addr show 2>/dev/null | grep -v '^lo' || echo '(ip недоступен)')"

# --- сеть: внешний IP (3 бесплатных источника по очереди) ----------------------
EXT_IP=""
for src in "https://api.ipify.org" "https://ifconfig.me" "https://icanhazip.com"; do
  EXT_IP="$(curl -4 -fsS --max-time 6 "$src" 2>/dev/null | tr -d '[:space:]')"
  [ -n "$EXT_IP" ] && break
done
[ -n "$EXT_IP" ] || EXT_IP="(не определился — исходящий HTTP запрещён?)"

# --- гео-IP -------------------------------------------------------------------
GEO="$(curl -fsS --max-time 8 'http://ip-api.com/json/?fields=status,country,countryCode,regionName,city,isp,org,as,lat,lon,timezone,query' 2>/dev/null \
  || curl -fsS --max-time 8 'https://ipinfo.io/json' 2>/dev/null \
  || echo '(гео-сервисы недоступны)')"

# --- cloud-метаданные (DO / YC), ни один не обязателен -------------------------
DO_META="$(curl -fsS --max-time 3 http://169.254.169.254/metadata/v1/id 2>/dev/null && printf ' (DigitalOcean droplet id выше)' || echo '—')"
YC_META="$(curl -fsS --max-time 3 -H 'Metadata-Flavor: Google' \
  'http://169.254.169.254/computeMetadata/v1/instance/name' 2>/dev/null \
  && printf ' / ' \
  && curl -fsS --max-time 3 -H 'Metadata-Flavor: Google' \
     'http://169.254.169.254/computeMetadata/v1/instance/zone' 2>/dev/null \
  || echo '—')"
CPU_MODEL="$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed 's/^ //' || echo '?')"

# --- сборка отчёта -------------------------------------------------------------
{
  echo "# Probe: $HOSTNAME_NOW"
  echo
  echo "Дата снимка: $(date '+%Y-%m-%d %H:%M:%S %Z'). Источник: probe-machine.sh (read-only)."
  echo
  echo "## 1. ОС и ядро"
  echo '```'
  grep PRETTY_NAME /etc/os-release 2>/dev/null || echo "(нет /etc/os-release)"
  echo "ядро: $(uname -r)"
  echo "arch: $(uname -m)"
  echo "uptime: $(uptime -p 2>/dev/null || uptime 2>/dev/null || echo '(недоступен)')"
  echo '```'
  echo
  echo "## 2. CPU / RAM / диск"
  echo '```'
  echo "CPU: $(nproc 2>/dev/null || echo '?') vCPU — $CPU_MODEL"
  echo "load: $(cat /proc/loadavg 2>/dev/null || echo '?')"
  run_or_na free -h
  echo
  run_or_na df -h --exclude-type=tmpfs --exclude-type=devtmpfs
  echo
  run_or_na lsblk
  echo '```'
  echo
  echo "## 3. Сеть"
  echo
  echo "- Внутренние IP: см. ниже"
  echo "- Внешний IP: **$EXT_IP**"
  echo "- Узел-ориентир: $PROBE_TARGET"
  echo
  echo "### Внутренние интерфейсы"
  echo '```'
  echo "$INT_IPS"
  echo '```'
  echo
  echo "### Гео-IP (без ключей)"
  echo '```json'
  echo "$GEO"
  echo '```'
  echo
  echo "### Cloud-метаданные"
  echo "- DigitalOcean droplet id: $DO_META"
  echo "- Yandex Cloud имя/зона: $YC_META"
  echo
  echo "## 4. Открытые порты (ss)"
  echo '```'
  run_or_na ss -tulpn
  echo '```'
  echo
  echo "## 5. Пинг и трасса до $PROBE_TARGET"
  echo '```'
  run_or_na ping -c 4 -W 3 "$PROBE_TARGET"
  echo
  run_or_na tracepath -n -m 15 "$PROBE_TARGET"
  echo '```'
  echo
  echo "## 6. Платформы на борту (docker / k3s)"
  echo '```'
  if have docker; then
    echo "docker: $(docker --version 2>/dev/null)"
    echo "compose: $(docker compose version 2>/dev/null || echo 'plugin нет')"
    echo "контейнеров: $(docker ps -q 2>/dev/null | wc -l) запущено"
  else
    echo "docker: (не установлен)"
  fi
  if have k3s; then
    echo "k3s: $(k3s --version 2>/dev/null | head -1)"
    echo "узлы: $(k3s kubectl get nodes 2>/dev/null | tr '\n' ' | ')"
  else
    echo "k3s: (не установлен)"
  fi
  if have ufw; then echo "ufw: $(ufw status 2>/dev/null | head -1)"; else echo "ufw: (не установлен)"; fi
  if have fail2ban-client; then echo "fail2ban: $(fail2ban-client status 2>/dev/null | tr '\n' ' ' || echo 'не отвечает')"; else echo "fail2ban: (не установлен)"; fi
  echo '```'
  echo
  echo "## 7. Вывод: что умеет машина"
  echo
  echo "- [ ] bootstrap выполнен? (см. секции 4 и 6)"
  echo "- [ ] внешний IP совпадает с ожидаемым от DO/YC?"
  echo "- [ ] гео-IP разумный (регион облачного провайдера)?"
  echo "- [ ] порты стенда (3000/8081/5678/3001/51820udp/6443) слушаются после deploy-polygons?"
  echo
} > "$REPORT"

log "ГОТОВО: отчёт $REPORT (read-only, система не менялась)"
