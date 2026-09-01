#!/usr/bin/env bash
set -euo pipefail

# predeploy runs after Elastic Beanstalk has staged the application source.
if [ -f /var/app/staging/backend/requirements.txt ]; then
  APP_ROOT="/var/app/staging"
elif [ -f /var/app/current/backend/requirements.txt ]; then
  APP_ROOT="/var/app/current"
else
  echo "HaqDesk source tree is not available for dependency installation" >&2
  exit 1
fi

export TMPDIR="$APP_ROOT/.pip-tmp"
mkdir -p "$TMPDIR"

if ! command -v python3.11 >/dev/null 2>&1; then
  dnf install -y python3.11 python3.11-pip
fi

python3.11 -m venv "$APP_ROOT/.venv"
"$APP_ROOT/.venv/bin/python" -m pip install --upgrade pip

# EB instances do not have GPUs. Install a direct CPU-only wheel so pip does
# not resolve the generic PyPI Torch release and its CUDA packages.
CPU_TORCH_WHEEL="https://download-r2.pytorch.org/whl/cpu/torch-2.7.1%2Bcpu-cp311-cp311-manylinux_2_28_x86_64.whl"
"$APP_ROOT/.venv/bin/pip" install --no-cache-dir "$CPU_TORCH_WHEEL"

# Install the remaining backend dependencies without allowing the generic
# torch requirement to replace the CPU-only wheel above.
EB_REQUIREMENTS="$APP_ROOT/.requirements-eb.txt"
grep -v -E '^[[:space:]]*torch([[:space:]]|$)' "$APP_ROOT/backend/requirements.txt" > "$EB_REQUIREMENTS"
"$APP_ROOT/.venv/bin/pip" install --no-cache-dir -r "$EB_REQUIREMENTS"
rm -f "$EB_REQUIREMENTS"

npm --prefix "$APP_ROOT/frontend" ci --no-audit --no-fund || npm --prefix "$APP_ROOT/frontend" install --no-audit --no-fund
