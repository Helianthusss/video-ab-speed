#!/usr/bin/env bash
# Dat ten mien, tai khoan va mat khau, roi bat HTTPS.
#   sudo bash configure.sh
set -euo pipefail

IP=$(curl -fsS --max-time 10 https://checkip.amazonaws.com | tr -d '[:space:]')
DEFAULT_HOST="${IP//./-}.sslip.io"

read -rp "Ten mien [$DEFAULT_HOST]: " HOST
HOST="${HOST:-$DEFAULT_HOST}"
read -rp "Ten dang nhap [demo]: " USERNAME
USERNAME="${USERNAME:-demo}"
read -rsp "Mat khau: " PASSWORD; echo
[ -n "$PASSWORD" ] || { echo "Mat khau khong duoc de trong" >&2; exit 1; }

cat > /etc/video-ab.env <<ENV
AB_ALLOWED_HOST=$HOST
AB_USERNAME=$USERNAME
AB_PASSWORD=$PASSWORD
ENV
chmod 600 /etc/video-ab.env

# Caddy tu xin va gia han chung chi Let's Encrypt cho ten mien nay.
cat > /etc/caddy/Caddyfile <<CADDY
$HOST {
    reverse_proxy 127.0.0.1:8765
    request_body {
        max_size 2GB
    }
}
CADDY

systemctl restart video-ab caddy
echo
echo "Dia chi: https://$HOST"
echo "Tai khoan: $USERNAME"
