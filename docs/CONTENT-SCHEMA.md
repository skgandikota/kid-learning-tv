# Content schema reference

Content is local UTF-8 JSON. The authoritative category and nickname schemas are `content/schemas/category.schema.json` and `content/schemas/nicknames.schema.json`; runtime checks in `app/services/content.py` impose additional constraints.

## Category example

```json
{
  "id": "sample",
  "name": "Sample",
  "enabled": true,
  "answers": [
    {
      "name": "Example",
      "aliases": ["Sample answer"],
      "pronunciation": ["ig-zam-pul"],
      "image": "images/example.svg",
      "facts": ["A parent-reviewed fact."]
    }
  ]
}
```

The filename must be `sample.json`. IDs match `^[a-z0-9][a-z0-9-]*$`. Names are bounded; each answer requires a name, and category/answer/alias names are checked for normalized duplicates. `image`, if supplied, must be relative and must not include `..`; assets remain local.

## Other formats

- Nicknames: array of objects with required `name` (1–60 chars) and optional `enabled` boolean; names must be unique case-insensitively.
- Memory: `{ "id": "<filename-id>", "items": ["..."] }`, with a non-empty list of non-blank strings.
- Activity prompts: a list of entries with `id`, `name`, `prompt`, and optional `enabled`.

Run `python tools/content_validator.py` to validate categories, nicknames, and prompts. Memory files are checked when loaded for a game. Content suitability remains the parent's responsibility.
