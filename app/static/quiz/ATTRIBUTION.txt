# Offline quiz artwork: sources, attribution and licenses

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

Run `python tools\fetch_quiz_assets.py` from the project root to refresh from
the same immutable public GitHub revisions. Only the standard library is used.
The tool downloads SVGs, license notices, and reference JSON/GeoJSON; it installs
no packages, models or videos. Reference datasets are processed in memory and
are not bundled. Production/runtime needs no network. The catalog module
validates local paths and missing files at load time. All attribution and full
upstream license texts ship with the local bundle; keep them with redistributions.

## Pinned upstream license evidence

- **openmoji** — CC-BY-SA-4.0; revision `aeb8bb3a59e2de39c754ac79180c8131c906acea`; [upstream license](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/LICENSE.txt); local `app/static/quiz/licenses/openmoji.txt`.
- **simple-icons** — CC0-1.0; revision `0af835e2949a9222965522780e5e0810d3c53382`; [upstream license](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/LICENSE.md); local `app/static/quiz/licenses/simple-icons.txt`.
- **flag-icons** — MIT; revision `ac7e0eb3259eb62aa6100c435607e2fe03896a97`; [upstream license](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/LICENSE); local `app/static/quiz/licenses/flag-icons.txt`.
- **natural-earth** — Public domain; revision `ca96624a56bd078437bca8184e78163e5039ad19`; [upstream license](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/LICENSE.md); local `app/static/quiz/licenses/natural-earth.txt`.

OpenMoji's separate artwork/code licensing is stated in its [pinned README](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/README.md). Only artwork is bundled, not its LGPL code.

## Per-asset source ledger

| Local SVG | Answer | License | Exact source / upstream provenance |
| --- | --- | --- | --- |
| `/static/quiz/cars/audi.svg` | Audi | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/audi.svg); brand source: https://www.audi.com/ci/en/intro/basics/rings.html |
| `/static/quiz/cars/bmw.svg` | BMW | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/bmw.svg); brand source: https://www.bmw.de |
| `/static/quiz/cars/ford.svg` | Ford | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/ford.svg); brand source: https://secure.ford.com/brochures/ |
| `/static/quiz/cars/honda.svg` | Honda | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/honda.svg); brand source: https://www.honda.ie |
| `/static/quiz/cars/toyota.svg` | Toyota | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/toyota.svg); brand source: https://www.toyota.com/brandguidelines/logo/ |
| `/static/quiz/cars/mercedes.svg` | Mercedes | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/mercedes.svg); brand source: https://www.mercedes-benz.com |
| `/static/quiz/cars/tesla.svg` | Tesla | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/tesla.svg); brand source: https://www.tesla.com/tesla-gallery |
| `/static/quiz/cars/volkswagen.svg` | Volkswagen | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/volkswagen.svg); brand source: https://www.vw.com |
| `/static/quiz/cars/volvo.svg` | Volvo | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/volvo.svg); brand source: https://www.media.volvocars.com/global/en-gb/logos |
| `/static/quiz/cars/hyundai.svg` | Hyundai | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/hyundai.svg); brand source: https://www.hyundai.com |
| `/static/quiz/cars/nissan.svg` | Nissan | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/nissan.svg); brand source: https://www.nissan.ie |
| `/static/quiz/cars/kia.svg` | Kia | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/kia.svg); brand source: https://www.kia.com |
| `/static/quiz/cars/renault.svg` | Renault | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/renault.svg); brand source: https://en.media.groupe.renault.com/news/renault-news-march-2021-5f28-989c5.html |
| `/static/quiz/cars/peugeot.svg` | Peugeot | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/peugeot.svg); brand source: https://www.peugeot.co.uk |
| `/static/quiz/cars/suzuki.svg` | Suzuki | CC0-1.0 | [pinned source](https://raw.githubusercontent.com/simple-icons/simple-icons/0af835e2949a9222965522780e5e0810d3c53382/icons/suzuki.svg); brand source: https://www.suzuki.ie |
| `/static/quiz/animals/dog.svg` | Dog | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F415.svg) |
| `/static/quiz/animals/cat.svg` | Cat | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F408.svg) |
| `/static/quiz/animals/lion.svg` | Lion | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F981.svg) |
| `/static/quiz/animals/elephant.svg` | Elephant | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F418.svg) |
| `/static/quiz/animals/giraffe.svg` | Giraffe | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F992.svg) |
| `/static/quiz/animals/zebra.svg` | Zebra | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F993.svg) |
| `/static/quiz/animals/monkey.svg` | Monkey | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F412.svg) |
| `/static/quiz/animals/rabbit.svg` | Rabbit | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F407.svg) |
| `/static/quiz/animals/cow.svg` | Cow | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F404.svg) |
| `/static/quiz/animals/pig.svg` | Pig | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F416.svg) |
| `/static/quiz/vegetables/carrot.svg` | Carrot | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F955.svg) |
| `/static/quiz/vegetables/broccoli.svg` | Broccoli | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F966.svg) |
| `/static/quiz/vegetables/potato.svg` | Potato | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F954.svg) |
| `/static/quiz/vegetables/tomato.svg` | Tomato | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F345.svg) |
| `/static/quiz/vegetables/cucumber.svg` | Cucumber | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F952.svg) |
| `/static/quiz/vegetables/corn.svg` | Corn | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F33D.svg) |
| `/static/quiz/vegetables/onion.svg` | Onion | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F9C5.svg) |
| `/static/quiz/vegetables/pepper.svg` | Pepper | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1FAD1.svg) |
| `/static/quiz/vegetables/eggplant.svg` | Eggplant | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F346.svg) |
| `/static/quiz/vegetables/hot-pepper.svg` | Chilli pepper | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F336.svg) |
| `/static/quiz/fruits/apple.svg` | Apple | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F34E.svg) |
| `/static/quiz/fruits/banana.svg` | Banana | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F34C.svg) |
| `/static/quiz/fruits/orange.svg` | Orange | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F34A.svg) |
| `/static/quiz/fruits/grapes.svg` | Grapes | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F347.svg) |
| `/static/quiz/fruits/strawberry.svg` | Strawberry | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F353.svg) |
| `/static/quiz/fruits/watermelon.svg` | Watermelon | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F349.svg) |
| `/static/quiz/fruits/pineapple.svg` | Pineapple | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F34D.svg) |
| `/static/quiz/fruits/pear.svg` | Pear | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F350.svg) |
| `/static/quiz/fruits/peach.svg` | Peach | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F351.svg) |
| `/static/quiz/fruits/cherries.svg` | Cherries | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F352.svg) |
| `/static/quiz/birds/parrot.svg` | Parrot | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F99C.svg) |
| `/static/quiz/birds/chicken.svg` | Chicken | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F414.svg) |
| `/static/quiz/birds/duck.svg` | Duck | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F986.svg) |
| `/static/quiz/birds/penguin.svg` | Penguin | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F427.svg) |
| `/static/quiz/birds/owl.svg` | Owl | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F989.svg) |
| `/static/quiz/birds/eagle.svg` | Eagle | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F985.svg) |
| `/static/quiz/birds/dove.svg` | Dove | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F54A.svg) |
| `/static/quiz/birds/turkey.svg` | Turkey | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F983.svg) |
| `/static/quiz/birds/flamingo.svg` | Flamingo | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F9A9.svg) |
| `/static/quiz/birds/peacock.svg` | Peacock | CC-BY-SA-4.0 | [pinned source](https://raw.githubusercontent.com/hfg-gmuend/openmoji/aeb8bb3a59e2de39c754ac79180c8131c906acea/color/svg/1F99A.svg) |
| `/static/quiz/countries/united-kingdom.svg` | United Kingdom | Public domain | [pinned source](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_10m_admin_0_countries.geojson); feature `ADM0_A3=GBR` |
| `/static/quiz/countries/india.svg` | India | Public domain | [pinned source](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_10m_admin_0_countries.geojson); feature `ADM0_A3=IND` |
| `/static/quiz/countries/italy.svg` | Italy | Public domain | [pinned source](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_10m_admin_0_countries.geojson); feature `ADM0_A3=ITA` |
| `/static/quiz/countries/australia.svg` | Australia | Public domain | [pinned source](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_10m_admin_0_countries.geojson); feature `ADM0_A3=AUS` |
| `/static/quiz/countries/japan.svg` | Japan | Public domain | [pinned source](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_10m_admin_0_countries.geojson); feature `ADM0_A3=JPN` |
| `/static/quiz/countries/france.svg` | France | Public domain | [pinned source](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_10m_admin_0_countries.geojson); feature `ADM0_A3=FRA` |
| `/static/quiz/countries/brazil.svg` | Brazil | Public domain | [pinned source](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_10m_admin_0_countries.geojson); feature `ADM0_A3=BRA` |
| `/static/quiz/countries/united-states.svg` | United States | Public domain | [pinned source](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_10m_admin_0_countries.geojson); feature `ADM0_A3=USA` |
| `/static/quiz/flags/india.svg` | India | MIT | [pinned source](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/flags/4x3/in.svg) |
| `/static/quiz/flags/united-kingdom.svg` | United Kingdom | MIT | [pinned source](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/flags/4x3/gb.svg) |
| `/static/quiz/flags/united-states.svg` | United States | MIT | [pinned source](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/flags/4x3/us.svg) |
| `/static/quiz/flags/france.svg` | France | MIT | [pinned source](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/flags/4x3/fr.svg) |
| `/static/quiz/flags/japan.svg` | Japan | MIT | [pinned source](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/flags/4x3/jp.svg) |
| `/static/quiz/flags/italy.svg` | Italy | MIT | [pinned source](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/flags/4x3/it.svg) |
| `/static/quiz/flags/brazil.svg` | Brazil | MIT | [pinned source](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/flags/4x3/br.svg) |
| `/static/quiz/flags/germany.svg` | Germany | MIT | [pinned source](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/flags/4x3/de.svg) |
| `/static/quiz/flags/canada.svg` | Canada | MIT | [pinned source](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/flags/4x3/ca.svg) |
| `/static/quiz/flags/australia.svg` | Australia | MIT | [pinned source](https://raw.githubusercontent.com/lipis/flag-icons/ac7e0eb3259eb62aa6100c435607e2fe03896a97/flags/4x3/au.svg) |

## Full bundled upstream license notices

### openmoji

```text
Attribution-ShareAlike 4.0 International

=======================================================================

Creative Commons Corporation ("Creative Commons") is not a law firm and
does not provide legal services or legal advice. Distribution of
Creative Commons public licenses does not create a lawyer-client or
other relationship. Creative Commons makes its licenses and related
information available on an "as-is" basis. Creative Commons gives no
warranties regarding its licenses, any material licensed under their
terms and conditions, or any related information. Creative Commons
disclaims all liability for damages resulting from their use to the
fullest extent possible.

Using Creative Commons Public Licenses

Creative Commons public licenses provide a standard set of terms and
conditions that creators and other rights holders may use to share
original works of authorship and other material subject to copyright
and certain other rights specified in the public license below. The
following considerations are for informational purposes only, are not
exhaustive, and do not form part of our licenses.

     Considerations for licensors: Our public licenses are
     intended for use by those authorized to give the public
     permission to use material in ways otherwise restricted by
     copyright and certain other rights. Our licenses are
     irrevocable. Licensors should read and understand the terms
     and conditions of the license they choose before applying it.
     Licensors should also secure all rights necessary before
     applying our licenses so that the public can reuse the
     material as expected. Licensors should clearly mark any
     material not subject to the license. This includes other CC-
     licensed material, or material used under an exception or
     limitation to copyright. More considerations for licensors:
    wiki.creativecommons.org/Considerations_for_licensors

     Considerations for the public: By using one of our public
     licenses, a licensor grants the public permission to use the
     licensed material under specified terms and conditions. If
     the licensor's permission is not necessary for any reason--for
     example, because of any applicable exception or limitation to
     copyright--then that use is not regulated by the license. Our
     licenses grant only permissions under copyright and certain
     other rights that a licensor has authority to grant. Use of
     the licensed material may still be restricted for other
     reasons, including because others have copyright or other
     rights in the material. A licensor may make special requests,
     such as asking that all changes be marked or described.
     Although not required by our licenses, you are encouraged to
     respect those requests where reasonable. More considerations
     for the public:
    wiki.creativecommons.org/Considerations_for_licensees

=======================================================================

Creative Commons Attribution-ShareAlike 4.0 International Public
License

By exercising the Licensed Rights (defined below), You accept and agree
to be bound by the terms and conditions of this Creative Commons
Attribution-ShareAlike 4.0 International Public License ("Public
License"). To the extent this Public License may be interpreted as a
contract, You are granted the Licensed Rights in consideration of Your
acceptance of these terms and conditions, and the Licensor grants You
such rights in consideration of benefits the Licensor receives from
making the Licensed Material available under these terms and
conditions.


Section 1 -- Definitions.

  a. Adapted Material means material subject to Copyright and Similar
     Rights that is derived from or based upon the Licensed Material
     and in which the Licensed Material is translated, altered,
     arranged, transformed, or otherwise modified in a manner requiring
     permission under the Copyright and Similar Rights held by the
     Licensor. For purposes of this Public License, where the Licensed
     Material is a musical work, performance, or sound recording,
     Adapted Material is always produced where the Licensed Material is
     synched in timed relation with a moving image.

  b. Adapter's License means the license You apply to Your Copyright
     and Similar Rights in Your contributions to Adapted Material in
     accordance with the terms and conditions of this Public License.

  c. BY-SA Compatible License means a license listed at
     creativecommons.org/compatiblelicenses, approved by Creative
     Commons as essentially the equivalent of this Public License.

  d. Copyright and Similar Rights means copyright and/or similar rights
     closely related to copyright including, without limitation,
     performance, broadcast, sound recording, and Sui Generis Database
     Rights, without regard to how the rights are labeled or
     categorized. For purposes of this Public License, the rights
     specified in Section 2(b)(1)-(2) are not Copyright and Similar
     Rights.

  e. Effective Technological Measures means those measures that, in the
     absence of proper authority, may not be circumvented under laws
     fulfilling obligations under Article 11 of the WIPO Copyright
     Treaty adopted on December 20, 1996, and/or similar international
     agreements.

  f. Exceptions and Limitations means fair use, fair dealing, and/or
     any other exception or limitation to Copyright and Similar Rights
     that applies to Your use of the Licensed Material.

  g. License Elements means the license attributes listed in the name
     of a Creative Commons Public License. The License Elements of this
     Public License are Attribution and ShareAlike.

  h. Licensed Material means the artistic or literary work, database,
     or other material to which the Licensor applied this Public
     License.

  i. Licensed Rights means the rights granted to You subject to the
     terms and conditions of this Public License, which are limited to
     all Copyright and Similar Rights that apply to Your use of the
     Licensed Material and that the Licensor has authority to license.

  j. Licensor means the individual(s) or entity(ies) granting rights
     under this Public License.

  k. Share means to provide material to the public by any means or
     process that requires permission under the Licensed Rights, such
     as reproduction, public display, public performance, distribution,
     dissemination, communication, or importation, and to make material
     available to the public including in ways that members of the
     public may access the material from a place and at a time
     individually chosen by them.

  l. Sui Generis Database Rights means rights other than copyright
     resulting from Directive 96/9/EC of the European Parliament and of
     the Council of 11 March 1996 on the legal protection of databases,
     as amended and/or succeeded, as well as other essentially
     equivalent rights anywhere in the world.

  m. You means the individual or entity exercising the Licensed Rights
     under this Public License. Your has a corresponding meaning.


Section 2 -- Scope.

  a. License grant.

       1. Subject to the terms and conditions of this Public License,
          the Licensor hereby grants You a worldwide, royalty-free,
          non-sublicensable, non-exclusive, irrevocable license to
          exercise the Licensed Rights in the Licensed Material to:

            a. reproduce and Share the Licensed Material, in whole or
               in part; and

            b. produce, reproduce, and Share Adapted Material.

       2. Exceptions and Limitations. For the avoidance of doubt, where
          Exceptions and Limitations apply to Your use, this Public
          License does not apply, and You do not need to comply with
          its terms and conditions.

       3. Term. The term of this Public License is specified in Section
          6(a).

       4. Media and formats; technical modifications allowed. The
          Licensor authorizes You to exercise the Licensed Rights in
          all media and formats whether now known or hereafter created,
          and to make technical modifications necessary to do so. The
          Licensor waives and/or agrees not to assert any right or
          authority to forbid You from making technical modifications
          necessary to exercise the Licensed Rights, including
          technical modifications necessary to circumvent Effective
          Technological Measures. For purposes of this Public License,
          simply making modifications authorized by this Section 2(a)
          (4) never produces Adapted Material.

       5. Downstream recipients.

            a. Offer from the Licensor -- Licensed Material. Every
               recipient of the Licensed Material automatically
               receives an offer from the Licensor to exercise the
               Licensed Rights under the terms and conditions of this
               Public License.

            b. Additional offer from the Licensor -- Adapted Material.
               Every recipient of Adapted Material from You
               automatically receives an offer from the Licensor to
               exercise the Licensed Rights in the Adapted Material
               under the conditions of the Adapter's License You apply.

            c. No downstream restrictions. You may not offer or impose
               any additional or different terms or conditions on, or
               apply any Effective Technological Measures to, the
               Licensed Material if doing so restricts exercise of the
               Licensed Rights by any recipient of the Licensed
               Material.

       6. No endorsement. Nothing in this Public License constitutes or
          may be construed as permission to assert or imply that You
          are, or that Your use of the Licensed Material is, connected
          with, or sponsored, endorsed, or granted official status by,
          the Licensor or others designated to receive attribution as
          provided in Section 3(a)(1)(A)(i).

  b. Other rights.

       1. Moral rights, such as the right of integrity, are not
          licensed under this Public License, nor are publicity,
          privacy, and/or other similar personality rights; however, to
          the extent possible, the Licensor waives and/or agrees not to
          assert any such rights held by the Licensor to the limited
          extent necessary to allow You to exercise the Licensed
          Rights, but not otherwise.

       2. Patent and trademark rights are not licensed under this
          Public License.

       3. To the extent possible, the Licensor waives any right to
          collect royalties from You for the exercise of the Licensed
          Rights, whether directly or through a collecting society
          under any voluntary or waivable statutory or compulsory
          licensing scheme. In all other cases the Licensor expressly
          reserves any right to collect such royalties.


Section 3 -- License Conditions.

Your exercise of the Licensed Rights is expressly made subject to the
following conditions.

  a. Attribution.

       1. If You Share the Licensed Material (including in modified
          form), You must:

            a. retain the following if it is supplied by the Licensor
               with the Licensed Material:

                 i. identification of the creator(s) of the Licensed
                    Material and any others designated to receive
                    attribution, in any reasonable manner requested by
                    the Licensor (including by pseudonym if
                    designated);

                ii. a copyright notice;

               iii. a notice that refers to this Public License;

                iv. a notice that refers to the disclaimer of
                    warranties;

                 v. a URI or hyperlink to the Licensed Material to the
                    extent reasonably practicable;

            b. indicate if You modified the Licensed Material and
               retain an indication of any previous modifications; and

            c. indicate the Licensed Material is licensed under this
               Public License, and include the text of, or the URI or
               hyperlink to, this Public License.

       2. You may satisfy the conditions in Section 3(a)(1) in any
          reasonable manner based on the medium, means, and context in
          which You Share the Licensed Material. For example, it may be
          reasonable to satisfy the conditions by providing a URI or
          hyperlink to a resource that includes the required
          information.

       3. If requested by the Licensor, You must remove any of the
          information required by Section 3(a)(1)(A) to the extent
          reasonably practicable.

  b. ShareAlike.

     In addition to the conditions in Section 3(a), if You Share
     Adapted Material You produce, the following conditions also apply.

       1. The Adapter's License You apply must be a Creative Commons
          license with the same License Elements, this version or
          later, or a BY-SA Compatible License.

       2. You must include the text of, or the URI or hyperlink to, the
          Adapter's License You apply. You may satisfy this condition
          in any reasonable manner based on the medium, means, and
          context in which You Share Adapted Material.

       3. You may not offer or impose any additional or different terms
          or conditions on, or apply any Effective Technological
          Measures to, Adapted Material that restrict exercise of the
          rights granted under the Adapter's License You apply.


Section 4 -- Sui Generis Database Rights.

Where the Licensed Rights include Sui Generis Database Rights that
apply to Your use of the Licensed Material:

  a. for the avoidance of doubt, Section 2(a)(1) grants You the right
     to extract, reuse, reproduce, and Share all or a substantial
     portion of the contents of the database;

  b. if You include all or a substantial portion of the database
     contents in a database in which You have Sui Generis Database
     Rights, then the database in which You have Sui Generis Database
     Rights (but not its individual contents) is Adapted Material,

     including for purposes of Section 3(b); and
  c. You must comply with the conditions in Section 3(a) if You Share
     all or a substantial portion of the contents of the database.

For the avoidance of doubt, this Section 4 supplements and does not
replace Your obligations under this Public License where the Licensed
Rights include other Copyright and Similar Rights.


Section 5 -- Disclaimer of Warranties and Limitation of Liability.

  a. UNLESS OTHERWISE SEPARATELY UNDERTAKEN BY THE LICENSOR, TO THE
     EXTENT POSSIBLE, THE LICENSOR OFFERS THE LICENSED MATERIAL AS-IS
     AND AS-AVAILABLE, AND MAKES NO REPRESENTATIONS OR WARRANTIES OF
     ANY KIND CONCERNING THE LICENSED MATERIAL, WHETHER EXPRESS,
     IMPLIED, STATUTORY, OR OTHER. THIS INCLUDES, WITHOUT LIMITATION,
     WARRANTIES OF TITLE, MERCHANTABILITY, FITNESS FOR A PARTICULAR
     PURPOSE, NON-INFRINGEMENT, ABSENCE OF LATENT OR OTHER DEFECTS,
     ACCURACY, OR THE PRESENCE OR ABSENCE OF ERRORS, WHETHER OR NOT
     KNOWN OR DISCOVERABLE. WHERE DISCLAIMERS OF WARRANTIES ARE NOT
     ALLOWED IN FULL OR IN PART, THIS DISCLAIMER MAY NOT APPLY TO YOU.

  b. TO THE EXTENT POSSIBLE, IN NO EVENT WILL THE LICENSOR BE LIABLE
     TO YOU ON ANY LEGAL THEORY (INCLUDING, WITHOUT LIMITATION,
     NEGLIGENCE) OR OTHERWISE FOR ANY DIRECT, SPECIAL, INDIRECT,
     INCIDENTAL, CONSEQUENTIAL, PUNITIVE, EXEMPLARY, OR OTHER LOSSES,
     COSTS, EXPENSES, OR DAMAGES ARISING OUT OF THIS PUBLIC LICENSE OR
     USE OF THE LICENSED MATERIAL, EVEN IF THE LICENSOR HAS BEEN
     ADVISED OF THE POSSIBILITY OF SUCH LOSSES, COSTS, EXPENSES, OR
     DAMAGES. WHERE A LIMITATION OF LIABILITY IS NOT ALLOWED IN FULL OR
     IN PART, THIS LIMITATION MAY NOT APPLY TO YOU.

  c. The disclaimer of warranties and limitation of liability provided
     above shall be interpreted in a manner that, to the extent
     possible, most closely approximates an absolute disclaimer and
     waiver of all liability.


Section 6 -- Term and Termination.

  a. This Public License applies for the term of the Copyright and
     Similar Rights licensed here. However, if You fail to comply with
     this Public License, then Your rights under this Public License
     terminate automatically.

  b. Where Your right to use the Licensed Material has terminated under
     Section 6(a), it reinstates:

       1. automatically as of the date the violation is cured, provided
          it is cured within 30 days of Your discovery of the
          violation; or

       2. upon express reinstatement by the Licensor.

     For the avoidance of doubt, this Section 6(b) does not affect any
     right the Licensor may have to seek remedies for Your violations
     of this Public License.

  c. For the avoidance of doubt, the Licensor may also offer the
     Licensed Material under separate terms or conditions or stop
     distributing the Licensed Material at any time; however, doing so
     will not terminate this Public License.

  d. Sections 1, 5, 6, 7, and 8 survive termination of this Public
     License.


Section 7 -- Other Terms and Conditions.

  a. The Licensor shall not be bound by any additional or different
     terms or conditions communicated by You unless expressly agreed.

  b. Any arrangements, understandings, or agreements regarding the
     Licensed Material not stated herein are separate from and
     independent of the terms and conditions of this Public License.


Section 8 -- Interpretation.

  a. For the avoidance of doubt, this Public License does not, and
     shall not be interpreted to, reduce, limit, restrict, or impose
     conditions on any use of the Licensed Material that could lawfully
     be made without permission under this Public License.

  b. To the extent possible, if any provision of this Public License is
     deemed unenforceable, it shall be automatically reformed to the
     minimum extent necessary to make it enforceable. If the provision
     cannot be reformed, it shall be severed from this Public License
     without affecting the enforceability of the remaining terms and
     conditions.

  c. No term or condition of this Public License will be waived and no
     failure to comply consented to unless expressly agreed to by the
     Licensor.

  d. Nothing in this Public License constitutes or may be interpreted
     as a limitation upon, or waiver of, any privileges and immunities
     that apply to the Licensor or You, including from the legal
     processes of any jurisdiction or authority.


=======================================================================

Creative Commons is not a party to its public
licenses. Notwithstanding, Creative Commons may elect to apply one of
its public licenses to material it publishes and in those instances
will be considered the “Licensor.” The text of the Creative Commons
public licenses is dedicated to the public domain under the CC0 Public
Domain Dedication. Except for the limited purpose of indicating that
material is shared under a Creative Commons public license or as
otherwise permitted by the Creative Commons policies published at
creativecommons.org/policies, Creative Commons does not authorize the
use of the trademark "Creative Commons" or any other trademark or logo
of Creative Commons without its prior written consent including,
without limitation, in connection with any unauthorized modifications
to any of its public licenses or any other arrangements,
understandings, or agreements concerning use of licensed material. For
the avoidance of doubt, this paragraph does not form part of the
public licenses.

Creative Commons may be contacted at creativecommons.org.
```

### simple-icons

```text
# CC0 1.0 Universal

## Statement of Purpose

The laws of most jurisdictions throughout the world automatically confer exclusive Copyright and Related Rights (defined below) upon the creator and subsequent owner(s) (each and all, an “owner”) of an original work of authorship and/or a database (each, a “Work”).

Certain owners wish to permanently relinquish those rights to a Work for the purpose of contributing to a commons of creative, cultural and scientific works (“Commons”) that the public can reliably and without fear of later claims of infringement build upon, modify, incorporate in other works, reuse and redistribute as freely as possible in any form whatsoever and for any purposes, including without limitation commercial purposes. These owners may contribute to the Commons to promote the ideal of a free culture and the further production of creative, cultural and scientific works, or to gain reputation or greater distribution for their Work in part through the use and efforts of others.

For these and/or other purposes and motivations, and without any expectation of additional consideration or compensation, the person associating CC0 with a Work (the “Affirmer”), to the extent that he or she is an owner of Copyright and Related Rights in the Work, voluntarily elects to apply CC0 to the Work and publicly distribute the Work under its terms, with knowledge of his or her Copyright and Related Rights in the Work and the meaning and intended legal effect of CC0 on those rights.

1. Copyright and Related Rights. A Work made available under CC0 may be protected by copyright and related or neighboring rights (“Copyright and Related Rights”). Copyright and Related Rights include, but are not limited to, the following:
    1. the right to reproduce, adapt, distribute, perform, display, communicate, and translate a Work;
    2. moral rights retained by the original author(s) and/or performer(s);
    3. publicity and privacy rights pertaining to a person’s image or likeness depicted in a Work;
    4. rights protecting against unfair competition in regards to a Work, subject to the limitations in paragraph 4(i), below;
    5. rights protecting the extraction, dissemination, use and reuse of data in a Work;
    6. database rights (such as those arising under Directive 96/9/EC of the European Parliament and of the Council of 11 March 1996 on the legal protection of databases, and under any national implementation thereof, including any amended or successor version of such directive); and
    7. other similar, equivalent or corresponding rights throughout the world based on applicable law or treaty, and any national implementations thereof.

2. Waiver. To the greatest extent permitted by, but not in contravention of, applicable law, Affirmer hereby overtly, fully, permanently, irrevocably and unconditionally waives, abandons, and surrenders all of Affirmer’s Copyright and Related Rights and associated claims and causes of action, whether now known or unknown (including existing as well as future claims and causes of action), in the Work (i) in all territories worldwide, (ii) for the maximum duration provided by applicable law or treaty (including future time extensions), (iii) in any current or future medium and for any number of copies, and (iv) for any purpose whatsoever, including without limitation commercial, advertising or promotional purposes (the “Waiver”). Affirmer makes the Waiver for the benefit of each member of the public at large and to the detriment of Affirmer’s heirs and successors, fully intending that such Waiver shall not be subject to revocation, rescission, cancellation, termination, or any other legal or equitable action to disrupt the quiet enjoyment of the Work by the public as contemplated by Affirmer’s express Statement of Purpose.

3. Public License Fallback. Should any part of the Waiver for any reason be judged legally invalid or ineffective under applicable law, then the Waiver shall be preserved to the maximum extent permitted taking into account Affirmer’s express Statement of Purpose. In addition, to the extent the Waiver is so judged Affirmer hereby grants to each affected person a royalty-free, non transferable, non sublicensable, non exclusive, irrevocable and unconditional license to exercise Affirmer’s Copyright and Related Rights in the Work (i) in all territories worldwide, (ii) for the maximum duration provided by applicable law or treaty (including future time extensions), (iii) in any current or future medium and for any number of copies, and (iv) for any purpose whatsoever, including without limitation commercial, advertising or promotional purposes (the “License”). The License shall be deemed effective as of the date CC0 was applied by Affirmer to the Work. Should any part of the License for any reason be judged legally invalid or ineffective under applicable law, such partial invalidity or ineffectiveness shall not invalidate the remainder of the License, and in such case Affirmer hereby affirms that he or she will not (i) exercise any of his or her remaining Copyright and Related Rights in the Work or (ii) assert any associated claims and causes of action with respect to the Work, in either case contrary to Affirmer’s express Statement of Purpose.

4. Limitations and Disclaimers.
    1. No trademark or patent rights held by Affirmer are waived, abandoned, surrendered, licensed or otherwise affected by this document.
    2. Affirmer offers the Work as-is and makes no representations or warranties of any kind concerning the Work, express, implied, statutory or otherwise, including without limitation warranties of title, merchantability, fitness for a particular purpose, non infringement, or the absence of latent or other defects, accuracy, or the present or absence of errors, whether or not discoverable, all to the greatest extent permissible under applicable law.
    3. Affirmer disclaims responsibility for clearing rights of other persons that may apply to the Work or any use thereof, including without limitation any person’s Copyright and Related Rights in the Work. Further, Affirmer disclaims responsibility for obtaining any necessary consents, permissions or other rights required for any use of the Work.
    4. Affirmer understands and acknowledges that Creative Commons is not a party to this document and has no duty or obligation with respect to this CC0 or use of the Work.

For more information, please see https://creativecommons.org/publicdomain/zero/1.0/.
```

### flag-icons

```text
The MIT License (MIT)

Copyright (c) 2013 Panayiotis Lipiridis

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### natural-earth

```text
# Everything here is public domain.

[Full terms of service »](http://www.naturalearthdata.com/about/terms-of-use/)

All versions of Natural Earth raster + vector map data found on this website are in the public domain. You may use the maps in any manner, including modifying the content and design, electronic dissemination, and offset printing. The primary authors, _Tom Patterson_ and _Nathaniel Vaughn Kelso_, and all other contributors renounce all financial claim to the maps and invites you to use them for personal, educational, and commercial purposes.

# Credits

No permission is needed to use Natural Earth. Crediting the authors is unnecessary.

However, if you wish to cite the map data, simply use one of the following.

    Short text: Made with Natural Earth.
    
    Long text: Made with Natural Earth. Free vector and raster map data @ naturalearthdata.com.

Three logo options:

![Blue with white](http://www.naturalearthdata.com/wp-content/uploads/2009/08/NEV-Logo-color_sm.png)

[Download Large Transparent PNG](http://www.naturalearthdata.com/wp-content/uploads/2009/08/NEV-Logo-color.png)
[Download EPS](http://www.naturalearthdata.com/wp-content/uploads/2009/08/NEV%20Logo%20color.zip)

![Black with white](http://www.naturalearthdata.com/wp-content/uploads/2009/08/NEV-Logo-Black_sm.png)

[Download Large Transparent PNG](http://www.naturalearthdata.com/wp-content/uploads/2009/08/NEV-Logo-Black.png)
[Download EPS](http://www.naturalearthdata.com/wp-content/uploads/2009/08/NEV%20Logo%20Black.zip)


![White with transparent](http://www.naturalearthdata.com/wp-content/uploads/2009/08/NEV-Logo-White_sm.png)

[Download Large Transparent PNG](http://www.naturalearthdata.com/wp-content/uploads/2009/08/NEV-Logo-White.png)
[Download EPS](http://www.naturalearthdata.com/wp-content/uploads/2009/08/NEV%20Logo%20White.zip)

# Your due diligence

All users of Natural Earth are highly encouraged to read about data sources and manipulation in the [Data Creation](http://www.naturalearthdata.com/about/data-creation/) section.

The authors provide Natural Earth as a public service and are not responsible for any problems relating to accuracy, content, design, and how it is used. If you find an error or omission, please [report it](http://www.naturalearthdata.com/corrections/index.php?a=add) for future updates.

# Releases

The authors used data from The Washington Post, here is their release:

    Natural Earth is hereby granted a non-exclusive license to use the data being 
    provided by The Washington Post for the sole purpose of creating a world base map.  
    The Washington Post makes no claims as to the completeness, accuracy or content of 
    the data, and makes no representation of any kind, including, but not limited to, 
    any warranty as to the accuracy or fitness of the data for a particular use (nor 
    shall the act of distribution constitute any such warranty). No responsibility is 
    assumed by The Washington Post for any claims arising out of Natural Earth’s use 
    of the data.

The author’s used river and lake data (for Europe only) from the European Commission, Joint Research Centre, Institute for Environment and Sustainability, here is their release:

    Natural Earth is hereby granted a non-exclusive license to use the data being 
    provided by European Commission, Joint Research Centre, Institute for Environment 
    and Sustainability (JRC IES) for the sole purpose of creating a world base map. The 
    EC JRC IES makes no claims as to the completeness, accuracy or content of the data, 
    and makes no representation of any kind, including, but not limited to, any warranty 
    as to the accuracy or fitness of the data for a particular use (nor shall the act of 
    distribution constitute any such warranty). No responsibility is assumed by EC JRC 
    IES for any claims arising out of Natural Earth’s use of the data.

The author’s used road transportation data (for North America only) from XNR Productions, here is their release:

    Natural Earth is hereby granted a non-exclusive license to use the data being 
    provided by XNR Productions for the sole purpose of creating a world base map. 
    XNR makes no claims as to the completeness, accuracy or content of the data, and 
    makes no representation of any kind, including, but not limited to, any warranty 
    as to the accuracy or fitness of the data for a particular use (nor shall the act 
    of distribution constitute any such warranty). No responsibility is assumed by XNR 
    for any claims arising out of Natural Earth’s use of the data.

Happy mapping!
```
