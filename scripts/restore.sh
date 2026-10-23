#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
require_root
archive="${1:-}"
[[ -f "$archive" ]] || die "Usage: sudo $0 /path/to/kid-learning-tv-backup-*.tar.gz"
[[ -d "$INSTALL_DIR/content" && -d "$STATE_DIR" ]] || die "Install the appliance before restoring data and content."
tar -tzf "$archive" >/dev/null || die "The backup archive is unreadable."
while IFS= read -r member; do
    [[ "$member" != /* && "/$member/" != *"/../"* ]] || die "Unsafe path found in archive; restore refused."
    case "${member%%/*}" in kid-learning-tv|content) ;; *) die "Unexpected archive path; restore refused." ;; esac
done < <(tar -tzf "$archive")
tar -tvzf "$archive" | awk 'substr($0, 1, 1) !~ /^[-d]$/ { exit 1 }' || die "Backup contains a link or special file; restore refused."
tar -tzf "$archive" | grep -Eq '^kid-learning-tv(/|$)' || die "Archive does not contain the expected data directory."
tar -tzf "$archive" | grep -Eq '^content/categories/' || die "Archive does not contain local learning content."
confirm "Restore $archive over current data and content? Separate pre-restore copies will be kept."
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
old="${STATE_DIR}.pre-restore-$stamp"
old_content="${INSTALL_DIR}/content.pre-restore-$stamp"
[[ ! -e "$old" && ! -e "$old_content" ]] || die "A pre-restore snapshot already exists for this timestamp; retry in a moment."
was_active=0
systemctl is-active --quiet "$SERVICE_NAME.service" && was_active=1 || true
staging=""
cleanup() {
    [[ -z "$staging" ]] || rm -rf -- "$staging"
    ((was_active == 0)) || systemctl start "$SERVICE_NAME.service" || true
}
trap cleanup EXIT
if ((was_active != 0)); then systemctl stop "$SERVICE_NAME.service" || die "Could not stop the service before restore."; fi
if [[ -d "$STATE_DIR" ]]; then cp -a "$STATE_DIR" "$old"; fi
staging="$(mktemp -d "${STATE_DIR}.restore.XXXXXX")"
tar -xzf "$archive" --no-same-owner --no-same-permissions -C "$staging"
[[ -f "$staging/kid-learning-tv/kid-learning-tv.sqlite3" ]] || die "Backup is missing the application database."
[[ -d "$staging/content/categories" ]] || die "Backup is missing local learning content."
rm -rf -- "$STATE_DIR"
mv -- "$staging/kid-learning-tv" "$STATE_DIR"
mv -- "$INSTALL_DIR/content" "$old_content"
mv -- "$staging/content" "$INSTALL_DIR/content"
chown -R kid-learning-tv:kid-learning-tv "$STATE_DIR"
chown -R kid-learning-tv:kid-learning-tv "$INSTALL_DIR/content"
cleanup
trap - EXIT
info "Data and content restored. Previous data retained at $old and $old_content"
