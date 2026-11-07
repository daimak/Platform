#!/usr/bin/env bash
# bootstrap.sh — универсальная инициализация свежей ВМ (Ubuntu 24.04 LTS) для Platform Evo.
# Площадка задаётся аргументом: do | yc (влияет только на метки/подсказки, шаги идентичны).
#
# Что делает (идемпотентно — повторный запуск ничего не ломает):
#   1) apt update + upgrade
#   2) timezone Asia/Tashkent
#   3) ufw: 22, 80, 443 + порты стенда (3000, 8081, 5678, 3001, 51820/udp, 6443)
#   4) fail2ban (sshd, backend=systemd — Ubuntu 24.04 без rsyslog/auth.log)
#   5) SSH hardening (key-only, PermitRootLogin prohibit-password) через /etc/ssh/sshd_config.d/00-evo-hardening.conf
#   6) пользователь deploy (sudo NOPASSWD) + его authorized_keys
#   7) unattended-upgrades (ежедневные автообновления безопасности)
#   8) docker + docker compose plugin
#
# Секретов НЕТ: публичный ключ берётся из переменной окружения DEPLOY_SSH_KEY
# ЛИБО копируется из authorized_keys вызывающего пользователя (root). Ключи и токены
# Дмитрий кладёт руками в Workspace/.env (не в git).
#
# Usage:
#   sudo bash bootstrap.sh do        # на DigitalOcean дроплете
#   sudo bash bootstrap.sh yc        # на Yandex Cloud ВМ
#   sudo DEPLOY_SSH_KEY='ssh-ed25519 AAAA...' bash bootstrap.sh do
# Без аргументов — печатает этот help и ничего не выполняет.

set -Eeuo pipefail

PLATFORM="${1:-}"
DEPLOY_USER="deploy"
DEPLOY_SSH_KEY="${DEPLOY_SSH_KEY:-}"
STAND_PORTS=("22/tcp" "80/tcp" "443/tcp" "3000/tcp" "8081/tcp" "5678/tcp" "3001/tcp" "51820/udp" "6443/tcp")

log() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
die() { printf '[ОШИБКА] %s\n' "$*" >&2; exit 1; }

usage() {
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# --- dry-run безопасность: без аргументов только help -----------------------
[ -z "$PLATFORM" ] && usage
[ "$PLATFORM" = "-h" ] || [ "$PLATFORM" = "--help" ] && usage
[ "$PLATFORM" = "do" ] || [ "$PLATFORM" = "yc" ] || { usage; die "аргумент должен быть do или yc, получено: $PLATFORM"; }
[ "$(id -u)" -eq 0 ] || die "запускайте от root: sudo bash bootstrap.sh $PLATFORM"
. /etc/os-release 2>/dev/null || true
[ "${VERSION_ID:-}" = "24.04" ] || log "ПРЕДУПРЕЖДЕНИЕ: сценарий рассчитан на Ubuntu 24.04, у вас ${PRETTY_NAME:-неизвестно} — продолжаю."

# --- 1. apt update + upgrade ------------------------------------------------
log "1/8 apt update/upgrade..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

# --- 2. timezone ------------------------------------------------------------
log "2/8 timezone Asia/Tashkent..."
timedatectl set-timezone Asia/Tashkent

# --- 3. базовые пакеты -------------------------------------------------------
log "3/8 пакеты: ufw fail2ban unattended-upgrades curl jq htop git..."
apt-get install -y ufw fail2ban unattended-upgrades ca-certificates curl gnupg jq htop git openssh-server

# --- 4. ufw -----------------------------------------------------------------
log "4/8 ufw: default deny incoming, разрешённые порты: ${STAND_PORTS[*]}..."
ufw default deny incoming
ufw default allow outgoing
for port in "${STAND_PORTS[@]}"; do
  ufw allow "$port" >/dev/null
done
ufw --force enable
ufw status verbose

# --- 5. fail2ban (backend=systemd для Ubuntu 24.04) --------------------------
log "5/8 fail2ban: jail sshd..."
cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
backend = systemd
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
backend = systemd
EOF
systemctl enable --now fail2ban >/dev/null 2>&1 || systemctl restart fail2ban
systemctl restart fail2ban

# --- 6. SSH hardening + пользователь deploy ----------------------------------
log "6/8 SSH hardening + пользователь $DEPLOY_USER..."
if ! id -u "$DEPLOY_USER" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "EVO deploy" "$DEPLOY_USER"
fi
# deploy без пароля → sudo без пароля (иначе sudo недоступен в принципе)
install -m 0440 -o root -g root /dev/null /etc/sudoers.d/90-evo-deploy
printf '%s ALL=(ALL) NOPASSWD:ALL\n' "$DEPLOY_USER" > /etc/sudoers.d/90-evo-deploy
visudo -cf /etc/sudoers.d/90-evo-deploy || die "sudoers для deploy невалиден"

HOMEDIR="$(getent passwd "$DEPLOY_USER" | cut -d: -f6)"
install -d -m 0700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "$HOMEDIR/.ssh"
KEYFILE="$HOMEDIR/.ssh/authorized_keys"
if [ -n "$DEPLOY_SSH_KEY" ]; then
  printf '%s\n' "$DEPLOY_SSH_KEY" >> "$KEYFILE"
  log "ключ добавлен из переменной окружения DEPLOY_SSH_KEY"
elif [ -s /root/.ssh/authorized_keys ]; then
  cp -n /root/.ssh/authorized_keys "$KEYFILE" || true
  log "ключи скопированы из /root/.ssh/authorized_keys"
else
  log "ПРЕДУПРЕЖДЕНИЕ: ключей нет (ни DEPLOY_SSH_KEY, ни /root/.ssh/authorized_keys) — password-auth НЕ отключаю, чтобы не потерять доступ. Положите ключ и перезапустите."
  HARDEN_KEYS="skip"
fi
[ -f "$KEYFILE" ] && chown "$DEPLOY_USER:$DEPLOY_USER" "$KEYFILE" && chmod 0600 "$KEYFILE"

# 00- префикс важен: sshd читает sshd_config.d раньше основного файла,
# «первое значение выигрывает» — наш файл обязан сортироваться раньше 50-cloud-init.conf
cat > /etc/ssh/sshd_config.d/00-evo-hardening.conf <<'EOF'
PermitRootLogin prohibit-password
PubkeyAuthentication yes
KbdInteractiveAuthentication no
EOF
if [ "${HARDEN_KEYS:-}" != "skip" ]; then
  printf 'PasswordAuthentication no\n' >> /etc/ssh/sshd_config.d/00-evo-hardening.conf
fi
sshd -t || die "конфиг sshd невалиден — исправьте /etc/ssh/sshd_config.d/00-evo-hardening.conf"
systemctl restart ssh

# --- 7. unattended-upgrades --------------------------------------------------
log "7/8 unattended-upgrades..."
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
systemctl enable --now unattended-upgrades >/dev/null 2>&1 || true

# --- 8. docker + compose plugin ----------------------------------------------
log "8/8 docker + docker compose plugin..."
if command -v docker >/dev/null 2>&1; then
  log "docker уже установлен: $(docker --version)"
else
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker
if id -u "$DEPLOY_USER" >/dev/null 2>&1 && ! id -nG "$DEPLOY_USER" | grep -qw docker; then
  usermod -aG docker "$DEPLOY_USER"
fi
docker compose version || die "docker compose plugin не найден"

log "ГОТОВО: bootstrap ($PLATFORM) завершён."
log "Дальше: sudo bash probe-machine.sh   → отчёт о машине"
log "       sudo bash deploy-polygons.sh  → стенды (Juice Shop, DVWA, n8n, Uptime-Kuma, WireGuard)"
log "       sudo bash install-k3s.sh      → k3s master"
log "Проверка снаружи: ssh $DEPLOY_USER@<внешний_IP> (паролей нет — только ключ)."
