from unittest.mock import Mock

import pytest

from app.adventures import AUDIO, GAME_IDS, default_settings
from app.main import create_app
from tests.conftest import csrf_for


def post(client, action, **extra):
    return client.post("/api/child/adventures", json={"action": action, **extra}, headers={"X-CSRF-Token": csrf_for(client)})


def parent_login(client):
    headers = {"X-CSRF-Token": csrf_for(client)}
    result = client.post("/api/setup", json={"pin": "654321"}, headers=headers)
    assert result.status_code == 200
    return {"X-CSRF-Token": result.json["csrf_token"]}


def test_child_controls_csrf_stale_turns_and_pictures(client, app):
    assert client.post("/api/child/adventures", json={"action": "menu"}).status_code == 400
    assert post(client, "menu").json["playback"]["mode"] == "adventure-menu"
    assert len(client.get("/api/adventures/catalog").json["games"]) == 7
    for invalid in (None, [], {}):
        assert post(client, invalid).status_code == 400
    for game_id in GAME_IDS:
        response = post(client, "start", id=game_id)
        assert response.status_code == 200
        game = response.json["playback"]["adventure"]
        for item in game["choices"]:
            assert client.get(item["image"]).status_code == 200
    game = post(client, "start", id="vehicle").json["playback"]["adventure"]
    wrong = post(client, "pick", token=game["token"], choice="triangle")
    assert wrong.json["feedback"]
    assert wrong.json["playback"]["adventure"]["phase"] == "play"
    correct = post(client, "pick", token=game["token"], choice="circle")
    assert correct.json["playback"]["adventure"]["phase"] == "success"
    assert post(client, "pick", token=game["token"], choice="circle").status_code == 400
    assert post(client, "next", token=correct.json["playback"]["adventure"]["token"]).json["playback"]["adventure"]["index"] == 1
    assert app.extensions["klt_playback"].adventure.id == "vehicle"
    assert post(client, "close").json["playback"]["mode"] == "blank"


@pytest.mark.parametrize("mode", ["food", "video", "quiz", "matching", "typing"])
def test_other_activities_interrupt_and_block_child_adventures(client, app, mode):
    playback = app.extensions["klt_playback"]
    playback.start_adventure("rescue")
    if mode == "food":
        playback.food(True)
    elif mode == "video":
        playback.start([{"id": "test", "title": "test", "duration": 4}])
    elif mode == "quiz":
        playback.start_quiz("animals")
    elif mode == "matching":
        playback.start_matching()
    else:
        playback.start_typing("flash")
    assert playback.adventure is None
    for action in ("menu", "start", "close", "pick", "next"):
        assert post(client, action, id="rescue").status_code == 423
    assert playback.mode == mode


def test_adventures_block_other_child_games(client):
    post(client, "start", id="rescue")
    headers = {"X-CSRF-Token": csrf_for(client)}
    for game in ("quiz", "matching", "typing"):
        assert client.post(f"/api/child/{game}", json={"action": "menu"}, headers=headers).status_code == 423


def test_parent_settings_require_login_persist_and_disable_active_game(client, app):
    headers = {"X-CSRF-Token": csrf_for(client)}
    assert client.get("/api/parent/adventures").status_code == 401
    assert client.post("/api/parent/adventures", json={"action": "menu"}, headers=headers).status_code == 401
    headers = parent_login(client)
    settings = {**default_settings(), "enabled": ["rescue"], "rescue_max": 5, "bag_size": 3, "spoken": False}
    endpoint = "/api/parent/adventures"
    assert client.post(endpoint, json={"action": "settings", "settings": settings}, headers=headers).status_code == 200
    assert client.get(endpoint).json["settings"] == settings
    assert [game["id"] for game in client.get("/api/adventures/catalog").json["games"]] == ["rescue"]
    assert post(client, "start", id="monster").status_code == 400
    active = client.post(endpoint, json={"action": "start", "id": "rescue"}, headers=headers)
    assert active.json["playback"]["adventure"]["spoken"] is False
    settings["enabled"] = []
    assert client.post(endpoint, json={"action": "settings", "settings": settings}, headers=headers).json["playback"]["mode"] == "adventure-menu"
    fresh_app = create_app({"DATA_DIR": app.config["DATA_DIR"], "SECRET_KEY": "test"})
    assert fresh_app.extensions["klt_db"].adventure_settings() == settings
    settings["rescue_max"] = 500
    assert client.post(endpoint, json={"action": "settings", "settings": settings}, headers=headers).status_code == 400
    assert fresh_app.extensions["klt_db"].adventure_settings()["rescue_max"] == 5


def test_parent_can_interrupt_food_but_close_does_not_stop_unrelated_activity(client, app):
    headers = parent_login(client)
    playback = app.extensions["klt_playback"]
    playback.food(True)
    endpoint = "/api/parent/adventures"
    assert client.post(endpoint, json={"action": "close"}, headers=headers).status_code == 400
    assert playback.mode == "food"
    assert client.post(endpoint, json={"action": "start", "id": "robot"}, headers=headers).json["playback"]["mode"] == "adventure"


def test_adventure_audio_is_local_allowlisted_and_reports_failure(client, app):
    voice = app.extensions["klt_quiz_speech"]
    voice.audio = Mock(return_value=b"RIFFtest")
    key = next(iter(AUDIO))
    assert client.get(f"/api/adventures/audio/{key}").mimetype == "audio/wav"
    voice.audio.assert_called_once_with(AUDIO[key])
    assert client.get("/api/adventures/audio/arbitrary").status_code == 400
    assert client.get(f"/api/adventures/audio/{key}", environ_overrides={"REMOTE_ADDR": "192.168.1.9"}).status_code == 403
    voice.audio.side_effect = RuntimeError("engine unavailable")
    assert client.get(f"/api/adventures/audio/{key}").status_code == 503
