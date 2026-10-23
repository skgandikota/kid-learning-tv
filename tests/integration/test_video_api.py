import pytest

from app.auth.security import hash_pin
from tests.conftest import csrf_for


@pytest.fixture
def parent(client, app):
    app.extensions["klt_db"].set_pin_hash(hash_pin("123456"))
    response = client.post("/api/login", json={"pin": "123456"}, headers={"X-CSRF-Token": csrf_for(client)})
    client.environ_base["HTTP_X_CSRF_TOKEN"] = response.json["csrf_token"]
    return client


@pytest.fixture
def fake_library(app, tmp_path, monkeypatch):
    library = app.extensions["klt_videos"]
    items = [{"id": "a", "title": "First", "duration": 10}, {"id": "b", "title": "Second", "duration": 20}]
    def selected(ids):
        if any(item not in {"a", "b"} for item in ids):
            raise ValueError("Video not found.")
        return [next(item for item in items if item["id"] == id_) for id_ in ids]
    monkeypatch.setattr(library, "items", selected)
    monkeypatch.setattr(library, "list", lambda: items)
    return library


def test_parent_only_video_mutations_and_listing(client):
    headers = {"X-CSRF-Token": csrf_for(client)}
    assert client.get("/api/parent/videos").status_code == 401
    for endpoint, body in [("play", {"ids": ["a"]}), ("control", {"action": "pause"}),
                           ("download", {"url": "https://youtu.be/abc", "title": "Test"})]:
        assert client.post(f"/api/parent/videos/{endpoint}", json=body, headers=headers).status_code == 401


def test_download_is_queued_without_starting_tv(parent, app, fake_library, monkeypatch):
    calls = []
    def queue(url, title):
        calls.append((url, title))
        return {"id": "job", "title": title, "status": "queued", "progress": 0, "error": ""}
    monkeypatch.setattr(fake_library, "download", queue)
    result = parent.post("/api/parent/videos/download",
                         json={"url": "https://youtu.be/abcdefghijk", "title": "My video"})
    assert result.status_code == 202
    assert result.json["job"]["status"] == "queued"
    assert calls == [("https://youtu.be/abcdefghijk", "My video")]
    assert app.extensions["klt_playback"].mode == "blank"


def test_order_controls_completion_food_and_loopback_reports(parent, app, fake_library):
    assert parent.post("/api/parent/videos/play", json={"ids": ["a"]},
                       headers={"X-CSRF-Token": "wrong"}).status_code == 400
    response = parent.post("/api/parent/videos/play", json={"ids": ["b", "a"]})
    assert response.status_code == 200
    assert [item["id"] for item in response.json["playback"]["queue"]] == ["b", "a"]
    state = response.json["playback"]
    report = {"session": state["session"], "revision": state["revision"],
              "event": "ended", "position": 20, "buffering": False}
    assert parent.post("/api/tv/playback", json=report,
                       environ_overrides={"REMOTE_ADDR": "192.168.1.2"}).status_code == 403
    assert parent.post("/api/tv/playback", json=report).status_code == 200
    assert parent.post("/api/tv/playback", json=report).status_code == 409
    state = parent.get("/api/display").json["playback"]
    report.update(revision=state["revision"], position=10)
    assert parent.post("/api/tv/playback", json=report).status_code == 200
    assert parent.get("/api/display").json["playback"]["mode"] == "finished"
    assert parent.post("/api/parent/food-time", json={"enabled": True}).status_code == 200
    assert parent.get("/api/display").json["playback"]["mode"] == "food"


@pytest.mark.parametrize("ids", [[], ["a", "a"], ["missing"], ["a"] * 51, [1], None])
def test_bad_playlist_never_starts(parent, app, fake_library, ids):
    assert parent.post("/api/parent/videos/play", json={"ids": ids}).status_code == 400
    assert app.extensions["klt_playback"].mode == "blank"


def test_range_stream_and_path_confinement(parent, app, fake_library, tmp_path, monkeypatch):
    path = tmp_path / "video.mp4"
    path.write_bytes(b"0123456789")
    monkeypatch.setattr(fake_library, "resolve", lambda id_: path if id_ == "a" else (_ for _ in ()).throw(ValueError("missing")))
    response = parent.get("/api/videos/a", headers={"Range": "bytes=2-5"})
    assert response.status_code == 206
    assert response.data == b"2345"
    assert parent.get("/api/videos/missing").status_code == 404
    with app.test_client() as guest:
        assert guest.get("/api/videos/a", environ_overrides={"REMOTE_ADDR": "192.168.1.2"}).status_code == 403
