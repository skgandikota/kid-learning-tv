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
