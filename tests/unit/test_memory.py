from app.games.memory import MemoryGame


class FirstChoice:
    @staticmethod
    def choice(values):
        return values[0]


ITEMS = {"id": "shopping", "name": "Shopping", "items": ["apple", "bread", "milk", "carrot", "orange", "rice"]}


def test_memory_round_alternates_and_never_reuses_items():
    game = MemoryGame(ITEMS, level=2, retries=1, rng=FirstChoice())
    initial = game.start()
    assert initial == ["apple"]
    result = game.check(["apple", "bread"])
    assert result["status"] == "continue"
    assert result["app_added"] not in {"apple", "bread"}
    assert len(result["sequence"]) == 3
    assert len(set(result["sequence"])) == 3


def test_missing_wrong_order_extra_and_unknown_item_are_friendly_retries():
    game = MemoryGame(ITEMS, level=2, retries=1, rng=FirstChoice())
    first = game.start()
    assert game.check(first)["reason"] == "add_one_item"
    correct = game.check([*first, "bread"])
    assert correct["status"] == "continue"
    expected = correct["sequence"]
    wrong_order = [expected[1], expected[0], *expected[2:], "carrot"]
    assert game.check(wrong_order)["reason"] == "wrong_order"
    assert game.check([*expected, "carrot", "orange"])["reason"] == "add_one_item"
    assert game.check([*expected, "not an item"])["reason"] == "unknown_item"


def test_repeated_child_item_is_rejected():
    game = MemoryGame(ITEMS, level=2, retries=1, rng=FirstChoice())
    first = game.start()
    assert game.check([*first, first[0]])["reason"] == "repeated_item"


def test_picture_assistance_and_retry_state():
    game = MemoryGame(ITEMS, level=1, retries=1, rng=FirstChoice())
    game.start()
    assert game.picture_visible
    game.hide_pictures()
    assert not game.picture_visible
    assert game.use_retry() == {"status": "retry", "remaining": 0}
    assert game.use_retry() == {"status": "ended"}


def test_level_completion_and_empty_content():
    game = MemoryGame(ITEMS, level=1, retries=1, rng=FirstChoice())
    sequence = game.start()
    result = game.check([*sequence, "bread"])
    assert result["status"] == "ended"
    assert not game.picture_visible
    empty = MemoryGame({"id": "none", "items": []})
    assert empty.start() == []
    assert empty.state == "unavailable"
