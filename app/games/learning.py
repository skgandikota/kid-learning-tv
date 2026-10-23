"""Small original browser activities with server-owned answers and card state."""
from __future__ import annotations

import random
import secrets
import time


ACTIVITIES = (
    {"id": "matching-pairs", "name": "Matching pairs", "description": "Find four pairs of hidden pictures."},
    {"id": "count-objects", "name": "Count the stars", "description": "Count one to five stars and choose the number."},
    {"id": "match-colours", "name": "Match the colour", "description": "Find the colour that matches the big picture."},
    {"id": "match-shapes", "name": "Match the shape", "description": "Find the shape that matches the big picture."},
)
ACTIVITY_IDS = frozenset(item["id"] for item in ACTIVITIES)
COLOURS = ("red", "blue", "green", "yellow")
SHAPES = ("circle", "square", "triangle", "star")


def validate_enabled(value):
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) for item in value)
        or len(value) != len(set(value))
        or set(value) - ACTIVITY_IDS
    ):
        raise ValueError("Choose enabled activities from the learning library.")


class LearningGame:
    def __init__(self, activity_id: str, rng=None):
        if not isinstance(activity_id, str) or activity_id not in ACTIVITY_IDS:
            raise ValueError("That learning activity is unavailable.")
        self.activity_id = activity_id
        self.name = next(item["name"] for item in ACTIVITIES if item["id"] == activity_id)
        self.rng = rng or random.SystemRandom()
        self.session_id = secrets.token_hex(16)
        self.revision = 0
        self.completed = False
        self.reveal_until = None
        self.matched = set()
        self.revealed = []
        self.score = 0
        if activity_id == "matching-pairs":
            self.deck = list(SHAPES) * 2
            self.rng.shuffle(self.deck)
            self.total = len(SHAPES)
            self.message = "Turn over two cards. Can you find a pair?"
        else:
            choices = {
                "count-objects": ("1", "2", "3", "4", "5"),
                "match-colours": COLOURS,
                "match-shapes": SHAPES,
            }
            self.options = list(choices[activity_id])
            self.targets = list(self.options)
            self.rng.shuffle(self.targets)
            self.total = len(self.targets)
            self.message = self.prompt()

    def prompt(self):
        if self.activity_id == "count-objects":
            return "How many stars can you count?"
        if self.activity_id == "match-colours":
            return f"Find the {self.targets[self.score]} colour."
        return f"Find the {self.targets[self.score]}."

    def snapshot(self):
        result = {
            "activity_id": self.activity_id, "name": self.name,
            "session_id": self.session_id, "revision": self.revision,
            "completed": self.completed, "score": self.score, "total": self.total,
            "message": self.message, "waiting": self.reveal_until is not None,
        }
        if self.activity_id == "matching-pairs":
            result["cards"] = [
                {
                    "id": index, "matched": index in self.matched,
                    "picture": picture if index in self.matched or index in self.revealed else None,
                }
                for index, picture in enumerate(self.deck)
            ]
        else:
            result["target"] = None if self.completed else self.targets[self.score]
            result["options"] = list(self.options)
        return result

    def check_request(self, body):
        if (
            body.get("session_id") != self.session_id
            or type(body.get("revision")) is not int
            or body["revision"] != self.revision
        ):
            raise ValueError("That turn has changed. Wait for the current board.")

    def answer(self, body, now=None):
        self.check_request(body)
        if self.completed or self.reveal_until is not None:
            raise ValueError("Wait for the current cards to finish.")
        if self.activity_id == "matching-pairs":
            index = body.get("choice")
            if type(index) is not int or not 0 <= index < len(self.deck):
                raise ValueError("Choose a card on the board.")
            if index in self.matched or index in self.revealed:
                raise ValueError("Choose a different face-down card.")
            self.revealed.append(index)
            if len(self.revealed) == 2:
                first, second = self.revealed
                if self.deck[first] == self.deck[second]:
                    self.matched.update(self.revealed)
                    self.revealed.clear()
                    self.score += 1
                    self.message = "You found a pair! Find another one."
                else:
                    self.reveal_until = (time.time() if now is None else now) + 1.4
                    self.message = "Not a pair this time. Have another go."
            else:
                self.message = "Now turn over another card."
        else:
            choice = body.get("choice")
            if not isinstance(choice, str) or choice not in self.options:
                raise ValueError("Choose one of the answers on the screen.")
            if choice == self.targets[self.score]:
                self.score += 1
                if self.score < self.total:
                    self.message = "That's right! " + self.prompt()
            else:
                self.message = "Good try. " + self.prompt()
        self.completed = self.score == self.total
        if self.completed:
            self.message = "You did it! A grown-up can choose what we play next."
        self.revision += 1

    def settle(self, body, now=None):
        self.check_request(body)
        if self.reveal_until is None or (time.time() if now is None else now) < self.reveal_until:
            return False
        self.revealed.clear()
        self.reveal_until = None
        self.message = "Turn over two cards. Can you find a pair?"
        self.revision += 1
        return True
