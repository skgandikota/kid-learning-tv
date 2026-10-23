from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.main import create_app


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app(tmp_path):
    content = tmp_path / "content"
    shutil.copytree(ROOT / "content", content)
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "DATA_DIR": tmp_path / "data",
        "CONTENT_DIR": content,
        "SETTINGS": {
            "host": "127.0.0.1",
            "port": 8765,
            "session_minutes": 30,
            "break_reminder_minutes": 20,
            "retries": 1,
            "volume": 70,
            "muted": False,
            "voice_enabled": False,
            "tts_voice": "en-gb",
            "speech_rate": 145,
            "stt_profile": "manual-parent-assist",
            "history_enabled": False,
            "low_animation": False,
            "reduced_assets": False,
            "memory_level": 2,
            "memory_picture_seconds": 4,
            "memory_categories": ["shopping", "animals", "colours", "vehicles", "home"],
            "enabled_categories": [
                "animals", "cars", "london-stations", "fruits", "vegetables",
                "colours", "shapes", "dinosaurs", "countries", "things-at-home",
            ],
            "enabled_nicknames": None,
            "nicknames_enabled": True,
        },
    })


@pytest.fixture
def client(app):
    return app.test_client()


def csrf_for(client):
    page = client.get("/parent").get_data(as_text=True)
    import re
    return re.search(r'<meta name="csrf-token" content="([^"]+)"', page).group(1)


def setup_parent(client, pin="123456"):
    csrf = csrf_for(client)
    response = client.post("/api/setup", json={"pin": pin}, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    return response.get_json()["csrf_token"]


@pytest.fixture
def parent_client(client):
    token = setup_parent(client)
    client.environ_base["HTTP_X_CSRF_TOKEN"] = token
    return client
