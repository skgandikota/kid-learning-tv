#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
require_root
confirm "Uninstall the service and application files? Saved data in $STATE_DIR will be kept."
systemctl disable --now "$SERVICE_NAME.service" 2>/dev/null || true
rm -f "/etc/systemd/system/$SERVICE_NAME.service"
systemctl daemon-reload
info "Service and unit removed. Application files and data were retained."
info "Disable kiosk autostart separately from each desktop account with scripts/disable-kiosk.sh before removing application files."
info "After checking your backups, remove them manually if desired: $INSTALL_DIR and $STATE_DIR"
