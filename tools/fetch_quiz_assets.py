"""Rebuild the bundled quiz artwork from pinned, public GitHub sources.

Uses only Python's standard library. This is a maintainer tool, never a runtime
dependency. Run from the project root: python tools\\fetch_quiz_assets.py
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "app" / "static" / "quiz"
REVISIONS = {
    "openmoji": "aeb8bb3a59e2de39c754ac79180c8131c906acea",
    "simple-icons": "0af835e2949a9222965522780e5e0810d3c53382",
    "flag-icons": "ac7e0eb3259eb62aa6100c435607e2fe03896a97",
    "natural-earth": "ca96624a56bd078437bca8184e78163e5039ad19",
}
REPOS = {
    "openmoji": "hfg-gmuend/openmoji",
    "simple-icons": "simple-icons/simple-icons",
    "flag-icons": "lipis/flag-icons",
    "natural-earth": "nvkelso/natural-earth-vector",
}
LICENSES = {
    "openmoji": ("CC-BY-SA-4.0", "LICENSE.txt"),
    "simple-icons": ("CC0-1.0", "LICENSE.md"),
    "flag-icons": ("MIT", "LICENSE"),
    "natural-earth": ("Public domain", "LICENSE.md"),
}
CATEGORY_INFO = [
    ("cars", "Car logos", False),
    ("animals", "Animals", False),
    ("vegetables", "Vegetables", False),
    ("fruits", "Fruits", False),
    ("birds", "Birds", False),
    ("countries", "Country shapes", True),
    ("flags", "Flags", True),
]
CAR_NAMES = [
    "Audi", "BMW", "Ford", "Honda", "Toyota", "Mercedes", "Tesla",
    "Volkswagen", "Volvo", "Hyundai", "Nissan", "Kia", "Renault",
    "Peugeot", "Suzuki",
]
# Display names deliberately use familiar spoken words, not Unicode annotations.
EMOJI = {
    "animals": [
        ("dog", "Dog", "1F415"), ("cat", "Cat", "1F408"),
        ("lion", "Lion", "1F981"), ("elephant", "Elephant", "1F418"),
        ("giraffe", "Giraffe", "1F992"), ("zebra", "Zebra", "1F993"),
        ("monkey", "Monkey", "1F412"), ("rabbit", "Rabbit", "1F407"),
        ("cow", "Cow", "1F404"), ("pig", "Pig", "1F416"),
    ],
    "vegetables": [
        ("carrot", "Carrot", "1F955"), ("broccoli", "Broccoli", "1F966"),
        ("potato", "Potato", "1F954"), ("tomato", "Tomato", "1F345"),
        ("cucumber", "Cucumber", "1F952"), ("corn", "Corn", "1F33D"),
        ("onion", "Onion", "1F9C5"), ("pepper", "Pepper", "1FAD1"),
        ("eggplant", "Eggplant", "1F346"), ("hot-pepper", "Chilli pepper", "1F336"),
    ],
    "fruits": [
        ("apple", "Apple", "1F34E"), ("banana", "Banana", "1F34C"),
        ("orange", "Orange", "1F34A"), ("grapes", "Grapes", "1F347"),
        ("strawberry", "Strawberry", "1F353"),
        ("watermelon", "Watermelon", "1F349"),
        ("pineapple", "Pineapple", "1F34D"), ("pear", "Pear", "1F350"),
        ("peach", "Peach", "1F351"), ("cherries", "Cherries", "1F352"),
    ],
    "birds": [
        ("parrot", "Parrot", "1F99C"), ("chicken", "Chicken", "1F414"),
        ("duck", "Duck", "1F986"), ("penguin", "Penguin", "1F427"),
        ("owl", "Owl", "1F989"), ("eagle", "Eagle", "1F985"),
        ("dove", "Dove", "1F54A"), ("turkey", "Turkey", "1F983"),
        ("flamingo", "Flamingo", "1F9A9"), ("peacock", "Peacock", "1F99A"),
    ],
}
COUNTRIES = [
    ("united-kingdom", "United Kingdom", "GBR", -3),
    ("india", "India", "IND", 79),
    ("italy", "Italy", "ITA", 12),
    ("australia", "Australia", "AUS", 134),
    ("japan", "Japan", "JPN", 138),
    ("france", "France", "FRA", 2),
    ("brazil", "Brazil", "BRA", -52),
    ("united-states", "United States", "USA", -110),
]
FLAGS = [
    ("india", "India", "in"), ("united-kingdom", "United Kingdom", "gb"),
    ("united-states", "United States", "us"), ("france", "France", "fr"),
    ("japan", "Japan", "jp"), ("italy", "Italy", "it"),
    ("brazil", "Brazil", "br"), ("germany", "Germany", "de"),
    ("canada", "Canada", "ca"), ("australia", "Australia", "au"),
]


def source_url(project: str, path: str) -> str:
    return (
        f"https://raw.githubusercontent.com/{REPOS[project]}/"
        f"{REVISIONS[project]}/{path}"
    )


def download(url: str) -> bytes:
    if not url.startswith("https://raw.githubusercontent.com/"):
        raise ValueError("Only public, pinned GitHub raw sources are permitted")
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "kid-learning-tv-assets"}), timeout=120) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raise AssertionError("unreachable")


def validate_svg(raw: bytes) -> None:
    root = ET.fromstring(raw)
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("Expected SVG artwork")
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in {"script", "foreignObject", "text", "image"}:
            raise ValueError(f"Non-self-contained or labelled SVG: {tag}")
        for key, value in element.attrib.items():
            if key.lower().startswith("on"):
                raise ValueError("SVG event handler")
            if key.rsplit("}", 1)[-1] == "href" and not value.startswith("#"):
                raise ValueError("External SVG reference")
            if re.search(r"url\s*\(\s*['\"]?(?!#)", value, re.I):
                raise ValueError("External SVG style resource")


def ring_area(ring: list) -> float:
    return abs(sum(
        a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:])
    )) / 2


def country_svg(geometry: dict, central_longitude: float) -> tuple[bytes, dict]:
    """Project actual source rings north-up; retain offshore polygons in insets."""
    if geometry["type"] not in {"Polygon", "MultiPolygon"}:
        raise ValueError("Unsupported country geometry")
    coordinates = geometry["coordinates"]
    polygons = coordinates if geometry["type"] == "MultiPolygon" else [coordinates]
    polygons = [
        [
            [
                (central_longitude + ((lon - central_longitude + 180) % 360 - 180), lat)
                for lon, lat, *_ in ring
            ]
            for ring in polygon
        ]
        for polygon in polygons
    ]
    groups = []
    for polygon in polygons:
        points = polygon[0]
        bounds = [
            min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points),
        ]
        groups.append({"polygons": [polygon], "bounds": bounds})

    # Nearby islands share a projection with their mainland. Truly remote
    # territories remain separate instead of shrinking the mainland to a dot.
    changed = True
    while changed:
        changed = False
        for i, left in enumerate(groups):
            a = left["bounds"]
            for j in range(i + 1, len(groups)):
                b = groups[j]["bounds"]
                cos_lat = math.cos(math.radians((a[1] + a[3] + b[1] + b[3]) / 4))
                dx = max(0, a[0] - b[2], b[0] - a[2]) * cos_lat
                dy = max(0, a[1] - b[3], b[1] - a[3])
                if math.hypot(dx, dy) <= 3:
                    left["polygons"].extend(groups[j]["polygons"])
                    left["bounds"] = [
                        min(a[0], b[0]), min(a[1], b[1]),
                        max(a[2], b[2]), max(a[3], b[3]),
                    ]
                    groups.pop(j)
                    changed = True
                    break
            if changed:
                break
    groups.sort(
        key=lambda group: sum(ring_area(p[0]) for p in group["polygons"]),
        reverse=True,
    )
    insets = len(groups) - 1
    columns = min(insets, 5) if insets else 0
    rows = math.ceil(insets / columns) if insets else 0
    inset_height = min(130, 260 / rows) if rows else 0
    main_height = 640 - rows * inset_height
    paths = []
    frames = []
    for index, group in enumerate(groups):
        if index == 0:
            panel = (16, 16, 608, main_height - 32)
        else:
            column = (index - 1) % columns
            row = (index - 1) // columns
            panel = (
                column * 640 / columns + 8,
                main_height + row * inset_height + 8,
                640 / columns - 16,
                inset_height - 16,
            )
            frames.append(
                '<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" '
                'rx="8" fill="#f1f5f9" stroke="#cbd5e1"/>' % panel
            )
        x, y, width, height = panel
        west, south, east, north = group["bounds"]
        cos_lat = math.cos(math.radians((south + north) / 2))
        projected_width = max((east - west) * cos_lat, 1e-9)
        projected_height = max(north - south, 1e-9)
        scale = min((width - 12) / projected_width, (height - 12) / projected_height)
        offset_x = x + (width - projected_width * scale) / 2
        offset_y = y + (height - projected_height * scale) / 2
        for polygon in group["polygons"]:
            commands = []
            for ring in polygon:
                commands.append("M" + " L".join(
                    f"{offset_x + (lon - west) * cos_lat * scale:.3f},"
                    f"{offset_y + (north - lat) * scale:.3f}"
                    for lon, lat in ring
                ) + " Z")
            paths.append(
                f'<path fill="#152c4d" fill-rule="evenodd" d="{" ".join(commands)}"/>'
            )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640">'
        + "".join(frames + paths) + "</svg>\n"
    ).encode()
    return svg, {
        "polygons": len(polygons),
        "rings": sum(len(p) for p in polygons),
        "insets": insets,
        "projection": "local equirectangular, north up; remote-territory insets",
    }


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    categories = {
        key: {"id": key, "name": name, "harder": harder, "items": []}
        for key, name, harder in CATEGORY_INFO
    }
    license_texts = {}
    for project, (_, path) in LICENSES.items():
        raw = download(source_url(project, path))
        license_texts[project] = raw.decode("utf-8")
        target = DEST / "licenses" / f"{project}.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)

    logo_metadata = json.loads(download(source_url("simple-icons", "_data/simple-icons.json")))
    logos = {icon["title"]: icon for icon in logo_metadata["icons"]}
    emoji_metadata = json.loads(download(source_url("openmoji", "data/openmoji.json")))
    emoji_annotations = {entry["hexcode"]: entry["annotation"] for entry in emoji_metadata}
    jobs = []
    for name in CAR_NAMES:
        if name not in logos:
            raise ValueError(f"Missing licensed upstream car logo: {name}; do not substitute")
        if "license" in logos[name]:
            raise ValueError(f"Car logo has a per-icon license override: {name}")
        slug = name.lower()
        jobs.append(("cars", slug, name, "simple-icons", f"icons/{slug}.svg", {
            "upstream_source": logos[name]["source"],
            **({"speech": "B M W"} if name == "BMW" else {}),
            **({"speech": "Mercedes Benz"} if name == "Mercedes" else {}),
        }))
    for category, entries in EMOJI.items():
        for slug, name, code in entries:
            if code not in emoji_annotations:
                raise ValueError(f"Unknown OpenMoji code: {code}")
            jobs.append((category, slug, name, "openmoji", f"color/svg/{code}.svg", {
                "upstream_annotation": emoji_annotations[code],
            }))
    for slug, name, code in FLAGS:
        jobs.append(("flags", slug, name, "flag-icons", f"flags/4x3/{code}.svg", {}))

    def fetch(job):
        category, slug, name, project, path, extra = job
        url = source_url(project, path)
        raw = download(url)
        validate_svg(raw)
        return category, slug, name, project, url, raw, extra

    def save(category, slug, name, project, url, raw, extra):
        target = DEST / category / f"{slug}.svg"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        categories[category]["items"].append({
            "id": slug, "name": name,
            "image": f"/static/quiz/{category}/{slug}.svg",
            "source": url, "license": LICENSES[project][0],
            "project": project, "sha256": hashlib.sha256(raw).hexdigest(),
            **extra,
        })

    with ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(fetch, jobs):
            save(*result)

    geo_url = source_url("natural-earth", "geojson/ne_10m_admin_0_countries.geojson")
    features = json.loads(download(geo_url))["features"]
    by_code = {feature["properties"]["ADM0_A3"]: feature for feature in features}
    for slug, name, code, central_longitude in COUNTRIES:
        geometry = by_code[code]["geometry"]
        raw, extra = country_svg(geometry, central_longitude)
        validate_svg(raw)
        save("countries", slug, name, "natural-earth", geo_url, raw, {
            "source_feature": f"ADM0_A3={code}",
            "changes": "Projected and fitted source coordinates; remote polygons in insets",
            **extra,
        })
    catalog = {"schema_version": 1, "categories": list(categories.values())}
    (DEST / "catalog.json").write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    attribution = build_attribution(catalog, license_texts)
    (ROOT / "docs" / "QUIZ-ASSET-LICENSES.md").write_text(attribution, encoding="utf-8")
    (DEST / "ATTRIBUTION.txt").write_text(attribution, encoding="utf-8")
    for category in categories.values():
        print(f"{category['id']}: {len(category['items'])}")


def build_attribution(catalog: dict, license_texts: dict) -> str:
    text = """# Offline quiz artwork: sources, attribution and licenses

These 73 SVG images are bundled locally. The quiz catalog never requests remote
artwork. `app/static/quiz/catalog.json` records each exact pinned source URL,
license, SHA-256, and (where relevant) original annotation or geometry feature.
This notice is also bundled as `/static/quiz/ATTRIBUTION.txt`.

## OpenMoji illustrations (40 images)

All emojis designed by OpenMoji — the open-source emoji and icon project.
Creators: Benedikt Groß, Hendrik Utz, and the OpenMoji contributors
(HfG Schwäbisch Gmünd). Project: https://openmoji.org/

License: Creative Commons Attribution-ShareAlike 4.0 International
(CC BY-SA 4.0): https://creativecommons.org/licenses/by-sa/4.0/

The animal, vegetable, fruit and bird SVGs are **unmodified upstream color SVGs**.
Their filenames and catalog display names differ; the artwork itself does not.
Retain attribution and the license notice when redistributing these images.
Adapted versions of these illustrations must be shared under CC BY-SA 4.0
(or a compatible license), with changes identified. This asset license does not
relicense the unrelated application code.

The orange is OpenMoji's “tangerine”; the apple is “red apple”; corn is
“ear of corn”; pepper is “bell pepper”. Tomato and eggplant use familiar
culinary vegetable categories, not botanical classification. These are real
published illustrations, not photographs or AI-generated guesses.

## Simple Icons car logos (15 images)

Unmodified monochrome SVGs from Simple Icons **11.15.0**, pinned to the commit
below (the annotated tag points to that commit). Upstream's repository license
is CC0 1.0 Universal: https://creativecommons.org/publicdomain/zero/1.0/
The selected icon records were checked for per-icon licensing overrides; none
has one. The table and catalog retain both the pinned file and the brand source
reported by that version of Simple Icons. No images were scraped from brand sites.

**Trademark caveat:** CC0 covers the supplied icon artwork only to the extent
the contributors can license it. It does not grant trademark, endorsement or
other third-party rights. Brand names and logos remain their owners' trademarks.
This independent educational identification quiz is not affiliated with,
sponsored by, or endorsed by any manufacturer. The selection is a starter set,
not “all brands”. Review local trademark rules before distributing commercially.
No unverified substitute logos were used and no requested starter brand was
omitted. Some real logos naturally contain lettering (including the name), so
these questions cannot always hide the answer completely.

Use a light image background: these originals are black monochrome marks.

## Natural Earth country silhouettes (8 images)

Made with Natural Earth. Authors: Tom Patterson, Nathaniel Vaughn Kelso and
Natural Earth contributors. Source is the pinned **1:10m Admin-0 Countries**
GeoJSON below. The upstream license explicitly places all map data in the
**public domain**, permitting modification and redistribution.

Changes: generated SVGs project the actual geographic coordinate rings using a
local equirectangular projection (longitude scaled by cos of the region's
mid-latitude), north up, then uniformly fit each panel. Antimeridian longitudes
are unwrapped around a country-specific central meridian. There is no invented
outline, arbitrary rotation, dropped polygon, or omitted hole. Nearby islands
are grouped with the mainland; remote territories/islands use pale framed
insets at independent scales, rather than being stretched, discarded or
overlaid on the mainland. Insets have no written labels to avoid giving away
quiz answers. Relative placement and scale between inset panels are not
geographic; shapes within each panel remain geographic.

Every polygon and ring **present in this generalized source feature** is
retained, including Alaska, Hawaii, French Guiana, Corsica, Tasmania and the
source's smaller islands. Natural Earth's 1:10m generalization is not an
exhaustive inventory of every real-world islet. Country/territory membership
and disputed boundaries follow upstream Admin-0 features, not a political
claim by this application. No sovereign dependencies are invented or silently
appended from other features.

## flag-icons flags (10 images)

Unmodified 4:3 SVGs from flag-icons by Panayiotis Lipiridis and contributors.
License: MIT. The full copyright and permission notice is included below and
in `/static/quiz/licenses/flag-icons.txt`. Country names are quiz answers;
SVGs do not add visible text labels.

## Catalog API

`app.quiz_catalog.CATEGORIES` is a tuple of dictionaries containing `id`, `name`,
`count`, `harder` (boolean), and a representative `image` (local URL) for each
category tile. IDs, in order: `cars`, `animals`, `vegetables`, `fruits`, `birds`,
`countries`, `flags`. Country shapes and flags are marked harder.

`get_items(category)` returns a fresh list of dictionaries with `id`, `name`,
`image`, and optional `speech` (for example BMW uses `B M W`). Unknown category
IDs raise `ValueError`. All image URLs begin `/static/quiz/`. The caller samples
and times the questions; five questions is a suitable default. This module does
not implement screens, playback, random selection or a network service.

## Reproducibility and offline use

Run `python tools\\fetch_quiz_assets.py` from the project root to refresh from
the same immutable public GitHub revisions. Only the standard library is used.
The tool downloads SVGs, license notices, and reference JSON/GeoJSON; it installs
no packages, models or videos. Reference datasets are processed in memory and
are not bundled. Production/runtime needs no network. The catalog module
validates local paths and missing files at load time. All attribution and full
upstream license texts ship with the local bundle; keep them with redistributions.

## Pinned upstream license evidence

"""
    for project, (license_name, license_path) in LICENSES.items():
        text += (
            f"- **{project}** — {license_name}; revision `{REVISIONS[project]}`; "
            f"[upstream license]({source_url(project, license_path)}); "
            f"local `app/static/quiz/licenses/{project}.txt`.\n"
        )
    text += (
        "\nOpenMoji's separate artwork/code licensing is stated in its "
        f"[pinned README]({source_url('openmoji', 'README.md')}). "
        "Only artwork is bundled, not its LGPL code.\n\n"
        "## Per-asset source ledger\n\n"
        "| Local SVG | Answer | License | Exact source / upstream provenance |\n"
        "| --- | --- | --- | --- |\n"
    )
    for category in catalog["categories"]:
        for item in category["items"]:
            provenance = (
                f"; brand source: {item['upstream_source']}"
                if "upstream_source" in item else ""
            )
            if "source_feature" in item:
                provenance += f"; feature `{item['source_feature']}`"
            text += (
                f"| `{item['image']}` | {item['name']} | {item['license']} | "
                f"[pinned source]({item['source']}){provenance} |\n"
            )
    text += "\n## Full bundled upstream license notices\n"
    for project, license_text in license_texts.items():
        text += f"\n### {project}\n\n```text\n{license_text.rstrip()}\n```\n"
    return text


if __name__ == "__main__":
    main()
