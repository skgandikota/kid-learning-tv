"""Memory Chain sequence selection and answer comparison."""
from __future__ import annotations

import random

from app.games.avocado import normalize


class MemoryGame:
    LEVELS = {
        1: {"min_items": 2, "max_items": 3, "pictures": True},
        2: {"min_items": 3, "max_items": 5, "pictures": True},
        3: {"min_items": 5, "max_items": 8, "pictures": False},
    }

    def __init__(self, category: dict, level: int = 1, retries: int = 1, rng=None):
        self.category = category
        self.level = int(level) if int(level) in self.LEVELS else 1
        self.retries_allowed = max(0, int(retries))
        self.retries_left = self.retries_allowed
        self.rng = rng or random.SystemRandom()
        self.sequence: list[str] = []
        self.state = "ready"
        self.picture_visible = False

    def start(self) -> list[str]:
        choices = list(dict.fromkeys(self.category.get("items", [])))
        if not choices:
            self.state = "unavailable"
            return []
        self.max_items = min(self.LEVELS[self.level]["max_items"], len(choices))
        self.sequence = [self.rng.choice(choices)]
        self.state = "child_turn"
        self.picture_visible = self.LEVELS[self.level]["pictures"]
        return list(self.sequence)

    def check(self, answer: list[str]) -> dict:
        if self.state != "child_turn":
            return {"status": "not_accepting"}
        actual = [normalize(item) for item in answer]
        expected = [normalize(item) for item in self.sequence]
        if actual[:len(expected)] != expected:
            reason = "wrong_order" if sorted(actual[:len(expected)]) == sorted(expected) else "sequence_differs"
            return {"status": "retry", "reason": reason, "remaining": self.retries_left}
        if len(actual) != len(expected) + 1:
            return {"status": "retry", "reason": "add_one_item", "remaining": self.retries_left}
        if actual[-1] in expected:
            return {"status": "retry", "reason": "repeated_item", "remaining": self.retries_left}
        canonical = {normalize(item): item for item in self.category.get("items", [])}
        if actual[-1] not in canonical:
            return {"status": "retry", "reason": "unknown_item", "remaining": self.retries_left}
        self.sequence.append(canonical[actual[-1]])
        self.retries_left = self.retries_allowed
        app_added = None
        if len(self.sequence) < self.max_items:
            available = [item for item in self.category["items"] if normalize(item) not in {normalize(x) for x in self.sequence}]
            if available:
                app_added = self.rng.choice(available)
                self.sequence.append(app_added)
        if len(self.sequence) >= self.max_items or app_added is None:
            self.state = "ended"
            self.picture_visible = False
            return {"status": "ended", "sequence": list(self.sequence), "child_item": canonical[actual[-1]]}
        self.picture_visible = self.LEVELS[self.level]["pictures"]
        return {
            "status": "continue",
            "sequence": list(self.sequence),
            "app_added": app_added,
            "child_item": canonical[actual[-1]],
        }

    def hide_pictures(self):
        self.picture_visible = False

    def use_retry(self) -> dict:
        if self.retries_left > 0:
            self.retries_left -= 1
            return {"status": "retry", "remaining": self.retries_left}
        self.state = "ended"
        return {"status": "ended"}
