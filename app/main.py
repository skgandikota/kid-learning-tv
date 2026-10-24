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
from app.quiz import validate_settings
from app.quiz_catalog import CATEGORIES, get_items
from app.quiz_speech import QuizSpeech
from app.phonics_speech import PhonicsSpeech
from app.typing_game import LESSONS, get_lesson, sound_step


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
    speech = QuizSpeech(data_dir)
    app.extensions["klt_quiz_speech"] = speech
    phonics = PhonicsSpeech(data_dir)
    app.extensions["klt_phonics_speech"] = phonics

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
            "connect-src 'self'; media-src 'self' blob:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
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

    @app.get("/api/quiz/catalog")
    def quiz_catalog():
        return jsonify({"categories": CATEGORIES})

    @app.post("/api/child/quiz")
    def child_quiz():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValueError("Choose a quiz.")
        with playback.lock:
            if playback.mode not in {"blank", "quiz-menu", "quiz"}:
                return jsonify({"error": "A grown-up is using the TV."}), 423
            action = body.get("action")
            if action == "start":
                playback.start_quiz(body.get("category"))
            elif action in {"menu", "close"}:
                playback.quiz_command(action)
            else:
                raise ValueError("Choose a quiz or close it.")
        return jsonify({"ok": True})

    @app.get("/api/parent/quiz")
    def parent_quiz():
        if not session.get("parent_authenticated"):
            return jsonify({"error": "Parent sign-in required."}), 401
        return jsonify({
            "categories": CATEGORIES, "settings": database.quiz_settings(),
            "playback": playback.snapshot(), "speech": speech.status(),
        })

    @app.post("/api/child/matching")
    def child_matching():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValueError("Choose a card control.")
        with playback.lock:
            if playback.mode not in {"blank", "matching"}:
                return jsonify({"error": "Close the current activity before opening Card match."}), 423
            action = body.get("action")
            if action == "start":
                playback.start_matching()
            elif action == "close":
                playback.food(False)
            elif action == "flip":
                if playback.matching is None or not playback.matching.flip(body.get("token"), body.get("index")):
                    return jsonify({"error": "That card turn has changed. Choose another card."}), 409
                playback.revision += 1
            else:
                raise ValueError("Choose a card or close the game.")
            return jsonify({"ok": True, "playback": playback.snapshot()})

    @app.post("/api/parent/quiz")
    def parent_quiz_action():
        if not session.get("parent_authenticated"):
            return jsonify({"error": "Parent sign-in required."}), 401
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValueError("Choose a quiz control.")
        action = body.get("action")
        if action == "settings":
            database.set_quiz_settings(validate_settings(body.get("settings")))
        elif action == "start":
            playback.start_quiz(body.get("category"))
        else:
            playback.quiz_command(action)
        return jsonify({"ok": True})

    @app.get("/api/typing/catalog")
    def typing_catalog():
        return jsonify({"lessons": [
            {key: item[key] for key in ("id", "name", "image", "category", "blend")}
            for item in LESSONS
        ]})

    @app.post("/api/child/typing")
    def child_typing():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValueError("Choose a typing activity.")
        with playback.lock:
            if playback.mode not in {"blank", "typing-menu", "typing"}:
                return jsonify({"error": "Close the current activity before opening Hero Typing."}), 423
            action = body.get("action")
            accepted = True
            sound = None
            if action == "menu":
                playback.food(False)
                playback.mode = "typing-menu"
            elif action == "start":
                playback.start_typing(body.get("id"))
            elif action == "close":
                playback.food(False)
            elif action == "key":
                game = playback.typing
                if game is None:
                    raise ValueError("Choose a name first.")
                accepted = game.type_key(body.get("token"), body.get("position"), body.get("key"))
                if accepted:
                    sound = sound_step(game.item, game.position)
                    playback.revision += 1
            elif action in {"next", "previous", "advance"}:
                game = playback.typing
                if game is None or body.get("token") != game.token:
                    raise ValueError("That typing turn has changed. Choose the current arrow.")
                if action == "advance" and not game.snapshot()["complete"]:
                    raise ValueError("Finish this name before moving on automatically.")
                index = next(index for index, item in enumerate(LESSONS) if item["id"] == game.item["id"])
                target = index - 1 if action == "previous" else index + 1
                if 0 <= target < len(LESSONS):
                    playback.start_typing(LESSONS[target]["id"])
                else:
                    playback.food(False)
                    playback.mode = "typing-menu"
            else:
                raise ValueError("Choose a name, letter or close.")
            return jsonify({
                "ok": True, "accepted": accepted, "playback": playback.snapshot(),
                "sound": bool(sound and sound["sound"]),
                "blend": bool(sound and sound["blend"]),
            })

    @app.get("/api/typing/audio/<item_id>/<int:position>/<kind>")
    def typing_audio(item_id, position, kind):
        if request.remote_addr not in {"127.0.0.1", "::1"} and not session.get("parent_authenticated"):
            return jsonify({"error": "Local TV or parent sign-in required."}), 403
        item = get_lesson(item_id)
        try:
            audio = speech.audio(item["name"]) if kind == "name" and position == 0 else phonics.audio(item_id, position, kind)
        except (OSError, RuntimeError) as error:
            app.logger.error("Typing sound failed: %s", error)
            return jsonify({"error": "Typing sounds are unavailable. Run the laptop update and check eSpeak NG and volume."}), 503
        from flask import Response
        return Response(audio, mimetype="audio/wav")

    @app.post("/api/tv/quiz")
    def tv_quiz():
        if request.remote_addr not in {"127.0.0.1", "::1"}:
            return jsonify({"error": "Only the laptop TV can report quiz progress."}), 403
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValueError("Invalid quiz report.")
        with playback.lock:
            quiz = playback.quiz
            if playback.mode != "quiz" or quiz is None:
                return jsonify({"error": "That quiz has closed."}), 409
            action = body.get("action")
            if action == "ready":
                accepted = quiz.ready(body.get("token"))
            elif action == "speech-done":
                warning = body.get("warning", "")
                if not isinstance(warning, str):
                    raise ValueError("Invalid speech status.")
                accepted = quiz.speech_done(body.get("token"), warning)
            elif action == "image-error":
                warning = body.get("warning")
                if not isinstance(warning, str):
                    raise ValueError("Invalid image status.")
                accepted = body.get("token") == quiz.token
                if accepted:
                    quiz.warning = warning[:240]
            else:
                raise ValueError("Invalid quiz report.")
            if not accepted:
                return jsonify({"error": "That quiz picture has changed."}), 409
        return jsonify({"ok": True})

    @app.get("/api/quiz/audio/<category>/<item_id>")
    def quiz_audio(category, item_id):
        if request.remote_addr not in {"127.0.0.1", "::1"} and not session.get("parent_authenticated"):
            return jsonify({"error": "Local TV or parent sign-in required."}), 403
        item = next((item for item in get_items(category) if item["id"] == item_id), None)
        if item is None:
            return jsonify({"error": "Quiz answer not found."}), 404
        try:
            audio = speech.audio(item.get("speech", item["name"]))
        except (OSError, RuntimeError, ValueError) as error:
            app.logger.error("Quiz speech failed: %s", error)
            return jsonify({"error": "Quiz speech is unavailable. Check parent Quiz sound status."}), 503
        from flask import Response
        return Response(audio, mimetype="audio/wav")

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
