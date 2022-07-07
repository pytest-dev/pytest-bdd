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
from __future__ import annotations

import typing

import pytest
from _pytest.fixtures import FixtureDef, FixtureRequest

from .parsers import get_parser
from .types import GIVEN, THEN, WHEN
from .utils import get_caller_module_locals, setdefault

if typing.TYPE_CHECKING:
    from typing import Any, Callable


def get_step_fixture_name(name: str, type_: str) -> str:
    """Get step fixture name.

    :param name: string
    :param type: step type
    :return: step fixture name
    :rtype: string
    """
    return f"pytestbdd_{type_}_{name}"


def given(
    name: Any,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
) -> Callable:
    """Given step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.

    :return: Decorator function for the step.
    """
    return _step_decorator(GIVEN, name, converters=converters, target_fixture=target_fixture)


def when(name: Any, converters: dict[str, Callable] | None = None, target_fixture: str | None = None) -> Callable:
    """When step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.

    :return: Decorator function for the step.
    """
    return _step_decorator(WHEN, name, converters=converters, target_fixture=target_fixture)


def then(name: Any, converters: dict[str, Callable] | None = None, target_fixture: str | None = None) -> Callable:
    """Then step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.

    :return: Decorator function for the step.
    """
    return _step_decorator(THEN, name, converters=converters, target_fixture=target_fixture)


def _step_decorator(
    step_type: str,
    step_name: Any,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
) -> Callable:
    """Step decorator for the type and the name.

    :param str step_type: Step type (GIVEN, WHEN or THEN).
    :param str step_name: Step name as in the feature file.
    :param dict converters: Optional step arguments converters mapping
    :param target_fixture: Optional fixture name to replace by step definition

    :return: Decorator function for the step.
    """

    def decorator(func: Callable) -> Callable:
        step_func = func
        parser_instance = get_parser(step_name)
        parsed_step_name = parser_instance.name

        # TODO: Try to not attach to both step_func and lazy_step_func

        step_func.__name__ = str(parsed_step_name)

        def lazy_step_func() -> Callable:
            return step_func

        step_func.step_type = step_type
        lazy_step_func.step_type = step_type

        # Preserve the docstring
        lazy_step_func.__doc__ = func.__doc__

        setdefault(step_func, "_pytest_bdd_parsers", []).append(parser_instance)
        setdefault(lazy_step_func, "_pytest_bdd_parsers", []).append(parser_instance)

        if converters:
            step_func.converters = lazy_step_func.converters = converters

        step_func.target_fixture = lazy_step_func.target_fixture = target_fixture

        lazy_step_func = pytest.fixture()(lazy_step_func)
        fixture_step_name = get_step_fixture_name(parsed_step_name, step_type)

        caller_locals = get_caller_module_locals()
        caller_locals[fixture_step_name] = lazy_step_func
        return func

    return decorator


def inject_fixture(request: FixtureRequest, arg: str, value: Any) -> None:
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

    def fin() -> None:
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
