#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
browser=""
for candidate in chromium chromium-browser google-chrome; do
    if command -v "$candidate" >/dev/null 2>&1; then browser="$(command -v "$candidate")"; break; fi
done
[[ -n "$browser" ]] || die "Install Chromium or Google Chrome, or disable kiosk autostart."
url="${KLT_KIOSK_URL:-http://127.0.0.1:8765/}"
while true; do
    "$browser" --kiosk --no-first-run --disable-translate "$url" || true
    sleep 3
done
