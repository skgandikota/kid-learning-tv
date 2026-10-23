#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
if [[ -x "$INSTALL_DIR/.venv/bin/python" ]]; then
    (cd "$INSTALL_DIR" && "$INSTALL_DIR/.venv/bin/python" tools/diagnostics.py)
else
    (cd "$SOURCE_DIR" && python3 tools/diagnostics.py)
fi
if command -v systemctl >/dev/null 2>&1; then
    systemctl --no-pager --full status "$SERVICE_NAME.service" || true
    journalctl -u "$SERVICE_NAME.service" -n 80 --no-pager || true
fi
if command -v curl >/dev/null 2>&1; then curl --fail --silent --show-error --max-time 3 http://127.0.0.1:8765/api/health || true; printf '\n'; fi
