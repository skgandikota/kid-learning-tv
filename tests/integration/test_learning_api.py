import pytest

from app.main import create_app


def turn(game, choice=None):
    return {"session_id": game.session_id, "revision": game.revision, "choice": choice}


def parent_action(client, action, **extra):
    return client.post("/api/parent/action", json={"action": action, **extra})


def start_learning(client, activity_id="matching-pairs"):
    assert parent_action(client, "learning_enabled", activity_id=activity_id, enabled=True).status_code == 200
    response = parent_action(client, "start_learning", activity_id=activity_id)
    assert response.status_code == 200
    return response.get_json()["state"]


def test_library_is_parent_only_disabled_by_default_and_preferences_survive_restart(parent_client, app):
    anonymous = app.test_client()
    assert anonymous.get("/api/parent/state").status_code == 401
    assert parent_action(anonymous, "learning_enabled", activity_id="matching-pairs", enabled=True).status_code != 200
    assert parent_action(parent_client, "start_learning", activity_id="matching-pairs").status_code == 400
    assert parent_client.get("/api/state").get_json()["enabled_learning_activities"] == []
    state = start_learning(parent_client)
    assert state["screen"] == "learning"
    assert state["parent_managed_activity"]
    restored = create_app(app.config).test_client().get("/api/state").get_json()
    assert restored["enabled_learning_activities"] == ["matching-pairs"]
    assert restored["learning_game"] is None
    assert restored["screen"] == "home"


@pytest.mark.parametrize("action", [
    "home", "start_learning", "start_avocado", "start_memory", "activity",
    "rocky_request", "rocky_done", "video_ended",
])
def test_child_cannot_launch_or_leave_parent_selected_activity(parent_client, app, action):
    start_learning(parent_client)
    child = app.test_client()
    response = child.post("/api/child/action", json={"action": action})
    assert response.status_code == 423
    assert child.get("/api/state").get_json()["screen"] == "learning"


def test_pause_lock_break_and_parent_home_keep_control_with_parent(parent_client, app):
    start_learning(parent_client)
    child = app.test_client()
    game = app.extensions["klt_runtime"].learning_game
    body = {"action": "learning_answer", **turn(game, 0)}
    assert parent_action(parent_client, "pause").status_code == 200
    assert child.post("/api/child/action", json=body).status_code == 423
    parent_action(parent_client, "resume")
    assert child.post("/api/child/action", json=body).status_code == 200
    parent_action(parent_client, "lock")
    assert child.post("/api/child/action", json=body).status_code == 423
    unlocked = parent_action(parent_client, "unlock").get_json()["state"]
    assert unlocked["screen"] == "learning"
    assert unlocked["learning_game"]["cards"][0]["picture"] is not None
    child.post("/api/child/action", json={"action": "session_break"})
    assert child.post("/api/child/action", json={"action": "home"}).status_code == 423
    assert parent_action(parent_client, "resume").get_json()["state"]["screen"] == "learning"
    assert parent_action(parent_client, "home").get_json()["state"]["learning_game"] is None
    assert child.post("/api/child/action", json={"action": "rocky_request"}).status_code == 200


def test_parent_can_disable_active_game_and_rejects_bad_library_changes(parent_client):
    start_learning(parent_client)
    for activity_id, enabled in [("unknown", True), ([], True), ("matching-pairs", "yes")]:
        assert parent_action(parent_client, "learning_enabled", activity_id=activity_id, enabled=enabled).status_code == 400
    disabled = parent_action(parent_client, "learning_enabled", activity_id="matching-pairs", enabled=False)
    state = disabled.get_json()["state"]
    assert state["learning_game"] is None
    assert state["screen"] == "home"
    assert state["enabled_learning_activities"] == []
    assert parent_action(parent_client, "start_learning", activity_id="matching-pairs").status_code == 400


def test_child_can_complete_pairs_but_cannot_restart_and_parent_can_switch(parent_client, app):
    start_learning(parent_client)
    child = app.test_client()
    game = app.extensions["klt_runtime"].learning_game
    for picture in set(game.deck):
        for index, value in enumerate(game.deck):
            if value == picture:
                response = child.post("/api/child/action", json={"action": "learning_answer", **turn(game, index)})
                assert response.status_code == 200
    state = response.get_json()["state"]
    assert state["learning_game"]["completed"]
    assert state["screen"] == "learning"
    assert child.post("/api/child/action", json={"action": "reset"}).status_code == 423
    old_turn = turn(game, 0)
    reset = parent_action(parent_client, "reset").get_json()["state"]
    assert reset["learning_game"]["session_id"] != old_turn["session_id"]
    assert child.post("/api/child/action", json={"action": "learning_answer", **old_turn}).status_code == 400
    switched = start_learning(parent_client, "count-objects")
    assert switched["learning_game"]["activity_id"] == "count-objects"
    legacy = parent_action(parent_client, "start_avocado", category_id="animals").get_json()["state"]
    assert legacy["learning_game"] is None
    assert legacy["parent_managed_activity"] is False


def test_import_checks_learning_ids_and_does_not_silently_disable_active_game(parent_client):
    for enabled in ["matching-pairs", [[]], ["unknown"]]:
        response = parent_client.post("/api/parent/import", json={
            "version": 1, "settings": {"enabled_learning_activities": enabled},
        })
        assert response.status_code == 400
    start_learning(parent_client)
    response = parent_client.post("/api/parent/import", json={
        "version": 1, "settings": {"enabled_learning_activities": []},
    })
    assert response.status_code == 400
    assert parent_client.get("/api/state").get_json()["enabled_learning_activities"] == ["matching-pairs"]


def test_disabling_a_locked_activity_preserves_the_screen_lock(parent_client):
    start_learning(parent_client)
    parent_action(parent_client, "lock")
    disabled = parent_action(parent_client, "learning_enabled", activity_id="matching-pairs", enabled=False)
    assert disabled.get_json()["state"]["screen"] == "locked"
    assert disabled.get_json()["state"]["locked"] is True
    assert disabled.get_json()["state"]["learning_game"] is None
