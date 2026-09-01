#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/var/app/staging"
export TMPDIR="$APP_ROOT/.pip-tmp"
mkdir -p "$TMPDIR"

if ! command -v python3.11 >/dev/null 2>&1; then
  dnf install -y python3.11 python3.11-pip
fi

python3.11 -m venv "$APP_ROOT/.venv"
"$APP_ROOT/.venv/bin/python" -m pip install --upgrade pip
"$APP_ROOT/.venv/bin/pip" install --no-cache-dir -r "$APP_ROOT/backend/requirements.txt"

npm --prefix "$APP_ROOT/frontend" ci --no-audit --no-fund || npm --prefix "$APP_ROOT/frontend" install --no-audit --no-fund
