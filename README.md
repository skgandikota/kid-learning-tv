# Kid Learning TV

An offline-first, local-network learning and games appliance for a child-friendly TV. The current app includes the Avocado answer game, Memory Chain, parent controls, local content, optional local eSpeak speech, and a parent-uploaded video library.

## Quick start

For local development, install Python 3.10+, then run:

```bash
python -m venv .venv
# Activate the environment using your operating system's instructions.
python -m pip install -e .
python -m app.main
```

Open `http://127.0.0.1:8765/`; use `/parent` for parent setup and controls. `scripts/run-development.sh` is a convenience for Linux/macOS. The production scripts and systemd unit target a Lubuntu/Linux installation; see [INSTALLATION.md](INSTALLATION.md).

## Important capabilities and limits

- The app serves locally and is designed to keep learning content and app data on the appliance.
- The parent **Learning library** enables and launches matching pairs, counting, colour matching and shape matching inside the TV interface. Only a parent can restart or exit these games. They are original browser activities, not the full GCompris suite.
- Optional **offline English voice play** uses the laptop microphone, Vosk and local eSpeak NG prompts. See [INSTALLATION.md](INSTALLATION.md) for one-time voice setup. No cloud recognition or saved microphone audio. Home has picture icons; tap or say Avocado to start Animals immediately.
- Ask Rocky is a simulated activity; it does not record or retain audio. The bundled Rocky art is original helper art, not Paw Patrol artwork.
- There is no YouTube downloader. Parents may upload local MP4/WebM videos through the parent UI.
- LAN access uses HTTP by default. Keep the device on a trusted private network; do not expose its port to the internet.

Read [QUICK-START.md](QUICK-START.md), [SECURITY.md](SECURITY.md), and [PRIVACY.md](PRIVACY.md) before use.
