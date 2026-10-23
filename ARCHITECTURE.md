# Architecture

## Runtime

`app.main` creates the Flask application and the SQLite database. When waitress is installed, the entry point serves it with waitress; otherwise the code falls back to Flask's built-in server, which is intended for development rather than production. The deployment installer provisions waitress separately because the project dependency manifest currently lists Flask and jsonschema only.

The local web UI is served from `app/templates` and `app/static`. Content is loaded from local JSON in `content/` and checked with JSON Schema plus application-level validation. `app/games` contains game logic; `app/events` provides the in-process event bus. Optional offline voice uses browser microphone capture on localhost, a 16 kHz PCM AudioWorklet, Silero speech detection, CPU INT8 Whisper base.en recognition and Piper WAV prompts played by the TV browser. Utterances are capped at 18 seconds and end after 1.25 seconds of silence. Turn revisions reject stale audio before and after inference. Neural inference runs outside the game-state lock so parent controls remain responsive. The browser stops capture during prompts, slow requests and non-listening screens; audio is never persisted.

## Persistence and network

- SQLite: `<KLT_DATA_DIR>/kid-learning-tv.sqlite3` (default `var/kid-learning-tv.sqlite3` in a checkout; installer uses `/var/lib/kid-learning-tv`).
- Uploaded parent videos: `<KLT_DATA_DIR>/media`.
- Settings: `config/default.json`, optionally overlaid by `KLT_CONFIG`.
- Content root: `KLT_CONTENT_DIR` (defaults to the repository's `content` directory).
- HTTP listener: `KLT_HOST` and `KLT_PORT`, defaults `0.0.0.0:8765`.

The systemd unit runs as an unprivileged account. The browser kiosk is an optional desktop-user autostart, separate from the server process. Local APIs do not require internet access. The parent interface supports remote controls over the LAN.

## Data flow

The browser calls local JSON APIs; parent-only actions require authenticated session state and CSRF checks. Game state/events are in-process. Persistent settings, parent PIN hash, activity history, event records, and media metadata use SQLite. The event table is bounded by the app; history is opt-in in settings. Uploaded video bytes are stored locally.

## Boundaries

There is no cloud backend, Alexa skill endpoint, YouTube integration or chatbot. Voice models run locally after one-time downloads. Ask Rocky is simulated and does not capture audio.
