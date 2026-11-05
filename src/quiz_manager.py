import time


class Question:
    def __init__(self, text, correct_answer, time_limit):
        self.text = text
        self.correct_answer = correct_answer
        self.time_limit = time_limit


class QuizManager:
    def __init__(self):
        self.questions = []
        self.score = 0
        self.current_question_index = 0

    def add_question(self, question: Question):
        self.questions.append(question)

    def submit_answer(self, user_answer, time_taken):
        if self.current_question_index >= len(self.questions):
            raise IndexError("Все вопросы викторины уже пройдены.")
        current_q = self.questions[self.current_question_index]
        if time_taken > current_q.time_limit:
            self.current_question_index += 1
            return "Время истекло! Ответ не засчитан."
        if user_answer.strip().lower() == current_q.correct_answer.strip().lower():
            self.score += 1
            status = "Правильно!"
        else:
            status = "Неправильно!"
        self.current_question_index += 1
        return status

    def get_current_question(self):
        if self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
