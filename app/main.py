"""Offline-first TV and parent-control web application."""
from __future__ import annotations

import functools
import json
import os
import secrets
import socket
import threading
import time
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, session
from werkzeug.exceptions import RequestEntityTooLarge

from app.auth.security import hash_pin, valid_pin, verify_pin
from app.config import CONTENT_DIR, DATA_DIR, HOST, PORT, ROOT, SECURE_COOKIE, SETTINGS
from app.database import Database
from app.events.bus import EventBus
from app.games.avocado import AvocadoGame
from app.games.base import (
    ACTIVITY_SELECTED, ANSWER_ACCEPTED, ANSWER_CONFIRMATION_REQUIRED, ANSWER_HEARD,
    ANSWER_REJECTED, ANSWER_REPEATED, APPLICATION_STARTED, CATEGORY_SELECTED,
    GAME_PAUSED, GAME_RESUMED, GAME_STARTED, NICKNAME_ASSIGNED, RETRY_GRANTED,
    ROUND_ENDED, SCREEN_LOCKED, SCREEN_UNLOCKED, TURN_STARTED,
)
from app.games.memory import MemoryGame
from app.games.learning import ACTIVITIES, LearningGame, validate_enabled
from app.services.content import ContentError, ContentStore
from app.voice.tts import SpeechOutput


def _secret_key(data_dir: Path) -> str:
    path = data_dir / "secret.key"
    data_dir.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path.read_text(encoding="ascii").strip()
    value = secrets.token_urlsafe(48)
    path.write_text(value, encoding="ascii")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return value


class Runtime:
    def __init__(self, db: Database, content: ContentStore, settings: dict):
        self.db = db
        self.content = content
        self.settings = {**settings, **(db.get("preferences", {}) or {})}
        self.settings.setdefault("enabled_learning_activities", [])
        self.lock = threading.RLock()
        self.bus = EventBus()
        self.tts = SpeechOutput()
        self.started_at = time.time()
        self.session_started_at = None
        self.break_prompted = False
        self.state = {
            "screen": "home",
            "activity": None,
            "game": None,
            "game_state": "idle",
            "category_id": None,
            "category_name": None,
            "used_answers": [],
            "message": "Hello! Choose a fun activity.",
            "nickname": None,
            "pending_answer": None,
            "locked": False,
            "paused": False,
            "break_mode": False,
            "muted": bool(self.settings.get("muted", False)),
            "volume": int(self.settings.get("volume", 70)),
            "updated_at": int(time.time()),
        }
        self.avocado: AvocadoGame | None = None
        self.memory: MemoryGame | None = None
        self.learning_game: LearningGame | None = None
        self.emit(APPLICATION_STARTED)

    def emit(self, event_type: str, payload: dict | None = None):
        payload = payload or {}
        self.state["updated_at"] = int(time.time())
        if self.settings.get("history_enabled", False):
            self.db.record_event(event_type, {})
        self.bus.publish(event_type, self.snapshot())

    def record_history(self, activity: str, summary: str):
        if self.settings.get("history_enabled", False):
            self.db.add_history(activity, summary)

    def speak(self, text: str):
        if self.settings.get("voice_enabled") and not self.state["muted"]:
            self.tts.say(
                text,
                self.settings.get("tts_voice", "en-gb"),
                int(self.settings.get("speech_rate", 145)),
                self.state["volume"],
            )

    def snapshot(self) -> dict:
        with self.lock:
            data = dict(self.state)
            data["used_answers"] = list(self.state["used_answers"])
            data["categories"] = [
                {"id": item["id"], "name": item["name"], "enabled": item.get("enabled", True)}
                for item in self.content.categories()
                if item.get("enabled", True) and item["id"] in self.settings.get("enabled_categories", [])
            ]
            data["memory_categories"] = [
                {"id": key, "name": self.content.memory_category(key)["name"]}
                for key in self.settings.get("memory_categories", [])
                if self.content.memory_category(key)
            ]
            data["prompts"] = self.content.prompts()
            data["voice_available"] = self.tts.available()
            data["voice_enabled"] = bool(self.settings.get("voice_enabled"))
            data["low_animation"] = bool(self.settings.get("low_animation"))
            data["memory_picture_seconds"] = int(self.settings.get("memory_picture_seconds", 4))
            data["stt_profile"] = self.settings.get("stt_profile", "manual-parent-assist")
            data["session_started_at"] = self.session_started_at
            minutes = int(self.settings.get("session_minutes", 0))
            data["session_limit_seconds"] = minutes * 60
            data["break_reminder_seconds"] = int(self.settings.get("break_reminder_minutes", 0)) * 60
            elapsed = int(time.time() - self.session_started_at) if self.session_started_at else 0
            data["session_remaining"] = (
                max(0, minutes * 60 - elapsed)
                if minutes and self.session_started_at else None
            )
            reminder = int(self.settings.get("break_reminder_minutes", 0))
            data["break_due"] = bool(reminder and self.session_started_at and elapsed >= reminder * 60)
            data["break_prompted"] = self.break_prompted
            data["parent_managed_activity"] = self.learning_game is not None
            data["learning_game"] = self.learning_game.snapshot() if self.learning_game else None
            data["enabled_learning_activities"] = list(self.settings["enabled_learning_activities"])
            return data

    def start_learning(self, activity_id):
        if not isinstance(activity_id, str) or activity_id not in self.settings.get("enabled_learning_activities", []):
            raise ValueError("Enable this activity in the learning library first.")
        game = LearningGame(activity_id)
        if self.state.get("break_mode"):
            self.session_started_at = time.time()
            self.break_prompted = False
        self.learning_game = game
        self.avocado = None
        self.memory = None
        self.session_started_at = self.session_started_at or time.time()
        self.state.update({
            "screen": "learning", "activity": game.name, "game": "learning",
            "game_state": "active", "message": game.message,
            "locked": False, "paused": False, "break_mode": False,
            "category_id": None, "category_name": None, "used_answers": [],
            "pending_answer": None, "nickname": None, "media_id": None, "media_title": None,
        })
        self.emit(GAME_STARTED, {"game": game.activity_id})
        self.speak(game.message)

    def update_learning(self):
        self.state["message"] = self.learning_game.message
        self.state["game_state"] = "completed" if self.learning_game.completed else "active"
        self.emit("LEARNING_UPDATED")
        self.speak(self.state["message"])

    def update(self, event_type: str, message: str | None = None, **changes):
        self.state.update(changes)
        if message is not None:
            self.state["message"] = message
        self.emit(event_type)

    def start_avocado(self, category_id: str):
        category = self.content.category(category_id)
        if (
            not category
            or not category.get("enabled", True)
            or category_id not in self.settings.get("enabled_categories", [])
            or not category.get("answers")
        ):
            raise ValueError("That category is unavailable. Choose another one.")
        if self.state.get("break_mode"):
            self.session_started_at = time.time()
            self.break_prompted = False
        self.avocado = AvocadoGame(category, self.settings.get("retries", 1))
        self.memory = None
        self.session_started_at = self.session_started_at or time.time()
        self.state.update({
            "screen": "avocado",
            "activity": "avocado",
            "game": "avocado",
            "game_state": "child_turn",
            "category_id": category_id,
            "category_name": category["name"],
            "used_answers": [],
            "nickname": None,
            "pending_answer": None,
            "paused": False,
            "break_mode": False,
            "locked": False,
        })
        self.emit(CATEGORY_SELECTED, {"category_id": category_id})
        self.emit(GAME_STARTED, {"game": "avocado"})
        self.state["message"] = f"Avocado, avocado! Let's name {category['name'].lower()}."
        self.speak(self.state["message"])
        self.emit(TURN_STARTED, {"turn": "child"})

    def end_round(self, summary: str = "That was a brilliant round."):
        nickname = None
        if self.avocado:
            self.avocado.state = "ended"
        names = self.content.nicknames()
        enabled_names = self.settings.get("enabled_nicknames")
        if not self.settings.get("nicknames_enabled", True):
            names = []
        elif enabled_names is not None:
            names = [name for name in names if name in enabled_names]
        if names:
            import random
            nickname = random.SystemRandom().choice(names)
        self.state.update({
            "screen": "nickname" if nickname else "round-complete",
            "game_state": "ended",
            "nickname": nickname,
            "pending_answer": None,
            "message": f"{summary} You're {nickname}!" if nickname else summary,
        })
        self.record_history(str(self.state.get("activity") or "game"), self.state["message"])
        self.emit(ROUND_ENDED, {"used_answers": self.state["used_answers"]})
        if nickname:
            self.emit(NICKNAME_ASSIGNED, {"nickname": nickname})
        self.speak(self.state["message"])

    def handle_avocado_answer(self, text: str) -> dict:
        if not self.avocado or self.state["game"] != "avocado":
            raise ValueError("Start an Avocado round first.")
        if self.state["paused"] or self.state["locked"]:
            raise ValueError("The game is paused.")
        if not isinstance(text, str) or not text.strip() or len(text) > 100:
            raise ValueError("Please enter a short answer.")
        self.emit(ANSWER_HEARD, {"source": "manual-parent-assist", "text": text[:100]})
        result = self.avocado.submit(text)
        if result["status"] == "confirm":
            self.state.update({
                "screen": "confirmation",
                "pending_answer": result["answer"],
                "game_state": "confirmation",
                "message": f"Did you say {result['answer']}?",
            })
            self.emit(ANSWER_CONFIRMATION_REQUIRED, {"answer": result["answer"], "confidence": result["confidence"]})
            self.speak(self.state["message"])
            return result
        if result["status"] == "repeat":
            self.state.update({"screen": "avocado", "message": "You already told me that one. Say another!"})
            self.emit(ANSWER_REPEATED, {"answer": result["answer"]})
            retry = self.avocado.retry_or_end(self.content.nicknames())
            if retry["status"] == "retry":
                self.emit(RETRY_GRANTED, {"remaining": retry["remaining"]})
            else:
                self.end_round("Good try. That was a brilliant round.")
            self.speak(self.state["message"])
            return result
        if result["status"] != "accepted":
            self.state.update({"screen": "avocado", "message": "Good try. Let's try another answer."})
            retry = self.avocado.retry_or_end(self.content.nicknames())
            if retry["status"] == "retry":
                self.emit(RETRY_GRANTED, {"remaining": retry["remaining"]})
            else:
                self.end_round()
            self.speak(self.state["message"])
            return result
        self.state["used_answers"] = self.avocado.summary()
        self.emit(ANSWER_ACCEPTED, {"answer": result["answer"]})
        self.state["message"] = f"Lovely answer: {result['answer']}!"
        next_answer = self.avocado.application_answer()
        if next_answer is None:
            self.end_round("We used all the answers. You did a brilliant job.")
            return {"status": "accepted", "answer": result["answer"], "round_ended": True}
        self.state["used_answers"] = self.avocado.summary()
        self.state["message"] = f"I'll say {next_answer}. Your turn!"
        self.speak(self.state["message"])
        self.state["screen"] = "avocado"
        self.state["game_state"] = "child_turn"
        self.emit(TURN_STARTED, {"turn": "child", "application_answer": next_answer})
        return {"status": "accepted", "answer": result["answer"], "application_answer": next_answer}

    def handle_memory_start(self, category_id: str):
        category = self.content.memory_category(category_id)
        if not category or category_id not in self.settings.get("memory_categories", []):
            raise ValueError("That memory category is unavailable.")
        if self.state.get("break_mode"):
            self.session_started_at = time.time()
            self.break_prompted = False
        self.memory = MemoryGame(
            category, self.settings.get("memory_level", 1), self.settings.get("retries", 1)
        )
        sequence = self.memory.start()
        if not sequence:
            raise ValueError("There are no items in this category yet.")
        self.avocado = None
        self.state.update({
            "screen": "memory",
            "activity": "memory",
            "game": "memory",
            "game_state": "child_turn",
            "category_id": category_id,
            "category_name": category["name"],
            "used_answers": [],
            "nickname": None,
            "pending_answer": None,
            "message": "I went to the shop and bought " + ", ".join(sequence) + ". Now it is your turn!",
            "memory_sequence": sequence,
            "memory_picture_visible": self.memory.picture_visible,
        })
        self.emit(GAME_STARTED, {"game": "memory", "level": self.memory.level})
        self.speak(self.state["message"])

    def handle_memory_answer(self, text: str):
        if not self.memory or not isinstance(text, str) or len(text) > 300:
            raise ValueError("Start a Memory Chain round and enter a short sequence.")
        items = [part.strip() for part in text.split(",") if part.strip()]
        result = self.memory.check(items)
        if result["status"] in {"continue", "ended"}:
            self.state["memory_sequence"] = result["sequence"]
            self.state["memory_picture_visible"] = self.memory.picture_visible
            if result["status"] == "ended":
                self.state["game_state"] = "ended"
                self.state["screen"] = "round-complete"
                self.state["message"] = "You remembered and added to the whole list. Brilliant listening!"
                self.record_history("memory", self.state["message"])
                self.emit(ROUND_ENDED, {"game": "memory", "status": "completed"})
            else:
                self.state["game_state"] = "child_turn"
                self.state["screen"] = "memory"
                self.state["message"] = "Brilliant! I added " + result["app_added"] + ". Now say the whole list and add one more."
                self.emit(TURN_STARTED, {"turn": "child", "application_added": result["app_added"]})
            self.speak(self.state["message"])
            return result
        if self.memory.retries_left > 0:
            retry = self.memory.use_retry()
            self.state["message"] = "Good try. Let's listen to the list once more."
            self.state["memory_picture_visible"] = self.memory.picture_visible
            self.emit(RETRY_GRANTED, retry)
        else:
            self.memory.state = "ended"
            self.state.update({"game_state": "ended", "screen": "round-complete", "message": "You had a lovely go. Let's play again!"})
            self.record_history("memory", self.state["message"])
            self.emit(ROUND_ENDED, {"game": "memory", "status": result["reason"]})
        self.speak(self.state["message"])
        return result


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=None,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=SECURE_COOKIE,
        PERMANENT_SESSION_LIFETIME=1800,
        MAX_CONTENT_LENGTH=32 * 1024,
        DATA_DIR=DATA_DIR,
        CONTENT_DIR=CONTENT_DIR,
        SETTINGS=SETTINGS,
        TESTING=False,
    )
    if overrides:
        app.config.update(overrides)
    data_dir = Path(app.config["DATA_DIR"]).resolve()
    content_dir = Path(app.config["CONTENT_DIR"]).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    app.secret_key = app.config["SECRET_KEY"] or _secret_key(data_dir)
    database = Database(data_dir / "kid-learning-tv.sqlite3")
    content = ContentStore(content_dir)
    content.validate_all()
    runtime = Runtime(database, content, app.config["SETTINGS"])
    app.extensions["klt_db"] = database
    app.extensions["klt_runtime"] = runtime
    app.extensions["klt_content"] = content

    @app.before_request
    def request_size_limit():
        request.max_content_length = 256 * 1024 * 1024 if request.path == "/api/parent/media/upload" else 32 * 1024

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    def csrf_token():
        token = session.get("csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        return token

    def check_csrf():
        expected = session.get("csrf_token", "")
        supplied = request.headers.get("X-CSRF-Token", "")
        from hmac import compare_digest
        return bool(expected and supplied and compare_digest(expected, supplied))

    def parent_required(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            if not session.get("parent_authenticated"):
                return jsonify({"error": "Parent sign-in required."}), 401
            return fn(*args, **kwargs)
        return wrapped

    def protected_post(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            if not check_csrf():
                return jsonify({"error": "Security token expired. Reload the page and try again."}), 400
            if not session.get("parent_authenticated"):
                return jsonify({"error": "Parent sign-in required."}), 401
            return fn(*args, **kwargs)
        return wrapped

    def serialized(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            with runtime.lock:
                return fn(*args, **kwargs)
        return wrapped

    @app.errorhandler(RequestEntityTooLarge)
    def oversized(_error):
        return jsonify({"error": "Request is too large."}), 413

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "That local resource was not found."}), 404

    @app.errorhandler(ContentError)
    def content_error(error):
        return jsonify({"error": str(error)}), 400

    @app.get("/")
    def tv():
        token = csrf_token()
        return render_template("tv.html", csrf_token=token)

    @app.get("/parent")
    def parent():
        token = csrf_token()
        return render_template(
            "parent.html",
            csrf_token=token,
            configured=database.get_pin_hash() is not None,
        )

    @app.get("/api/state")
    def child_state():
        return jsonify(runtime.snapshot())

    @app.post("/api/child/action")
    @serialized
    def child_action():
        body = request.get_json(silent=True) or {}
        action = body.get("action")
        if runtime.state["locked"]:
            return jsonify({"error": "A grown-up will be right back."}), 423
        if runtime.learning_game and action not in {
            "learning_answer", "learning_settle", "session_break", "session_reminder",
        }:
            return jsonify({"error": "A grown-up chooses when to change this activity."}), 423
        if action in {"learning_answer", "learning_settle"}:
            if not runtime.learning_game or runtime.state["screen"] != "learning":
                raise ValueError("No learning activity is ready to play.")
            if runtime.state["paused"]:
                return jsonify({"error": "The activity is paused by a grown-up."}), 423
            if action == "learning_answer":
                runtime.learning_game.answer(body)
                runtime.update_learning()
                if runtime.learning_game.completed:
                    runtime.record_history(runtime.learning_game.activity_id, runtime.learning_game.message)
            elif runtime.learning_game.settle(body):
                runtime.update_learning()
        elif action == "start_avocado":
            runtime.start_avocado(body.get("category_id", ""))
        elif action == "answer":
            runtime.handle_avocado_answer(body.get("text", ""))
        elif action == "start_memory":
            runtime.handle_memory_start(body.get("category_id", "shopping"))
        elif action == "memory_answer":
            runtime.handle_memory_answer(body.get("text", ""))
        elif action == "hide_memory_pictures":
            if runtime.memory:
                runtime.memory.hide_pictures()
                runtime.state["memory_picture_visible"] = False
                runtime.emit("MEMORY_PICTURES_HIDDEN")
        elif action == "activity":
            prompt = next((item for item in runtime.content.prompts() if item["id"] == body.get("prompt_id")), None)
            if not prompt:
                raise ValueError("That activity prompt is unavailable.")
            runtime.state.update({
                "screen": "activity", "activity": prompt["name"], "game": None,
                "game_state": "active", "message": prompt["prompt"],
                "activity_image": prompt.get("image"),
            })
            runtime.session_started_at = runtime.session_started_at or time.time()
            runtime.emit(ACTIVITY_SELECTED, {"activity": prompt["name"]})
            runtime.speak(prompt["prompt"])
        elif action == "home":
            if runtime.state.get("break_mode"):
                runtime.session_started_at = time.time()
                runtime.break_prompted = False
            runtime.avocado = None
            runtime.memory = None
            runtime.state.update({
                "screen": "home", "activity": None, "game": None, "game_state": "idle",
                "category_id": None, "category_name": None, "used_answers": [],
                "pending_answer": None, "nickname": None, "break_mode": False,
                "message": "Choose a fun activity.",
            })
            runtime.emit("RETURNED_HOME")
        elif action == "rocky_request":
            runtime.state.update({
                "screen": "ask-rocky", "activity": "Ask Rocky", "game": None,
                "game_state": "request-open", "rocky_request_open": True,
                "rocky_message_pending": True,
                "rocky_reply": None,
                "message": "Rocky is busy right now. Leave a message after the beep, and Rocky will get back to you.",
            })
            runtime.emit("ROCKY_REQUEST_OPENED")
            runtime.speak(runtime.state["message"])
        elif action in {"rocky_close", "rocky_done"}:
            runtime.state.update({
                "screen": "home", "activity": None, "game_state": "idle",
                "rocky_request_open": False,
                "message": "Thanks! Rocky will get back to you.",
            })
            runtime.emit("ROCKY_REQUEST_CLOSED")
        elif action == "video_ended":
            if runtime.state.get("screen") != "video" or body.get("media_id") != runtime.state.get("media_id"):
                raise ValueError("No matching video is playing.")
            runtime.state.update({
                "screen": "home", "activity": None, "game_state": "completed",
                "media_id": None, "media_title": None, "media_command": "stop",
                "message": "That was fun! What shall we do next?",
            })
            runtime.emit("MEDIA_ENDED")
        elif action == "session_break":
            runtime.break_prompted = True
            runtime.state.update({
                "screen": "break", "break_mode": True, "game_state": "break",
                "message": "Let's take a little break. Stretch and have a drink of water.",
            })
            runtime.emit(ACTIVITY_SELECTED, {"activity": "break"})
            runtime.speak(runtime.state["message"])
        elif action == "session_reminder":
            if not runtime.break_prompted:
                runtime.break_prompted = True
                runtime.state.update({
                    "screen": "break", "break_mode": True, "game_state": "break",
                    "message": "How about a little stretch and a drink of water?",
                })
                runtime.emit(ACTIVITY_SELECTED, {"activity": "break reminder"})
                runtime.speak(runtime.state["message"])
        else:
            raise ValueError("Unknown child action.")
        return jsonify({"ok": True, "state": runtime.snapshot()})

    @app.get("/api/events")
    def child_events():
        try:
            after = max(0, int(request.headers.get("Last-Event-ID", "0")))
        except ValueError:
            after = 0
        return Response(runtime.bus.stream(after), mimetype="text/event-stream")

    @app.post("/api/setup")
    def setup_parent():
        if not check_csrf():
            return jsonify({"error": "Reload the page and try again."}), 400
        if database.get_pin_hash() is not None:
            return jsonify({"error": "Parent PIN is already configured."}), 409
        pin = (request.get_json(silent=True) or {}).get("pin")
        if not valid_pin(pin):
            return jsonify({"error": "Choose a PIN with 6 to 12 digits."}), 400
        database.set_pin_hash(hash_pin(pin))
        database.record_attempt(True)
        session.clear()
        session.permanent = True
        session["parent_authenticated"] = True
        csrf_token()
        return jsonify({"ok": True, "csrf_token": session["csrf_token"]})

    @app.post("/api/login")
    def login():
        if not check_csrf():
            return jsonify({"error": "Reload the page and try again."}), 400
        now = int(time.time())
        if database.attempts_since(now - 300) >= 5:
            return jsonify({"error": "Too many attempts. Wait five minutes, then try again."}), 429
        pin = (request.get_json(silent=True) or {}).get("pin")
        stored = database.get_pin_hash()
        succeeded = bool(stored and isinstance(pin, str) and verify_pin(pin, stored))
        database.record_attempt(succeeded)
        if not succeeded:
            return jsonify({"error": "That PIN did not match."}), 401
        session.clear()
        session.permanent = True
        session["parent_authenticated"] = True
        csrf_token()
        return jsonify({"ok": True, "csrf_token": session["csrf_token"]})

    @app.post("/api/logout")
    @protected_post
    def logout():
        session.clear()
        return jsonify({"ok": True})

    @app.get("/api/parent/state")
    @parent_required
    def parent_state():
        port = request.environ.get("SERVER_PORT", str(PORT))
        local_url = f"http://{socket.gethostname()}.local:{port}/parent"
        return jsonify({
            "state": runtime.snapshot(),
            "settings": runtime.settings,
            "hostname": socket.gethostname(),
            "configured_url": local_url,
            "history_enabled": runtime.settings.get("history_enabled", False),
            "learning_catalog": list(ACTIVITIES),
        })

    @app.get("/api/parent/qr")
    @parent_required
    def parent_qr():
        try:
            import qrcode
            from qrcode.image.svg import SvgPathImage
        except ImportError:
            return jsonify({"error": "Install the optional qrcode package to generate a QR code."}), 503
        url = f"http://{socket.gethostname()}.local:{request.host.split(':')[-1]}/parent"
        image = qrcode.make(url, image_factory=SvgPathImage, border=2)
        from io import BytesIO
        output = BytesIO()
        image.save(output)
        return Response(output.getvalue(), mimetype="image/svg+xml")

    @app.get("/api/parent/events")
    @parent_required
    def parent_events():
        return child_events()

    @app.post("/api/parent/action")
    @protected_post
    @serialized
    def parent_action():
        body = request.get_json(silent=True) or {}
        action = body.get("action")
        state = runtime.state
        was_learning = runtime.learning_game is not None
        if action == "start_learning":
            runtime.start_learning(body.get("activity_id"))
        elif action == "learning_enabled":
            activity_id = body.get("activity_id")
            enabled = body.get("enabled")
            validate_enabled([activity_id])
            if not isinstance(enabled, bool):
                raise ValueError("Activity availability must be true or false.")
            ids = list(runtime.settings.get("enabled_learning_activities", []))
            if enabled and activity_id not in ids:
                ids.append(activity_id)
            elif not enabled and activity_id in ids:
                ids.remove(activity_id)
            runtime.settings["enabled_learning_activities"] = ids
            database.set("preferences", runtime.settings)
            if not enabled and runtime.learning_game and runtime.learning_game.activity_id == activity_id:
                runtime.learning_game = None
                state.update({
                    "screen": "locked" if state["locked"] else "home",
                    "activity": None, "game": None, "game_state": "idle",
                    "paused": False, "break_mode": False,
                    "message": "A grown-up is choosing the next activity.",
                })
            runtime.emit("LEARNING_LIBRARY_CHANGED")
        elif action == "start_avocado":
            runtime.start_avocado(body.get("category_id", ""))
        elif action == "start_memory":
            runtime.handle_memory_start(body.get("category_id", "shopping"))
        elif action == "answer":
            runtime.handle_avocado_answer(body.get("text", ""))
        elif action == "memory_answer":
            runtime.handle_memory_answer(body.get("text", ""))
        elif action == "accept_answer":
            if not runtime.avocado:
                raise ValueError("There is no answer awaiting confirmation.")
            result = runtime.avocado.resolve_pending(True)
            runtime.state["pending_answer"] = None
            runtime.state["screen"] = "avocado"
            runtime.state["game_state"] = "child_turn"
            if result["status"] == "accepted":
                runtime.state["used_answers"] = runtime.avocado.summary()
                runtime.emit(ANSWER_ACCEPTED, {"answer": result["answer"], "parent_confirmed": True})
                answer = runtime.avocado.application_answer()
                if answer is None:
                    runtime.end_round("We used all the answers. You did a brilliant job.")
                else:
                    runtime.state["used_answers"] = runtime.avocado.summary()
                    runtime.state["message"] = f"I'll say {answer}. Your turn!"
                    runtime.speak(runtime.state["message"])
                    runtime.emit(TURN_STARTED, {"turn": "child", "application_answer": answer})
            elif result["status"] == "repeat":
                runtime.state["message"] = "You already used that one. Let's try another."
                runtime.emit(ANSWER_REPEATED, {"answer": result["answer"]})
                retry = runtime.avocado.retry_or_end(runtime.content.nicknames())
                if retry["status"] == "retry":
                    runtime.emit(RETRY_GRANTED, retry)
                else:
                    runtime.end_round()
        elif action == "reject_answer":
            if not runtime.avocado:
                raise ValueError("There is no answer awaiting confirmation.")
            runtime.avocado.resolve_pending(False)
            runtime.state.update({"pending_answer": None, "screen": "avocado", "game_state": "child_turn"})
            retry = runtime.avocado.retry_or_end(runtime.content.nicknames())
            runtime.state["message"] = "I heard something different. Can you say it again?"
            runtime.emit(ANSWER_REJECTED)
            if retry["status"] == "retry":
                runtime.emit(RETRY_GRANTED, retry)
            else:
                runtime.end_round()
            runtime.speak(runtime.state["message"])
        elif action == "correct_answer":
            if not runtime.avocado:
                raise ValueError("There is no answer awaiting confirmation.")
            result = runtime.avocado.resolve_pending(False, body.get("text", ""))
            runtime.state.update({"pending_answer": None, "screen": "avocado", "game_state": "child_turn"})
            if result["status"] == "accepted":
                runtime.state["used_answers"] = runtime.avocado.summary()
                runtime.emit(ANSWER_ACCEPTED, {"answer": result["answer"], "parent_corrected": True})
                answer = runtime.avocado.application_answer()
                if answer is None:
                    runtime.end_round("We used all the answers. You did a brilliant job.")
                else:
                    runtime.state["used_answers"] = runtime.avocado.summary()
                    runtime.state["message"] = f"I'll say {answer}. Your turn!"
                    runtime.speak(runtime.state["message"])
                    runtime.emit(TURN_STARTED, {"turn": "child", "application_answer": answer})
            elif result["status"] == "repeat":
                runtime.state["message"] = "You already used that one. Let's try another."
                runtime.emit(ANSWER_REPEATED, {"answer": result["answer"]})
                retry = runtime.avocado.retry_or_end(runtime.content.nicknames())
                if retry["status"] == "retry":
                    runtime.emit(RETRY_GRANTED, retry)
                else:
                    runtime.end_round()
            else:
                raise ValueError("The correction was not in this category.")
        elif action in {"retry", "skip_turn"}:
            if not runtime.avocado:
                raise ValueError("Start an Avocado round first.")
            if action == "skip_turn":
                answer = runtime.avocado.application_answer()
                if answer is None:
                    runtime.end_round("We used all the answers. You did a brilliant job.")
                    return jsonify({"ok": True, "state": runtime.snapshot()})
                runtime.state["used_answers"] = runtime.avocado.summary()
                runtime.state.update({"screen": "avocado", "game_state": "child_turn", "message": f"I'll say {answer}. Your turn!"})
                runtime.emit(TURN_STARTED, {"turn": "child", "application_answer": answer})
                return jsonify({"ok": True, "state": runtime.snapshot()})
            result = runtime.avocado.retry_or_end(runtime.content.nicknames())
            if result["status"] == "retry":
                runtime.state.update({"screen": "avocado", "game_state": "child_turn", "message": "Let's try together!"})
                runtime.emit(RETRY_GRANTED, result)
            else:
                runtime.end_round()
        elif action == "pause":
            state["paused"] = True
            if runtime.learning_game:
                state["game_state"] = "paused"
            runtime.update(GAME_PAUSED, "The game is paused.")
        elif action == "resume":
            state["paused"] = False
            if runtime.learning_game:
                if state.get("break_mode"):
                    runtime.session_started_at = time.time()
                    runtime.break_prompted = False
                state.update({"screen": "learning", "break_mode": False})
                state["game_state"] = "completed" if runtime.learning_game.completed else "active"
            runtime.update(GAME_RESUMED, runtime.learning_game.message if runtime.learning_game else "Ready when you are!")
        elif action == "home":
            if state.get("break_mode"):
                runtime.session_started_at = time.time()
                runtime.break_prompted = False
            runtime.avocado = None
            runtime.memory = None
            runtime.state.update({
                "screen": "home", "activity": None, "game": None, "game_state": "idle",
                "category_id": None, "category_name": None, "used_answers": [],
                "pending_answer": None, "nickname": None, "paused": False, "break_mode": False,
                "media_id": None, "media_title": None,
                "message": "Hello! Choose a fun activity.",
            })
            runtime.emit("RETURNED_HOME")
        elif action == "play_video":
            media_id = body.get("media_id")
            media = database.get_media(media_id) if isinstance(media_id, str) else None
            if not media:
                raise ValueError("That local video is unavailable.")
            runtime.state.update({
                "screen": "video", "activity": "Video", "game": None, "game_state": "playing",
                "media_id": media["id"], "media_title": media["title"], "media_command": "play",
                "media_command_seq": int(state.get("media_command_seq", 0)) + 1,
                "media_position": 0, "message": f"Now playing {media['title']}.",
            })
            runtime.emit("MEDIA_PLAY", {"media_id": media["id"]})
        elif action in {"media_pause", "media_play", "media_stop"}:
            if state.get("screen") != "video":
                raise ValueError("There is no video playing.")
            command = action.removeprefix("media_")
            runtime.state["media_command"] = command
            runtime.state["media_command_seq"] = int(state.get("media_command_seq", 0)) + 1
            runtime.state["game_state"] = "stopped" if command == "stop" else ("paused" if command == "pause" else "playing")
            if command == "stop":
                runtime.state.update({"screen": "home", "activity": None, "media_id": None, "media_title": None})
            runtime.emit("MEDIA_" + command.upper())
        elif action == "media_seek":
            seconds = body.get("seconds")
            if state.get("screen") != "video" or not isinstance(seconds, (int, float)) or not 0 <= seconds <= 86400:
                raise ValueError("Choose a valid position in the current video.")
            runtime.state.update({
                "media_command": "seek", "media_position": float(seconds),
                "media_command_seq": int(state.get("media_command_seq", 0)) + 1,
            })
            runtime.emit("MEDIA_SEEK", {"seconds": float(seconds)})
        elif action == "reset":
            if runtime.learning_game:
                runtime.start_learning(runtime.learning_game.activity_id)
            elif state.get("game") == "avocado" and state.get("category_id"):
                runtime.start_avocado(state["category_id"])
            elif state.get("game") == "memory" and state.get("category_id"):
                runtime.handle_memory_start(state["category_id"])
            else:
                raise ValueError("There is no active game to reset.")
        elif action == "end_round":
            runtime.end_round()
        elif action == "lock":
            state["locked"] = True
            state["screen"] = "locked"
            state["message"] = "A grown-up will be right back."
            runtime.emit(SCREEN_LOCKED)
        elif action == "unlock":
            state["locked"] = False
            state["screen"] = "learning" if runtime.learning_game else "home"
            state["message"] = runtime.learning_game.message if runtime.learning_game else "Ready for another fun activity?"
            runtime.emit(SCREEN_UNLOCKED)
        elif action == "break":
            state["break_mode"] = True
            state["screen"] = "break"
            state["message"] = "Let's take a little break. Stretch and have a drink of water."
            runtime.emit(ACTIVITY_SELECTED, {"activity": "break"})
            runtime.speak(state["message"])
        elif action == "set_volume":
            value = body.get("volume")
            if type(value) is not int or not 0 <= value <= 100:
                raise ValueError("Volume must be between 0 and 100.")
            state["volume"] = value
            runtime.settings["volume"] = value
            runtime.db.set("preferences", runtime.settings)
            runtime.emit("VOLUME_CHANGED", {"volume": value})
        elif action == "mute":
            muted = body.get("muted")
            if not isinstance(muted, bool):
                raise ValueError("Mute must be true or false.")
            state["muted"] = muted
            runtime.settings["muted"] = muted
            runtime.db.set("preferences", runtime.settings)
            runtime.emit("MUTE_CHANGED", {"muted": muted})
        elif action == "stop_speech":
            runtime.tts.stop()
            return jsonify({"ok": True, "state": runtime.snapshot()})
        elif action == "test_voice":
            if not runtime.tts.available():
                raise ValueError("eSpeak NG is not installed. Install espeak-ng to test offline speech.")
            runtime.tts.say("Hello! This is the offline voice test.", runtime.settings.get("tts_voice", "en-gb"), int(runtime.settings.get("speech_rate", 145)), state["volume"])
            return jsonify({"ok": True, "state": runtime.snapshot(), "message": "Offline voice test started."})
        elif action == "activity":
            prompt_id = body.get("prompt_id")
            prompt = next((item for item in runtime.content.prompts() if item["id"] == prompt_id), None)
            if not prompt:
                raise ValueError("That activity prompt is unavailable.")
            state.update({
                "screen": "activity", "activity": prompt["name"], "game": None,
                "game_state": "active", "message": prompt["prompt"], "nickname": None,
                "activity_image": prompt.get("image"),
            })
            runtime.emit(ACTIVITY_SELECTED, {"activity": prompt["name"], "prompt_id": prompt_id})
            runtime.speak(prompt["prompt"])
        elif action == "rocky_request":
            runtime.state.update({
                "screen": "ask-rocky", "activity": "Ask Rocky", "game": None,
                "game_state": "request-open", "rocky_request_open": True,
                "rocky_reply": None,
                "message": "Rocky is busy right now. Leave a message after the beep, and Rocky will get back to you.",
            })
            runtime.emit("ROCKY_REQUEST_OPENED")
        elif action == "rocky_close":
            runtime.state.update({
                "screen": "home", "activity": None, "game_state": "idle",
                "rocky_request_open": False,
                "message": "Thanks! Rocky will get back to you.",
            })
            runtime.emit("ROCKY_REQUEST_CLOSED")
        elif action == "rocky_reply":
            reply = body.get("text")
            if not isinstance(reply, str) or not reply.strip() or len(reply) > 240:
                raise ValueError("Enter a short message for the child.")
            runtime.state.update({
                "screen": "ask-rocky", "activity": "Ask Rocky",
                "game_state": "reply", "rocky_request_open": False,
                "rocky_message_pending": False,
                "rocky_reply": reply.strip(),
                "message": "Rocky says: " + reply.strip(),
            })
            runtime.emit("ROCKY_REPLIED")
            runtime.speak(runtime.state["message"])
        elif action == "settings":
            changes = body.get("settings")
            if not isinstance(changes, dict) or set(changes) - {
                "session_minutes", "break_reminder_minutes", "retries", "voice_enabled",
                "speech_rate", "tts_voice", "memory_level", "memory_picture_seconds",
                "enabled_categories", "enabled_nicknames", "history_enabled", "low_animation",
                "nicknames_enabled", "memory_categories",
            }:
                raise ValueError("One or more settings are not supported.")
            for key, value in changes.items():
                bounds = {
                    "session_minutes": (0, 240), "break_reminder_minutes": (0, 240),
                    "retries": (0, 5), "speech_rate": (100, 200),
                    "memory_level": (1, 3), "memory_picture_seconds": (0, 60),
                }
                if key in bounds:
                    minimum, maximum = bounds[key]
                    if type(value) is not int or not minimum <= value <= maximum:
                        raise ValueError(f"Invalid value for {key}.")
                elif key in {"voice_enabled", "history_enabled", "low_animation", "nicknames_enabled"} and not isinstance(value, bool):
                    raise ValueError(f"Invalid value for {key}.")
                elif key == "tts_voice" and value not in {"en-gb", "en-us", "en"}:
                    raise ValueError("Unsupported local speech voice.")
                elif key in {"enabled_categories", "enabled_nicknames", "memory_categories"} and (
                    not isinstance(value, list) or len(value) > 200 or any(not isinstance(item, str) for item in value)
                ):
                    raise ValueError(f"Invalid list for {key}.")
            valid_category_ids = {item["id"] for item in content.categories()}
            if "enabled_categories" in changes and set(changes["enabled_categories"]) - valid_category_ids:
                raise ValueError("The category list contains an unknown category.")
            valid_names = set(content.nicknames())
            if "enabled_nicknames" in changes and set(changes["enabled_nicknames"]) - valid_names:
                raise ValueError("The nickname list contains an unknown nickname.")
            if "memory_categories" in changes:
                memory_dir = content.root / "memory"
                valid_memories = {path.stem for path in memory_dir.glob("*.json")}
                if set(changes["memory_categories"]) - valid_memories:
                    raise ValueError("The memory category list contains an unknown category.")
            runtime.settings.update(changes)
            runtime.db.set("preferences", runtime.settings)
            runtime.emit("SETTINGS_CHANGED", changes)
        else:
            raise ValueError("Unknown parent action.")
        if was_learning and action in {
            "start_avocado", "start_memory", "home", "play_video", "end_round",
            "activity", "rocky_request", "rocky_close", "rocky_reply",
        }:
            runtime.learning_game = None
            runtime.emit("LEARNING_CLOSED")
        return jsonify({"ok": True, "state": runtime.snapshot()})

    @app.post("/api/parent/categories")
    @protected_post
    def save_category():
        value = request.get_json(silent=True)
        if not isinstance(value, dict):
            return jsonify({"error": "Expected a category JSON object."}), 400
        content.save_category(value)
        runtime.emit("CONTENT_CHANGED", {"category_id": value["id"]})
        return jsonify({"ok": True})

    @app.get("/api/parent/categories")
    @parent_required
    def get_categories():
        return jsonify({"categories": content.categories(), "nicknames": content.nickname_data()})

    @app.get("/api/parent/media")
    @parent_required
    def list_media():
        return jsonify({"videos": database.list_media()})

    @app.post("/api/parent/media/upload")
    @protected_post
    def upload_media():
        from werkzeug.utils import secure_filename
        uploaded = request.files.get("video")
        title = (request.form.get("title") or "").strip()
        if not uploaded or not title or len(title) > 100:
            return jsonify({"error": "Choose a video file and enter a title up to 100 characters."}), 400
        extension = Path(secure_filename(uploaded.filename or "")).suffix.lower()
        signatures = {".mp4": (4, b"ftyp"), ".webm": (0, b"\x1aE\xdf\xa3")}
        if extension not in signatures:
            return jsonify({"error": "Only parent-provided MP4 or WebM files are supported."}), 400
        offset, marker = signatures[extension]
        uploaded.stream.seek(offset)
        if uploaded.stream.read(len(marker)) != marker:
            return jsonify({"error": "The file signature does not match a supported video type."}), 400
        uploaded.stream.seek(0)
        media_id = secrets.token_hex(16)
        media_type = "video/mp4" if extension == ".mp4" else "video/webm"
        media_dir = data_dir / "media"
        media_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        target = media_dir / f"{media_id}{extension}"
        uploaded.save(target)
        try:
            target.chmod(0o600)
        except OSError:
            pass
        database.add_media(media_id, title, target.name, media_type)
        runtime.emit("MEDIA_LIBRARY_CHANGED", {"media_id": media_id})
        return jsonify({"ok": True, "video": {"id": media_id, "title": title, "media_type": media_type}})

    @app.delete("/api/parent/media/<media_id>")
    @parent_required
    def delete_media(media_id):
        if not check_csrf():
            return jsonify({"error": "Security token expired."}), 400
        media = database.get_media(media_id)
        if not media:
            return jsonify({"error": "Video was not found."}), 404
        if runtime.state.get("media_id") == media_id:
            return jsonify({"error": "Stop playback before removing this video."}), 409
        media_dir = (data_dir / "media").resolve()
        file_path = (media_dir / media["filename"]).resolve()
        if file_path.parent != media_dir:
            return jsonify({"error": "Stored video path is invalid."}), 400
        file_path.unlink(missing_ok=True)
        database.delete_media(media_id)
        runtime.emit("MEDIA_LIBRARY_CHANGED", {"media_id": media_id})
        return jsonify({"ok": True})

    @app.get("/api/media/<media_id>")
    def stream_media(media_id):
        import re
        from flask import send_file
        if not re.fullmatch(r"[a-f0-9]{32}", media_id):
            return jsonify({"error": "Video was not found."}), 404
        media = database.get_media(media_id)
        if not media:
            return jsonify({"error": "Video was not found."}), 404
        media_dir = (data_dir / "media").resolve()
        file_path = (media_dir / media["filename"]).resolve()
        if file_path.parent != media_dir or not file_path.is_file():
            return jsonify({"error": "Video was not found."}), 404
        return send_file(file_path, mimetype=media["media_type"], conditional=True, max_age=0)

    @app.post("/api/child/media-progress")
    def media_progress():
        body = request.get_json(silent=True) or {}
        seconds = body.get("seconds")
        if (
            runtime.state.get("screen") != "video"
            or body.get("media_id") != runtime.state.get("media_id")
            or not isinstance(seconds, (int, float))
            or not 0 <= seconds <= 86400
        ):
            return jsonify({"error": "Invalid video progress."}), 400
        runtime.state["media_position"] = float(seconds)
        runtime.bus.publish("MEDIA_PROGRESS", runtime.snapshot())
        return jsonify({"ok": True})

    @app.post("/api/child/video-ended")
    def video_ended():
        body = request.get_json(silent=True) or {}
        if runtime.state.get("screen") != "video" or body.get("media_id") != runtime.state.get("media_id"):
            return jsonify({"error": "No matching video is playing."}), 400
        runtime.state.update({
            "screen": "home", "activity": None, "game_state": "completed",
            "media_id": None, "media_title": None, "media_command": "stop",
            "media_command_seq": int(runtime.state.get("media_command_seq", 0)) + 1,
            "message": "That was fun! What shall we do next?",
        })
        runtime.emit("MEDIA_ENDED")
        return jsonify({"ok": True})

    @app.post("/api/parent/nicknames")
    @protected_post
    def save_nicknames():
        value = request.get_json(silent=True)
        if not isinstance(value, list) or len(value) > 100:
            return jsonify({"error": "Nickname list must contain at most 100 items."}), 400
        content.save_nicknames(value)
        runtime.emit("CONTENT_CHANGED", {"content": "nicknames"})
        return jsonify({"ok": True})

    @app.get("/api/parent/export")
    @parent_required
    def export_settings():
        response = jsonify({"version": 1, "settings": runtime.settings})
        response.headers["Content-Disposition"] = "attachment; filename=kid-learning-tv-settings.json"
        return response

    @app.post("/api/parent/import")
    @protected_post
    @serialized
    def import_settings():
        payload = request.get_json(silent=True) or {}
        values = payload.get("settings")
        allowed = {
            "session_minutes", "break_reminder_minutes", "retries", "volume", "muted",
            "voice_enabled", "tts_voice", "speech_rate", "stt_profile", "history_enabled",
            "low_animation", "reduced_assets", "memory_level", "memory_picture_seconds",
            "memory_categories", "enabled_categories", "enabled_nicknames", "nicknames_enabled",
            "enabled_learning_activities",
        }
        if (
            payload.get("version") != 1
            or not isinstance(values, dict)
            or len(values) > 40
            or set(values) - allowed
        ):
            return jsonify({"error": "Invalid settings export."}), 400
        if "enabled_learning_activities" in values:
            validate_enabled(values["enabled_learning_activities"])
            if runtime.learning_game and runtime.learning_game.activity_id not in values["enabled_learning_activities"]:
                raise ValueError("Return home before importing settings that disable the current activity.")
        if "enabled_categories" in values:
            valid_ids = {item["id"] for item in content.categories()}
            categories_value = values["enabled_categories"]
            if (
                not isinstance(categories_value, list)
                or any(not isinstance(item, str) for item in categories_value)
                or set(categories_value) - valid_ids
            ):
                return jsonify({"error": "Settings contain an unknown category."}), 400
        if "enabled_nicknames" in values and values["enabled_nicknames"] is not None:
            valid_names = set(content.nicknames())
            nickname_value = values["enabled_nicknames"]
            if (
                not isinstance(nickname_value, list)
                or any(not isinstance(item, str) for item in nickname_value)
                or set(nickname_value) - valid_names
            ):
                return jsonify({"error": "Settings contain an unknown nickname."}), 400
        numeric_bounds = {
            "session_minutes": (0, 240), "break_reminder_minutes": (0, 240),
            "retries": (0, 5), "volume": (0, 100), "speech_rate": (100, 200),
            "memory_level": (1, 3), "memory_picture_seconds": (0, 60),
        }
        for key, bounds in numeric_bounds.items():
            if key in values and (type(values[key]) is not int or not bounds[0] <= values[key] <= bounds[1]):
                return jsonify({"error": f"Invalid value for {key}."}), 400
        for key in ("muted", "voice_enabled", "history_enabled", "low_animation", "reduced_assets", "nicknames_enabled"):
            if key in values and not isinstance(values[key], bool):
                return jsonify({"error": f"Invalid value for {key}."}), 400
        if "memory_categories" in values:
            memory_ids = {path.stem for path in (content.root / "memory").glob("*.json")}
            memory_value = values["memory_categories"]
            if (
                not isinstance(memory_value, list)
                or any(not isinstance(item, str) for item in memory_value)
                or set(memory_value) - memory_ids
            ):
                return jsonify({"error": "Settings contain an unknown memory category."}), 400
        if "stt_profile" in values and (
            not isinstance(values["stt_profile"], str)
            or values["stt_profile"] not in {"no-stt", "very-low-resource", "balanced", "manual-parent-assist"}
        ):
            return jsonify({"error": "Unsupported speech-input profile."}), 400
        if "tts_voice" in values and (
            not isinstance(values["tts_voice"], str)
            or values["tts_voice"] not in {"en-gb", "en-us", "en"}
        ):
            return jsonify({"error": "Unsupported local speech voice."}), 400
        runtime.settings.update(values)
        runtime.state["volume"] = int(runtime.settings.get("volume", runtime.state["volume"]))
        runtime.state["muted"] = bool(runtime.settings.get("muted", runtime.state["muted"]))
        runtime.db.set("preferences", runtime.settings)
        runtime.emit("SETTINGS_CHANGED")
        return jsonify({"ok": True})

    @app.post("/api/parent/history/delete")
    @protected_post
    def delete_history():
        if (request.get_json(silent=True) or {}).get("confirmation") != "DELETE":
            return jsonify({"error": "Type DELETE to confirm."}), 400
        database.delete_history()
        runtime.emit("HISTORY_DELETED")
        return jsonify({"ok": True})

    @app.post("/api/parent/pin")
    @protected_post
    def change_pin():
        body = request.get_json(silent=True) or {}
        old_pin, new_pin = body.get("old_pin"), body.get("new_pin")
        stored = database.get_pin_hash()
        if not stored or not isinstance(old_pin, str) or not verify_pin(old_pin, stored):
            return jsonify({"error": "Current PIN did not match."}), 401
        if not valid_pin(new_pin):
            return jsonify({"error": "Choose a new PIN with 6 to 12 digits."}), 400
        database.set_pin_hash(hash_pin(new_pin))
        return jsonify({"ok": True})

    @app.get("/api/parent/backup")
    @parent_required
    def download_backup():
        from io import BytesIO
        import sqlite3
        output = BytesIO()
        backup_path = data_dir / f".download-{secrets.token_hex(8)}.sqlite3"
        descriptor = os.open(backup_path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        os.close(descriptor)
        source = sqlite3.connect(database.path)
        target = sqlite3.connect(backup_path)
        try:
            source.backup(target)
            target.close()
            source.close()
            output.write(backup_path.read_bytes())
            output.seek(0)
        finally:
            target.close()
            source.close()
            backup_path.unlink(missing_ok=True)
        return Response(
            output.getvalue(), mimetype="application/vnd.sqlite3",
            headers={"Content-Disposition": "attachment; filename=kid-learning-tv-backup.sqlite3"},
        )

    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "database": database.path.exists(),
            "stt": "manual-parent-assist",
            "tts_available": runtime.tts.available(),
            "uptime_seconds": int(time.time() - runtime.started_at),
        })

    @app.errorhandler(ValueError)
    def bad_request(error):
        return jsonify({"error": str(error)}), 400

    return app


app = create_app()


def main():
    try:
        from waitress import serve
        serve(app, host=HOST, port=PORT, threads=6, channel_timeout=30)
    except ImportError:
        app.run(host=HOST, port=PORT, threaded=True, debug=False)


if __name__ == "__main__":
    main()
