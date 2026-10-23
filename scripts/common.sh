#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SOURCE_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
INSTALL_DIR="/opt/kid-learning-tv"
STATE_DIR="/var/lib/kid-learning-tv"
SERVICE_NAME="kid-learning-tv"

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
info() { printf '%s\n' "$*"; }
require_root() { [[ "${EUID:-$(id -u)}" -eq 0 ]] || die "Run this command with sudo/root."; }
confirm() {
    local answer
    read -r -p "${1} [y/N] " answer
    [[ "$answer" == "y" || "$answer" == "Y" ]] || die "Cancelled; no changes made."
}
service_action() {
    command -v systemctl >/dev/null 2>&1 || die "systemctl is not available on this host."
    systemctl "$@" "$SERVICE_NAME"
}
app_python() {
    [[ -x "$INSTALL_DIR/.venv/bin/python" ]] || die "Application environment not found at $INSTALL_DIR/.venv. Install first."
    "$INSTALL_DIR/.venv/bin/python" "$@"
}
verify_video_tools() {
    command -v runuser >/dev/null 2>&1 || die "runuser is required to verify media tools as the service account."
    runuser -u kid-learning-tv -- ffmpeg -version >/dev/null || die "FFmpeg verification failed."
    runuser -u kid-learning-tv -- ffprobe -version >/dev/null || die "FFprobe verification failed."
    runuser -u kid-learning-tv -- "$INSTALL_DIR/.venv/bin/python" -c 'import yt_dlp, yt_dlp_ejs' \
        || die "YouTube downloader verification failed."
    runuser -u kid-learning-tv -- "$INSTALL_DIR/.venv/bin/deno" --version >/dev/null \
        || die "Deno JavaScript runtime verification failed."
}
