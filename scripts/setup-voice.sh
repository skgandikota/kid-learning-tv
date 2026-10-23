#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
require_root
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || die "Install or update the application first."
confirm "Install offline English voice (about 40 MB model download) and enable the laptop microphone for play?"
command -v apt-get >/dev/null 2>&1 || die "This setup script requires Lubuntu/Ubuntu apt-get."
apt-get update
apt-get install -y espeak-ng
(
    umask 022
    "$INSTALL_DIR/.venv/bin/python" -m pip install "$INSTALL_DIR[voice]"
    "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/tools/setup_voice.py"
)
chmod -R a+rX "$INSTALL_DIR/.venv" "$INSTALL_DIR/models"
systemctl stop "$SERVICE_NAME.service"
if ! runuser -u kid-learning-tv -- env KLT_DATA_DIR="$STATE_DIR" \
    "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/tools/setup_voice.py" --enable; then
    systemctl start "$SERVICE_NAME.service"
    die "Voice setup failed. The service was restarted without enabling voice."
fi
systemctl start "$SERVICE_NAME.service"
info "Open http://127.0.0.1:8765/ in Chromium on the laptop. Tap Start voice and allow microphone access once."
info "Speak near the laptop microphone. Audio stays on this laptop and is never saved."
