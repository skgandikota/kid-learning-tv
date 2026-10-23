# Architecture

Flask serves the TV document at `/` and PIN login at `/parent`.
Waitress serves HTTP on the configured host and port (8765 by default).
The parent page uses a small local script for sign-in/sign-out and Food time.
An authenticated, CSRF-protected POST sets a persisted SQLite display flag.
The TV polls `/api/display` every 750 ms without overlapping requests and shows
the supplied local PNG with `object-fit: contain`, without any controls or clock.

SQLite stores parent credentials and rate-limited login attempts. Existing PIN
hashes remain compatible. Sessions use HTTP-only, SameSite cookies and POST
requests require a session CSRF token. `/api/health` reports basic service status.

Game, voice, AI and event-stream code remain removed. The updater replaces
the application tree to remove stale routes/assets and no longer downloads models.
Runtime data and legacy content are preserved separately.

The Video panel uses a local folder library and a single background yt-dlp job.
Only explicitly submitted YouTube video URLs are downloaded. FFprobe inspects
browser-compatible files; FFmpeg merges downloaded streams. The service account
owns `/var/lib/kid-learning-tv/videos`; staging files are not part of the library.

`Playback` owns a locked in-memory playlist. Parent controls update a command
revision, and a loopback-only, CSRF-protected TV report updates measured progress.
Stale reports cannot undo a seek, skip, pause or replacement playlist. Video
completion advances the queue on the server; the last video switches to the
parent-supplied end photo. The TV polls every 500 ms, reports once per second, and has no
playback controls. Parent panel polls show actual position/buffering/errors.
No playback is automatically restored after a service restart.
