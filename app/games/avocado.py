"""Data-driven Avocado answer matching and round mechanics."""
from __future__ import annotations

import difflib
import random
import re
import unicodedata


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _plural_forms(value: str) -> set[str]:
    forms = {value}
    if value.endswith("y") and len(value) > 1:
        forms.add(value[:-1] + "ies")
    elif value.endswith(("s", "x", "ch", "sh")):
        forms.add(value + "es")
    else:
        forms.add(value + "s")
    if value.endswith("ies"):
        forms.add(value[:-3] + "y")
    if value.endswith("es"):
        forms.add(value[:-2])
    if value.endswith("s") and not value.endswith("ss"):
        forms.add(value[:-1])
    return forms


class AnswerMatcher:
    def __init__(self, entries: list[dict]):
        self.entries = entries
        self.lookup: dict[str, int] = {}
        for index, item in enumerate(entries):
            labels = [item["name"], *item.get("aliases", []), *item.get("pronunciation", [])]
            for label in labels:
                normalized = normalize(label)
                for variant in _plural_forms(normalized):
                    if variant:
                        self.lookup.setdefault(variant, index)

    def match(self, text: str) -> dict:
        normalized = normalize(text)
        if not normalized:
            return {"status": "not_found", "confidence": 0.0}
        exact = self.lookup.get(normalized)
        if exact is not None:
            return {"status": "match", "index": exact, "confidence": 1.0}
        candidates = difflib.get_close_matches(normalized, self.lookup.keys(), n=1, cutoff=0.80)
        if candidates:
            label = candidates[0]
            confidence = difflib.SequenceMatcher(None, normalized, label).ratio()
            if confidence >= 0.80:
                return {
                    "status": "confirm",
                    "index": self.lookup[label],
                    "confidence": round(confidence, 3),
                }
        return {"status": "not_found", "confidence": 0.0}


class AvocadoGame:
    def __init__(self, category: dict, retries: int = 1, rng=None):
        self.category = category
        self.entries = category.get("answers", [])
        self.matcher = AnswerMatcher(self.entries)
        self.retries_allowed = max(0, int(retries))
        self.retries_left = self.retries_allowed
        self.used: list[int] = []
        self.pending: dict | None = None
        self.state = "child_turn"
        self.nickname: str | None = None
        self.rng = rng or random.SystemRandom()

    def submit(self, text: str) -> dict:
        if self.state != "child_turn":
            return {"status": "not_accepting"}
        result = self.matcher.match(text)
        if result["status"] == "confirm":
            self.pending = result
            return {
                "status": "confirm",
                "answer": self.entries[result["index"]]["name"],
                "confidence": result["confidence"],
            }
        if result["status"] == "not_found":
            return {"status": "not_found"}
        index = result["index"]
        if index in self.used:
            return {"status": "repeat", "answer": self.entries[index]["name"]}
        self.used.append(index)
        self.state = "app_turn"
        return {"status": "accepted", "answer": self.entries[index]["name"]}

    def resolve_pending(self, accepted: bool, corrected: str | None = None) -> dict:
        if not self.pending:
            return {"status": "no_pending_answer"}
        pending = self.pending
        self.pending = None
        if not accepted and corrected:
            result = self.matcher.match(corrected)
            if result["status"] == "match":
                pending = result
            else:
                return {"status": "not_found"}
        elif not accepted:
            return {"status": "rejected"}
        index = pending["index"]
        if index in self.used:
            return {"status": "repeat", "answer": self.entries[index]["name"]}
        self.used.append(index)
        self.state = "app_turn"
        return {"status": "accepted", "answer": self.entries[index]["name"]}

    def application_answer(self) -> str | None:
        available = [index for index in range(len(self.entries)) if index not in self.used]
        if not available:
            self.state = "ended"
            return None
        selected = self.rng.choice(available)
        self.used.append(selected)
        self.state = "child_turn"
        return self.entries[selected]["name"]

    def retry_or_end(self, nicknames: list[str]) -> dict:
        if self.retries_left > 0:
            self.retries_left -= 1
            return {"status": "retry", "remaining": self.retries_left}
        self.state = "ended"
        enabled = list(nicknames)
        self.nickname = self.rng.choice(enabled) if enabled else None
        return {"status": "ended", "nickname": self.nickname}

    def summary(self) -> list[str]:
        return [self.entries[index]["name"] for index in self.used]
