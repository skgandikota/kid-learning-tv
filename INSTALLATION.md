# Installation (Lubuntu/Linux)

These instructions describe the deployment assets in this repository; they are not a claim that a Lubuntu installation or systemd service has been exercised.

## Requirements

- Lubuntu or another systemd-based Linux desktop, Python 3.10+, `python3-venv`, and pip.
- Network access during installation for Python packages, unless a complete compatible wheelhouse is supplied with `KLT_WHEELHOUSE`.
- For kiosk mode, Chromium (`chromium` or `chromium-browser`) or Google Chrome.
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

## Offline voice setup

After a normal installation, run:

```bash
sudo bash /opt/kid-learning-tv/scripts/setup-voice.sh
```

This installs Piper, faster-whisper and their CPU dependencies, downloads about
220 MB of pinned models from Hugging Face (British English Cori speech and
Whisper base.en recognition), verifies both as the service account, enables
offline speech and restarts the app. Allow extra disk space for Python packages
and download staging; the model downloader requires at least 1 GB free after
package installation. Internet is needed only for setup. Models stay under
`/opt/kid-learning-tv/models`; they are not included in the Git repository.

On the laptop, open **http://127.0.0.1:8765/** in Chromium. Tap **Start voice**
once and allow microphone access. Select the laptop's built-in microphone in
Lubuntu audio settings. Prompts play through the browser's chosen audio output
(select HDMI for the TV). No extra OS microphone permissions are given to the
background service.

Say **Avocado** to start Animals, **Memory** for Shopping Memory Chain, or
**Ask Rocky** for the pretend message. Tap Home picture cards for the same
actions; Avocado no longer has a second selection screen. In Avocado, speak an
animal name. In Memory Chain, say the list in order and add one item. A fuzzy
Avocado match asks for a spoken **yes** or **no**. Parent-launched counting,
colour and shape games also accept spoken answers. Matching pairs stays
tap/click and can only be launched/exited by a parent.

Audio capture stops during prompts, pause, lock, video, matching pairs and the
pretend Rocky message. Recognition uses memory only; audio is not saved or sent
to any cloud service. Recognition quality for a three-year-old, distance from
the built-in microphone and the laptop's performance must be checked on-device;
synthetic adult-like test speech is not evidence of child-speech accuracy.
Whisper uses CPU INT8 and two inference threads; no GPU is needed. RAM usage and
latency on this laptop have not been measured. During slow recognition, the UI
shows **Thinking...** and pauses capture instead of overflowing an audio queue.
Parent pause, lock and Home remain available during inference.

Parents can switch voice answers off under **Sound and session**. Without voice
setup, parent-assisted typed answers remain available.

For an existing GitHub installation, the update now installs all neural voice
software and models automatically; no separate voice setup command is needed:

```bash
cd ~/kid-learning-tv
git pull --ff-only origin main
sudo bash scripts/update.sh "$PWD"
```

The first update needs internet and takes longer while packages/models download.
Later updates reuse complete models. Existing parent voice settings are preserved:
if voice was off, enable **Speak prompts** and **Offline voice answers** under
**Sound and session**. Refresh the laptop's localhost page and tap **Start voice**.
If setup fails, the update reports the error and leaves the service stopped;
resolve it and rerun the same update command or use rollback.

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
