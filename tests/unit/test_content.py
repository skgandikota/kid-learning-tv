import json

import pytest

from app.services.content import ContentError, ContentStore


def test_all_packaged_content_validates():
    from pathlib import Path
    store = ContentStore(Path(__file__).resolve().parents[2] / "content")
    assert len(store.categories()) >= 8
    assert store.nicknames()
    assert store.prompts()


def test_duplicate_alias_and_unsafe_image_path_rejected(tmp_path):
    from pathlib import Path
    import shutil
    root = Path(__file__).resolve().parents[2] / "content"
    copy = tmp_path / "content"
    shutil.copytree(root, copy)
    store = ContentStore(copy)
    duplicate = {"id": "custom", "name": "Custom", "answers": [
        {"name": "Car", "aliases": []},
        {"name": "CAR", "aliases": []}
    ]}
    with pytest.raises(ContentError, match="Duplicate"):
        store.validate_category(duplicate)
    unsafe = {"id": "custom", "name": "Custom", "answers": [
        {"name": "Car", "image": "../secret.png"}
    ]}
    with pytest.raises(ContentError, match="paths"):
        store.validate_category(unsafe)


def test_category_file_id_and_schema_are_checked(tmp_path):
    from pathlib import Path
    import shutil
    root = Path(__file__).resolve().parents[2] / "content"
    copy = tmp_path / "content"
    shutil.copytree(root, copy)
    store = ContentStore(copy)
    (copy / "categories" / "broken.json").write_text(json.dumps({"id": "bad id", "name": "Bad", "answers": []}))
    with pytest.raises(ContentError):
        store.categories()
