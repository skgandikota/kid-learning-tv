#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
require_root

command -v python3 >/dev/null 2>&1 || die "Install Python 3.10+ and python3-venv first."
python3 -c 'import sys; raise SystemExit(sys.version_info < (3,10))' || die "Python 3.10 or later is required."
[[ -f "$SOURCE_DIR/pyproject.toml" && -d "$SOURCE_DIR/app" ]] || die "Run this from a complete project checkout."
confirm "Install the appliance to $INSTALL_DIR, enable its system service, and start it?"

if ! id kid-learning-tv >/dev/null 2>&1; then
    useradd --system --home-dir "$STATE_DIR" --shell /usr/sbin/nologin kid-learning-tv
fi
install -d -o kid-learning-tv -g kid-learning-tv -m 0750 "$STATE_DIR" "$STATE_DIR/media"
install -d -m 0755 "$INSTALL_DIR"
if [[ "$SOURCE_DIR" != "$INSTALL_DIR" ]]; then
    preserve_content=0
    [[ ! -f "$STATE_DIR/kid-learning-tv.sqlite3" ]] || preserve_content=1
    for item in app config content tools systemd kiosk docs; do
        if [[ ! -d "$SOURCE_DIR/$item" && ( "$item" == docs || "$item" == kiosk ) ]]; then continue; fi
        if [[ "$item" == content && "$preserve_content" == 1 ]]; then continue; fi
        [[ -d "$SOURCE_DIR/$item" ]] || die "Missing project directory: $item"
        install -d -m 0755 "$INSTALL_DIR/$item"
        cp -a "$SOURCE_DIR/$item/." "$INSTALL_DIR/$item/"
    done
    for item in pyproject.toml requirements.lock README.md; do
        [[ -f "$SOURCE_DIR/$item" ]] || die "Missing project file: $item"
        cp -a "$SOURCE_DIR/$item" "$INSTALL_DIR/"
    done
    install -d -m 0755 "$INSTALL_DIR/scripts"
    cp -a "$SOURCE_DIR/scripts/." "$INSTALL_DIR/scripts/"
fi
chown -R kid-learning-tv:kid-learning-tv "$INSTALL_DIR/content" "$STATE_DIR"
(
    umask 022
    python3 -m venv "$INSTALL_DIR/.venv"
    if [[ -n "${KLT_WHEELHOUSE:-}" ]]; then
        [[ -d "$KLT_WHEELHOUSE" ]] || die "KLT_WHEELHOUSE is not a directory."
        "$INSTALL_DIR/.venv/bin/pip" install --no-index --find-links "$KLT_WHEELHOUSE" "$INSTALL_DIR" waitress
    else
        "$INSTALL_DIR/.venv/bin/pip" install "$INSTALL_DIR" waitress
    fi
)
# Repair environments left root-only by an earlier installation attempt.
chmod -R a+rX "$INSTALL_DIR/.venv"
PYTHONPATH="$INSTALL_DIR" "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/tools/content_validator.py" || die "Content validation failed; fix local content before enabling the service."
command -v runuser >/dev/null 2>&1 || die "runuser is required to securely set the PIN as the service account."
pin_status="$(runuser -u kid-learning-tv -- env KLT_DATA_DIR="$STATE_DIR" PYTHONPATH="$INSTALL_DIR" \
    "$INSTALL_DIR/.venv/bin/python" -c 'import os; from pathlib import Path; from app.database import Database; print("configured" if Database(Path(os.environ["KLT_DATA_DIR"]) / "kid-learning-tv.sqlite3").get_pin_hash() else "missing")')"
if [[ "$pin_status" != "configured" ]]; then
    [[ -t 0 && -t 1 ]] || die "Initial parent PIN setup needs an interactive terminal. Rerun install.sh from a local terminal."
    if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet "$SERVICE_NAME.service"; then
        systemctl stop "$SERVICE_NAME.service" || die "Could not stop the service before initial PIN setup."
    fi
    info "No parent PIN is configured. Enter it twice at the hidden prompts; only its salted hash is stored."
    runuser -u kid-learning-tv -- env KLT_DATA_DIR="$STATE_DIR" "$INSTALL_DIR/.venv/bin/python" \
        "$INSTALL_DIR/tools/set_parent_pin.py" || die "Initial PIN setup failed; the service was not enabled."
fi
install -d -m 0755 /etc/kid-learning-tv /etc/systemd/system
if [[ ! -e /etc/kid-learning-tv/kid-learning-tv.env ]]; then
    cat > /etc/kid-learning-tv/kid-learning-tv.env <<EOF
KLT_HOST=0.0.0.0
KLT_PORT=8765
KLT_DATA_DIR=$STATE_DIR
KLT_CONFIG=config/default.json
KLT_CONTENT_DIR=$INSTALL_DIR/content
KLT_SECURE_COOKIE=0
EOF
    chmod 0640 /etc/kid-learning-tv/kid-learning-tv.env
    chown root:kid-learning-tv /etc/kid-learning-tv/kid-learning-tv.env
fi
install -m 0644 "$INSTALL_DIR/systemd/kid-learning-tv.service" /etc/systemd/system/kid-learning-tv.service
systemctl daemon-reload
systemctl enable --now kid-learning-tv.service
info "Installed. Check with: systemctl status kid-learning-tv"
info "Open http://<appliance-address>:8765/ on the local network and sign in using the PIN set during installation."
