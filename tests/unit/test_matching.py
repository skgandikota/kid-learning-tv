from collections import Counter

import pytest

from app.matching import MatchingGame


@pytest.fixture
def game():
    now = [100.0]
    return MatchingGame(clock=lambda: now[0]), now


def pairs(game):
    grouped = {}
    for index, item in enumerate(game.cards):
        grouped.setdefault(item["image"], []).append(index)
    return list(grouped.values())


def test_all_five_rounds_have_exact_pairs_then_finish(game):
    match, now = game
    for round_number, count in enumerate((4, 6, 8, 10, 12), start=1):
        snapshot = match.snapshot()
        assert snapshot["round"] == round_number
        assert len(snapshot["cards"]) == count
        assert set(Counter(card["image"] for card in match.cards).values()) == {2}
        assert all(card["image"] is None for card in snapshot["cards"])
        for first, second in pairs(match):
            assert match.flip(match.token, first)
            assert match.flip(match.token, second)
            assert match.snapshot()["phase"] == "match"
            now[0] += 0.81
            assert match.snapshot()["cards"][first]["removed"]
        assert match.snapshot()["phase"] == "round-done"
        now[0] += 1.51
    assert match.snapshot()["phase"] == "complete"
    assert match.matches == 20


def test_mismatch_stays_open_then_flips_back_without_removing(game):
    match, now = game
    first, second = (pair[0] for pair in pairs(match))
    assert match.flip(match.token, first)
    assert match.flip(match.token, second)
    now[0] += 1
    snapshot = match.snapshot()
    assert snapshot["phase"] == "mismatch"
    assert sum(card["face_up"] for card in snapshot["cards"]) == 2
    assert not match.flip(match.token, pairs(match)[0][1])
    now[0] += 0.51
    snapshot = match.snapshot()
    assert snapshot["phase"] == "playing"
    assert all(not card["face_up"] and not card["removed"] for card in snapshot["cards"])
    assert match.matches == 0


def test_duplicate_removed_and_stale_clicks_cannot_form_pairs(game):
    match, now = game
    first, second = pairs(match)[0]
    assert match.flip(match.token, first)
    assert not match.flip(match.token, first)
    assert not match.flip("old", second)
    assert match.flip(match.token, second)
    now[0] += 1
    assert not match.flip(match.token, first)
    assert match.matches == 1


@pytest.mark.parametrize("index", [-1, 4, None, True, 1.5, "0"])
def test_invalid_card_indexes_are_explicit_errors(game, index):
    with pytest.raises(ValueError, match="Choose a card"):
        game[0].flip(game[0].token, index)
