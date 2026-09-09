#!/usr/bin/env bash
# Nap video demo, dat ten mien va mat khau, bat HTTPS roi khoi dong.
#
#   bash configure.sh <duong-dan-video> <mat-khau> [ten-mien]
#
set -euo pipefail

CLIP="${1:?Can duong dan video, vi du: bash configure.sh /root/demo.mp4 matkhau}"
PASSWORD="${2:?Can mat khau dang nhap}"
APP_DIR=/opt/video-ab
SERVICE_USER=videoab
USERNAME=demo

IP=$(curl -fsS --max-time 10 https://checkip.amazonaws.com | tr -d '[:space:]')
HOST="${3:-${IP//./-}.sslip.io}"

echo "==> 1/3 Nap video va lap chi muc PTS"
install -o "$SERVICE_USER" -g "$SERVICE_USER" -m 644 "$CLIP" "$APP_DIR/demo.mp4"
sudo -u "$SERVICE_USER" env \
    AB_DATA_DIR="$APP_DIR/data" AB_OUTPUT_DIR="$APP_DIR/outputs" \
    "$APP_DIR/.venv/bin/python" "$APP_DIR/deploy/huggingface/seed_demo.py" "$APP_DIR/demo.mp4"

echo "==> 2/3 Ghi cau hinh"
cat > /etc/video-ab.env <<ENV
AB_ALLOWED_HOST=$HOST
AB_USERNAME=$USERNAME
AB_PASSWORD=$PASSWORD
ENV
chmod 600 /etc/video-ab.env

# Caddy tu xin chung chi Let's Encrypt cho ten mien nay va tu gia han.
cat > /etc/caddy/Caddyfile <<CADDY
$HOST {
    reverse_proxy 127.0.0.1:8765
    request_body {
        max_size 2GB
    }
}
CADDY

echo "==> 3/3 Khoi dong dich vu"
systemctl restart video-ab caddy
sleep 5
systemctl is-active --quiet video-ab && echo "  video-ab: dang chay" || echo "  video-ab: LOI"
systemctl is-active --quiet caddy && echo "  caddy   : dang chay" || echo "  caddy   : LOI"

echo
echo "Dia chi  : https://$HOST"
echo "Tai khoan: $USERNAME"
