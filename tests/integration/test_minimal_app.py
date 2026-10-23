import sqlite3

import pytest

from app.auth.security import hash_pin
from app.main import create_app
from tests.conftest import csrf_for


def test_tv_is_empty_and_has_no_scripts_or_controls(client):
    page = client.get("/")
    assert page.status_code == 200
    assert '<body class="tv"></body>' in page.text
    assert "<script" not in page.text
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
    assert client.post("/api/logout", json={}, headers={"X-CSRF-Token": token}).status_code == 400
    assert client.post("/api/logout", json={}, headers={"X-CSRF-Token": response.json["csrf_token"]}).status_code == 200
    assert "Parent login" in client.get("/parent").text


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
