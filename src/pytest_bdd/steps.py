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
from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import count
from typing import Callable, Literal, TypeVar
from weakref import WeakKeyDictionary

import pytest
from typing_extensions import ParamSpec

from .parser import Step
from .parsers import StepParser, get_parser
from .utils import get_caller_module_locals

P = ParamSpec("P")
T = TypeVar("T")

step_function_context_registry: WeakKeyDictionary[Callable[..., object], StepFunctionContext] = WeakKeyDictionary()


@enum.unique
class StepNamePrefix(enum.Enum):
    step_def = "pytestbdd_stepdef"
    step_impl = "pytestbdd_stepimpl"


@dataclass
class StepFunctionContext:
    type: Literal["given", "when", "then"] | None
    step_func: Callable[..., object]
    parser: StepParser
    converters: dict[str, Callable[[str], object]] = field(default_factory=dict)
    target_fixture: str | None = None


def get_step_fixture_name(step: Step) -> str:
    """Get step fixture name"""
    return f"{StepNamePrefix.step_impl.value}_{step.type}_{step.name}"


def given(
    name: str | StepParser,
    converters: dict[str, Callable[[str], object]] | None = None,
    target_fixture: str | None = None,
    stacklevel: int = 1,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Given step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return step(name, "given", converters=converters, target_fixture=target_fixture, stacklevel=stacklevel)


def when(
    name: str | StepParser,
    converters: dict[str, Callable[[str], object]] | None = None,
    target_fixture: str | None = None,
    stacklevel: int = 1,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """When step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return step(name, "when", converters=converters, target_fixture=target_fixture, stacklevel=stacklevel)


def then(
    name: str | StepParser,
    converters: dict[str, Callable[[str], object]] | None = None,
    target_fixture: str | None = None,
    stacklevel: int = 1,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Then step decorator.

    :param name: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return step(name, "then", converters=converters, target_fixture=target_fixture, stacklevel=stacklevel)


def step(
    name: str | StepParser,
    type_: Literal["given", "when", "then"] | None = None,
    converters: dict[str, Callable[[str], object]] | None = None,
    target_fixture: str | None = None,
    stacklevel: int = 1,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Generic step decorator.

    :param name: Step name as in the feature file.
    :param type_: Step type ("given", "when" or "then"). If None, this step will work for all the types.
    :param converters: Optional step arguments converters mapping.
    :param target_fixture: Optional fixture name to replace by step definition.
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.

    Example:
    >>> @step("there is a wallet", target_fixture="wallet")
    >>> def _() -> dict[str, int]:
    >>>     return {"eur": 0, "usd": 0}

    """
    if converters is None:
        converters = {}

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
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

        step_function_context_registry[step_function_marker] = context

        caller_locals = get_caller_module_locals(stacklevel=stacklevel)
        fixture_step_name = find_unique_name(
            f"{StepNamePrefix.step_def.value}_{type_ or '*'}_{parser.name}", seen=caller_locals.keys()
        )
        caller_locals[fixture_step_name] = pytest.fixture(name=fixture_step_name)(step_function_marker)
        return func

    return decorator


def find_unique_name(name: str, seen: Iterable[str]) -> str:
    """Find a unique name among a set of strings.

    New names are generated by appending an increasing number at the end of the name.

    Example:
    >>> find_unique_name("foo", ["foo", "foo_1"])
    'foo_2'
    """
    seen = set(seen)
    if name not in seen:
        return name

    # Generate new names with increasing numbers
    for i in count(1):
        new_name = f"{name}_{i}"
        if new_name not in seen:
            return new_name

    # This line will never be reached, but it's here to satisfy mypy
    raise RuntimeError("Unable to find a unique name")
