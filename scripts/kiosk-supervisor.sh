#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
browser=""
for candidate in chromium chromium-browser google-chrome; do
    if command -v "$candidate" >/dev/null 2>&1; then browser="$(command -v "$candidate")"; break; fi
done
[[ -n "$browser" ]] || die "Install Chromium or Google Chrome, or disable kiosk autostart."
url="${KLT_KIOSK_URL:-http://127.0.0.1:8765/}"

# Wait up to 60 seconds for the app so Chromium does not open on an error page at boot.
if command -v curl >/dev/null 2>&1; then
    for _ in $(seq 1 60); do
        curl --silent --fail --max-time 2 "${url%/}/api/health" >/dev/null && break
        sleep 1
    done
fi

# Alt+F4 (clean exit) stays closed. A crash restarts Chromium after 3 seconds.
while true; do
    status=0
    "$browser" --kiosk --no-first-run --disable-translate --noerrdialogs \
        --disable-session-crashed-bubble --password-store=basic \
        --autoplay-policy=no-user-gesture-required "$url" || status=$?
    [[ "$status" -eq 0 ]] && exit 0
    info "Chromium exited with status $status; restarting in 3 seconds."
    sleep 3
done