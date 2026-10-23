"""Offline checks of the shipped quiz catalog, artwork and attribution."""

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pytest

from app import quiz_catalog


ASSET_ROOT = Path(quiz_catalog.__file__).resolve().parent / "static" / "quiz"
SVG_NS = "{http://www.w3.org/2000/svg}"


def test_categories_have_enough_unique_local_questions():
    assert [category["id"] for category in quiz_catalog.CATEGORIES] == [
        "cars", "animals", "vegetables", "fruits", "birds", "countries", "flags",
    ]
    for category in quiz_catalog.CATEGORIES:
        assert category["name"]
        assert isinstance(category["harder"], bool)
        items = quiz_catalog.get_items(category["id"])
        assert len(items) == category["count"] >= 5
        assert category["image"] in {item["image"] for item in items}
        assert len({item["id"] for item in items}) == len(items)
        assert len({item["name"] for item in items}) == len(items)
        for item in items:
            assert item["name"].strip()
            assert item["image"] == f"/static/quiz/{category['id']}/{item['id']}.svg"


def test_every_svg_is_local_self_contained_unlabelled_and_parses():
    for category in quiz_catalog.CATEGORIES:
        for item in quiz_catalog.get_items(category["id"]):
            filename = ASSET_ROOT / category["id"] / f"{item['id']}.svg"
            root = ET.fromstring(filename.read_bytes())
            assert root.tag == SVG_NS + "svg"
            assert root.get("viewBox")
            assert any(element.tag == SVG_NS + "path" for element in root.iter())
            for element in root.iter():
                assert element.tag.rsplit("}", 1)[-1] not in {
                    "script", "foreignObject", "text", "image",
                }
                for key, value in element.attrib.items():
                    assert not key.lower().startswith("on")
                    if key.rsplit("}", 1)[-1] == "href":
                        assert value.startswith("#")
                    assert not re.search(r"url\s*\(\s*['\"]?(?!#)", value, re.I)


def test_each_asset_has_pinned_provenance_license_and_matching_hash():
    catalog = json.loads((ASSET_ROOT / "catalog.json").read_text(encoding="utf-8"))
    attribution = (ASSET_ROOT / "ATTRIBUTION.txt").read_text(encoding="utf-8")
    for category in catalog["categories"]:
        for item in category["items"]:
            assert re.match(
                r"https://raw\.githubusercontent\.com/[^/]+/[^/]+/[a-f0-9]{40}/",
                item["source"],
            )
            assert item["source"] in attribution
            assert item["image"] in attribution
            assert item["license"] in {"CC0-1.0", "CC-BY-SA-4.0", "MIT", "Public domain"}
            assert (ASSET_ROOT / "licenses" / f"{item['project']}.txt").is_file()
            raw = (ASSET_ROOT / category["id"] / f"{item['id']}.svg").read_bytes()
            assert hashlib.sha256(raw).hexdigest() == item["sha256"]


def test_country_images_retain_all_source_polygons_and_holes():
    catalog = json.loads((ASSET_ROOT / "catalog.json").read_text(encoding="utf-8"))
    countries = next(c for c in catalog["categories"] if c["id"] == "countries")
    for item in countries["items"]:
        root = ET.parse(ASSET_ROOT / "countries" / f"{item['id']}.svg").getroot()
        paths = list(root.iter(SVG_NS + "path"))
        assert len(paths) == item["polygons"]
        assert sum(path.attrib["d"].count("M") for path in paths) == item["rings"]
        assert all(path.get("fill-rule") == "evenodd" for path in paths)
        assert len(list(root.iter(SVG_NS + "rect"))) == item["insets"]
        # Fitting must retain every coordinate inside the canvas, not clip islands.
        for path in paths:
            for x, y in re.findall(r"(-?\d+\.\d+),(-?\d+\.\d+)", path.attrib["d"]):
                assert 0 <= float(x) <= 640
                assert 0 <= float(y) <= 640


@pytest.mark.parametrize("category", ["", "unknown", "CARS", "../cars", None, [], {}])
def test_unknown_category_is_rejected(category):
    with pytest.raises(ValueError, match="Unknown quiz category"):
        quiz_catalog.get_items(category)


def test_caller_changes_do_not_modify_the_catalog():
    original = quiz_catalog.get_items("cars")
    changed = quiz_catalog.get_items("cars")
    changed[0]["name"] = "Not a car"
    changed.pop()
    assert quiz_catalog.get_items("cars") == original


def test_loader_rejects_missing_local_asset(monkeypatch):
    monkeypatch.setattr(Path, "is_file", lambda path: False)
    with pytest.raises(ValueError, match="Missing local quiz image"):
        quiz_catalog._load_catalog()


@pytest.mark.parametrize("bad_image", [
    "https://example.com/logo.svg",
    "/static/quiz/cars/../../outside.svg",
])
def test_loader_rejects_remote_or_traversing_paths(monkeypatch, bad_image):
    catalog = json.loads((ASSET_ROOT / "catalog.json").read_text(encoding="utf-8"))
    catalog["categories"][0]["items"][0]["image"] = bad_image
    monkeypatch.setattr(quiz_catalog.json, "load", lambda stream: catalog)
    with pytest.raises(ValueError, match="Invalid local quiz image"):
        quiz_catalog._load_catalog()
