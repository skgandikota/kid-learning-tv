# Installation (Lubuntu/Linux)

These instructions describe the deployment assets in this repository; they are not a claim that a Lubuntu installation or systemd service has been exercised.

## Requirements

- Lubuntu or another systemd-based Linux desktop, Python 3.10+, `python3-venv`, and pip.
- Network access during installation for Python packages, unless a complete compatible wheelhouse is supplied with `KLT_WHEELHOUSE`.
- For kiosk mode, Chromium (`chromium` or `chromium-browser`) or Google Chrome. eSpeak NG is optional for local speech.
- A private home LAN. The default service listens on all interfaces at TCP port 8765; do not port-forward it.

## Install

From the checked-out project directory, review the scripts and run:

```bash
sudo bash scripts/install.sh
```

The installer asks for confirmation, creates the restricted `kid-learning-tv` service account, stores mutable app data in `/var/lib/kid-learning-tv`, creates a virtual environment under `/opt/kid-learning-tv`, and validates content. On a first install it then securely prompts twice for a parent PIN using hidden terminal input and stores only the salted hash, as the service account, before enabling/starting the systemd service. Run installation from an interactive local terminal; without one, first-time installation stops before the service is enabled. Package installation normally needs internet access. To install only from a prepared wheelhouse:

```bash
sudo KLT_WHEELHOUSE=/path/to/wheelhouse bash scripts/install.sh
```

The wheelhouse must contain every required compatible dependency, including Flask, jsonschema, waitress, and their dependencies. The installer preserves an existing `/etc/kid-learning-tv/kid-learning-tv.env`; review that file before starting the app.

The installer validates the bundled content before enabling the service and stops if validation fails. The current bundled content passes `python tools/content_validator.py`. For a forgotten PIN, use `sudo bash /opt/kid-learning-tv/scripts/reset-parent-pin.sh`; the same hidden-input utility updates only the database hash and does not put the PIN in command arguments or files.

Check `systemctl status kid-learning-tv`, then open `http://<device-IP>:8765/`. Use the PIN created during installation to sign in at `/parent`. Use the device's local address, not a public address.

## Kiosk

Log into the desktop as the ordinary kiosk account and run `bash /opt/kid-learning-tv/scripts/enable-kiosk.sh`. This installs the `kid-learning-kiosk.service` systemd **user** unit and a desktop-login trigger; the browser starts on the next desktop login. Keep a separate administrator/recovery account. To stop the browser and disable autostart, run `bash /opt/kid-learning-tv/scripts/disable-kiosk.sh` as the same desktop user. If the kiosk obscures the desktop, recover locally through another account or a text console; the scripts do not enable shell or remote access.

## Operations

```bash
sudo bash /opt/kid-learning-tv/scripts/diagnose.sh
sudo bash /opt/kid-learning-tv/scripts/backup.sh /path/to/protected-backups
sudo bash /opt/kid-learning-tv/scripts/update.sh /path/to/new-checkout
sudo bash /opt/kid-learning-tv/scripts/rollback.sh
```

Backups include the SQLite/media data directory and the mutable local `content/` tree. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for recovery and [PRIVACY.md](PRIVACY.md) before backing up data.

Before manually deleting the retained installation after uninstall, disable kiosk autostart from each desktop account using `scripts/disable-kiosk.sh`.
