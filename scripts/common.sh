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
setup_quiz_voice() {
    install -d -o kid-learning-tv -g kid-learning-tv -m 0750 "$STATE_DIR/quiz-audio" "$STATE_DIR/phonics-audio"
    if [[ "${KLT_QUIZ_NATURAL_VOICE:-1}" == 1 ]]; then
        install -d -m 0755 "$INSTALL_DIR/models"
        info "Setting up optional local Piper voice on this laptop (model download required once)."
        if (
            umask 022
            "$INSTALL_DIR/.venv/bin/pip" install "$INSTALL_DIR[quiz-voice]"
        ); then
            if ! "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/tools/setup_quiz_voice.py" --data-dir "$STATE_DIR"; then
                info "WARNING: Natural voice setup failed. Checking the basic offline voice instead."
            fi
        else
            info "WARNING: Piper package installation failed. Checking the basic offline voice instead."
        fi
    else
        info "Skipping natural-voice downloads (KLT_QUIZ_NATURAL_VOICE=0)."
    fi
    chmod -R a+rX "$INSTALL_DIR/.venv"
    if [[ -d "$INSTALL_DIR/models/piper-cori-medium" ]]; then
        chmod -R a+rX "$INSTALL_DIR/models/piper-cori-medium"
    fi
    chown -R kid-learning-tv:kid-learning-tv "$STATE_DIR/quiz-audio"
    runuser -u kid-learning-tv -- "$INSTALL_DIR/.venv/bin/python" \
        "$INSTALL_DIR/tools/setup_quiz_voice.py" --verify --data-dir "$STATE_DIR" \
        || die "Neither natural nor fallback quiz speech works. Fix the reported error before starting."
    runuser -u kid-learning-tv -- env PYTHONPATH="$INSTALL_DIR" \
        "$INSTALL_DIR/.venv/bin/python" -c \
        'import sys; from app.phonics_speech import PhonicsSpeech; PhonicsSpeech(sys.argv[1]).audio("flash", 1, "sound")' "$STATE_DIR" \
        || die "Hero Typing phonics failed. Check eSpeak NG before starting."
}
