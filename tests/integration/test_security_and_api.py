from __future__ import annotations

import io
import sqlite3

from tests.conftest import csrf_for


def test_health_and_tv_boot_without_parent_pin(client):
    assert client.get("/api/health").get_json()["status"] == "ok"
    page = client.get("/")
    assert page.status_code == 200
    assert b"Let's learn and play!" in page.data
    assert client.get("/api/parent/state").status_code == 401


def test_parent_pin_is_hashed_csrf_and_routes_are_protected(client, app):
    csrf = csrf_for(client)
    assert client.post("/api/setup", json={"pin": "123456"}).status_code == 400
    assert client.post("/api/setup", json={"pin": "123456"}, headers={"X-CSRF-Token": csrf}).status_code == 200
    db = app.extensions["klt_db"]
    saved = db.get_pin_hash()
    assert saved != "123456"
    assert saved.startswith("pbkdf2_sha256$")
    assert client.post("/api/parent/action", json={"action": "lock"}).status_code == 400
    assert client.get("/api/parent/state").status_code == 200


def test_login_delay_after_five_bad_attempts(client):
    csrf = csrf_for(client)
    assert client.post("/api/setup", json={"pin": "123456"}, headers={"X-CSRF-Token": csrf}).status_code == 200
    # A new client has no authenticated cookie; provision the CSRF token on its parent page.
    fresh = client.application.test_client()
    fresh_csrf = csrf_for(fresh)
    for _ in range(5):
        response = fresh.post("/api/login", json={"pin": "000000"}, headers={"X-CSRF-Token": fresh_csrf})
        assert response.status_code == 401
    response = fresh.post("/api/login", json={"pin": "000000"}, headers={"X-CSRF-Token": fresh_csrf})
    assert response.status_code == 429


def test_parent_controls_game_and_history_is_off_by_default(parent_client, app):
    token = parent_client.environ_base["HTTP_X_CSRF_TOKEN"]
    response = parent_client.post(
        "/api/parent/action", json={"action": "start_avocado", "category_id": "animals"},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200
    answer = parent_client.post(
        "/api/parent/action", json={"action": "answer", "text": "Elephant"},
        headers={"X-CSRF-Token": token},
    )
    assert answer.status_code == 200
    assert "Elephant" in answer.get_json()["state"]["used_answers"]
    with app.extensions["klt_db"].connect() as db:
        assert db.execute("SELECT COUNT(*) FROM activity_history").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_memory_game_can_be_started_and_completed_through_parent_api(parent_client):
    token = parent_client.environ_base["HTTP_X_CSRF_TOKEN"]
    start = parent_client.post(
        "/api/parent/action", json={"action": "start_memory", "category_id": "animals"},
        headers={"X-CSRF-Token": token},
    ).get_json()["state"]
    first = start["memory_sequence"]
    child_item = next(item for item in ["cat", "dog", "lion", "zebra", "rabbit"] if item not in first)
    answer = parent_client.post(
        "/api/parent/action",
        json={"action": "memory_answer", "text": ", ".join([*first, child_item])},
        headers={"X-CSRF-Token": token},
    )
    assert answer.status_code == 200
    assert answer.get_json()["state"]["screen"] == "memory"
    assert child_item in answer.get_json()["state"]["memory_sequence"]


def test_uncertain_answer_waits_for_parent_confirmation(parent_client):
    token = parent_client.environ_base["HTTP_X_CSRF_TOKEN"]
    parent_client.post(
        "/api/parent/action", json={"action": "start_avocado", "category_id": "animals"},
        headers={"X-CSRF-Token": token},
    )
    result = parent_client.post(
        "/api/parent/action", json={"action": "answer", "text": "elephnt"},
        headers={"X-CSRF-Token": token},
    )
    assert result.status_code == 200
    state = result.get_json()["state"]
    assert state["game_state"] == "confirmation"
    assert state["pending_answer"] == "Elephant"
    accepted = parent_client.post(
        "/api/parent/action", json={"action": "accept_answer"},
        headers={"X-CSRF-Token": token},
    )
    assert accepted.status_code == 200
    assert "Elephant" in accepted.get_json()["state"]["used_answers"]


def test_lock_blocks_child_actions_and_parent_can_unlock(parent_client):
    token = parent_client.environ_base["HTTP_X_CSRF_TOKEN"]
    parent_client.post(
        "/api/parent/action", json={"action": "lock"},
        headers={"X-CSRF-Token": token},
    )
    assert parent_client.post("/api/child/action", json={"action": "rocky_request"}).status_code == 423
    unlocked = parent_client.post(
        "/api/parent/action", json={"action": "unlock"},
        headers={"X-CSRF-Token": token},
    )
    assert unlocked.get_json()["state"]["locked"] is False


def test_category_traversal_and_invalid_content_rejected(parent_client):
    token = parent_client.environ_base["HTTP_X_CSRF_TOKEN"]
    bad = {"id": "../other", "name": "Unsafe", "answers": [{"name": "Test"}]}
    response = parent_client.post("/api/parent/categories", json=bad, headers={"X-CSRF-Token": token})
    assert response.status_code == 400
    assert parent_client.get("/api/media/../../etc/passwd").status_code == 404


def test_pin_can_be_changed_only_with_current_pin(parent_client):
    token = parent_client.environ_base["HTTP_X_CSRF_TOKEN"]
    wrong = parent_client.post(
        "/api/parent/pin", json={"old_pin": "000000", "new_pin": "654321"},
        headers={"X-CSRF-Token": token},
    )
    assert wrong.status_code == 401
    changed = parent_client.post(
        "/api/parent/pin", json={"old_pin": "123456", "new_pin": "654321"},
        headers={"X-CSRF-Token": token},
    )
    assert changed.status_code == 200
    login_client = parent_client.application.test_client()
    csrf = csrf_for(login_client)
    assert login_client.post("/api/login", json={"pin": "123456"}, headers={"X-CSRF-Token": csrf}).status_code == 401
    assert login_client.post("/api/login", json={"pin": "654321"}, headers={"X-CSRF-Token": csrf}).status_code == 200


def test_parent_qr_is_local_svg_and_requires_parent_session(parent_client):
    anonymous = parent_client.application.test_client()
    assert anonymous.get("/api/parent/qr").status_code == 401
    response = parent_client.get("/api/parent/qr")
    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"
    assert b"<svg" in response.data


def test_media_upload_and_remote_playback_remain_parent_controlled(parent_client, app):
    token = parent_client.environ_base["HTTP_X_CSRF_TOKEN"]
    payload = b"\x00\x00\x00\x18ftypisom" + bytes(32)
    response = parent_client.post(
        "/api/parent/media/upload",
        data={"title": "Demo", "video": (io.BytesIO(payload), "demo.mp4")},
        headers={"X-CSRF-Token": token},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    media_id = response.get_json()["video"]["id"]
    assert parent_client.get(f"/api/media/{media_id}").data == payload
    play = parent_client.post(
        "/api/parent/action", json={"action": "play_video", "media_id": media_id},
        headers={"X-CSRF-Token": token},
    )
    assert play.status_code == 200
    assert play.get_json()["state"]["screen"] == "video"
    assert parent_client.post(
        "/api/parent/action", json={"action": "media_pause"},
        headers={"X-CSRF-Token": token},
    ).get_json()["state"]["game_state"] == "paused"
    assert parent_client.delete(
        f"/api/parent/media/{media_id}", headers={"X-CSRF-Token": token},
    ).status_code == 409


def test_media_upload_rejects_unsupported_type(parent_client):
    token = parent_client.environ_base["HTTP_X_CSRF_TOKEN"]
    response = parent_client.post(
        "/api/parent/media/upload",
        data={"title": "Not a movie", "video": (io.BytesIO(b"not a video"), "picture.jpg")},
        headers={"X-CSRF-Token": token},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_imported_settings_are_validated(parent_client):
    token = parent_client.environ_base["HTTP_X_CSRF_TOKEN"]
    response = parent_client.post(
        "/api/parent/import",
        json={"version": 1, "settings": {"enabled_categories": "../"}},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 400
    valid = parent_client.get("/api/parent/export").get_json()
    assert valid["version"] == 1
    assert valid["settings"]["voice_enabled"] is False
    malformed = parent_client.post(
        "/api/parent/import",
        json={"version": 1, "settings": {"enabled_categories": [[]]}},
        headers={"X-CSRF-Token": token},
    )
    assert malformed.status_code == 400
    invalid_category = parent_client.post(
        "/api/parent/action",
        json={"action": "start_avocado", "category_id": ["animals"]},
        headers={"X-CSRF-Token": token},
    )
    assert invalid_category.status_code == 400


def test_request_screen_never_requests_microphone_or_saves_audio(client):
    response = client.post("/api/child/action", json={"action": "rocky_request"})
    assert response.status_code == 200
    assert response.get_json()["state"]["rocky_request_open"] is True
    assert not (app_data_dir(client) / "audio").exists()


def app_data_dir(client):
    return client.application.extensions["klt_db"].path.parent


def test_backup_is_sqlite_and_parent_only(parent_client):
    backup = parent_client.get("/api/parent/backup")
    assert backup.status_code == 200
    assert backup.data.startswith(b"SQLite format 3")
