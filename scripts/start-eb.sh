#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/var/app/current"

if [ -x "$APP_ROOT/.venv/bin/python" ]; then
  PYTHON_BIN="$APP_ROOT/.venv/bin/python"
elif [ -x "/var/app/haqdesk-venv/bin/python" ]; then
  PYTHON_BIN="/var/app/haqdesk-venv/bin/python"
else
  echo HaqDesk Python runtime is unavailable
  exit 1
fi

if [ -x "$APP_ROOT/frontend/node_modules/.bin/next" ]; then
  FRONTEND_BIN_DIR="$APP_ROOT/frontend/node_modules/.bin"
elif [ -x "/var/app/haqdesk-frontend/node_modules/.bin/next" ]; then
  FRONTEND_BIN_DIR="/var/app/haqdesk-frontend/node_modules/.bin"
else
  echo HaqDesk frontend runtime is unavailable
  exit 1
fi

cd "$APP_ROOT/frontend"
PATH="$FRONTEND_BIN_DIR:$PATH" npm run start -- --hostname 127.0.0.1 --port 3000 &
FRONTEND_PID=$!

cd "$APP_ROOT/backend"
"$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

cleanup() {
  kill "$FRONTEND_PID" "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT TERM INT

wait -n "$FRONTEND_PID" "$BACKEND_PID"
exit $?
