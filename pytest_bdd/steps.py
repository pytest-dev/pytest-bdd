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

import enum
from dataclasses import dataclass, field
from itertools import count
from typing import Any, Callable, Iterable, TypeVar

import pytest
from _pytest.fixtures import FixtureDef, FixtureRequest
from typing_extensions import Literal

from .parser import Step
from .parsers import StepParser, get_parser
from .types import GIVEN, THEN, WHEN
from .utils import get_caller_module_locals

TCallable = TypeVar("TCallable", bound=Callable[..., Any])


@enum.unique
class StepNamePrefix(enum.Enum):
    step_def = "pytestbdd_stepdef"
    step_impl = "pytestbdd_stepimpl"


@dataclass
class StepFunctionContext:
    type: Literal["given", "when", "then"] | None
    step_func: Callable[..., Any]
    parser: StepParser
    converters: dict[str, Callable[..., Any]] = field(default_factory=dict)
    target_fixture: str | None = None


def get_step_fixture_name(step: Step) -> str:
    """Get step fixture name"""
    return f"{StepNamePrefix.step_impl.value}_{step.type}_{step.name}"


def given(
    name: str | StepParser,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    stacklevel: int = 1,
) -> Callable:
    """Given step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return step(name, GIVEN, converters=converters, target_fixture=target_fixture, stacklevel=stacklevel)


def when(
    name: str | StepParser,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    stacklevel: int = 1,
) -> Callable:
    """When step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return step(name, WHEN, converters=converters, target_fixture=target_fixture, stacklevel=stacklevel)


def then(
    name: str | StepParser,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    stacklevel: int = 1,
) -> Callable:
    """Then step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return step(name, THEN, converters=converters, target_fixture=target_fixture, stacklevel=stacklevel)


def step(
    name: str | StepParser,
    type_: Literal["given", "when", "then"] | None = None,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    stacklevel: int = 1,
) -> Callable[[TCallable], TCallable]:
    """Generic step decorator.

    :param name: Step name as in the feature file.
    :param type_: Step type ("given", "when" or "then"). If None, this step will work for all the types.
    :param converters: Optional step arguments converters mapping.
    :param target_fixture: Optional fixture name to replace by step definition.
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.

    Example:
    >>> @step("there is an wallet", target_fixture="wallet")
    >>> def _() -> dict[str, int]:
    >>>     return {"eur": 0, "usd": 0}

    """
    if converters is None:
        converters = {}

    def decorator(func: TCallable) -> TCallable:
        parser = get_parser(name)

        context = StepFunctionContext(
            type=type_,
            step_func=func,
            parser=parser,
            converters=converters,
            target_fixture=target_fixture,
        )

        def step_function_marker() -> StepFunctionContext:
            return context

        step_function_marker._pytest_bdd_step_context = context

        caller_locals = get_caller_module_locals(stacklevel=stacklevel)
        fixture_step_name = find_unique_name(
            f"{StepNamePrefix.step_def.value}_{type_ or '*'}_{parser.name}", seen=caller_locals.keys()
        )
        caller_locals[fixture_step_name] = pytest.fixture(name=fixture_step_name)(step_function_marker)
        return func

    return decorator


def find_unique_name(name: str, seen: Iterable[str]) -> str:
    """Find unique name among a set of strings.

    New names are generated by appending an increasing number at the end of the name.

    Example:
    >>> find_unique_name("foo", ["foo", "foo_1"])
    'foo_2'
    """
    seen = set(seen)
    if name not in seen:
        return name

    for i in count(1):
        new_name = f"{name}_{i}"
        if new_name not in seen:
            return new_name


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

        if old_fd is not None:
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
