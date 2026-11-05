"""TDD unit tests and SDD example-based specification checks."""

import pytest

from quiz_manager import (
    CORRECT_MESSAGE,
    INCORRECT_MESSAGE,
    TIMEOUT_MESSAGE,
    Question,
    QuizManager,
)


def test_correct_answer_increases_score(fake_timing):
    clock, timer_factory, timers = fake_timing
    quiz = QuizManager(clock=clock, timer_factory=timer_factory)
    quiz.add_question(Question("Сколько планет в Солнечной системе?", "8", 5))

    assert quiz.get_current_question().correct_answer == "8"
    assert quiz.submit_answer("8") == CORRECT_MESSAGE
    assert quiz.score == 1
    assert timers[0].cancelled


def test_incorrect_answer_does_not_increase_score(fake_timing):
    clock, timer_factory, _ = fake_timing
    quiz = QuizManager(clock=clock, timer_factory=timer_factory)
    quiz.add_question(Question("Сколько планет?", "8", 5))
    quiz.get_current_question()

    assert quiz.submit_answer("9") == INCORRECT_MESSAGE
    assert quiz.score == 0


def test_timer_closes_question_automatically_and_rejects_late_answer(fake_timing):
    clock, timer_factory, timers = fake_timing
    quiz = QuizManager(clock=clock, timer_factory=timer_factory)
    quiz.add_question(Question("2 + 2?", "4", 5))
    quiz.add_question(Question("Столица Франции?", "Париж", 5))
    quiz.get_current_question()

    clock.advance(5)
    timers[0].fire()

    assert quiz.is_question_closed
    assert quiz.last_result == TIMEOUT_MESSAGE
    assert quiz.submit_answer("4") == TIMEOUT_MESSAGE
    assert quiz.score == 0
    assert quiz.get_current_question().text == "Столица Франции?"


def test_answer_at_exact_deadline_is_not_accepted(fake_timing):
    clock, timer_factory, _ = fake_timing
    quiz = QuizManager(clock=clock, timer_factory=timer_factory)
    quiz.add_question(Question("2 + 2?", "4", 5))
    quiz.get_current_question()
    clock.advance(5)

    assert quiz.submit_answer("4") == TIMEOUT_MESSAGE
    assert quiz.score == 0


def test_remaining_time_is_measured_with_monotonic_clock(fake_timing):
    clock, timer_factory, _ = fake_timing
    quiz = QuizManager(clock=clock, timer_factory=timer_factory)
    quiz.add_question(Question("Вопрос", "ответ", 8))
    quiz.get_current_question()
    clock.advance(2.5)

    assert quiz.remaining_time() == pytest.approx(5.5)


@pytest.mark.parametrize(
    ("answer", "elapsed", "expected_result", "expected_score"),
    [
        ("4", 1, CORRECT_MESSAGE, 1),
        ("5", 1, INCORRECT_MESSAGE, 0),
        ("4", 5, TIMEOUT_MESSAGE, 0),
        (" 4 ", 1, CORRECT_MESSAGE, 1),
    ],
    ids=["correct-in-time", "wrong-in-time", "correct-but-late", "trimmed-answer"],
)
def test_sdd_specification_examples(
    fake_timing, answer, elapsed, expected_result, expected_score
):
    clock, timer_factory, _ = fake_timing
    quiz = QuizManager(clock=clock, timer_factory=timer_factory)
    quiz.add_question(Question("2 + 2?", "4", 5))
    quiz.get_current_question()
    clock.advance(elapsed)

    actual_result = quiz.submit_answer(answer)

    assert actual_result == expected_result
    assert quiz.score == expected_score


def test_question_rejects_invalid_time_limit():
    with pytest.raises(ValueError):
        Question("Вопрос", "ответ", 0)
    with pytest.raises(ValueError):
        Question("Вопрос", "ответ", float("inf"))
