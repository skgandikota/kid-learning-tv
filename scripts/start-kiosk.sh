#!/usr/bin/env bash
set -Eeuo pipefail
if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    printf 'Error: Run the kiosk as the desktop user, without sudo.\n' >&2
    exit 1
fi
exec /bin/bash "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/kiosk-supervisor.sh"
