#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/var/app/staging"

if ! command -v python3 >/dev/null 2>&1; then
  dnf install -y python3
fi

python3 -m venv "$APP_ROOT/.venv"
"$APP_ROOT/.venv/bin/python" -m pip install --upgrade pip
"$APP_ROOT/.venv/bin/pip" install --no-cache-dir -r "$APP_ROOT/backend/requirements.txt"

npm --prefix "$APP_ROOT/frontend" ci --omit=dev
