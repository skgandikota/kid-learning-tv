#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
[[ "${EUID:-$(id -u)}" -ne 0 ]] || die "Run as the Lubuntu desktop user, without sudo; the script requests sudo when needed."
command -v python3 >/dev/null 2>&1 || die "python3 is required."
command -v sudo >/dev/null 2>&1 || die "sudo is required."
confirm "Keep running with the lid closed on BOTH battery and charger? Keep vents clear; battery can still run out."
target="/etc/systemd/logind.conf.d/90-kid-learning-tv-lid.conf"
source_config="$SOURCE_DIR/config/logind-lid.conf"
[[ -f "$source_config" ]] || die "Missing $source_config"
sudo -v
if sudo test -e "$target" && ! sudo cmp -s "$source_config" "$target"; then
    die "$target already contains different settings. Review it before continuing."
fi
python3 "$SOURCE_DIR/tools/configure_lid.py" "${XDG_CONFIG_HOME:-$HOME/.config}/lxqt/lxqt-powermanagement.conf"
sudo install -d -m 0755 /etc/systemd/logind.conf.d
sudo install -m 0644 "$source_config" "$target"
info "Saved LXQt and system lid settings. Reboot when ready to apply both; this script does not restart your desktop."
info "Critical-battery protection and idle/screen-lock settings are unchanged. Do not leave a running laptop in a bag."
