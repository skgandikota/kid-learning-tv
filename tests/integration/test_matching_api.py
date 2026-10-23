from tests.conftest import csrf_for


def test_child_can_play_and_reload_preserves_board(client, app):
    headers = {"X-CSRF-Token": csrf_for(client)}
    assert client.post("/api/child/matching", json={"action": "start"}).status_code == 400
    result = client.post("/api/child/matching", json={"action": "start"}, headers=headers)
    assert result.status_code == 200
    game = result.json["playback"]["matching"]
    token = game["token"]
    assert len(game["cards"]) == 4
    assert client.post("/api/child/matching", json={
        "action": "flip", "token": token, "index": 0,
    }, headers=headers).status_code == 200
    assert client.get("/").status_code == 200
    snapshot = client.get("/api/display").json["playback"]
    assert snapshot["matching"]["token"] == token
    assert snapshot["matching"]["cards"][0]["face_up"]
    assert client.post("/api/child/matching", json={
        "action": "flip", "token": token, "index": 0,
    }, headers=headers).status_code == 409
    assert client.post("/api/child/matching", json={"action": "close"}, headers=headers).status_code == 200
    assert client.get("/api/display").json["playback"]["mode"] == "blank"
    assert app.extensions["klt_playback"].matching is None


def test_restart_rejects_old_board_and_bad_indexes(client):
    headers = {"X-CSRF-Token": csrf_for(client)}
    old = client.post("/api/child/matching", json={"action": "start"}, headers=headers).json["playback"]["matching"]["token"]
    new = client.post("/api/child/matching", json={"action": "start"}, headers=headers).json["playback"]["matching"]["token"]
    assert old != new
    assert client.post("/api/child/matching", json={
        "action": "flip", "token": old, "index": 0,
    }, headers=headers).status_code == 409
    assert client.post("/api/child/matching", json={
        "action": "flip", "token": new, "index": 99,
    }, headers=headers).status_code == 400


def test_food_and_video_interrupt_and_cannot_be_closed_by_game(client, app):
    headers = {"X-CSRF-Token": csrf_for(client)}
    playback = app.extensions["klt_playback"]
    for mode in ("food", "video", "finished"):
        playback.start_matching()
        if mode == "food":
            playback.food(True)
        else:
            playback.start([{"id": "demo", "title": "Demo", "duration": 10}])
            if mode == "finished":
                playback.advance()
        assert playback.matching is None
        for action in ("start", "close", "flip"):
            assert client.post("/api/child/matching", json={"action": action}, headers=headers).status_code == 423
        assert playback.snapshot()["mode"] == mode


def test_quiz_and_matching_are_exclusive(client, app):
    headers = {"X-CSRF-Token": csrf_for(client)}
    playback = app.extensions["klt_playback"]
    playback.start_matching()
    assert client.post("/api/child/quiz", json={"action": "menu"}, headers=headers).status_code == 423
    playback.start_quiz("animals")
    assert playback.matching is None
    assert client.post("/api/child/matching", json={"action": "start"}, headers=headers).status_code == 423
