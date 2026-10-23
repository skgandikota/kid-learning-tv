#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
require_root
releases="/var/backups/kid-learning-tv/releases"
[[ -d "$releases" ]] || die "No saved release snapshots found."
mapfile -t snapshots < <(find "$releases" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -r)
((${#snapshots[@]})) || die "No saved release snapshots found."
snapshot="${1:-$releases/${snapshots[0]}}"
[[ -d "$snapshot" && "$snapshot" == "$releases/"* ]] || die "Choose a snapshot under $releases."
confirm "Restore application files from $snapshot? User data will not be changed."
restart_service=1
trap 'if [[ "${restart_service:-0}" == 1 ]]; then systemctl start "$SERVICE_NAME.service" || true; fi' EXIT
systemctl stop "$SERVICE_NAME.service"
for item in app config tools scripts systemd kiosk docs pyproject.toml requirements.lock README.md; do
    if [[ -e "$snapshot/$item" ]]; then
        rm -rf -- "$INSTALL_DIR/$item"
        cp -a "$snapshot/$item" "$INSTALL_DIR/"
    fi
done
chown -R kid-learning-tv:kid-learning-tv "$INSTALL_DIR/content"
"$INSTALL_DIR/.venv/bin/pip" install "$INSTALL_DIR" waitress
systemctl start "$SERVICE_NAME.service"
restart_service=0
trap - EXIT
info "Restored saved application files. Database and media were preserved."
