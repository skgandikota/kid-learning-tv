#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
require_root
[[ -x "$INSTALL_DIR/.venv/bin/python" ]] || die "Install the appliance first."
[[ -f "$INSTALL_DIR/tools/set_parent_pin.py" ]] || die "PIN setup utility not found in the installed tools directory."
command -v runuser >/dev/null 2>&1 || die "runuser is required to safely update the PIN as the service account."
command -v systemctl >/dev/null 2>&1 || die "systemctl is required to manage the appliance service."
[[ -t 0 && -t 1 ]] || die "PIN reset needs an interactive terminal."
confirm "Replace the parent PIN hash? You must set a new 6–12 digit PIN twice."
was_active=0
systemctl is-active --quiet "$SERVICE_NAME.service" && was_active=1 || true
restore_service() { ((was_active == 0)) || systemctl start "$SERVICE_NAME.service" || true; }
trap restore_service EXIT
if ((was_active != 0)); then systemctl stop "$SERVICE_NAME.service" || die "Could not stop the service before changing the PIN."; fi
runuser -u kid-learning-tv -- env KLT_DATA_DIR="$STATE_DIR" "$INSTALL_DIR/.venv/bin/python" \
    "$INSTALL_DIR/tools/set_parent_pin.py"
restore_service
trap - EXIT
