import pytest

from app.typing_game import LESSONS, TypingGame, sound_step


def test_flash_types_sounds_and_waits_for_sh_team():
    game = TypingGame("flash")
    assert game.type_key(game.token, 0, "f")
    assert sound_step(game.item, 1)["sound"] == "f"
    assert game.type_key(game.token, 1, "L")
    assert sound_step(game.item, 2)["blend"] == "fl"
    assert game.type_key(game.token, 2, "a")
    assert sound_step(game.item, 3)["blend"] == "fla"
    assert game.type_key(game.token, 3, "s")
    assert sound_step(game.item, 4) is None
    assert game.type_key(game.token, 4, "h")
    assert sound_step(game.item, 5)["sound"] == "S"
    assert sound_step(game.item, 5)["blend"] == "flaS"
    assert game.snapshot()["complete"]


def test_wrong_key_does_not_advance_or_store_input():
    game = TypingGame("flash")
    assert not game.type_key(game.token, 0, "z")
    assert game.position == 0
    assert "key" not in game.snapshot()
    with pytest.raises(ValueError, match="turn has changed"):
        game.type_key("stale", 0, "f")
    game.type_key(game.token, 0, "f")
    with pytest.raises(ValueError, match="turn has changed"):
        game.type_key(game.token, 0, "l")


@pytest.mark.parametrize("key", ["ff", "", "1", None, "é", " "])
def test_typing_rejects_non_letter_keys(key):
    game = TypingGame("flash")
    with pytest.raises(ValueError):
        game.type_key(game.token, 0, key)


def test_all_lessons_have_complete_sound_groups_and_finish():
    assert len({item["id"] for item in LESSONS}) == len(LESSONS)
    for item in LESSONS:
        game = TypingGame(item["id"])
        target = item["word"].replace(" ", "")
        assert "".join(group["letters"] for group in item["groups"]) == target
        assert all(group["sound"] for group in item["groups"])
        for position, key in enumerate(target):
            assert game.type_key(game.token, position, key)
        assert game.snapshot()["complete"]
        with pytest.raises(ValueError, match="finished"):
            game.type_key(game.token, game.position, "a")


def test_irregular_names_do_not_teach_invented_prefix_blends():
    for item_id in ("iron-man", "wonder-woman", "captain-america", "buzz-lightyear"):
        game = TypingGame(item_id)
        assert game.item["blend"] is False
        for position in range(1, len(game.item["word"].replace(" ", "")) + 1):
            step = sound_step(game.item, position)
            assert step is None or step["blend"] is None


def test_everyday_words_include_household_objects_and_body_parts():
    words = {item["name"] for item in LESSONS if item["category"] == "words"}
    assert {"Table", "Chair", "Bed", "Cup", "Book", "Ball"} <= words
    assert {"Head", "Hair", "Eye", "Ear", "Nose", "Mouth", "Tooth", "Hand", "Foot", "Arm", "Leg"} <= words
    for item_id, position, expected in (
        ("chair", 1, None), ("chair", 2, "tS"), ("chair", 5, "e@"),
        ("mouth", 2, None), ("mouth", 3, "aU"), ("mouth", 5, "T"),
        ("tooth", 3, "u:"), ("foot", 3, "U"),
    ):
        step = sound_step(TypingGame(item_id).item, position)
        assert (step["sound"] if step else None) == expected
