import pytest

from app.quiz import QuizRound, validate_settings


@pytest.fixture
def round_():
    now = [100.0]
    quiz = QuizRound("cars", {"seconds": 10, "count": 5, "ticking": True}, clock=lambda: now[0])
    return quiz, now


def test_timer_starts_after_image_ready_and_answer_stays_for_speech(round_):
    quiz, now = round_
    now[0] += 100
    assert quiz.snapshot()["phase"] == "loading"
    assert not quiz.ready("old-token")
    assert quiz.ready(quiz.token)
    assert not quiz.ready(quiz.token)
    assert quiz.snapshot()["remaining"] == 10
    now[0] += 9
    assert quiz.snapshot()["phase"] == "question"
    now[0] += 1
    assert quiz.snapshot()["phase"] == "answer"
    now[0] += 4
    assert quiz.snapshot()["phase"] == "answer"
    assert quiz.speech_done(quiz.token)
    assert quiz.snapshot()["phase"] == "loading"
    assert quiz.index == 1


def test_pause_preserves_question_and_reveal_clock(round_):
    quiz, now = round_
    quiz.ready(quiz.token)
    now[0] += 3
    quiz.pause(True)
    now[0] += 100
    assert quiz.snapshot()["remaining"] == 7
    quiz.pause(False)
    now[0] += 7
    assert quiz.snapshot()["phase"] == "answer"
    quiz.speech_done(quiz.token)
    quiz.pause(True)
    now[0] += 100
    assert quiz.snapshot()["phase"] == "answer"
    quiz.pause(False)
    now[0] += 4
    assert quiz.snapshot()["phase"] == "loading"


def test_stale_reports_cannot_advance_new_slide_and_round_completes(round_):
    quiz, _ = round_
    token = quiz.token
    quiz.next()
    assert not quiz.ready(token)
    assert not quiz.speech_done(token)
    for _ in range(4):
        quiz.next()
    assert quiz.snapshot()["phase"] == "complete"


def test_missing_tv_audio_does_not_hang_round_forever(round_):
    quiz, now = round_
    quiz.reveal()
    now[0] += 17
    snapshot = quiz.snapshot()
    assert snapshot["phase"] == "loading"
    assert "speech did not finish" in snapshot["warning"]


def test_round_has_unique_random_pictures_and_count_is_capped_by_catalog():
    quiz = QuizRound("cars", {"seconds": 5, "count": 10, "ticking": False})
    assert len({item["id"] for item in quiz.items}) == len(quiz.items)
    assert 5 <= len(quiz.items) <= 10
    with pytest.raises(ValueError):
        QuizRound("missing", {"seconds": 5, "count": 5})


@pytest.mark.parametrize("settings", [
    None, {}, {"seconds": True, "count": 5, "ticking": True},
    {"seconds": 6, "count": 5, "ticking": True},
    {"seconds": 10, "count": 100, "ticking": True},
    {"seconds": 10, "count": 5, "ticking": 1},
])
def test_invalid_settings_rejected(settings):
    with pytest.raises(ValueError):
        validate_settings(settings)
