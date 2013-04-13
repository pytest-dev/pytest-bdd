"""Step decorators.

Example:

@given('I have an article')
def article(author):
    return create_test_article(author=author)


@when('I go to the article page')
def go_to_the_article_page(browser, article):
    browser.visit(urljoin(browser.url, '/articles/{0}/'.format(article.id)))


@then('I should not see the error message')
def no_error_message(browser):
    with pytest.raises(ElementDoesNotExist):
        browser.find_by_css('.message.error').first


Multiple names for the steps:

@given('I have an article')
@given('there is an article')
def article(author):
    return create_test_article(author=author)


Reusing existing fixtures for a different step name:

given('I have a beautiful article', fixture='article')

"""

import inspect
import pytest

from pytest_bdd.types import GIVEN, WHEN, THEN
from pytest_bdd.feature import remove_prefix


class StepError(Exception):
    pass


def given(name, fixture=None):
    """Given step decorator.

    :param name: Given step name.
    :param fixture: Optional name of the fixture to reuse.

    :raises: StepError in case of wrong configuration.
    :note: Can't be used as a decorator when the fixture is specified.
    """
    name = remove_prefix(name)
    if fixture is not None:
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        func = getattr(module, fixture, lambda request: request.getfuncargvalue(fixture))
        func = _decorate_step(func, GIVEN, name)
        setattr(module, name, func)
        return _not_a_fixture_decorator

    return _step_decorator(GIVEN, name)


def when(name):
    """When step decorator.

    :param name: Step name.
    :raises: StepError in case of wrong configuration.
    """
    return _step_decorator(WHEN, name)


def then(name):
    """Then step decorator.

    :param name: Step name.
    :raises: StepError in case of wrong configuration.
    """
    return _step_decorator(THEN, name)


def _not_a_fixture_decorator(func):
    """Function that prevents the decoration.

    :param func: Function that is going to be decorated.
    :raises: `StepError` if was used as a decorator.
    """
    raise StepError('Cannot be used as a decorator when the fixture is specified')


def _decorate_step(func, step_type, step_name):
    """Decorate the step function.

    :param func: Step function.
    :param step_type: Step type (GIVEN, WHEN or THEN).
    :param step_name: Step name as in the feature file.

    :raises: StepError when step types mismatch.
    """
    old_type = getattr(func, '__step_type__', None)
    if old_type is None:
        func = pytest.fixture(func)

    if old_type and old_type != step_type:
        raise StepError('Step type mismatched')

    func.__step_type__ = step_type
    if not hasattr(func, '__step_names__'):
        func.__step_names__ = []

    if step_name in func.__step_names__:
        raise StepError('Step already has this name')

    func.__step_names__.append(step_name)
    return func


def _step_decorator(step_type, step_name):
    """Step decorator for the type and the name.
    :param step_type: Step type (GIVEN, WHEN or THEN).
    :param step_name: Step name as in the feature file.

    :return: Decorator function for the step.
    :raises: StepError when step types mismatch.

    :note: If the step type is GIVEN it will automatically apply the pytest
    fixture decorator to the step function.
    """
    step_name = remove_prefix(step_name)

    def decorator(func):
        if step_name in getattr(func, '__step_names__', []):
            raise StepError('Step already has this name')

        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])

        # When and then steps are functions
        if step_type != GIVEN:
            func = lambda request: func
        func = _decorate_step(func, step_type, step_name)

        setattr(module, step_name, func)
        return func

    return decorator
