#!/usr/bin/env bash
# Cai dat cong cu khao sat toc do A-B tren mot may chu Ubuntu moi.
# Ma nguon duoc chep san vao /opt/video-ab truoc khi chay script nay.
#
#   bash install.sh
#
set -euo pipefail

APP_DIR=/opt/video-ab
SERVICE_USER=videoab

echo "==> 1/5 Cai goi he thong"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
# fonts-dejavu-core: reportlab can font Unicode de xuat PDF tieng Viet
apt-get install -y -qq python3-venv python3-dev curl fonts-dejavu-core \
    debian-keyring debian-archive-keyring apt-transport-https

echo "==> 2/5 Cai Caddy de tu xin va gia han chung chi HTTPS"
if ! command -v caddy >/dev/null 2>&1; then
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
        | gpg --batch --yes --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
        > /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -qq
    apt-get install -y -qq caddy
fi

echo "==> 3/5 Tao tai khoan dich vu"
id -u "$SERVICE_USER" >/dev/null 2>&1 \
    || useradd --system --create-home --shell /usr/sbin/nologin "$SERVICE_USER"

echo "==> 4/5 Cai thu vien Python"
[ -x "$APP_DIR/.venv/bin/python" ] || python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
mkdir -p "$APP_DIR/data" "$APP_DIR/outputs"
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

echo "==> 5/5 Tao dich vu tu khoi dong cung may"
cat > /etc/systemd/system/video-ab.service <<UNIT
[Unit]
Description=Video A-B travel speed survey
After=network.target

[Service]
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment=AB_DATA_DIR=$APP_DIR/data
Environment=AB_OUTPUT_DIR=$APP_DIR/outputs
EnvironmentFile=/etc/video-ab.env
ExecStart=$APP_DIR/.venv/bin/gunicorn --workers 1 --threads 4 --timeout 300 \\
    --bind 127.0.0.1:8765 video_ab.web:app
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

touch /etc/video-ab.env
chmod 600 /etc/video-ab.env
systemctl daemon-reload
systemctl enable --quiet video-ab

echo
echo "Cai dat xong. Tiep theo: seed.sh roi configure.sh"
