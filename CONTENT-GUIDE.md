# Content guide

Learning content is local JSON under `content/`. Validate it before use with `bash scripts/validate-content.sh` on Linux or `PYTHONPATH=. python tools/content_validator.py` from the project root in a prepared Python environment.

## Category files

Each `content/categories/<id>.json` corresponds to a unique lower-case hyphenated ID and has an `id`, non-empty `name` (up to 60 characters), and an `answers` list. Each answer requires a unique `name`; optional fields include `aliases`, `pronunciation`, `image`, and `facts`. Image paths must be relative and cannot traverse parent directories. The exact enforced shape is in `content/schemas/category.schema.json`.

`content/memory/*.json` holds a category `id` and a list of non-empty item strings. `content/nicknames.json` is an array of `{ "name": "...", "enabled": true }` entries; names must be unique. `content/activities/prompts.json` holds enabled activity prompt objects.

## Safe editing

Keep filenames aligned to IDs, use UTF-8 JSON, avoid duplicate normalized answer names/aliases, and keep all assets local. Make a backup before editing. The app validates loaded content, but valid JSON alone does not guarantee age-appropriate or accurate educational material; a parent should review every change.
