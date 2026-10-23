#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
cd "$SOURCE_DIR"
python3 -m venv .venv
if [[ -x .venv/bin/pip ]]; then
    .venv/bin/pip install -e . waitress
    exec .venv/bin/python -m app.main
fi
die "This script targets Linux/Unix virtualenvs; use your platform's Python environment on other systems."
