#!/bin/bash
set -u
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
APP_PORT="${AB_PORT:-8766}"
APP_URL="http://127.0.0.1:${APP_PORT}"

if curl --silent --fail "${APP_URL}/api/sessions" >/dev/null 2>&1; then
  open "$APP_URL"
  exit 0
fi

if [ ! -x "$PROJECT_DIR/.venv/bin/python" ]; then
  echo "Phần mềm chưa được cài đặt đầy đủ. Vui lòng liên hệ người phụ trách."
  echo "Nhấn Enter để đóng cửa sổ này."
  read -r
  exit 1
fi

echo "Đang mở phần mềm khảo sát tốc độ A-B..."
AB_HOST=127.0.0.1 AB_PORT="$APP_PORT" "$PROJECT_DIR/.venv/bin/python" app.py &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null' EXIT INT TERM
for _ in {1..100}; do
  if curl --silent --fail "${APP_URL}/api/sessions" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

if ! curl --silent --fail "${APP_URL}/api/sessions" >/dev/null 2>&1; then
  echo "Không thể khởi động phần mềm. Vui lòng gửi ảnh cửa sổ này cho người phụ trách."
  echo "Nhấn Enter để đóng cửa sổ này."
  read -r
  exit 1
fi

open "$APP_URL"
echo "Phần mềm đang chạy tại $APP_URL"
echo "Giữ cửa sổ này mở trong khi sử dụng. Đóng cửa sổ để tắt phần mềm."
wait "$SERVER_PID"
