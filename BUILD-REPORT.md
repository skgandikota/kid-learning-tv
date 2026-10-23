# Build and integration report

## Scope completed

Deployment/integration assets and documentation cover Linux/Lubuntu installation, service management, content validation, backup/restore, rollback, diagnostics, parent PIN recovery, optional kiosk mode and offline English voice setup. Alexa integration is not implemented.

## Project facts reflected

- Python package entry point: `python -m app.main`; Flask and jsonschema are declared.
- Production install script requests waitress separately because it is not in the present dependency manifest.
- SQLite defaults to `var/kid-learning-tv.sqlite3`; installer state uses `/var/lib/kid-learning-tv`.
- Default service address is `0.0.0.0:8765`, HTTP.
- Speech input is optional CPU INT8 Whisper through the localhost TV browser. Piper generates natural British prompts for browser playback. Updates install and verify both models while preserving parent voice settings. Without voice setup, parent-assisted input remains available.
- Ask Rocky is simulated with no audio recording/retention; original helper artwork only.
- Parent video upload supports local MP4/WebM; no YouTube downloader.
- Initial PIN setup and PIN reset use `tools/set_parent_pin.py` with hidden input, salted hashing, service-account ownership, and no plaintext command-line or file handling.

## Validation status

See `TEST-REPORT.md` for the current automated results and limitations. Installation and update scripts validate content before proceeding. Both the application system service and a desktop-user kiosk service unit are included.

No Lubuntu installation, systemd activation, kiosk behavior, iPhone Safari, or target hardware operation was tested.

## Learning library addition

Four original browser activities are included: matching pairs (four pairs),
counting one to five, colour matching and shape matching. Parent controls save
per-activity enable switches and launch, reset or exit games. The child can only
play the selected game; completion stays on screen. Hidden cards and answers are
managed by the server, and stale session/turn submissions are rejected.

A headless Microsoft Edge check on Windows exercised separate TV and phone-sized
parent pages: enable persistence across reload, mismatched-card reveal/hide,
matching-pairs completion/restart, all three choice games, pause/resume,
parent-only exit and disabling the current game. No JavaScript exceptions were
observed. This is not an iPhone Safari or Lubuntu hardware test.

No GCompris code, assets or full-suite download is bundled.

## Offline voice and picture Home

The previous speech engine had a synthetic-microphone browser check; that is not
validation of the new Piper/Whisper models. Current regression checks cover
utterance buffering, silence, bounded capture, stale turns, explicit failures,
and parent pause/lock during blocked inference/synthesis. Real bundled Silero
VAD accepted half-second silent input without identifying speech.

Piper/Whisper packages installed successfully on the development host. Model
downloads were blocked by the development network's web filter (HTTP 403), so
real synthesis, transcription and their latency remain unverified. The updater
downloads and loads both models as the restricted service account before
starting the app. Child speech, target microphone/speakers and Lubuntu operation
still require on-device checks.
