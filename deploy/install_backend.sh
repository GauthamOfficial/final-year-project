#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# install_backend.sh — Prompt 7A
#
# Bare-metal AWS EC2 (Ubuntu 22.04 LTS) bring-up for the LankaGuide AI
# Django backend. Idempotent — re-running picks up the latest commit.
#
# Pre-requisites on the EC2 instance:
#   • SSH access as `ubuntu`
#   • Security group: inbound 22, 80, 443 open
#   • IAM role attached if you plan to read secrets from SSM
#
# Usage:
#   sudo bash deploy/install_backend.sh           # full install
#   sudo bash deploy/install_backend.sh --redeploy  # pull + migrate + restart
#
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/your-org/lankaguide-backend.git}"
APP_DIR="/var/www/lankaguide"
APP_USER="ubuntu"
SERVICE_NAME="lankaguide"
WORKER_SERVICE="lankaguide-sentiment"
AGGREGATOR_SERVICE="lankaguide-trend-aggregator"
PYTHON_BIN="python3.11"

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

install_system_packages() {
    echo "==> Installing system packages..."
    apt-get update -y
    apt-get install -y \
        software-properties-common \
        curl ca-certificates gnupg lsb-release \
        build-essential gcc g++ git \
        nginx redis-server \
        pkg-config libmysqlclient-dev \
        certbot python3-certbot-nginx
    add-apt-repository -y ppa:deadsnakes/ppa || true
    apt-get update -y
    apt-get install -y "$PYTHON_BIN" "${PYTHON_BIN}-venv" "${PYTHON_BIN}-dev" python3-pip
    systemctl enable --now redis-server
}

prepare_app_dir() {
    echo "==> Preparing $APP_DIR"
    mkdir -p "$APP_DIR" /var/data/chroma
    chown -R "$APP_USER:$APP_USER" "$APP_DIR" /var/data/chroma
    if [[ ! -d "$APP_DIR/.git" ]]; then
        sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
    else
        sudo -u "$APP_USER" git -C "$APP_DIR" fetch --all
        sudo -u "$APP_USER" git -C "$APP_DIR" reset --hard origin/main
    fi
}

install_python_deps() {
    echo "==> Installing Python deps"
    sudo -u "$APP_USER" bash <<EOF
set -euo pipefail
cd "$APP_DIR"
if [[ ! -d venv ]]; then
    $PYTHON_BIN -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
EOF
}

write_env_file_if_missing() {
    if [[ -f "$APP_DIR/.env" ]]; then
        return
    fi
    echo "==> Writing $APP_DIR/.env (placeholder; replace with SSM-loaded secrets)"
    cat > "$APP_DIR/.env" <<'EOF'
DEBUG=False
DJANGO_SECRET_KEY=replace-me
DJANGO_ALLOWED_HOSTS=lankaguide.lk,www.lankaguide.lk

USE_SQLITE_FALLBACK=False
DB_NAME=lankaguide
DB_USER=lankaguide_user
DB_PASSWORD=replace-me
DB_HOST=replace-me.rds.amazonaws.com
DB_PORT=3306

REDIS_URL=redis://127.0.0.1:6379/1

GEMINI_API_KEY=replace-me
CHROMA_PERSIST_DIR=/var/data/chroma

KAFKA_BOOTSTRAP_SERVERS=replace-me:9092

CORS_ALLOWED_ORIGINS=https://lankaguide.lk,https://www.lankaguide.lk
EOF
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
}

run_migrations() {
    echo "==> Running migrations + collectstatic"
    sudo -u "$APP_USER" bash <<EOF
set -euo pipefail
cd "$APP_DIR"
source venv/bin/activate
python manage.py migrate --noinput
python manage.py collectstatic --noinput
EOF
}

write_systemd_unit() {
    echo "==> Writing systemd unit /etc/systemd/system/${SERVICE_NAME}.service"
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=LankaGuide AI Django App
After=network.target redis-server.service

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 4 \\
    --worker-class gthread \\
    --threads 2 \\
    --timeout 120 \\
    --bind unix:/run/gunicorn.sock \\
    lankaguide.wsgi:application
Restart=always
RuntimeDirectory=lankaguide
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF

    cat > "/etc/systemd/system/${WORKER_SERVICE}.service" <<EOF
[Unit]
Description=LankaGuide AI — Sentiment worker
After=network.target

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python manage.py start_sentiment_worker
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    cat > "/etc/systemd/system/${AGGREGATOR_SERVICE}.service" <<EOF
[Unit]
Description=LankaGuide AI — Trend aggregator
After=network.target ${WORKER_SERVICE}.service

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python manage.py start_trend_aggregator
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
}

write_nginx_config() {
    echo "==> Writing /etc/nginx/sites-available/lankaguide"
    install -m 0644 "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/lankaguide
    ln -sf /etc/nginx/sites-available/lankaguide /etc/nginx/sites-enabled/lankaguide
    rm -f /etc/nginx/sites-enabled/default
    nginx -t
    systemctl reload nginx
}

install_cron() {
    echo "==> Installing 6-hourly review-scraper cron"
    cat > /etc/cron.d/lankaguide-scraper <<EOF
0 */6 * * * $APP_USER cd $APP_DIR && $APP_DIR/venv/bin/python manage.py start_sentiment_worker --once >> /var/log/lankaguide-scraper.log 2>&1
EOF
    chmod 644 /etc/cron.d/lankaguide-scraper
}

start_services() {
    systemctl enable --now $SERVICE_NAME
    systemctl enable --now $WORKER_SERVICE
    systemctl enable --now $AGGREGATOR_SERVICE
    systemctl status --no-pager $SERVICE_NAME || true
}

setup_tls_hint() {
    cat <<EOF

==> Next steps for HTTPS:
    sudo certbot --nginx -d lankaguide.lk -d www.lankaguide.lk \\
         -m ops@lankaguide.lk --agree-tos --non-interactive

EOF
}

main() {
    require_root
    if [[ "$REDEPLOY" == "false" ]]; then
        install_system_packages
    fi
    prepare_app_dir
    install_python_deps
    write_env_file_if_missing
    run_migrations
    write_systemd_unit
    write_nginx_config
    install_cron
    if [[ "$REDEPLOY" == "true" ]]; then
        systemctl restart $SERVICE_NAME $WORKER_SERVICE $AGGREGATOR_SERVICE
    else
        start_services
        setup_tls_hint
    fi
    echo "==> Backend install complete."
}

main "$@"
