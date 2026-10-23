#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
[[ "${EUID:-$(id -u)}" -ne 0 ]] || die "Run as the desktop user, without sudo."
autostart="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
user_units="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
install -d -m 0755 "$autostart"
install -d -m 0755 "$user_units"
[[ -f "$INSTALL_DIR/systemd/kid-learning-kiosk.service" ]] || die "Kiosk service unit not found; install the appliance first."
install -m 0644 "$INSTALL_DIR/systemd/kid-learning-kiosk.service" "$user_units/kid-learning-kiosk.service"
cat > "$autostart/kid-learning-tv.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Kid Learning TV Kiosk
Comment=Open the local learning appliance
Exec=$INSTALL_DIR/scripts/start-kiosk.sh
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
chmod 0644 "$autostart/kid-learning-tv.desktop"
systemctl --user daemon-reload
info "Kiosk will start at the next desktop login via its systemd user service. Keep a separate administrator account/session for recovery."
