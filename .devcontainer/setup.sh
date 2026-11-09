#!/usr/bin/env bash
set -euo pipefail

python -m pip install -e '.[studio]'
bash .devcontainer/install-scummc.sh
