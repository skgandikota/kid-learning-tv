"""Load and validate local content without allowing paths outside the content tree."""
from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator


class ContentError(ValueError):
    pass


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContentError(f"Cannot read JSON content {path.name}: {exc}") from exc


class ContentStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.category_schema = _load_json(self.root / "schemas" / "category.schema.json")
        self.nickname_schema = _load_json(self.root / "schemas" / "nicknames.schema.json")
        self.activity_schema = _load_json(self.root / "schemas" / "activity.schema.json")
        self.memory_schema = _load_json(self.root / "schemas" / "memory.schema.json")
        self.facts_schema = _load_json(self.root / "schemas" / "facts.schema.json")
        self.categories_dir = (self.root / "categories").resolve()
        self._category_validator = Draft202012Validator(self.category_schema)
        self._nickname_validator = Draft202012Validator(self.nickname_schema)
        self._activity_validator = Draft202012Validator(self.activity_schema)
        self._memory_validator = Draft202012Validator(self.memory_schema)
        self._facts_validator = Draft202012Validator(self.facts_schema)

    def _safe_file(self, directory: Path, name: str) -> Path:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,59}\.json", name):
            raise ContentError("Invalid content file name.")
        path = (directory / name).resolve()
        if path.parent != directory.resolve():
            raise ContentError("Content path is outside the allowed directory.")
        return path

    def validate_category(self, value: dict):
        errors = sorted(self._category_validator.iter_errors(value), key=lambda item: list(item.path))
        if errors:
            raise ContentError("; ".join(error.message for error in errors))
        seen = {}
        for index, answer in enumerate(value["answers"]):
            for label in [answer["name"], *answer.get("aliases", []), *answer.get("pronunciation", [])]:
                key = re.sub(r"[^a-z0-9]", "", label.casefold())
                if not key:
                    raise ContentError("Answers and aliases must contain letters or numbers.")
                if key in seen and seen[key] != index:
                    raise ContentError(f"Duplicate answer or alias: {label}")
                seen[key] = index
            for asset in (answer.get("image"), answer.get("audio")):
                if asset:
                    normalized_path = asset.replace("\\", "/")
                    if (
                        Path(normalized_path).is_absolute()
                        or ".." in Path(normalized_path).parts
                        or ":" in normalized_path
                    ):
                        raise ContentError("Asset paths must stay within the local assets folder.")

    def categories(self) -> list[dict]:
        result = []
        for path in sorted(self.categories_dir.glob("*.json")):
            value = _load_json(path)
            self.validate_category(value)
            if path.stem != value["id"]:
                raise ContentError(f"Category id must match its filename: {path.name}")
            result.append(value)
        ids = [item["id"] for item in result]
        if len(ids) != len(set(ids)):
            raise ContentError("Category IDs must be unique.")
        return result

    def category(self, category_id: str) -> dict | None:
        if not isinstance(category_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,59}", category_id):
            return None
        path = self._safe_file(self.categories_dir, f"{category_id}.json")
        if not path.is_file():
            return None
        value = _load_json(path)
        self.validate_category(value)
        if value["id"] != category_id:
            raise ContentError("Category id does not match its filename.")
        return value

    def save_category(self, value: dict):
        self.validate_category(value)
        path = self._safe_file(self.categories_dir, f"{value['id']}.json")
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    def nicknames(self) -> list[str]:
        data = _load_json(self.root / "nicknames.json")
        errors = sorted(self._nickname_validator.iter_errors(data), key=lambda item: list(item.path))
        if errors:
            raise ContentError("; ".join(error.message for error in errors))
        return [item["name"] for item in data if item.get("enabled", True)]

    def nickname_data(self) -> list[dict]:
        data = _load_json(self.root / "nicknames.json")
        errors = sorted(self._nickname_validator.iter_errors(data), key=lambda item: list(item.path))
        if errors:
            raise ContentError("; ".join(error.message for error in errors))
        return data

    def save_nicknames(self, value):
        errors = sorted(self._nickname_validator.iter_errors(value), key=lambda item: list(item.path))
        if errors:
            raise ContentError("; ".join(error.message for error in errors))
        names = [item["name"].casefold() for item in value]
        if len(names) != len(set(names)):
            raise ContentError("Nickname names must be unique.")
        path = self.root / "nicknames.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    def memory_category(self, category_id: str) -> dict | None:
        if not isinstance(category_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,59}", category_id):
            return None
        directory = (self.root / "memory").resolve()
        path = self._safe_file(directory, f"{category_id}.json")
        if not path.is_file():
            return None
        value = _load_json(path)
        errors = sorted(self._memory_validator.iter_errors(value), key=lambda item: list(item.path))
        if errors or value.get("id") != category_id:
            raise ContentError("Invalid memory category.")
        return value

    def prompts(self) -> list[dict]:
        data = _load_json(self.root / "activities" / "prompts.json")
        errors = sorted(self._activity_validator.iter_errors(data), key=lambda item: list(item.path))
        if errors:
            raise ContentError("; ".join(error.message for error in errors))
        ids = [item["id"] for item in data]
        if len(ids) != len(set(ids)):
            raise ContentError("Activity prompt IDs must be unique.")
        return [
            item for item in data
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and isinstance(item.get("prompt"), str)
            and item.get("enabled", True)
        ]

    def animal_facts(self) -> list[dict]:
        data = _load_json(self.root / "facts" / "animals.json")
        errors = sorted(self._facts_validator.iter_errors(data), key=lambda item: list(item.path))
        if errors:
            raise ContentError("; ".join(error.message for error in errors))
        return data

    def validate_all(self):
        self.categories()
        self.nicknames()
        self.prompts()
        self.animal_facts()
        for path in sorted((self.root / "memory").glob("*.json")):
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,59}", path.stem):
                raise ContentError(f"Invalid memory content filename: {path.name}")
            self.memory_category(path.stem)
