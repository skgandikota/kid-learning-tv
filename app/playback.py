"""Server-owned playlist; the TV reports progress but parents own controls."""
from __future__ import annotations

import math
import threading
import time
import uuid


def seconds(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Use a valid time in seconds.")
    return float(value)


class Playback:
    def __init__(self, database):
        self.database = database
        self.lock = threading.RLock()
        self.session = uuid.uuid4().hex
        self.revision = 0
        self.seek_revision = 0
        self.mode = "food" if database.food_time() else "blank"
        self.queue = []
        self.index = 0
        self.position = 0.0
        self.paused = False
        self.volume = 0.7
        self.buffering = False
        self.error = ""
        self.last_seen = None

    def snapshot(self):
        with self.lock:
            current = self.queue[self.index] if self.mode == "video" else None
            elapsed = sum(item["duration"] for item in self.queue[:self.index]) + self.position
            total = sum(item["duration"] for item in self.queue)
            if self.mode == "finished":
                elapsed = total
            return {
                "session": self.session, "revision": self.revision, "mode": self.mode,
                "seek_revision": self.seek_revision,
                "queue": self.queue, "index": self.index, "current": current,
                "position": self.position, "paused": self.paused, "volume": self.volume,
                "buffering": self.buffering, "error": self.error,
                "remaining": max(0, total - elapsed), "total": total,
                "tv_connected": self.last_seen is not None and time.monotonic() - self.last_seen < 6,
            }

    def food(self, enabled):
        with self.lock:
            self.database.set_food_time(enabled)
            self.mode = "food" if enabled else "blank"
            self.queue = []
            self.index = 0
            self.position = 0.0
            self.error = ""
            self.buffering = False
            self.revision += 1

    def start(self, items):
        with self.lock:
            self.database.set_food_time(False)
            self.session = uuid.uuid4().hex
            self.mode = "video"
            self.queue = [dict(item) for item in items]
            self.index = 0
            self.position = 0.0
            self.paused = False
            self.buffering = True
            self.error = ""
            self.revision += 1

    def command(self, body):
        with self.lock:
            action = body.get("action")
            if action == "stop":
                self.food(False)
                return
            if self.mode != "video":
                raise ValueError("No video is playing.")
            if action == "pause":
                self.paused = True
            elif action == "resume":
                self.paused = False
                self.error = ""
            elif action == "seek":
                self.position = max(0, min(seconds(body.get("position")), self.queue[self.index]["duration"]))
                self.seek_revision += 1
            elif action == "volume":
                self.volume = max(0, min(seconds(body.get("volume")), 1))
            elif action in {"next", "previous"}:
                if action == "next":
                    self.advance()
                    return
                self.index = max(0, self.index - 1)
                self.position = 0.0
                self.seek_revision += 1
                self.buffering = True
                self.error = ""
            else:
                raise ValueError("Unknown video control.")
            self.revision += 1

    def advance(self):
        self.position = 0.0
        self.error = ""
        if self.index + 1 < len(self.queue):
            self.index += 1
            self.buffering = True
        else:
            self.mode = "finished"
            self.buffering = False
        self.revision += 1

    def report(self, body):
        with self.lock:
            self.last_seen = time.monotonic()
            if body.get("session") != self.session or body.get("revision") != self.revision:
                return False
            if self.mode != "video":
                return True
            event = body.get("event")
            if event not in {"progress", "ended", "error"}:
                raise ValueError("Unknown playback report.")
            position = seconds(body.get("position"))
            if position < 0 or position > self.queue[self.index]["duration"] + 2:
                raise ValueError("Playback time is outside this video.")
            if not isinstance(body.get("buffering"), bool):
                raise ValueError("Invalid buffering state.")
            if event == "ended":
                if self.paused:
                    return False
                if position < self.queue[self.index]["duration"] - 2:
                    raise ValueError("This video has not finished.")
                self.advance()
            else:
                self.position = min(position, self.queue[self.index]["duration"])
                self.buffering = body["buffering"]
                if event == "error":
                    message = body.get("error")
                    if not isinstance(message, str) or not message:
                        raise ValueError("A playback error needs a message.")
                    self.error = message[:240]
                    self.paused = True
                    self.revision += 1
            return True
