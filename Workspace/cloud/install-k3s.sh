#!/usr/bin/env bash
# install-k3s.sh — одномерный k3s-кластер для практики Platform Evo (Ubuntu 24.04).
#   Мастер:  sudo bash install-k3s.sh                          (первая машина)
#   Агент:   sudo bash install-k3s.sh --agent https://<MASTER_IP>:6443 --token <TOKEN>
#            (TOKEN печатает мастер после установки: /var/lib/rancher/k3s/server/node-token)
#
# Идемпотентно: если k3s уже работает в нужной роли — скрипт ничего не переустанавливает.
# Секретов НЕТ: токен агента передаётся переменной окружения K3S_TOKEN или флагом
# --token вручную (Дмитрий копирует с мастера). Канал k3s — stable.
#
# Без аргументов запускается как МАСТЕР (это не разрушительное действие);
# --help печатает этот текст.

set -Eeuo pipefail

MODE="master"
AGENT_URL=""
AGENT_TOKEN="${K3S_TOKEN:-}"
K3S_CHANNEL="stable"
EXTRA_ARGS="${K3S_EXTRA_ARGS:-}"

log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { printf '[ОШИБКА] %s\n' "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --agent)   MODE="agent"; AGENT_URL="${2:-}"; shift 2 ;;
    --token)   AGENT_TOKEN="${2:-}"; shift 2 ;;
    --channel) K3S_CHANNEL="${2:-stable}"; shift 2 ;;
    *) die "неизвестный аргумент: $1 (см. --help)" ;;
  esac
done

[ "$(id -u)" -eq 0 ] || die "запускайте от root: sudo bash install-k3s.sh"

# --- агент: нужны url и токен -------------------------------------------------
if [ "$MODE" = "agent" ]; then
  [ -n "$AGENT_URL" ] || die "укажите --agent https://<MASTER_IP>:6443"
  [ -n "$AGENT_TOKEN" ] || die "укажите --token <токен с мастера> или экспортируйте K3S_TOKEN"
  if systemctl is-active --quiet k3s-agent 2>/dev/null; then
    log "k3s-agent уже активен на $(hostname) — ничего не делаю."
    exit 0
  fi
  log "ставлю k3s-agent (channel=$K3S_CHANNEL, url=$AGENT_URL)..."
  curl -sfL https://get.k3s.io | \
    K3S_URL="$AGENT_URL" K3S_TOKEN="$AGENT_TOKEN" INSTALL_K3S_CHANNEL="$K3S_CHANNEL" sh -s -
  log "ГОТОВО: агент подключён. Проверка на мастере: kubectl get nodes"
  exit 0
fi

# --- мастер --------------------------------------------------------------------
if systemctl is-active --quiet k3s 2>/dev/null; then
  log "k3s уже активен на $(hostname) — ничего не переустанавливаю."
else
  log "ставлю k3s master (channel=$K3S_CHANNEL)..."
  # транзитный флаг --disable=traefik можно добавить через K3S_EXTRA_ARGS
  curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL="$K3S_CHANNEL" sh -s - \
    --write-kubeconfig-mode 644 $EXTRA_ARGS
  systemctl enable --now k3s
fi

# ufw: открыть API-сервер k3s (повторный allow безвреден)
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow 6443/tcp >/dev/null
fi

TOKENFILE="/var/lib/rancher/k3s/server/node-token"
for _ in $(seq 1 30); do
  [ -s "$TOKENFILE" ] && break
  sleep 2
done

log "статус: $(k3s kubectl get nodes 2>/dev/null || echo 'kubectl ещё поднимается — повторите k3s kubectl get nodes через минуту')"
if [ -s "$TOKENFILE" ]; then
  log "токен для агентов: $TOKENFILE"
  log "команда на второй машине:"
  log "  sudo K3S_TOKEN=\$(sudo cat $TOKENFILE) bash install-k3s.sh --agent https://$(hostname -I | awk '{print $1}'):6443"
else
  log "ПРЕДУПРЕЖДЕНИЕ: node-token ещё не появился — проверьте: journalctl -u k3s -e"
fi
log "ГОТОВО: k3s master на $(hostname). kubeconfig: /etc/rancher/k3s/k3s.yaml"
