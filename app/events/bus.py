"""Bounded in-process event bus used by server-sent events."""
from __future__ import annotations

import json
import threading
import time
from collections import deque


class EventBus:
    def __init__(self, limit: int = 50):
        self._events = deque(maxlen=limit)
        self._condition = threading.Condition()
        self._sequence = 0

    def publish(self, event_type: str, payload: dict):
        with self._condition:
            self._sequence += 1
            event = {"id": self._sequence, "type": event_type, "payload": payload, "at": int(time.time())}
            self._events.append(event)
            self._condition.notify_all()

    def stream(self, after: int = 0):
        cursor = after
        while True:
            with self._condition:
                pending = [event for event in self._events if event["id"] > cursor]
                if not pending:
                    self._condition.wait(timeout=15)
                    pending = [event for event in self._events if event["id"] > cursor]
            if not pending:
                yield ": keepalive\n\n"
                continue
            for event in pending:
                cursor = event["id"]
                yield f"id: {cursor}\ndata: {json.dumps(event, separators=(',', ':'))}\n\n"
