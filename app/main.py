"""Parent-controlled Food time display and PIN sign-in."""
from __future__ import annotations

import hmac
import secrets
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session, send_file
from werkzeug.exceptions import RequestEntityTooLarge

from app.auth.security import hash_pin, valid_pin, verify_pin
from app.config import DATA_DIR, HOST, PORT, SECURE_COOKIE
from app.database import Database
from app.playback import Playback
from app.video_library import VideoLibrary


def _secret_key(data_dir: Path) -> str:
    path = data_dir / "secret.key"
    if path.exists():
        return path.read_text(encoding="ascii").strip()
    value = secrets.token_urlsafe(48)
    with path.open("w", encoding="ascii") as output:
        path.chmod(0o600)
        output.write(value)
    return value


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=None, DATA_DIR=DATA_DIR,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=SECURE_COOKIE, PERMANENT_SESSION_LIFETIME=1800,
        MAX_CONTENT_LENGTH=32 * 1024,
    )
    if overrides:
        app.config.update(overrides)
    data_dir = Path(app.config["DATA_DIR"]).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    app.secret_key = app.config["SECRET_KEY"] or _secret_key(data_dir)
    database = Database(data_dir / "kid-learning-tv.sqlite3")
    app.extensions["klt_db"] = database
    playback = Playback(database)
    library = VideoLibrary(data_dir / "videos")
    app.extensions["klt_playback"] = playback
    app.extensions["klt_videos"] = library

    def csrf_token():
        if not session.get("csrf_token"):
            session["csrf_token"] = secrets.token_urlsafe(32)
        return session["csrf_token"]

    @app.before_request
    def protect_mutations():
        if request.method == "POST":
            expected = session.get("csrf_token", "")
            supplied = request.headers.get("X-CSRF-Token", "")
            if not expected or not supplied or not hmac.compare_digest(expected, supplied):
                return jsonify({"error": "Reload the page and try again."}), 400

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def tv():
        return render_template("tv.html", food_time=database.food_time(), csrf_token=csrf_token())

    @app.get("/parent")
    def parent():
        return render_template(
            "parent.html", csrf_token=csrf_token(),
            configured=database.get_pin_hash() is not None,
            authenticated=bool(session.get("parent_authenticated")),
            food_time=playback.snapshot()["mode"] == "food",
        )

    @app.get("/api/display")
    def display():
        state = playback.snapshot()
        return jsonify({"food_time": state["mode"] == "food", "playback": state})

    @app.post("/api/parent/food-time")
    def food_time():
        if not session.get("parent_authenticated"):
            return jsonify({"error": "Parent sign-in required."}), 401
        body = request.get_json(silent=True)
        enabled = body.get("enabled") if isinstance(body, dict) else None
        if not isinstance(enabled, bool):
            return jsonify({"error": "Food time must be on or off."}), 400
        playback.food(enabled)
        return jsonify({"ok": True, "food_time": enabled})

    @app.get("/api/parent/videos")
    def videos():
        if not session.get("parent_authenticated"):
            return jsonify({"error": "Parent sign-in required."}), 401
        return jsonify({
            "videos": library.list(), "downloads": library.jobs(),
            "folder": str(library.directory), "playback": playback.snapshot(),
        })

    @app.post("/api/parent/videos/download")
    def download_video():
        if not session.get("parent_authenticated"):
            return jsonify({"error": "Parent sign-in required."}), 401
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValueError("Provide a YouTube URL and title.")
        job = library.download(body.get("url"), body.get("title"))
        return jsonify({"ok": True, "job": job}), 202

    @app.post("/api/parent/videos/play")
    def play_videos():
        if not session.get("parent_authenticated"):
            return jsonify({"error": "Parent sign-in required."}), 401
        body = request.get_json(silent=True)
        ids = body.get("ids") if isinstance(body, dict) else None
        if not isinstance(ids, list) or not 1 <= len(ids) <= 50 or any(not isinstance(item, str) for item in ids):
            raise ValueError("Select between 1 and 50 videos in play order.")
        if len(set(ids)) != len(ids):
            raise ValueError("Select each video once.")
        playback.start(library.items(ids))
        return jsonify({"ok": True, "playback": playback.snapshot()})

    @app.post("/api/parent/videos/control")
    def video_control():
        if not session.get("parent_authenticated"):
            return jsonify({"error": "Parent sign-in required."}), 401
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValueError("Choose a video control.")
        playback.command(body)
        return jsonify({"ok": True, "playback": playback.snapshot()})

    @app.get("/api/videos/<video_id>")
    def stream_video(video_id):
        if request.remote_addr not in {"127.0.0.1", "::1"} and not session.get("parent_authenticated"):
            return jsonify({"error": "Local TV or parent sign-in required."}), 403
        try:
            path = library.resolve(video_id)
        except ValueError:
            return jsonify({"error": "Video file not found."}), 404
        return send_file(path, conditional=True)

    @app.post("/api/tv/playback")
    def tv_playback():
        if request.remote_addr not in {"127.0.0.1", "::1"}:
            return jsonify({"error": "Only the laptop TV can report playback."}), 403
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValueError("Invalid TV report.")
        if not playback.report(body):
            return jsonify({"error": "That playback command has changed."}), 409
        return jsonify({"ok": True})

    @app.post("/api/setup")
    def setup():
        if database.get_pin_hash():
            return jsonify({"error": "A parent PIN is already configured."}), 403
        if request.remote_addr not in {"127.0.0.1", "::1"}:
            return jsonify({"error": "Set the initial PIN on the laptop."}), 403
        body = request.get_json(silent=True)
        pin = body.get("pin") if isinstance(body, dict) else None
        if not valid_pin(pin):
            return jsonify({"error": "Use a PIN containing 6 to 12 digits."}), 400
        database.set_pin_hash(hash_pin(pin))
        return signed_in()

    def signed_in():
        session.clear()
        session.permanent = True
        session["parent_authenticated"] = True
        return jsonify({"ok": True, "csrf_token": csrf_token()})

    @app.post("/api/login")
    def login():
        if database.attempts_since(int(time.time()) - 300) >= 5:
            return jsonify({"error": "Too many attempts. Wait five minutes, then try again."}), 429
        body = request.get_json(silent=True)
        pin = body.get("pin") if isinstance(body, dict) else None
        stored = database.get_pin_hash()
        succeeded = bool(stored and isinstance(pin, str) and len(pin) <= 12 and verify_pin(pin, stored))
        database.record_attempt(succeeded)
        if not succeeded:
            return jsonify({"error": "That PIN did not match."}), 401
        return signed_in()

    @app.post("/api/logout")
    def logout():
        if not session.get("parent_authenticated"):
            return jsonify({"error": "Parent sign-in required."}), 401
        session.clear()
        return jsonify({"ok": True})

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "database": database.path.exists()})

    @app.errorhandler(RequestEntityTooLarge)
    def oversized(_error):
        return jsonify({"error": "Request is too large."}), 413

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "That local resource was not found."}), 404

    @app.errorhandler(ValueError)
    def invalid_input(error):
        return jsonify({"error": str(error)}), 400

    return app


app = create_app()


def main():
    from waitress import serve
    serve(app, host=HOST, port=PORT, threads=6, channel_timeout=30)


if __name__ == "__main__":
    main()
