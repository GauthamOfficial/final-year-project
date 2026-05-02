#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# install_frontend.sh — Prompt 7B
#
# Installs the Next.js 14 frontend on the same EC2 host (or a dedicated
# host) used by `install_backend.sh`. Uses Node 20 LTS via NodeSource,
# `npm ci` for reproducible installs, and a systemd unit running
# `next start` behind the existing Nginx reverse proxy.
#
# Usage:
#   sudo bash deploy/install_frontend.sh             # full install
#   sudo bash deploy/install_frontend.sh --redeploy  # pull + build + restart
#
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_URL="${FRONTEND_REPO_URL:-https://github.com/your-org/lankaguide-frontend.git}"
APP_DIR="/var/www/lankaguide-frontend"
APP_USER="ubuntu"
SERVICE_NAME="lankaguide-web"
NODE_VERSION="20"
PORT="3000"

REDEPLOY="false"
if [[ "${1:-}" == "--redeploy" ]]; then
    REDEPLOY="true"
fi

require_root() {
    if [[ "$(id -u)" -ne 0 ]]; then
        echo "This script must be run with sudo." >&2
        exit 1
    fi
}

install_node() {
    if command -v node >/dev/null 2>&1; then
        local current
        current="$(node -v | sed 's/^v//;s/\..*$//')"
        if [[ "$current" == "$NODE_VERSION" ]]; then
            echo "Node ${NODE_VERSION} already installed."
            return
        fi
    fi
    echo "==> Installing Node.js ${NODE_VERSION}"
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}.x" | bash -
    apt-get install -y nodejs
}

prepare_app_dir() {
    mkdir -p "$APP_DIR"
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    if [[ ! -d "$APP_DIR/.git" ]]; then
        sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
    else
        sudo -u "$APP_USER" git -C "$APP_DIR" fetch --all
        sudo -u "$APP_USER" git -C "$APP_DIR" reset --hard origin/main
    fi
}

write_env_if_missing() {
    if [[ -f "$APP_DIR/.env.local" ]]; then return; fi
    echo "==> Writing $APP_DIR/.env.local (placeholder)"
    cat > "$APP_DIR/.env.local" <<'EOF'
NEXT_PUBLIC_API_URL=https://lankaguide.lk
NEXT_PUBLIC_APP_NAME=LankaGuide AI
NODE_ENV=production
EOF
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env.local"
    chmod 600 "$APP_DIR/.env.local"
}

build_app() {
    echo "==> Installing & building Next.js"
    sudo -u "$APP_USER" bash <<EOF
set -euo pipefail
cd "$APP_DIR"
npm ci --no-audit --no-fund
npm run build
EOF
}

write_systemd_unit() {
    echo "==> Writing systemd unit /etc/systemd/system/${SERVICE_NAME}.service"
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=LankaGuide AI — Next.js frontend
After=network.target

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment=NODE_ENV=production
Environment=PORT=$PORT
EnvironmentFile=$APP_DIR/.env.local
ExecStart=/usr/bin/npm run start --silent
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
}

start_service() {
    systemctl enable --now "$SERVICE_NAME"
    systemctl status --no-pager "$SERVICE_NAME" || true
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx || true
    fi
}

main() {
    require_root
    if [[ "$REDEPLOY" == "false" ]]; then
        install_node
    fi
    prepare_app_dir
    write_env_if_missing
    build_app
    write_systemd_unit
    if [[ "$REDEPLOY" == "true" ]]; then
        systemctl restart "$SERVICE_NAME"
    else
        start_service
    fi
    echo "==> Frontend install complete — proxied at https://lankaguide.lk/"
}

main "$@"
