#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
[[ "${EUID:-$(id -u)}" -ne 0 ]] || die "Run as the desktop user, without sudo."
entry="${XDG_CONFIG_HOME:-$HOME/.config}/autostart/kid-learning-tv.desktop"
unit="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/kid-learning-kiosk.service"
if [[ -e "$entry" ]]; then
    confirm "Stop the kiosk browser and disable automatic kiosk startup for this desktop account?"
    systemctl --user stop kid-learning-kiosk.service 2>/dev/null || true
    rm -f -- "$entry" "$unit"
    systemctl --user daemon-reload 2>/dev/null || true
    info "Kiosk autostart disabled. Press Alt+F4 in the browser to close a directly launched kiosk."
else
    systemctl --user stop kid-learning-kiosk.service 2>/dev/null || true
    rm -f -- "$unit"
    systemctl --user daemon-reload 2>/dev/null || true
    info "Kiosk autostart is already disabled; its service unit was removed if present."
fi
