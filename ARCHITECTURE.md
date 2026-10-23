# Architecture

Flask serves a blank TV document at `/` and PIN login at `/parent`.
Waitress serves HTTP on the configured host and port (8765 by default).
The parent page uses a small local script for sign-in/sign-out.

SQLite stores parent credentials and rate-limited login attempts. Existing PIN
hashes remain compatible. Sessions use HTTP-only, SameSite cookies and POST
requests require a session CSRF token. `/api/health` reports basic service status.

Game, voice, AI, media and event-stream code has been removed. The updater replaces
the application tree to remove stale routes/assets and no longer downloads models.
Runtime data and legacy content are preserved separately.
