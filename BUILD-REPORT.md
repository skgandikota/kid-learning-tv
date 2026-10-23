# Build and integration report

## Scope completed

Deployment/integration assets and documentation cover Linux/Lubuntu installation, service management, content validation, backup/restore, rollback, diagnostics, parent PIN recovery, optional kiosk mode and offline English voice setup. Alexa integration is not implemented.

## Project facts reflected

- Python package entry point: `python -m app.main`; Flask and jsonschema are declared.
- Production install script requests waitress separately because it is not in the present dependency manifest.
- SQLite defaults to `var/kid-learning-tv.sqlite3`; installer state uses `/var/lib/kid-learning-tv`.
- Default service address is `0.0.0.0:8765`, HTTP.
- Speech input is optional offline Vosk through the localhost TV browser. eSpeak NG generates prompts for browser playback. Without voice setup, parent-assisted input remains available.
- Ask Rocky is simulated with no audio recording/retention; original helper artwork only.
- Parent video upload supports local MP4/WebM; no YouTube downloader.
- Initial PIN setup and PIN reset use `tools/set_parent_pin.py` with hidden input, salted hashing, service-account ownership, and no plaintext command-line or file handling.

## Validation status

The application test suite passed (71 tests). Python compilation, JavaScript syntax checks, shell syntax checks, content validation and wheel building passed after the voice changes. Installation and update scripts validate content before proceeding. Both the application system service and a desktop-user kiosk service unit are included. See `TEST-REPORT.md` for the test environment and limitations.

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

Chromium/Edge was exercised with a synthetic microphone source and the real
small English Vosk model: spoken Avocado passed through browser microphone
capture, the AudioWorklet and the local PCM API and started Animals. A real
eSpeak NG WAV generated on Linux decoded and played in the browser. Pausing
released the capture stream. Picture cards were present, Avocado started
directly without a category screen, and typed child input was absent in voice
mode. This does not establish young-child recognition accuracy or validate the
target laptop microphone, speaker output or Lubuntu installation.
