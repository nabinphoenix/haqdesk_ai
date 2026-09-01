#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/var/app/current"

cd "$APP_ROOT/frontend"
npm run start -- --hostname 127.0.0.1 --port 3000 &
FRONTEND_PID=$!

cd "$APP_ROOT/backend"
"$APP_ROOT/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

cleanup() {
  kill "$FRONTEND_PID" "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT TERM INT

wait -n "$FRONTEND_PID" "$BACKEND_PID"
exit $?
