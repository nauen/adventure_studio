#!/usr/bin/env bash
set -euo pipefail

# Do not launch a duplicate process when the Codespace is resumed.
if python -c 'import socket; s=socket.socket(); s.settimeout(1); e=s.connect_ex(("127.0.0.1", 7860)); s.close(); raise SystemExit(0 if e == 0 else 1)'; then
  echo "Adventure Studio already listens on port 7860"
  exit 0
fi

STUDIO_LOG_DIR="${TMPDIR:-/tmp}/adventure-studio"
mkdir -p "$STUDIO_LOG_DIR"
ADVENTURE_STUDIO_SCUMMC="${HOME}/.cache/adventure-studio/scummc" \
  nohup python -m adventure_studio.studio_gradio > "$STUDIO_LOG_DIR/gradio.log" 2>&1 < /dev/null &
echo "Adventure Studio starting on port 7860 (log: $STUDIO_LOG_DIR/gradio.log)"
