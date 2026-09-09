#!/usr/bin/env bash
# Nap video demo va tao san mot phien Demo.
#   sudo bash seed.sh /duong/dan/demo.mp4
set -euo pipefail
CLIP="${1:?Can duong dan toi file video, vi du: sudo bash seed.sh /home/ubuntu/demo.mp4}"
APP_DIR=/opt/video-ab
SERVICE_USER=videoab

[ -f "$CLIP" ] || { echo "Khong thay file: $CLIP" >&2; exit 1; }
install -o "$SERVICE_USER" -g "$SERVICE_USER" -m 644 "$CLIP" "$APP_DIR/demo.mp4"

echo "Dang lap chi muc PTS, mat vai phut voi video dai..."
sudo -u "$SERVICE_USER" env \
    AB_DATA_DIR="$APP_DIR/data" AB_OUTPUT_DIR="$APP_DIR/outputs" \
    "$APP_DIR/.venv/bin/python" "$APP_DIR/deploy/oracle/seed_demo.py" "$APP_DIR/demo.mp4"
echo "Xong."
