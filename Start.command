#!/bin/bash
set -e
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
if [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
  PY="$PROJECT_DIR/.venv/bin/python"
else
  PY="$(command -v python3)"
fi
"$PY" app.py &
SERVER_PID=$!
for _ in {1..50}; do
  if curl --silent --fail 'http://127.0.0.1:8765/api/sessions' >/dev/null; then
    break
  fi
  sleep 0.1
done
open 'http://127.0.0.1:8765'
wait "$SERVER_PID"
