#!/usr/bin/env python3
"""Emit a harmless sample event for adapter development."""
import json

print(json.dumps({
    "type": "ANSWER_HEARD",
    "requestId": "local-demo",
    "sessionId": "mock-session",
    "text": "elephant",
    "source": "mock-alexa",
}))
