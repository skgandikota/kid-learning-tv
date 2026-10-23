#!/usr/bin/env python3
"""Print a local mock input event; no microphone or audio file is used."""
import argparse
import json


parser = argparse.ArgumentParser()
parser.add_argument("text", help="Mock child answer")
args = parser.parse_args()
print(json.dumps({"type": "ANSWER_HEARD", "text": args.text, "source": "keyboard-mock"}))
