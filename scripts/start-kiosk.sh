#!/usr/bin/env bash
set -Eeuo pipefail
if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    printf 'Error: Run the kiosk as the desktop user, without sudo.\n' >&2
    exit 1
fi
if [[ -n "${DISPLAY:-}" ]]; then
    systemctl --user import-environment DISPLAY
fi
if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
    systemctl --user import-environment WAYLAND_DISPLAY
fi
if [[ -n "${XAUTHORITY:-}" ]]; then
    systemctl --user import-environment XAUTHORITY
fi
systemctl --user start kid-learning-kiosk.service
