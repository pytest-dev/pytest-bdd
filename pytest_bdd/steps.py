"""Step decorators.

Example:

@given("I have an article", target_fixture="article")
def given_article(author):
    return create_test_article(author=author)


@when("I go to the article page")
def go_to_the_article_page(browser, article):
    browser.visit(urljoin(browser.url, "/articles/{0}/".format(article.id)))


@then("I should not see the error message")
def no_error_message(browser):
    with pytest.raises(ElementDoesNotExist):
        browser.find_by_css(".message.error").first


Multiple names for the steps:

@given("I have an article")
@given("there is an article")
def article(author):
    return create_test_article(author=author)


Reusing existing fixtures for a different step name:


@given("I have a beautiful article")
def given_beautiful_article(article):
    pass

"""
import warnings
from typing import Dict, Optional

import pytest
from _pytest.fixtures import FixtureDef
from ordered_set import OrderedSet

from .parsers import get_parser
from .types import GIVEN, THEN, WHEN
from .utils import get_caller_module_locals
from .warning_types import PytestBDDStepDefinitionWarning


def get_step_fixture_name(name, type_):
    """Get step fixture name.

    :param name: string
    :param type: step type
    :return: step fixture name
    :rtype: string
    """
    return f"pytestbdd_{type_}_{name}"


def given(name, converters=None, target_fixture=None, target_fixtures=None):
    """Given step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.

    :return: Decorator function for the step.
    """
    return _step_decorator(
        GIVEN, name, converters=converters, target_fixture=target_fixture, target_fixtures=target_fixtures
    )


def when(name, converters=None, target_fixture=None, target_fixtures=None):
    """When step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.

    :return: Decorator function for the step.
    """
    return _step_decorator(
        WHEN, name, converters=converters, target_fixture=target_fixture, target_fixtures=target_fixtures
    )


def then(name, converters=None, target_fixture=None, target_fixtures=None):
    """Then step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.

    :return: Decorator function for the step.
    """
    return _step_decorator(
        THEN, name, converters=converters, target_fixture=target_fixture, target_fixtures=target_fixtures
    )


def _step_decorator(step_type, step_name, converters: Optional[Dict] = None, target_fixture=None, target_fixtures=None):
    """Step decorator for the type and the name.

    :param str step_type: Step type (GIVEN, WHEN or THEN).
    :param str step_name: Step name as in the feature file.
    :param dict converters: Optional step arguments converters mapping
    :param target_fixture: Optional fixture name to replace by step definition
    :param target_fixtures: Target fixture names to be replaced by steps definition function.

    :return: Decorator function for the step.
    """

    converters = converters or {}
    if target_fixture is not None and target_fixtures is not None:
        warnings.warn(PytestBDDStepDefinitionWarning("Both target_fixture and target_fixtures are specified"))
    target_fixtures = list(
        OrderedSet(
            [
                *([target_fixture] if target_fixture is not None else []),
                *(target_fixtures if target_fixtures is not None else []),
            ]
        )
    )

    def decorator(step_func):
        parser = get_parser(step_name)
        parsed_step_name = parser.name

        step_func.__name__ = str(parsed_step_name)

        def step_alias_func():
            return step_func

        step_func.step_type = step_alias_func.step_type = step_type

        # Preserve the docstring
        step_alias_func.__doc__ = step_func.__doc__

        step_func.parser = step_alias_func.parser = parser
        step_func.converters = step_alias_func.converters = converters

        step_func.target_fixtures = step_alias_func.target_fixtures = target_fixtures

        step_alias_fixture = pytest.fixture(step_alias_func)
        fixture_step_name = get_step_fixture_name(parsed_step_name, step_type)

        # Inject step alias fixture into module scope
        caller_locals = get_caller_module_locals()
        caller_locals[fixture_step_name] = step_alias_fixture
        return step_func

    return decorator


def inject_fixture(request, arg, value):
    """Inject fixture into pytest fixture request.

    :param request: pytest fixture request
    :param arg: argument name
    :param value: argument value
    """

    fd = FixtureDef(
        fixturemanager=request._fixturemanager,
        baseid=None,
        argname=arg,
        func=lambda: value,
        scope="function",
        params=None,
    )
    fd.cached_result = (value, 0, None)

    old_fd = request._fixture_defs.get(arg)
    add_fixturename = arg not in request.fixturenames

    def fin():
        request._fixturemanager._arg2fixturedefs[arg].remove(fd)
        request._fixture_defs[arg] = old_fd

        if add_fixturename:
            request._pyfuncitem._fixtureinfo.names_closure.remove(arg)

    request.addfinalizer(fin)

    # inject fixture definition
    request._fixturemanager._arg2fixturedefs.setdefault(arg, []).insert(0, fd)
    # inject fixture value in request cache
    request._fixture_defs[arg] = fd
    if add_fixturename:
        request._pyfuncitem._fixtureinfo.names_closure.append(arg)
