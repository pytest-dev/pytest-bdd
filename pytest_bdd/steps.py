"""Step decorators.

Example:

@given("I have an article", target_fixture="article")
def _(author):
    return create_test_article(author=author)


@when("I go to the article page")
def _(browser, article):
    browser.visit(urljoin(browser.url, "/articles/{0}/".format(article.id)))


@then("I should not see the error message")
def _(browser):
    with pytest.raises(ElementDoesNotExist):
        browser.find_by_css(".message.error").first


Multiple names for the steps:

@given("I have an article")
@given("there is an article")
def _(author):
    return create_test_article(author=author)


Reusing existing fixtures for a different step name:


@given("I have a beautiful article")
def _(article):
    pass

"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

import pytest
from _pytest.fixtures import FixtureDef, FixtureRequest
from typing_extensions import Literal

from .parsers import StepParser, get_parser
from .types import GIVEN, THEN, WHEN
from .utils import get_caller_module_locals

TCallable = TypeVar("TCallable", bound=Callable[..., Any])


@dataclass
class StepFunctionContext:
    name: str
    type: Literal["given", "when", "then"]
    step_func: Callable[..., Any]
    parser: StepParser
    converters: dict[str, Callable[..., Any]] = field(default_factory=dict)
    target_fixture: str | None = None


def get_step_fixture_name(name: str, type_: str) -> str:
    """Get step fixture name.

    :param name: string
    :param type: step type
    :return: step fixture name
    :rtype: string
    """
    return f"pytestbdd_{type_}_{name}"


def given(
    name: str | StepParser,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    caller_locals: dict[str, object] | None = None,
) -> Callable:
    """Given step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.

    :return: Decorator function for the step.
    """
    if caller_locals is None:
        caller_locals = get_caller_module_locals()
    return _step_decorator(
        GIVEN, name, converters=converters, target_fixture=target_fixture, caller_locals=caller_locals
    )


def when(
    name: str | StepParser,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    caller_locals: dict[str, object] | None = None,
) -> Callable:
    """When step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.

    :return: Decorator function for the step.
    """
    if caller_locals is None:
        caller_locals = get_caller_module_locals()
    return _step_decorator(
        WHEN, name, converters=converters, target_fixture=target_fixture, caller_locals=caller_locals
    )


def then(
    name: str | StepParser,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    caller_locals: dict[str, object] | None = None,
) -> Callable:
    """Then step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.

    :return: Decorator function for the step.
    """
    if caller_locals is None:
        caller_locals = get_caller_module_locals()
    return _step_decorator(
        THEN, name, converters=converters, target_fixture=target_fixture, caller_locals=caller_locals
    )


def _step_decorator(
    step_type: Literal["given", "when", "then"],
    step_name: str | StepParser,
    caller_locals: dict[str, object],
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
    if converters is None:
        converters = {}

    if caller_locals is None:
        caller_locals = get_caller_module_locals()

    def decorator(func: TCallable) -> TCallable:
        parser = get_parser(step_name)
        parsed_step_name = parser.name

        fixture_step_name = get_step_fixture_name(parsed_step_name, step_type)

        def step_function_marker() -> None:
            return None

        step_function_marker._pytest_bdd_step_context = StepFunctionContext(
            name=fixture_step_name,
            type=step_type,
            step_func=func,
            parser=parser,
            converters=converters,
            target_fixture=target_fixture,
        )

        caller_locals[fixture_step_name] = pytest.fixture(name=fixture_step_name)(step_function_marker)
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
    request._fixturemanager._arg2fixturedefs.setdefault(arg, []).append(fd)

    # inject fixture value in request cache
    request._fixture_defs[arg] = fd
    if add_fixturename:
        request._pyfuncitem._fixtureinfo.names_closure.append(arg)
