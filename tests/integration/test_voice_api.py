from unittest.mock import Mock

import pytest

from tests.conftest import csrf_for


@pytest.fixture
def voice_client(client, app):
    token = csrf_for(client)
    client.environ_base["HTTP_X_CSRF_TOKEN"] = token
    runtime = app.extensions["klt_runtime"]
    runtime.settings["voice_input_enabled"] = True
    runtime.settings["voice_enabled"] = True
    runtime.recognizer.available = Mock(return_value=True)
    return client


def speak(client, runtime, text, confidence=1):
    runtime.recognizer.accept = Mock(return_value={"text": text, "confidence": confidence})
    return client.post(
        f"/api/voice/audio?turn={runtime.voice_revision}",
        data=bytes(16000), content_type="application/octet-stream",
    )


def test_spoken_home_choice_starts_avocado_and_spoken_answer_advances(voice_client, app):
    runtime = app.extensions["klt_runtime"]
    state = speak(voice_client, runtime, "avocado").get_json()["state"]
    assert state["screen"] == "avocado"
    assert state["category_id"] == "animals"
    response = speak(voice_client, runtime, "elephant")
    assert response.status_code == 200
    assert "Elephant" in response.get_json()["state"]["used_answers"]
    assert response.get_json()["state"]["game_state"] == "child_turn"
    with runtime.db.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
    assert not list(runtime.db.path.parent.rglob("*.wav"))


def test_low_confidence_does_not_penalise_a_child(voice_client, app):
    runtime = app.extensions["klt_runtime"]
    runtime.start_avocado("animals")
    before = runtime.avocado.retries_left
    response = speak(voice_client, runtime, "elephant", .25)
    assert response.status_code == 200
    assert runtime.avocado.used == []
    assert runtime.avocado.retries_left == before
    assert "say it again" in runtime.state["message"]


def test_voice_confirmation_accepts_yes_without_a_parent_typing(voice_client, app):
    runtime = app.extensions["klt_runtime"]
    runtime.start_avocado("animals")
    runtime.handle_avocado_answer("elephnt")
    assert runtime.state["game_state"] == "confirmation"
    response = speak(voice_client, runtime, "yes")
    assert response.status_code == 200
    assert runtime.state["pending_answer"] is None
    assert "Elephant" in runtime.state["used_answers"]


@pytest.mark.parametrize("screen", ["video", "ask-rocky", "locked", "break"])
def test_microphone_is_rejected_on_non_listening_screens(voice_client, app, screen):
    runtime = app.extensions["klt_runtime"]
    runtime.state["screen"] = screen
    assert speak(voice_client, runtime, "avocado").status_code == 423
    runtime.recognizer.accept.assert_not_called()


def test_voice_needs_localhost_csrf_and_current_turn(voice_client, app):
    runtime = app.extensions["klt_runtime"]
    url = f"/api/voice/audio?turn={runtime.voice_revision}"
    assert voice_client.post(url, data=bytes(10), content_type="application/octet-stream",
                             environ_overrides={"REMOTE_ADDR": "192.168.1.3"}).status_code == 403
    assert app.test_client().post(url, data=bytes(10), content_type="application/octet-stream").status_code == 403
    assert voice_client.post("/api/voice/audio?turn=old", data=bytes(10),
                             content_type="application/octet-stream").status_code == 409
    assert voice_client.post(url, data=b"odd", content_type="application/octet-stream").status_code == 400
    runtime.state["paused"] = True
    assert voice_client.post(url, data=bytes(10), content_type="application/octet-stream").status_code == 423


def test_pair_game_remains_parent_launched_and_cannot_be_left_by_voice(voice_client, app):
    runtime = app.extensions["klt_runtime"]
    runtime.settings["enabled_learning_activities"] = ["matching-pairs"]
    runtime.start_learning("matching-pairs")
    assert speak(voice_client, runtime, "home").status_code == 423
    assert runtime.state["screen"] == "learning"


def test_voice_answers_choice_games_without_exposing_navigation(voice_client, app):
    runtime = app.extensions["klt_runtime"]
    runtime.settings["enabled_learning_activities"] = ["count-objects"]
    runtime.start_learning("count-objects")
    names = {"1": "one", "2": "two", "3": "three", "4": "four", "5": "five"}
    target = runtime.learning_game.snapshot()["target"]
    assert speak(voice_client, runtime, names[target]).status_code == 200
    assert runtime.learning_game.score == 1
    assert runtime.state["screen"] == "learning"


def test_voice_memory_list_is_parsed_and_checked(voice_client, app):
    runtime = app.extensions["klt_runtime"]
    runtime.handle_memory_start("shopping")
    first = runtime.memory.sequence[0]
    other = next(item for item in runtime.memory.category["items"] if item != first)
    result = speak(voice_client, runtime, f"{first} and {other}")
    assert result.status_code == 200
    assert other in runtime.memory.sequence


def test_speech_is_generated_for_the_current_prompt_only(voice_client, app):
    runtime = app.extensions["klt_runtime"]
    runtime.tts.wave = Mock(return_value=b"RIFFoffline-wave")
    response = voice_client.get(f"/api/voice/prompt?turn={runtime.voice_revision}")
    assert response.mimetype == "audio/wav"
    assert response.data == b"RIFFoffline-wave"
    assert "Say Avocado" in runtime.tts.wave.call_args.args[0]
    assert voice_client.get("/api/voice/prompt?turn=old").status_code == 409
    runtime.state["muted"] = True
    assert voice_client.get(f"/api/voice/prompt?turn={runtime.voice_revision}").status_code == 423


def test_microphone_status_does_not_interrupt_recognition(voice_client, app):
    runtime = app.extensions["klt_runtime"]
    before = runtime.voice_revision
    response = voice_client.post("/api/voice/status", json={"status": "listening"})
    assert response.status_code == 200
    assert runtime.voice_revision == before
    assert response.json["ok"]
    assert runtime.snapshot()["microphone_status"] == "listening"
    assert voice_client.post("/api/voice/status", json={"status": "invalid"}).status_code == 400
