"""Core logic for a quiz with a real per-question timer."""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Callable


TIMEOUT_MESSAGE = "Время истекло! Ответ не засчитан."
CORRECT_MESSAGE = "Правильно!"
INCORRECT_MESSAGE = "Неправильно!"


@dataclass(frozen=True, slots=True)
class Question:
    """A quiz question and the number of seconds available to answer it."""

    text: str
    correct_answer: str
    time_limit: float = 15.0

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("Текст вопроса не должен быть пустым.")
        if not isinstance(self.correct_answer, str) or not self.correct_answer.strip():
            raise ValueError("Правильный ответ не должен быть пустым.")
        if isinstance(self.time_limit, bool) or not isinstance(self.time_limit, (int, float)):
            raise TypeError("Лимит времени должен быть числом.")
        if not math.isfinite(self.time_limit) or self.time_limit <= 0:
            raise ValueError("Лимит времени должен быть положительным конечным числом.")


class QuizManager:
    """Manage quiz questions, scoring, and automatic timeouts.

    The clock and timer factory are injectable so timing behaviour can be
    tested deterministically without relying on arbitrary sleeps.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        timer_factory: Callable[..., threading.Timer] = threading.Timer,
    ) -> None:
        if not callable(clock) or not callable(timer_factory):
            raise TypeError("clock и timer_factory должны быть вызываемыми объектами.")
        self.questions: list[Question] = []
        self.score = 0
        self.current_question_index = 0
        self._clock = clock
        self._timer_factory = timer_factory
        self._lock = threading.RLock()
        self._started_at: float | None = None
        self._timer: threading.Timer | None = None
        self._question_closed = False
        self._last_result: str | None = None

    def add_question(self, question: Question) -> None:
        if not isinstance(question, Question):
            raise TypeError("Можно добавлять только объекты Question.")
        with self._lock:
            if self._started_at is not None or self.current_question_index > 0:
                raise RuntimeError("Нельзя добавлять вопросы после начала викторины.")
            self.questions.append(question)

    def get_current_question(self) -> Question | None:
        """Return the current question and start its timer on first access.

        Once a question is answered or times out, the next call advances to
        the following question. A late answer cannot be applied to that next
        question because submit_answer checks the closed state first.
        """
        with self._lock:
            if self.current_question_index >= len(self.questions):
                return None
            if self._question_closed:
                self._advance_locked()
            if self.current_question_index >= len(self.questions):
                return None
            self._start_current_question_locked()
            self._refresh_timeout_locked()
            if self._question_closed:
                return None
            return self.questions[self.current_question_index]

    def submit_answer(self, user_answer: str) -> str:
        """Submit an answer; elapsed time is measured by the manager itself."""
        if not isinstance(user_answer, str):
            raise TypeError("Ответ должен быть строкой.")
        with self._lock:
            if self.current_question_index >= len(self.questions):
                raise IndexError("Все вопросы викторины уже пройдены.")
            self._start_current_question_locked()
            self._refresh_timeout_locked()
            if self._question_closed:
                return self._last_result or TIMEOUT_MESSAGE

            question = self.questions[self.current_question_index]
            if user_answer.strip().casefold() == question.correct_answer.strip().casefold():
                self.score += 1
                result = CORRECT_MESSAGE
            else:
                result = INCORRECT_MESSAGE
            self._close_current_question_locked(result)
            return result

    def remaining_time(self) -> float:
        """Return seconds left for the current question, clamped to zero."""
        with self._lock:
            if self.current_question_index >= len(self.questions):
                return 0.0
            self._start_current_question_locked()
            self._refresh_timeout_locked()
            if self._question_closed or self._started_at is None:
                return 0.0
            limit = self.questions[self.current_question_index].time_limit
            return max(0.0, limit - (self._clock() - self._started_at))

    @property
    def is_question_closed(self) -> bool:
        """Whether the current question is closed (including timer expiry)."""
        with self._lock:
            self._refresh_timeout_locked()
            return self._question_closed

    @property
    def last_result(self) -> str | None:
        with self._lock:
            self._refresh_timeout_locked()
            return self._last_result

    @property
    def is_finished(self) -> bool:
        with self._lock:
            return (
                self.current_question_index >= len(self.questions)
                or (
                    self.current_question_index == len(self.questions) - 1
                    and self._question_closed
                )
            )

    def close(self) -> None:
        """Cancel an active timer. Safe to call when the quiz is already over."""
        with self._lock:
            self._cancel_timer_locked()

    def _start_current_question_locked(self) -> None:
        if self._started_at is not None or self._question_closed:
            return
        if self.current_question_index >= len(self.questions):
            return
        self._started_at = self._clock()
        question_index = self.current_question_index
        timer = self._timer_factory(
            self.questions[question_index].time_limit,
            self._on_timeout,
            args=(question_index,),
        )
        # threading.Timer is a Thread; daemon prevents it keeping Python alive.
        if hasattr(timer, "daemon"):
            timer.daemon = True
        self._timer = timer
        timer.start()

    def _on_timeout(self, question_index: int) -> None:
        with self._lock:
            if question_index != self.current_question_index or self._question_closed:
                return
            if self._started_at is None:
                return
            question = self.questions[question_index]
            elapsed = self._clock() - self._started_at
            if elapsed >= question.time_limit:
                self._close_current_question_locked(TIMEOUT_MESSAGE, cancel_timer=False)

    def _refresh_timeout_locked(self) -> None:
        if self._question_closed or self._started_at is None:
            return
        if self.current_question_index >= len(self.questions):
            return
        question = self.questions[self.current_question_index]
        if self._clock() - self._started_at >= question.time_limit:
            self._close_current_question_locked(TIMEOUT_MESSAGE)

    def _close_current_question_locked(self, result: str, *, cancel_timer: bool = True) -> None:
        self._question_closed = True
        self._last_result = result
        if cancel_timer:
            self._cancel_timer_locked()

    def _cancel_timer_locked(self) -> None:
        timer, self._timer = self._timer, None
        if timer is not None:
            timer.cancel()

    def _advance_locked(self) -> None:
        self._cancel_timer_locked()
        self.current_question_index += 1
        self._started_at = None
        self._question_closed = False
        self._last_result = None
