from app.games.avocado import AnswerMatcher, AvocadoGame, normalize


class FirstChoice:
    @staticmethod
    def choice(values):
        return values[0]


def category():
    return {
        "id": "animals",
        "name": "Animals",
        "answers": [
            {"name": "Elephant", "aliases": ["hippopotamus"], "pronunciation": ["ellie-fant"]},
            {"name": "King's Cross", "aliases": ["Kings Cross"]},
            {"name": "BMW", "aliases": ["B M W"]},
        ],
    }


def test_normalizes_case_punctuation_and_whitespace():
    assert normalize("  KING’S   CROSS!! ") == "kings cross"


def test_alias_abbreviation_pronunciation_and_plural_match():
    matcher = AnswerMatcher(category()["answers"])
    assert matcher.match("HIPPOPOTAMUSES")["status"] == "match"
    assert matcher.match("B. M. W.")["status"] == "match"
    assert matcher.match("King’s Cross")["status"] == "match"
    assert matcher.match("ellie fant")["status"] == "match"


def test_uncertain_fuzzy_match_requires_confirmation():
    result = AnswerMatcher(category()["answers"]).match("elephnt")
    assert result["status"] == "confirm"
    assert result["confidence"] < 1


def test_game_rejects_repeats_and_app_never_repeats():
    game = AvocadoGame(category(), retries=1, rng=FirstChoice())
    assert game.submit("elephants") == {"status": "accepted", "answer": "Elephant"}
    app_answer = game.application_answer()
    assert app_answer != "Elephant"
    assert game.submit("elephant")["status"] == "repeat"
    assert game.summary() == ["Elephant", app_answer]


def test_parent_confirmation_accept_reject_and_correction():
    game = AvocadoGame(category(), retries=1, rng=FirstChoice())
    result = game.submit("elephnt")
    assert result["status"] == "confirm"
    assert game.resolve_pending(True)["status"] == "accepted"

    game = AvocadoGame(category(), retries=1, rng=FirstChoice())
    game.submit("elephnt")
    assert game.resolve_pending(False)["status"] == "rejected"

    game.submit("elephnt")
    corrected = game.resolve_pending(False, "elephant")
    assert corrected == {"status": "accepted", "answer": "Elephant"}


def test_retries_round_end_and_empty_categories():
    game = AvocadoGame(category(), retries=1, rng=FirstChoice())
    assert game.retry_or_end([])["status"] == "retry"
    assert game.retry_or_end(["Bouncy Banana"]) == {"status": "ended", "nickname": "Bouncy Banana"}
    assert AvocadoGame({"id": "empty", "name": "Empty", "answers": []}).application_answer() is None


def test_answer_exhaustion_never_repeats():
    game = AvocadoGame(category(), retries=0, rng=FirstChoice())
    answers = set()
    first = game.application_answer()
    while first:
        assert first not in answers
        answers.add(first)
        first = game.application_answer()
    assert len(answers) == len(category()["answers"])
