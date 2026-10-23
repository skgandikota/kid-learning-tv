# Privacy and data handling

The app is designed to operate locally. Core pages, game logic, content, settings, and optional eSpeak NG speech output do not require a cloud service. The service uses the LAN for parent-device access when enabled.

## What may be stored

- Parent PIN verifier (salted PBKDF2-SHA256 hash), settings, login-attempt records, and app event records in SQLite.
- Activity summaries only when history is enabled; event records are bounded by the application.
- Parent-uploaded video files and metadata in the local data directory.
- Session cookies in the browser.

Optional offline speech recognition captures the laptop microphone only after
browser permission and local voice setup. Short PCM chunks go from the localhost
TV page to the recognizer on the same laptop. Audio and recognition results are
processed in memory, not written to files or sent to a cloud service. Recognized
game answers can appear in current game state like typed answers. Capture stops
during spoken prompts, pause, lock, video and non-voice activities. Ask Rocky
remains pretend and does not open the microphone or retain audio.

Voice setup downloads a fixed English Vosk model once from alphacephei.com and
installs dependencies; play itself needs no internet. eSpeak NG synthesizes
prompts locally and the TV browser plays them. No YouTube downloading is provided.

## Parent choices and retention

Parents can control history settings and delete history through the parent UI. Video removal is available through parent controls. Database and media deletion is not performed by uninstall or rollback scripts. Backups include the database, uploaded media, preferences, and mutable local content; store them securely and delete them when no longer needed.

The OS, browser, and network equipment may have their own logs or telemetry; those are outside the app's data handling. The local HTTP interface does not encrypt traffic.
