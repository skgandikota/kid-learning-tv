from unittest.mock import Mock

from tests.conftest import csrf_for


def test_typing_menu_start_wrong_right_and_next(client):
    headers = {"X-CSRF-Token": csrf_for(client)}
    assert client.post("/api/child/typing", json={"action": "menu"}).status_code == 400
    assert client.post("/api/child/typing", json={"action": "menu"}, headers=headers).status_code == 200
    assert client.get("/api/display").json["playback"]["mode"] == "typing-menu"
    game = client.post("/api/child/typing", json={"action": "start", "id": "flash"}, headers=headers).json["playback"]["typing"]
    token = game["token"]
    wrong = client.post("/api/child/typing", json={"action": "key", "token": token, "position": 0, "key": "z"}, headers=headers)
    assert wrong.json["accepted"] is False
    assert wrong.json["playback"]["typing"]["position"] == 0
    assert client.post("/api/child/typing", json={"action": "next", "token": token}, headers=headers).status_code == 400
    for position, key in enumerate("flash"):
        result = client.post("/api/child/typing", json={
            "action": "key", "token": token, "position": position, "key": key,
        }, headers=headers)
        assert result.json["accepted"] is True
        assert result.json["sound"] is (position != 3)
    assert result.json["playback"]["typing"]["complete"]
    result = client.post("/api/child/typing", json={"action": "next", "token": token}, headers=headers)
    assert result.json["playback"]["typing"]["item"]["id"] == "batman"
    assert client.post("/api/child/typing", json={"action": "key", "token": token, "position": 0, "key": "b"}, headers=headers).status_code == 400


def test_typing_audio_allowlist_and_failure(client, app):
    speech = app.extensions["klt_phonics_speech"]
    speech.audio = Mock(return_value=b"RIFFtest")
    assert client.get("/api/typing/audio/flash/1/sound").mimetype == "audio/wav"
    speech.audio.assert_called_once_with("flash", 1, "sound")
    assert client.get("/api/typing/audio/flash/1/sound", environ_overrides={"REMOTE_ADDR": "192.168.1.2"}).status_code == 403
    assert client.get("/api/typing/audio/unknown/1/sound").status_code == 400
    speech.audio.side_effect = RuntimeError("missing engine")
    assert client.get("/api/typing/audio/flash/1/sound").status_code == 503


def test_typing_interruptions_clear_state_and_block_child_controls(client, app):
    headers = {"X-CSRF-Token": csrf_for(client)}
    playback = app.extensions["klt_playback"]
    for mode in ("food", "video", "finished", "quiz", "matching"):
        playback.start_typing("flash")
        if mode == "food":
            playback.food(True)
        elif mode in {"video", "finished"}:
            playback.start([{"id": "demo", "title": "Demo", "duration": 10}])
            if mode == "finished":
                playback.advance()
        elif mode == "quiz":
            playback.start_quiz("animals")
        else:
            playback.start_matching()
        assert playback.typing is None
        for action in ("start", "close", "menu"):
            assert client.post("/api/child/typing", json={"action": action, "id": "flash"}, headers=headers).status_code == 423
        assert playback.snapshot()["mode"] == mode


def test_spaces_are_automatic_and_final_word_returns_to_menu(client):
    headers = {"X-CSRF-Token": csrf_for(client)}
    for item_id, target in (("ant-man", "antman"), ("fish", "fish")):
        game = client.post("/api/child/typing", json={"action": "start", "id": item_id}, headers=headers).json["playback"]["typing"]
        for position, key in enumerate(target):
            result = client.post("/api/child/typing", json={"action": "key", "token": game["token"], "position": position, "key": key}, headers=headers)
            assert result.status_code == 200
        assert result.json["playback"]["typing"]["complete"]
    result = client.post("/api/child/typing", json={"action": "next", "token": game["token"]}, headers=headers)
    assert result.json["playback"]["mode"] == "typing-menu"
