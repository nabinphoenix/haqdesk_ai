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

# A dependency rebuild can exceed EB's 15-minute deployment command timeout.
# Keep the virtual environment outside the versioned source tree and reuse it
# across application-version swaps. The existing environment is migrated once
# from the active application; a fresh CPU-only environment is a fallback.
RUNTIME_VENV="/var/app/haqdesk-venv"
if [ ! -x "$RUNTIME_VENV/bin/python" ]; then
  if [ -x /var/app/current/.venv/bin/python ]; then
    mv /var/app/current/.venv "$RUNTIME_VENV"
  else
    if ! command -v python3.11 >/dev/null 2>&1; then
      dnf install -y python3.11 python3.11-pip
    fi

    python3.11 -m venv "$RUNTIME_VENV"
    "$RUNTIME_VENV/bin/python" -m pip install --upgrade pip

    # EB instances do not have GPUs. Install a direct CPU-only wheel so pip
    # does not resolve the generic PyPI Torch release and CUDA packages.
    CPU_TORCH_WHEEL="https://download-r2.pytorch.org/whl/cpu/torch-2.7.1%2Bcpu-cp311-cp311-manylinux_2_28_x86_64.whl"
    "$RUNTIME_VENV/bin/pip" install --no-cache-dir "$CPU_TORCH_WHEEL"

    EB_REQUIREMENTS="$APP_ROOT/.requirements-eb.txt"
    grep -v -E '^[[:space:]]*torch([[:space:]]|$)' "$APP_ROOT/backend/requirements.txt" > "$EB_REQUIREMENTS"
    "$RUNTIME_VENV/bin/pip" install --no-cache-dir -r "$EB_REQUIREMENTS"
    rm -f "$EB_REQUIREMENTS"
  fi
fi

ln -sfn "$RUNTIME_VENV" "$APP_ROOT/.venv"

# Keep frontend dependencies outside the versioned source tree as well. This
# avoids re-downloading the same packages while the EB deployment command is
# holding the application offline. A new instance performs one install, then
# later version swaps reuse it.
RUNTIME_NODE_MODULES="/var/app/haqdesk-node-modules"
if [ ! -d "$RUNTIME_NODE_MODULES" ]; then
  if [ -d /var/app/current/frontend/node_modules ]; then
    mv /var/app/current/frontend/node_modules "$RUNTIME_NODE_MODULES"
  else
    npm --prefix "$APP_ROOT/frontend" ci --no-audit --no-fund || npm --prefix "$APP_ROOT/frontend" install --no-audit --no-fund
    mv "$APP_ROOT/frontend/node_modules" "$RUNTIME_NODE_MODULES"
  fi
fi

ln -sfn "$RUNTIME_NODE_MODULES" "$APP_ROOT/frontend/node_modules"
