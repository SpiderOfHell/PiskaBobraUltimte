from behave import given, when, then
from quiz_manager import QuizManager, Question


@given('в систему добавлен вопрос "{text}" с правильным ответом "{answer}" и лимитом времени {limit:d} секунд')
def step_impl(context, text, answer, limit):
    context.manager = QuizManager()
    context.question = Question(text, answer, time_limit=limit)
    context.manager.add_question(context.question)


@given('вопрос задан пользователю')
def step_impl(context):
    context.current_q = context.manager.get_current_question()
    assert context.current_q is not None


@when('пользователь вводит ответ "{user_answer}" за {time_taken:d} секунд')
def step_impl(context, user_answer, time_taken):
    context.result = context.manager.submit_answer(user_answer, time_taken=time_taken)


@when('время ожидания составляет {time_taken:d} секунд')
def step_impl(context, time_taken):
    context.result = context.manager.submit_answer(user_answer="", time_taken=time_taken)


@then('ответ принимается со статусом "{expected_status}"')
def step_impl(context, expected_status):
    assert context.result == expected_status, f"Ожидалось '{expected_status}', но получено '{context.result}'"


@then('вопрос закрывается автоматически со статусом "{expected_status}"')
def step_impl(context, expected_status):
    assert context.result == expected_status


@then('количество баллов становится равным {expected_score:d}')
def step_impl(context, expected_score):
    assert context.manager.score == expected_score


@then('количество баллов остается равным {expected_score:d}')
def step_impl(context, expected_score):
    assert context.manager.score == expected_score
