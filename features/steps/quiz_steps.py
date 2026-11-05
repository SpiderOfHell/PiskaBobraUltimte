import time

from behave import given, when, then

from quiz_manager import Question, QuizManager


@given('в систему добавлен вопрос "{text}" с правильным ответом "{answer}" и лимитом времени {limit:f} секунды')
def add_question(context, text, answer, limit):
    context.manager = QuizManager()
    context.manager.add_question(Question(text, answer, time_limit=limit))


@given("вопрос показан пользователю")
def show_question(context):
    context.question = context.manager.get_current_question()
    assert context.question is not None


@when('пользователь отвечает "{answer}"')
def submit_answer(context, answer):
    context.result = context.manager.submit_answer(answer)


@when("лимит времени истекает без ответа")
def wait_for_timeout(context):
    # The question's Timer closes it independently of this step.
    time.sleep(context.question.time_limit + 0.08)
    assert context.manager.is_question_closed
    context.result = context.manager.last_result


@then('система сообщает "{expected}"')
def check_result(context, expected):
    assert context.result == expected


@then("вопрос автоматически закрыт")
def check_question_closed(context):
    assert context.manager.is_question_closed


@then("счёт становится равен {expected_score:d}")
def check_score(context, expected_score):
    assert context.manager.score == expected_score
