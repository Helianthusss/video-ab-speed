#!/usr/bin/env bash
# Cai dat cong cu khao sat toc do A-B tren mot may ao Ubuntu.
# Chay mot lan, co the chay lai nhieu lan ma khong hong.
#
#   sudo bash setup.sh
#
set -euo pipefail

APP_DIR=/opt/video-ab
SERVICE_USER=videoab

echo "==> 1/6 Cai goi he thong"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
# fonts-dejavu-core: reportlab can font Unicode de xuat PDF tieng Viet
apt-get install -y -qq python3-venv python3-dev git curl fonts-dejavu-core \
    debian-keyring debian-archive-keyring apt-transport-https

echo "==> 2/6 Cai Caddy de tu xin chung chi HTTPS"
if ! command -v caddy >/dev/null 2>&1; then
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
        | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
        | tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
    apt-get update -qq
    apt-get install -y -qq caddy
fi

echo "==> 3/6 Tao tai khoan dich vu"
id -u "$SERVICE_USER" >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
# Ma nguon duoc chep len truoc bang scp, khong tai tu GitHub, de repo co the
# de o che do rieng tu.
if [ ! -f "$APP_DIR/requirements.txt" ]; then
    echo "Chua thay ma nguon tai $APP_DIR." >&2
    echo "Chep len truoc, vi du: scp -r ./ ubuntu@<IP>:/tmp/video-ab" >&2
    exit 1
fi

echo "==> 4/6 Cai thu vien Python"
[ -x "$APP_DIR/.venv/bin/python" ] || python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
mkdir -p "$APP_DIR/data" "$APP_DIR/outputs"
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

echo "==> 5/6 Mo cong 80 va 443 trong tuong lua cua may"
# Anh Ubuntu cua Oracle chan san moi cong tru SSH.
iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || iptables -I INPUT 6 -p tcp --dport 80 -j ACCEPT
iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT
command -v netfilter-persistent >/dev/null 2>&1 && netfilter-persistent save >/dev/null 2>&1 || true

echo "==> 6/6 Tao dich vu tu khoi dong cung may"
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
ExecStart=$APP_DIR/.venv/bin/gunicorn --workers 1 --threads 8 --timeout 300 \
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
echo "Xong phan cai dat. Ba buoc con lai:"
echo "  1. Tai video demo len may, roi chay:  sudo bash /opt/video-ab/deploy/oracle/seed.sh /duong/dan/demo.mp4"
echo "  2. Dat tai khoan va ten mien:         sudo bash /opt/video-ab/deploy/oracle/configure.sh"
echo "  3. Khoi dong:                         sudo systemctl restart video-ab caddy"
