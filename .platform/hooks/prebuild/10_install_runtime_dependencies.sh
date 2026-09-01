#!/usr/bin/env bash
set -euo pipefail

# Application files are not staged until the predeploy phase on the Node.js
# Elastic Beanstalk platform. Dependency installation belongs in the hook
# that runs after StageApplication, not here.
exit 0
