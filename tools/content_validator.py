#!/usr/bin/env python3
"""Validate packaged content files."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.content import ContentStore


def main():
    store = ContentStore(Path(__file__).resolve().parents[1] / "content")
    store.validate_all()
    categories = store.categories()
    store.nicknames()
    store.prompts()
    store.animal_facts()
    for category in categories:
        print(f"OK category: {category['id']} ({len(category['answers'])} answers)")
    print(f"OK nicknames: {len(store.nicknames())}")
    print(f"OK activity prompts: {len(store.prompts())}")
    print(f"OK animal fact entries: {len(store.animal_facts())}")
    print(f"OK memory categories: {len(list((store.root / 'memory').glob('*.json')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
