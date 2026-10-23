#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
require_root
SOURCE="${1:-$SOURCE_DIR}"
[[ -f "$SOURCE/pyproject.toml" && -d "$SOURCE/app" ]] || die "Usage: sudo $0 [project-source-directory]"
[[ -d "$INSTALL_DIR" ]] || die "Install not found at $INSTALL_DIR."
[[ "$(cd "$SOURCE" && pwd -P)" != "$INSTALL_DIR" ]] || die "Provide a separate updated project checkout as the source."
confirm "Back up the installed application and update it from $SOURCE? The service will briefly stop."
PYTHONPATH="$INSTALL_DIR" "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/tools/content_validator.py" || die "Installed content is invalid; update refused without changing files."
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="/var/backups/kid-learning-tv/releases/$stamp"
[[ ! -e "$backup" ]] || die "A release snapshot already exists for this timestamp; retry in a moment."
install -d -m 0700 "$backup"
for item in app config tools scripts systemd kiosk docs pyproject.toml requirements.lock README.md; do
    [[ ! -e "$INSTALL_DIR/$item" ]] || cp -a "$INSTALL_DIR/$item" "$backup/"
done
restart_service=1
trap 'if [[ "${restart_service:-0}" == 1 ]]; then systemctl start "$SERVICE_NAME.service" || true; fi' EXIT
systemctl stop "$SERVICE_NAME.service"
for item in app config tools scripts systemd kiosk docs; do
    if [[ ! -d "$SOURCE/$item" && ( "$item" == docs || "$item" == kiosk ) ]]; then continue; fi
    [[ -d "$SOURCE/$item" ]] || die "Source is missing project directory $item"
    install -d -m 0755 "$INSTALL_DIR/$item"
    cp -a "$SOURCE/$item/." "$INSTALL_DIR/$item/"
done
for item in pyproject.toml requirements.lock README.md; do
    [[ -f "$SOURCE/$item" ]] || die "Source is missing project file $item"
    cp -a "$SOURCE/$item" "$INSTALL_DIR/"
done
chown -R kid-learning-tv:kid-learning-tv "$INSTALL_DIR/content"
(
    umask 022
    "$INSTALL_DIR/.venv/bin/pip" install "$INSTALL_DIR" waitress
)
chmod -R a+rX "$INSTALL_DIR/.venv"
systemctl start "$SERVICE_NAME.service"
restart_service=0
trap - EXIT
info "Updated. Previous files retained at $backup. Use scripts/rollback.sh to restore."
