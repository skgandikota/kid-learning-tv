"""Small SQLite persistence layer for parent credentials and appliance state."""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    def connect(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def connection(self):
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def migrate(self):
        with self.connection() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS auth (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    pin_hash TEXT NOT NULL,
                    changed_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attempted_at INTEGER NOT NULL,
                    succeeded INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS activity_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at INTEGER NOT NULL,
                    activity TEXT NOT NULL,
                    summary TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS media_assets (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                """
            )

    def get(self, key: str, default=None):
        with self.connection() as db:
            row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return json.loads(row["value"]) if row else default

    def set(self, key: str, value):
        with self.connection() as db:
            db.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value)),
            )

    def record_event(self, event_type: str, payload: dict):
        with self.connection() as db:
            db.execute(
                "INSERT INTO events(created_at, event_type, payload) VALUES(?, ?, ?)",
                (int(time.time()), event_type, json.dumps(payload)),
            )
            db.execute("DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 500)")

    def add_history(self, activity: str, summary: str):
        with self.connection() as db:
            db.execute(
                "INSERT INTO activity_history(created_at, activity, summary) VALUES(?, ?, ?)",
                (int(time.time()), activity[:40], summary[:240]),
            )

    def delete_history(self):
        with self.connection() as db:
            db.execute("DELETE FROM activity_history")
            db.execute("DELETE FROM events")

    def attempts_since(self, timestamp: int) -> int:
        with self.connection() as db:
            row = db.execute(
                "SELECT COUNT(*) AS count FROM login_attempts WHERE attempted_at >= ? AND succeeded = 0",
                (timestamp,),
            ).fetchone()
            return int(row["count"])

    def record_attempt(self, succeeded: bool):
        now = int(time.time())
        with self.connection() as db:
            db.execute("INSERT INTO login_attempts(attempted_at, succeeded) VALUES(?, ?)", (now, int(succeeded)))
            db.execute("DELETE FROM login_attempts WHERE attempted_at < ?", (now - 86400,))

    def get_pin_hash(self):
        with self.connection() as db:
            row = db.execute("SELECT pin_hash FROM auth WHERE id = 1").fetchone()
            return row["pin_hash"] if row else None

    def set_pin_hash(self, pin_hash: str):
        with self.connection() as db:
            db.execute(
                "INSERT INTO auth(id, pin_hash, changed_at) VALUES(1, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET pin_hash=excluded.pin_hash, changed_at=excluded.changed_at",
                (pin_hash, int(time.time())),
            )

    def export_settings(self) -> dict:
        with self.connection() as db:
            return {row["key"]: json.loads(row["value"]) for row in db.execute("SELECT key, value FROM settings")}

    def import_settings(self, values: dict):
        with self.connection() as db:
            for key, value in values.items():
                db.execute(
                    "INSERT INTO settings(key, value) VALUES(?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, json.dumps(value)),
                )

    def add_media(self, media_id: str, title: str, filename: str, media_type: str):
        with self.connection() as db:
            db.execute(
                "INSERT INTO media_assets(id, title, filename, media_type, created_at) VALUES(?, ?, ?, ?, ?)",
                (media_id, title, filename, media_type, int(time.time())),
            )

    def list_media(self) -> list[dict]:
        with self.connection() as db:
            return [dict(row) for row in db.execute(
                "SELECT id, title, media_type, created_at FROM media_assets ORDER BY created_at DESC"
            )]

    def get_media(self, media_id: str):
        with self.connection() as db:
            row = db.execute("SELECT * FROM media_assets WHERE id = ?", (media_id,)).fetchone()
            return dict(row) if row else None

    def delete_media(self, media_id: str):
        with self.connection() as db:
            db.execute("DELETE FROM media_assets WHERE id = ?", (media_id,))
