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

"""

import pytest

from pytest_bdd.types import GIVEN, WHEN, THEN
from pytest_bdd.feature import remove_prefix


def given(name):
    """Given step decorator."""
    return _decorate_step(GIVEN, name)


def when(name):
    """When step decorator."""
    return _decorate_step(WHEN, name)


def then(name):
    """Then step decorator."""
    return _decorate_step(THEN, name)


def _decorate_step(step_type, step_name):
    """Decorates the step with name and type.
    :param step_type: GIVEN, WHEN or THEN.
    :param step_name: Step name as in the feature file.
    :return: Decorator function for the step.

    :note: If the step type is GIVEN it will automatically apply the pytest
    fixture decorator to the step function.
    """
    def decorator(func):
        func.__step_type__ = step_type
        func.__step_name__ = remove_prefix(step_name)
        if step_type == GIVEN:
            return pytest.fixture(func)
        return func
    return decorator
