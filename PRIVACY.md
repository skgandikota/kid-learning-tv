# Privacy and data handling

The app is designed to operate locally. Core pages, game logic, content, settings, and optional eSpeak NG speech output do not require a cloud service. The service uses the LAN for parent-device access when enabled.

## What may be stored

- Parent PIN verifier (salted PBKDF2-SHA256 hash), settings, login-attempt records, and app event records in SQLite.
- Activity summaries only when history is enabled; event records are bounded by the application.
- Parent-uploaded video files and metadata in the local data directory.
- Session cookies in the browser.

There is no speech-to-text or microphone recording pipeline. Ask Rocky is simulated and does not record or retain audio. No YouTube downloading is provided. eSpeak NG, if enabled, synthesizes speech locally.

## Parent choices and retention

Parents can control history settings and delete history through the parent UI. Video removal is available through parent controls. Database and media deletion is not performed by uninstall or rollback scripts. Backups include the database, uploaded media, preferences, and mutable local content; store them securely and delete them when no longer needed.

The OS, browser, and network equipment may have their own logs or telemetry; those are outside the app's data handling. The local HTTP interface does not encrypt traffic.
