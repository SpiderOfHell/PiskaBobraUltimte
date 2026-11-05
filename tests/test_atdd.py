"""Acceptance tests for complete user-visible quiz workflows."""

import time

from quiz_manager import CORRECT_MESSAGE, TIMEOUT_MESSAGE, Question, QuizManager


def test_user_can_answer_correctly_and_continue_quiz():
    quiz = QuizManager()
    quiz.add_question(Question("2 + 2?", "4", 2))
    quiz.add_question(Question("Столица Франции?", "Париж", 2))

    first = quiz.get_current_question()
    assert first.text == "2 + 2?"
    assert quiz.submit_answer("4") == CORRECT_MESSAGE
    assert quiz.score == 1

    second = quiz.get_current_question()
    assert second.text == "Столица Франции?"
    assert quiz.submit_answer("Париж") == CORRECT_MESSAGE
    assert quiz.score == 2
    assert quiz.get_current_question() is None

    quiz.close()


def test_answer_after_real_time_limit_is_not_counted():
    quiz = QuizManager()
    quiz.add_question(Question("2 + 2?", "4", 0.05))
    quiz.get_current_question()  # Starts a real threading.Timer.

    time.sleep(0.12)

    assert quiz.is_question_closed
    assert quiz.last_result == TIMEOUT_MESSAGE
    assert quiz.submit_answer("4") == TIMEOUT_MESSAGE
    assert quiz.score == 0
    quiz.close()
