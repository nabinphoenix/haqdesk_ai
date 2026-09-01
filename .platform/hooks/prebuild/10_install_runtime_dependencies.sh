#!/usr/bin/env bash
set -euo pipefail

# Runtime dependencies are installed in predeploy, after EB has staged the
# source bundle. Keeping prebuild side-effect free also supports EB self-start.
exit 0
