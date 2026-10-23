import sqlite3
import re

import pytest

from app.auth.security import hash_pin
from app.main import create_app
from tests.conftest import csrf_for


def test_tv_starts_blank_and_has_no_controls(client):
    page = client.get("/")
    assert page.status_code == 200
    assert 'alt="" draggable="false" hidden' in page.text
    assert "<button" not in page.text
    assert "no-store" in page.headers["Cache-Control"]


def test_parent_login_logout_and_refresh(client, app):
    app.extensions["klt_db"].set_pin_hash(hash_pin("123456"))
    token = csrf_for(client)
    assert "Parent login" in client.get("/parent").text
    response = client.post("/api/login", json={"pin": "123456"}, headers={"X-CSRF-Token": token})
    assert response.status_code == 200
    page = client.get("/parent").text
    assert "Signed in." in page
    assert '<form id="login"' not in page
    assert "Avocado" not in page
    assert 'id="food-time"' in page
    assert client.post("/api/logout", json={}, headers={"X-CSRF-Token": token}).status_code == 400
    assert client.post("/api/logout", json={}, headers={"X-CSRF-Token": response.json["csrf_token"]}).status_code == 200
    assert "Parent login" in client.get("/parent").text


def test_food_time_requires_parent_login_csrf_and_boolean(client, app):
    token = csrf_for(client)
    headers = {"X-CSRF-Token": token}
    assert 'id="food-time"' not in client.get("/parent").text
    assert client.post("/api/parent/food-time", json={"enabled": True}, headers=headers).status_code == 401
    app.extensions["klt_db"].set_pin_hash(hash_pin("123456"))
    login = client.post("/api/login", json={"pin": "123456"}, headers=headers)
    headers = {"X-CSRF-Token": login.json["csrf_token"]}
    assert client.post("/api/parent/food-time", json={"enabled": True}).status_code == 400
    for invalid in ("true", 1, None):
        assert client.post("/api/parent/food-time", json={"enabled": invalid}, headers=headers).status_code == 400
    assert client.get("/api/display").json["food_time"] is False
    assert client.post("/api/parent/food-time", json={"enabled": True}, headers=headers).json["food_time"] is True
    assert client.get("/api/display").json["food_time"] is True
    assert not re.search(r'id="food-time-image"[^>]*\bhidden\b', client.get("/").text)
    assert 'aria-pressed="true"' in client.get("/parent").text
    # A new app instance sees the same selection after a service restart.
    restarted = create_app({"TESTING": True, "SECRET_KEY": "test", "DATA_DIR": app.config["DATA_DIR"]})
    assert restarted.test_client().get("/api/display").json["food_time"] is True
    assert client.post("/api/parent/food-time", json={"enabled": False}, headers=headers).status_code == 200
    assert client.get("/api/display").json["food_time"] is False
    assert re.search(r'id="food-time-image"[^>]*\bhidden\b', client.get("/").text)


def test_wrong_pin_csrf_and_rate_limiting(client, app):
    app.extensions["klt_db"].set_pin_hash(hash_pin("123456"))
    token = csrf_for(client)
    assert client.post("/api/login", json={"pin": "123456"}).status_code == 400
    for _ in range(5):
        assert client.post("/api/login", json={"pin": "654321"}, headers={"X-CSRF-Token": token}).status_code == 401
    assert client.post("/api/login", json={"pin": "123456"}, headers={"X-CSRF-Token": token}).status_code == 429
    assert "Parent login" in client.get("/parent").text


def test_first_pin_setup_is_local_only_and_cannot_replace_existing_pin(client):
    token = csrf_for(client)
    headers = {"X-CSRF-Token": token}
    assert client.post("/api/setup", json={"pin": "123456"}, headers=headers,
                       environ_overrides={"REMOTE_ADDR": "192.168.1.2"}).status_code == 403
    assert client.post("/api/setup", json={"pin": "123"}, headers=headers).status_code == 400
    result = client.post("/api/setup", json={"pin": "123456"}, headers=headers)
    assert result.status_code == 200
    assert client.post("/api/setup", json={"pin": "654321"},
                       headers={"X-CSRF-Token": result.json["csrf_token"]}).status_code == 403


@pytest.mark.parametrize("path", [
    "/api/state", "/api/parent/state", "/api/voice/prompt",
    "/api/parent/media", "/api/events", "/static/js/voice.js",
    "/static/js/tv.js", "/static/js/learning.js",
])
def test_old_feature_endpoints_and_scripts_are_removed(client, path):
    assert client.get(path).status_code == 404


def test_existing_pin_and_legacy_data_survive_startup(tmp_path):
    path = tmp_path / "kid-learning-tv.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE auth (id INTEGER PRIMARY KEY, pin_hash TEXT NOT NULL, changed_at INTEGER NOT NULL)")
        db.execute("INSERT INTO auth VALUES(1, ?, 1)", (hash_pin("123456"),))
        db.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("INSERT INTO settings VALUES('preferences', '{}')")
    app = create_app({"TESTING": True, "SECRET_KEY": "test", "DATA_DIR": tmp_path})
    with app.test_client() as client:
        token = csrf_for(client)
        assert client.post("/api/login", json={"pin": "123456"}, headers={"X-CSRF-Token": token}).status_code == 200
        assert client.get("/api/health").json == {"status": "ok", "database": True}
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT value FROM settings").fetchone()[0] == "{}"
