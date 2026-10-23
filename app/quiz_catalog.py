"""Validated local artwork for identification quizzes; no network access.

``CATEGORIES`` exposes id/name/count/harder/image. ``get_items(category)`` returns
fresh item dictionaries (id/name/image and optional speech). The caller chooses
and times its own questions, normally five per quiz.
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re


_ASSET_ROOT = Path(__file__).resolve().parent / "static" / "quiz"
_EXPECTED_CATEGORIES = (
    "cars", "animals", "vegetables", "fruits", "birds", "countries", "flags",
)
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def _load_catalog() -> tuple[tuple[dict, ...], dict[str, tuple[dict, ...]]]:
    with (_ASSET_ROOT / "catalog.json").open(encoding="utf-8") as stream:
        catalog = json.load(stream)
    if catalog.get("schema_version") != 1:
        raise ValueError("Unsupported quiz catalog schema")
    categories = []
    items_by_category = {}
    for category in catalog["categories"]:
        category_id = category["id"]
        if category_id in items_by_category or category_id not in _EXPECTED_CATEGORIES:
            raise ValueError(f"Invalid quiz category: {category_id!r}")
        if not isinstance(category["harder"], bool):
            raise ValueError(f"Invalid difficulty flag: {category_id}")
        if not isinstance(category["name"], str) or not category["name"].strip():
            raise ValueError(f"Missing category name: {category_id}")
        seen = set()
        items = []
        for record in category["items"]:
            item_id = record["id"]
            if not isinstance(item_id, str) or not _SLUG.fullmatch(item_id) or item_id in seen:
                raise ValueError(f"Invalid or duplicate quiz item: {item_id!r}")
            seen.add(item_id)
            image = record["image"]
            expected = f"/static/quiz/{category_id}/{item_id}.svg"
            if image != expected:
                raise ValueError(f"Invalid local quiz image: {image!r}")
            relative = PurePosixPath(category_id) / f"{item_id}.svg"
            target = (_ASSET_ROOT / Path(*relative.parts)).resolve()
            if not target.is_relative_to(_ASSET_ROOT.resolve()) or not target.is_file():
                raise ValueError(f"Missing local quiz image: {image}")
            if not isinstance(record["name"], str) or not record["name"].strip():
                raise ValueError(f"Missing quiz answer: {category_id}/{item_id}")
            item = {"id": item_id, "name": record["name"], "image": image}
            if "speech" in record:
                if not isinstance(record["speech"], str) or not record["speech"].strip():
                    raise ValueError(f"Invalid spoken answer: {category_id}/{item_id}")
                item["speech"] = record["speech"]
            items.append(item)
        if len(items) < 5:
            raise ValueError(f"Quiz category needs at least five items: {category_id}")
        items_by_category[category_id] = tuple(items)
        categories.append({
            "id": category_id, "name": category["name"],
            "count": len(items), "harder": category["harder"],
            "image": items[0]["image"],
        })
    if tuple(items_by_category) != _EXPECTED_CATEGORIES:
        raise ValueError("Quiz catalog must contain all supported categories in order")
    return tuple(categories), items_by_category


CATEGORIES, _ITEMS = _load_catalog()


def get_items(category: str) -> list[dict]:
    """Return isolated item dictionaries; reject unsupported category IDs."""
    if not isinstance(category, str) or category not in _ITEMS:
        raise ValueError(f"Unknown quiz category: {category!r}")
    return [dict(item) for item in _ITEMS[category]]
