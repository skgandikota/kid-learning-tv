#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
require_root
destination="${1:-$PWD}"
[[ -d "$STATE_DIR" && -d "$INSTALL_DIR/content" ]] || die "Install the appliance before creating a data/content backup."
install -d -m 0700 "$destination"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$destination/kid-learning-tv-backup-$stamp.tar.gz"
[[ ! -e "$archive" ]] || die "Refusing to overwrite $archive."
confirm "Create a protected backup of $STATE_DIR at $archive? The service will briefly stop."
was_active=0
systemctl is-active --quiet "$SERVICE_NAME.service" && was_active=1 || true
trap 'if ((was_active != 0)); then systemctl start "$SERVICE_NAME.service" || true; fi' EXIT
if ((was_active != 0)); then systemctl stop "$SERVICE_NAME.service" || die "Could not stop the service for a consistent backup."; fi
tar -czf "$archive" -C "$(dirname "$STATE_DIR")" "$(basename "$STATE_DIR")" -C "$INSTALL_DIR" content
chmod 0600 "$archive"
if ((was_active != 0)); then systemctl start "$SERVICE_NAME.service"; fi
was_active=0
trap - EXIT
info "Backup created: $archive"
