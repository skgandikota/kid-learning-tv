"""Untimed pair matching, progressing from four to twelve cards."""
from __future__ import annotations

import random
import time
import uuid

from app.quiz_catalog import get_items


class MatchingGame:
    sizes = (4, 6, 8, 10, 12)

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.round = 0
        self.matches = 0
        self._new_board()

    def _new_board(self):
        self.token = uuid.uuid4().hex
        pictures = random.sample(get_items("animals") + get_items("fruits"), self.sizes[self.round] // 2)
        self.cards = [dict(item) for item in pictures for _ in range(2)]
        random.shuffle(self.cards)
        self.open = []
        self.removed = set()
        self.phase = "playing"
        self.deadline = None

    def advance(self):
        if self.deadline is None or self.clock() < self.deadline:
            return
        if self.phase in {"match", "mismatch"}:
            if self.phase == "match":
                self.removed.update(self.open)
            self.open = []
            self.deadline = None
            self.phase = "playing"
            if len(self.removed) == len(self.cards):
                self.phase = "round-done"
                self.deadline = self.clock() + 1.5
        elif self.phase == "round-done":
            if self.round + 1 < len(self.sizes):
                self.round += 1
                self._new_board()
            else:
                self.phase = "complete"
                self.deadline = None

    def flip(self, token, index):
        self.advance()
        if token != self.token or self.phase != "playing":
            return False
        if type(index) is not int or not 0 <= index < len(self.cards):
            raise ValueError("Choose a card on the board.")
        if index in self.open or index in self.removed:
            return False
        self.open.append(index)
        if len(self.open) == 2:
            first, second = self.open
            matched = self.cards[first]["image"] == self.cards[second]["image"]
            self.phase = "match" if matched else "mismatch"
            self.matches += int(matched)
            self.deadline = self.clock() + (0.8 if matched else 1.5)
        return True

    def snapshot(self):
        self.advance()
        return {
            "token": self.token, "round": self.round + 1, "rounds": len(self.sizes),
            "phase": self.phase, "matches": self.matches,
            "cards": [
                {"index": index, "face_up": index in self.open,
                 "removed": index in self.removed,
                 "image": item["image"] if index in self.open else None,
                 "name": item["name"] if index in self.open else None}
                for index, item in enumerate(self.cards)
            ],
        }
