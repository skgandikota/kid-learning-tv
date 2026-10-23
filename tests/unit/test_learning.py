import random

import pytest

from app.games.learning import LearningGame, validate_enabled


def turn(game, choice=None):
    return {"session_id": game.session_id, "revision": game.revision, "choice": choice}


@pytest.mark.parametrize("activity_id", ["count-objects", "match-colours", "match-shapes"])
def test_choice_games_retry_then_complete_without_changing_activity(activity_id):
    game = LearningGame(activity_id, rng=random.Random(7))
    target = game.snapshot()["target"]
    wrong = next(item for item in game.options if item != target)
    game.answer(turn(game, wrong))
    assert game.score == 0
    assert game.snapshot()["target"] == target
    while not game.completed:
        game.answer(turn(game, game.snapshot()["target"]))
    assert game.score == game.total
    assert game.snapshot()["target"] is None
    with pytest.raises(ValueError):
        game.answer(turn(game, game.options[0]))


def test_pairs_do_not_leak_hidden_pictures_and_mismatch_waits_before_hiding():
    game = LearningGame("matching-pairs", rng=random.Random(7))
    assert all(card["picture"] is None for card in game.snapshot()["cards"])
    first = 0
    second = next(index for index, picture in enumerate(game.deck) if picture != game.deck[first])
    game.answer(turn(game, first), now=10)
    with pytest.raises(ValueError):
        game.answer(turn(game, first), now=10)
    game.answer(turn(game, second), now=10)
    cards = game.snapshot()["cards"]
    assert sum(card["picture"] is not None for card in cards) == 2
    assert game.snapshot()["waiting"]
    with pytest.raises(ValueError):
        game.answer(turn(game, 3), now=11)
    assert game.settle(turn(game), now=11) is False
    assert game.settle(turn(game), now=11.5) is True
    assert all(card["picture"] is None for card in game.snapshot()["cards"])


def test_pairs_match_once_and_stale_requests_cannot_advance_new_turns():
    game = LearningGame("matching-pairs", rng=random.Random(7))
    stale = turn(game, 0)
    for picture in set(game.deck):
        pair = [index for index, value in enumerate(game.deck) if value == picture]
        for index in pair:
            game.answer(turn(game, index))
        assert all(game.snapshot()["cards"][index]["matched"] for index in pair)
        with pytest.raises(ValueError):
            game.answer(turn(game, pair[0]))
    assert game.completed
    assert game.score == 4
    with pytest.raises(ValueError):
        game.answer(stale)
    fresh = LearningGame("matching-pairs")
    with pytest.raises(ValueError):
        fresh.answer(stale)


@pytest.mark.parametrize("value", [None, "matching-pairs", [[]], ["unknown"], ["matching-pairs"] * 2])
def test_library_rejects_invalid_enabled_lists(value):
    with pytest.raises(ValueError):
        validate_enabled(value)
