#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
require_root
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || die "Install or update the application first."
enable_voice=1
if [[ "${1:-}" == "--update" ]]; then
    enable_voice=0
else
    confirm "Install natural British English speech and local Whisper AI (about 220 MB models), and enable voice play?"
fi
command -v apt-get >/dev/null 2>&1 || die "This setup script requires Lubuntu/Ubuntu apt-get."
apt-get update
apt-get install -y libgomp1
(
    umask 022
    "$INSTALL_DIR/.venv/bin/python" -m pip install "$INSTALL_DIR[voice]"
    "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/tools/setup_voice.py"
)
chmod -R a+rX "$INSTALL_DIR/.venv" "$INSTALL_DIR/models"
was_active=0
if systemctl is-active --quiet "$SERVICE_NAME.service"; then
    was_active=1
    systemctl stop "$SERVICE_NAME.service"
fi
verify_flag=--verify
[[ "$enable_voice" == 0 ]] || verify_flag=--enable
if ! runuser -u kid-learning-tv -- env KLT_DATA_DIR="$STATE_DIR" \
    "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/tools/setup_voice.py" "$verify_flag"; then
    if [[ "$was_active" == 1 ]]; then systemctl start "$SERVICE_NAME.service"; fi
    die "Neural voice verification failed; check disk space, memory and the error above."
fi
if [[ "$enable_voice" == 1 || "$was_active" == 1 ]]; then systemctl start "$SERVICE_NAME.service"; fi
info "Open http://127.0.0.1:8765/ in Chromium on the laptop. Tap Start voice and allow microphone access once."
info "Speak near the laptop microphone. Audio stays on this laptop and is never saved."
