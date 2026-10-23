#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
require_root
SOURCE="${1:-$SOURCE_DIR}"
[[ -f "$SOURCE/pyproject.toml" && -d "$SOURCE/app" ]] || die "Usage: sudo $0 [project-source-directory]"
[[ -d "$INSTALL_DIR" ]] || die "Install not found at $INSTALL_DIR."
[[ "$(cd "$SOURCE" && pwd -P)" != "$INSTALL_DIR" ]] || die "Provide a separate updated project checkout as the source."
confirm "Update Food time, Video, quizzes, Card match and Hero Typing? Installs media tools, eSpeak and optional local Piper voice/model on THIS laptop. Your PIN/files stay unchanged; no videos download."
command -v apt-get >/dev/null 2>&1 || die "Lubuntu/Ubuntu apt-get is required to install FFmpeg."
apt-get update
apt-get install -y ffmpeg espeak-ng
install -d -o kid-learning-tv -g kid-learning-tv -m 0750 "$STATE_DIR/videos"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="/var/backups/kid-learning-tv/releases/$stamp"
[[ ! -e "$backup" ]] || die "A release snapshot already exists for this timestamp; retry in a moment."
install -d -m 0700 "$backup"
for item in app config tools scripts systemd kiosk docs pyproject.toml requirements.lock README.md; do
    [[ ! -e "$INSTALL_DIR/$item" ]] || cp -a "$INSTALL_DIR/$item" "$backup/"
done
restart_service=1
trap 'if [[ "${restart_service:-0}" == 1 ]]; then printf "Update failed. Service remains stopped; fix the reported error and rerun update.sh, or use rollback.sh.\n" >&2; fi' EXIT
systemctl stop "$SERVICE_NAME.service"
# Replace the app tree so removed feature routes and static files cannot survive.
mv "$INSTALL_DIR/app" "$backup/previous-app"
if [[ -d "$INSTALL_DIR/build" ]]; then mv "$INSTALL_DIR/build" "$backup/previous-build"; fi
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
verify_video_tools
setup_quiz_voice
rm -f "$INSTALL_DIR/scripts/setup-voice.sh" "$INSTALL_DIR/tools/setup_voice.py" \
    "$INSTALL_DIR/scripts/validate-content.sh" "$INSTALL_DIR/tools/content_validator.py"
systemctl start "$SERVICE_NAME.service"
restart_service=0
trap - EXIT
info "Updated. Previous files retained at $backup. Use scripts/rollback.sh to restore."
