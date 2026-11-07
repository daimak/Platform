#!/usr/bin/env bash
# deploy-polygons.sh — деплой учебных стендов Platform Evo в docker compose (Ubuntu 24.04).
# Запускается НА СЕРВЕРЕ, рядом лежит каталог compose/ (из Workspace/cloud/).
#
# Стенды: juice-shop (3000), dvwa (8081), n8n (5678), uptime-kuma (3001), wireguard (51820/udp).
# Каждый — отдельный compose-файл в compose/, каталог /opt/polygons/<имя>/, свои пароли:
# генерация openssl rand на месте, в .env (chmod 600). Секретов В ЭТОМ СКРИПТЕ НЕТ.
#
# Usage:
#   sudo bash deploy-polygons.sh all                 # поднять все стенды
#   sudo bash deploy-polygons.sh dvwa                # один стенд
#   sudo bash deploy-polygons.sh wireguard --serverurl <внешний_IP_облака>
#   sudo bash deploy-polygons.sh stop dvwa           # остановить стенд (данные сохраняются)
#   sudo bash deploy-polygons.sh status              # что работает
# Без аргументов — только этот help, ничего не выполняет (правило dry-run).

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_SRC="$SCRIPT_DIR/compose"
ROOT="/opt/polygons"
SERVICES="juice-shop dvwa n8n uptime-kuma wireguard"

log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { printf '[ОШИБКА] %s\n' "$*" >&2; exit 1; }

usage() { sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0; }

is_service() { case " $SERVICES " in *" $1 "*) return 0;; *) return 1;; esac; }

# .env сервиса: создаётся один раз, повторный запуск НЕ перегенерирует (пароли стабильны)
ensure_env() {
  local dir="$1" svc="$2" serverurl="${3:-}"
  local envfile="$dir/.env"
  if [ -s "$envfile" ]; then
    log "$svc: .env уже есть — не трогаю ($(wc -c <"$envfile") байт)"
    return 0
  fi
  local content=""
  case "$svc" in
    dvwa)
      content="DVWA_DB_PASSWORD=$(openssl rand -hex 16)
DVWA_DB_ROOT_PASSWORD=$(openssl rand -hex 16)"
      ;;
    n8n)
      content="# плейсхолдеры; при https заполнить реальным доменом
N8N_HOST_PLACEHOLDER=localhost
N8N_WEBHOOK_URL_PLACEHOLDER=http://localhost:5678/"
      ;;
    wireguard)
      if [ -z "$serverurl" ]; then
        serverurl="$(curl -4 -fsS --max-time 8 https://api.ipify.org || true)"
        [ -n "$serverurl" ] || die "не смог определить внешний IP — передайте --serverurl <IP>"
        log "wireguard: SERVERURL автоопределён как $serverurl (проверьте, это внешний IP облака)"
      fi
      content="WG_SERVERURL=$serverurl"
      ;;
    *) return 0 ;;
  esac
  printf '%s\n' "$content" > "$envfile"
  chmod 600 "$envfile"
  log "$svc: .env сгенерирован (openssl rand), права 600"
}

deploy_one() {
  local svc="$1" serverurl="${2:-}"
  is_service "$svc" || die "неизвестный стенд: $svc (есть: $SERVICES)"
  [ -f "$COMPOSE_SRC/$svc.yml" ] || die "нет $COMPOSE_SRC/$svc.yml — загрузите каталог compose/ рядом со скриптом"
  local dir="$ROOT/$svc"
  install -d -m 0750 "$dir"
  install -m 0644 "$COMPOSE_SRC/$svc.yml" "$dir/docker-compose.yml"
  ensure_env "$dir" "$svc" "$serverurl"
  log "$svc: docker compose up -d..."
  docker compose --env-file "$dir/.env" -f "$dir/docker-compose.yml" up -d --pull missing
}

stop_one() {
  local svc="$1"
  local dir="$ROOT/$svc"
  [ -f "$dir/docker-compose.yml" ] || die "стенд $svc не развёрнут ($dir)"
  docker compose --env-file "$dir/.env" -f "$dir/docker-compose.yml" stop
  log "$svc: остановлен (данные в volumes сохранены)"
}

status_all() {
  local svc
  for svc in $SERVICES; do
    local dir="$ROOT/$svc"
    echo "=== $svc ==="
    if [ -f "$dir/docker-compose.yml" ]; then
      docker compose --env-file "$dir/.env" -f "$dir/docker-compose.yml" ps 2>/dev/null || true
    else
      echo "не развёрнут"
    fi
  done
}

# --- разбор аргументов ---------------------------------------------------------
[ $# -eq 0 ] && usage
CMD="$1"; shift || true
case "$CMD" in
  -h|--help) usage ;;
  status) [ "$(id -u)" -eq 0 ] || die "запускайте от root"; status_all; exit 0 ;;
  stop)
    [ $# -ge 1 ] || die "укажите стенд: $SERVICES"
    [ "$(id -u)" -eq 0 ] || die "запускайте от root"
    stop_one "$1"; exit 0
    ;;
esac

[ "$(id -u)" -eq 0 ] || die "запускайте от root: sudo bash deploy-polygons.sh ..."
command -v docker >/dev/null 2>&1 || die "docker не найден — сначала bootstrap.sh"
command -v openssl >/dev/null 2>&1 || die "openssl не найден"

SERVERURL="${WG_SERVERURL:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --serverurl) SERVERURL="${2:-}"; shift 2 ;;
    *) die "неизвестный флаг: $1" ;;
  esac
done

case "$CMD" in
  all) for svc in $SERVICES; do deploy_one "$svc" "$SERVERURL"; done ;;
  *)   deploy_one "$CMD" "$SERVERURL" ;;
esac

log "ГОТОВО: деплой завершён. Проверка: sudo bash deploy-polygons.sh status"
log "Порты снаружи: Juice Shop :3000, DVWA :8081, n8n :5678, Uptime-Kuma :3001, WireGuard :51820/udp"
log "Пароли DVWA: cat $ROOT/dvwa/.env (там же генерация в первый раз)."
