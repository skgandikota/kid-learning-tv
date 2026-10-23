#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
if [[ -x "$INSTALL_DIR/.venv/bin/python" ]]; then
    cd "$INSTALL_DIR"
    export PYTHONPATH="$INSTALL_DIR${PYTHONPATH:+:$PYTHONPATH}"
    exec "$INSTALL_DIR/.venv/bin/python" tools/content_validator.py
fi
cd "$SOURCE_DIR"
export PYTHONPATH="$SOURCE_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec python3 tools/content_validator.py
