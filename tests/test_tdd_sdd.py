import unittest
from quiz_manager import QuizManager, Question


class TestQuizManager(unittest.TestCase):
    def setUp(self):
        self.manager = QuizManager()
        self.q1 = Question("Сколько планет в Солнечной системе?", "8", time_limit=5)
        self.q2 = Question("Столица Франции?", "Париж", time_limit=5)
        self.manager.add_question(self.q1)
        self.manager.add_question(self.q2)

    def test_correct_answer_increases_score(self):
        """TDD: Проверка, что правильный ответ в рамках лимита времени увеличивает счет"""
        result = self.manager.submit_answer(user_answer="8", time_taken=3)
        self.assertEqual(result, "Правильно!")
        self.assertEqual(self.manager.score, 1)

    def test_incorrect_answer_does_not_increase_score(self):
        """TDD: Проверка, что неправильный ответ не начисляет баллы"""
        result = self.manager.submit_answer(user_answer="9", time_taken=2)
        self.assertEqual(result, "Неправильно!")
        self.assertEqual(self.manager.score, 0)

    def test_sdd_specification_table(self):
        # Строка 1: Успешный быстрый ответ
        res1 = self.manager.submit_answer(user_answer="8", time_taken=3)
        self.assertEqual(res1, "Правильно!")
        self.assertEqual(self.manager.score, 1)
        # Строка 2: Верный ответ, но время превышено (6 секунд при лимите 5)
        res2 = self.manager.submit_answer(user_answer="Париж", time_taken=6)
        self.assertEqual(res2, "Время истекло! Ответ не засчитан.")
        self.assertEqual(self.manager.score, 1, "Балл за Q2 не должен быть начислен!")


if __name__ == '__main__':
    unittest.main()