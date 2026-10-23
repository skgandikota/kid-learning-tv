"""Gentle timed picture rounds: no microphone, scoring or wrong-answer state."""
from __future__ import annotations

import random
import time
import uuid

from app.quiz_catalog import get_items


DEFAULTS = {"seconds": 10, "count": 5, "ticking": True}


def validate_settings(body):
    if not isinstance(body, dict):
        raise ValueError("Choose quiz settings.")
    seconds, count, ticking = body.get("seconds"), body.get("count"), body.get("ticking")
    if type(seconds) is not int or seconds not in {5, 10, 15, 20}:
        raise ValueError("Choose 5, 10, 15 or 20 seconds.")
    if type(count) is not int or count not in {5, 10}:
        raise ValueError("Choose five or ten pictures.")
    if not isinstance(ticking, bool):
        raise ValueError("Ticking must be on or off.")
    return {"seconds": seconds, "count": count, "ticking": ticking}


class QuizRound:
    def __init__(self, category, settings, clock=time.monotonic):
        items = get_items(category)
        self.items = random.sample(items, min(settings["count"], len(items)))
        self.category = category
        self.settings = dict(settings)
        self.clock = clock
        self.session = uuid.uuid4().hex
        self.index = 0
        self.phase = "loading"
        self.deadline = None
        self.paused = False
        self.remaining_on_pause = None
        self.speech_finished = False
        self.warning = ""

    def ready(self, token):
        if token != self.token or self.phase != "loading":
            return False
        self.phase = "question"
        self.deadline = self.clock() + self.settings["seconds"]
        if self.paused:
            self.remaining_on_pause = self.settings["seconds"]
        return True

    @property
    def token(self):
        return f"{self.session}:{self.index}"

    def reveal(self):
        self.phase = "answer"
        self.deadline = self.clock() + 4
        self.speech_finished = False
        if self.paused:
            self.remaining_on_pause = 4

    def next(self):
        self.remaining_on_pause = None
        if self.index + 1 >= len(self.items):
            self.phase = "complete"
            self.deadline = None
        else:
            self.index += 1
            self.phase = "loading"
            self.deadline = None
            self.speech_finished = False

    def pause(self, enabled):
        if enabled == self.paused:
            return
        now = self.clock()
        if enabled:
            self.remaining_on_pause = max(0, self.deadline - now) if self.deadline is not None else None
        elif self.remaining_on_pause is not None:
            self.deadline = now + self.remaining_on_pause
        self.paused = enabled

    def speech_done(self, token, warning=""):
        if token != self.token or self.phase != "answer":
            return False
        self.speech_finished = True
        self.warning = warning[:240]
        return True

    def snapshot(self):
        now = self.clock()
        if not self.paused and self.deadline is not None and now >= self.deadline:
            if self.phase == "question":
                self.reveal()
            elif self.phase == "answer" and (self.speech_finished or now >= self.deadline + 12):
                if not self.speech_finished:
                    self.warning = "TV speech did not finish; check sound on the laptop."
                self.next()
        item = self.items[self.index]
        remaining = self.remaining_on_pause if self.paused else (
            max(0, self.deadline - self.clock()) if self.deadline is not None else 0
        )
        return {
            "session": self.session, "token": self.token, "category": self.category,
            "index": self.index, "count": len(self.items), "phase": self.phase,
            "item": item, "remaining": remaining or 0,
            "seconds": self.settings["seconds"], "ticking": self.settings["ticking"],
            "paused": self.paused, "warning": self.warning,
        }
