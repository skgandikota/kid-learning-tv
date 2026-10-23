import pytest

from app.database import Database
from app.playback import Playback


@pytest.fixture
def playback(tmp_path):
    return Playback(Database(tmp_path / "test.sqlite3"))


def playlist():
    return [{"id": "one", "title": "First", "duration": 10}, {"id": "two", "title": "Second", "duration": 20}]


def report(playback, **changes):
    state = playback.snapshot()
    return {
        "session": state["session"], "revision": state["revision"],
        "event": "progress", "position": 4, "buffering": False, **changes,
    }


def test_queue_order_countdown_completion_and_stale_ended(playback):
    playback.start(playlist())
    assert playback.snapshot()["total"] == 30
    assert playback.report(report(playback))
    assert playback.snapshot()["remaining"] == 26
    ended = report(playback, event="ended", position=10)
    assert playback.report(ended)
    assert playback.snapshot()["current"]["id"] == "two"
    assert playback.snapshot()["remaining"] == 20
    assert not playback.report(ended)
    assert playback.snapshot()["index"] == 1
    assert playback.report(report(playback, event="ended", position=20))
    state = playback.snapshot()
    assert state["mode"] == "finished"
    assert state["remaining"] == 0
    assert state["current"] is None


def test_parent_controls_reject_stale_tv_reports_and_preserve_seek(playback):
    playback.start(playlist())
    old = report(playback)
    playback.command({"action": "seek", "position": 8})
    assert not playback.report(old)
    assert playback.snapshot()["position"] == 8
    seek_revision = playback.seek_revision
    playback.command({"action": "pause"})
    assert playback.paused
    assert not playback.report(report(playback, event="ended", position=10))
    playback.command({"action": "resume"})
    assert not playback.paused
    playback.command({"action": "volume", "volume": 0})
    assert playback.volume == 0
    assert playback.seek_revision == seek_revision
    playback.command({"action": "next"})
    assert playback.index == 1
    playback.command({"action": "previous"})
    assert playback.index == 0
    assert playback.position == 0
    playback.command({"action": "stop"})
    assert playback.snapshot()["mode"] == "blank"


def test_food_time_cancels_playlist_and_error_is_parent_visible(playback):
    playback.start(playlist())
    playback.report(report(playback, event="error", error="Cannot decode"))
    assert playback.snapshot()["error"] == "Cannot decode"
    assert playback.paused
    playback.command({"action": "resume"})
    assert playback.error == ""
    old = report(playback)
    playback.food(True)
    assert playback.snapshot()["mode"] == "food"
    assert playback.queue == []
    assert playback.database.food_time()
    assert not playback.report(old)
    playback.start(playlist())
    assert not playback.database.food_time()


@pytest.mark.parametrize("position", [None, "10", float("nan"), float("inf"), True])
def test_bad_seek_is_explicit(playback, position):
    playback.start(playlist())
    with pytest.raises(ValueError):
        playback.command({"action": "seek", "position": position})


def test_restart_does_not_automatically_restart_screen_time(playback):
    playback.start(playlist())
    assert Playback(playback.database).mode == "blank"
