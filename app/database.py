"""SQLite storage for parent credentials and sign-in attempts."""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
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
                CREATE TABLE IF NOT EXISTS tv_display (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    food_time INTEGER NOT NULL DEFAULT 0
                );
                INSERT OR IGNORE INTO tv_display(id, food_time) VALUES(1, 0);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA journal_mode = WAL")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def attempts_since(self, timestamp: int) -> int:
        with self.connection() as db:
            return db.execute(
                "SELECT COUNT(*) FROM login_attempts WHERE attempted_at >= ? AND succeeded = 0",
                (timestamp,),
            ).fetchone()[0]

    def record_attempt(self, succeeded: bool):
        now = int(time.time())
        with self.connection() as db:
            db.execute("INSERT INTO login_attempts(attempted_at, succeeded) VALUES(?, ?)", (now, int(succeeded)))
            db.execute("DELETE FROM login_attempts WHERE attempted_at < ?", (now - 86400,))

    def get_pin_hash(self):
        with self.connection() as db:
            row = db.execute("SELECT pin_hash FROM auth WHERE id = 1").fetchone()
            return row["pin_hash"] if row else None

    def food_time(self) -> bool:
        with self.connection() as db:
            return bool(db.execute("SELECT food_time FROM tv_display WHERE id = 1").fetchone()[0])

    def set_food_time(self, enabled: bool):
        with self.connection() as db:
            db.execute("UPDATE tv_display SET food_time = ? WHERE id = 1", (int(enabled),))

    def set_pin_hash(self, pin_hash: str):
        with self.connection() as db:
            db.execute(
                "INSERT INTO auth(id, pin_hash, changed_at) VALUES(1, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET pin_hash=excluded.pin_hash, changed_at=excluded.changed_at",
                (pin_hash, int(time.time())),
            )
