from pathlib import Path

import pytest

from app.adventures import (
    AdventureGame, AUDIO, ART, BAG_PLANS, GAME_IDS, HINT,
    audio_key, default_settings, validate_settings,
)
from app.quiz_speech import QuizSpeech


def complete_turn(game):
    if game.phase == "preview":
        game.command("ready", game.token)
    item = game.current
    answers = item["target"] if game.id == "bag" else (
        item["choices"][:item["quantity"]] if game.id == "rescue"
        else [item["target"]] * item["quantity"]
    )
    for answer in answers:
        game.command("pick", game.token, answer)


@pytest.mark.parametrize("game_id", GAME_IDS)
def test_all_seven_adventures_complete_without_timers_or_scores(game_id):
    settings = default_settings()
    settings.update(rescue_max=5, bag_size=3)
    game = AdventureGame(game_id, settings)
    for index in range(len(game.tasks)):
        assert game.index == index
        snap = game.snapshot()
        assert snap["audio"] in AUDIO
        complete_turn(game)
        assert game.phase == "success"
        assert game.snapshot()["audio"] in AUDIO
        with pytest.raises(ValueError):
            game.command("pick", game.token, game.current["choices"][0])
        game.command("next", game.token)
    assert game.phase == "finished"
    assert game.snapshot()["audio"] in AUDIO


def test_wrong_choices_and_old_turns_do_not_advance():
    game = AdventureGame("vehicle", default_settings())
    token = game.token
    assert game.command("pick", token, "triangle") == HINT
    assert game.token == token
    assert game.picked == []
    with pytest.raises(ValueError):
        game.command("next", token)
    game.command("pick", token, "circle")
    assert game.snapshot()["built"] == {"circle": 1}
    with pytest.raises(ValueError, match="turn has changed"):
        game.command("next", token)


def test_bag_hides_memory_and_can_show_it_again():
    game = AdventureGame("bag", default_settings())
    memory = game.snapshot()["memory"]
    assert len(memory) == 2
    game.command("ready", game.token)
    assert not game.snapshot()["memory"]
    assert not any(item["name"].lower() in game.snapshot()["prompt"].lower() for item in memory)
    game.command("pick", game.token, memory[0]["id"])
    with pytest.raises(ValueError, match="already safe"):
        game.command("pick", game.token, memory[0]["id"])
    game.command("remember", game.token)
    assert game.phase == "preview"
    assert len(game.snapshot()["memory"]) == 2
    assert not game.picked


def test_rescue_and_robot_count_each_click_and_preserve_assembled_parts():
    settings = default_settings()
    rescue = AdventureGame("rescue", settings)
    assert len(rescue.tasks) == 3
    complete_turn(rescue)
    rescue.command("next", rescue.token)
    first, second = rescue.current["choices"][:2]
    assert rescue.command("pick", rescue.token, first) == "One"
    assert rescue.phase == "play"
    assert rescue.snapshot()["collected"] == 1
    with pytest.raises(ValueError, match="already safe"):
        rescue.command("pick", rescue.token, first)
    rescue.command("pick", rescue.token, second)
    assert rescue.phase == "success"
    robot = AdventureGame("robot", settings)
    assert robot.command("pick", robot.token, "eye") == "One"
    assert robot.snapshot()["built"] == {"eye": 1}
    robot.command("pick", robot.token, "eye")
    robot.command("next", robot.token)
    assert robot.snapshot()["built"] == {"eye": 2}


def test_all_game_assets_exist_and_memory_speech_is_allowlisted():
    root = Path(__file__).resolve().parents[2] / "app"
    for item in ART.values():
        assert (root / item["image"].removeprefix("/")).is_file(), item["image"]
    for tasks in BAG_PLANS.values():
        for item in tasks:
            assert audio_key(item["prompt"]) in AUDIO
    for game_id in GAME_IDS:
        game = AdventureGame(game_id, default_settings())
        if game_id in {"vehicle", "robot"}:
            for part in ["base", *(item["target"] for item in game.tasks)]:
                assert (root / "static" / "images" / f"adventure-{game_id}-{part}.svg").is_file()
    for text in AUDIO.values():
        assert QuizSpeech._text(text) == text


@pytest.mark.parametrize("changes", [
    {"rescue_max": True}, {"rescue_max": 100}, {"bag_size": 5}, {"spoken": "yes"},
    {"enabled": "rescue"}, {"enabled": [None]}, {"enabled": ["unknown"]},
    {"enabled": ["rescue", "rescue"]},
])
def test_settings_reject_invalid_values(changes):
    with pytest.raises(ValueError):
        validate_settings({**default_settings(), **changes})


def test_disabled_and_unknown_games_cannot_start():
    settings = default_settings()
    settings["enabled"] = []
    assert validate_settings(settings) == settings
    for game_id in ("rescue", "unknown", None, []):
        with pytest.raises(ValueError):
            AdventureGame(game_id, settings)
