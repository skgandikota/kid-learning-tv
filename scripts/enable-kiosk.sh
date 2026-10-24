#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
[[ "${EUID:-$(id -u)}" -ne 0 ]] || die "Run as the desktop user, without sudo."
autostart="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
user_units="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
install -d -m 0755 "$autostart"
[[ -f "$INSTALL_DIR/scripts/kiosk-supervisor.sh" ]] || die "Kiosk launcher not found; install the appliance first."
if [[ -f "$user_units/kid-learning-kiosk.service" ]]; then
    systemctl --user stop kid-learning-kiosk.service
    rm -f -- "$user_units/kid-learning-kiosk.service"
    systemctl --user daemon-reload
fi
cat > "$autostart/kid-learning-tv.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Kid Learning TV Kiosk
Comment=Open the local learning appliance
Exec=/bin/bash $INSTALL_DIR/scripts/start-kiosk.sh
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
chmod 0644 "$autostart/kid-learning-tv.desktop"
info "Kiosk will launch directly in your desktop session at the next login. Press Alt+F4 to close it."
