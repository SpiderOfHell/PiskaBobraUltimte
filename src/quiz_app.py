"""Small cross-platform command-line interface for the timed quiz."""

from __future__ import annotations

import select
import sys
import time

from quiz_manager import Question, QuizManager


def _timed_input(prompt: str, timeout: float) -> str | None:
    """Read one line with a timeout on POSIX and Windows terminals."""
    print(prompt, end="", flush=True)
    if sys.platform == "win32":
        import msvcrt

        chars: list[str] = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                if char in ("\r", "\n"):
                    print()
                    return "".join(chars)
                if char == "\x03":
                    raise KeyboardInterrupt
                if char == "\b":
                    if chars:
                        chars.pop()
                        print("\b \b", end="", flush=True)
                else:
                    chars.append(char)
                    print(char, end="", flush=True)
            else:
                time.sleep(0.01)
        print()
        return None

    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if not ready:
        print()
        return None
    return sys.stdin.readline().rstrip("\r\n")


def build_demo_quiz() -> QuizManager:
    quiz = QuizManager()
    quiz.add_question(Question("Сколько планет в Солнечной системе?", "8", 15))
    quiz.add_question(Question("Столица Франции?", "Париж", 15))
    quiz.add_question(Question("Сколько будет 7 × 6?", "42", 15))
    return quiz


def main() -> int:
    quiz = build_demo_quiz()
    print("Викторина с таймером. На каждый вопрос даётся 15 секунд.\n")
    try:
        while True:
            question = quiz.get_current_question()
            if question is None:
                break
            print(f"\n{quiz.current_question_index + 1}. {question.text}")
            answer = _timed_input(
                f"Ваш ответ (осталось {question.time_limit:g} сек.): ",
                question.time_limit,
            )
            if answer is None:
                while not quiz.is_question_closed:
                    time.sleep(0.01)
                result = quiz.last_result
            else:
                result = quiz.submit_answer(answer)
            print(result)
            print(f"Текущий счёт: {quiz.score}")
    except (KeyboardInterrupt, EOFError):
        print("\nВикторина остановлена.")
    finally:
        quiz.close()
    print(f"\nИтоговый результат: {quiz.score} балл(ов) из {len(quiz.questions)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
