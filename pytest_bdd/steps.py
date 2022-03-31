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

import sys
import warnings
from contextlib import suppress
from itertools import zip_longest
from typing import TYPE_CHECKING, Iterable, Iterator, Sequence
from warnings import warn

import pytest
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest, call_fixture_func
from attr import Factory, attrib, attrs
from ordered_set import OrderedSet

from . import exceptions
from .parsers import StepParser, get_parser
from .utils import DefaultMapping, get_args, get_caller_module_locals, inject_fixture
from .warning_types import PytestBDDStepDefinitionWarning

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias


if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Callable

    from _pytest.config.argparsing import Parser

    from .parser import Scenario as ScenarioModel
    from .parser import Step as StepModel


GIVEN = "given"
WHEN = "when"
THEN = "then"
AND_AND = "and_and"
AND_BUT = "and_but"
AND_STAR = "and_star"
TAG = "tag"
CONTINUATION_STEP_TYPES = (AND_AND, AND_BUT, AND_STAR)
STEP_TYPES = (GIVEN, WHEN, THEN, *CONTINUATION_STEP_TYPES)


def add_options(parser: Parser):
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Steps")
    group.addoption(
        "--liberal-steps",
        action="store_true",
        dest="liberal_steps",
        default=None,
        help="Allow use different keywords with same step definition",
    )
    parser.addini(
        "liberal_steps",
        default=False,
        type="bool",
        help="Allow use different keywords with same step definition",
    )


def given(
    parserlike: Any,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
    liberal: bool | None = None,
) -> Callable:
    """Given step decorator.

    :param parserlike: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: Step parameters would be injected as fixtures
    :param liberal: Could step definition be used with other keywords

    :return: Decorator function for the step.
    """
    return Step.decorator_builder(
        GIVEN,
        parserlike,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        liberal=liberal,
    )


def when(
    parserlike: Any,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
    liberal: bool | None = None,
) -> Callable:
    """When step decorator.

    :param parserlike: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: Step parameters would be injected as fixtures
    :param liberal: Could step definition be used with other keywords

    :return: Decorator function for the step.
    """
    return Step.decorator_builder(
        WHEN,
        parserlike,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        liberal=liberal,
    )


def then(
    parserlike: Any,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
    liberal: bool | None = None,
) -> Callable:
    """Then step decorator.

    :param parserlike: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: Step parameters would be injected as fixtures
    :param liberal: Could step definition be used with other keywords

    :return: Decorator function for the step.
    """
    return Step.decorator_builder(
        THEN,
        parserlike,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        liberal=liberal,
    )


def step(
    parserlike: Any,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
):
    """Liberal step decorator which could be used with any keyword.

    :param parserlike: Step name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: Step parameters would be injected as fixtures

    :return: Decorator function for the step.
    """
    return Step.decorator_builder(
        None,
        parserlike,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        liberal=True,
    )


class Step:
    Model: TypeAlias = "StepModel"

    @attrs
    class Matcher:
        config: Config = attrib()
        step = attrib(init=False)
        step_registry: Step.Registry = attrib(init=False)

        class MatchNotFoundError(RuntimeError):
            pass

        def __call__(self, step: Step.Model, step_registry: Step.Registry) -> Step.Definition:
            self.step = step
            self.step_registry = step_registry

            step_definitions = list(
                self.find_step_definition_matches(
                    self.step_registry, (self.strict_matcher, self.liberal_matcher, self.alternate_matcher)
                )
            )

            if len(step_definitions) > 0:
                if len(step_definitions) > 1:
                    warn(PytestBDDStepDefinitionWarning(f"Alternative step definitions are found: {step_definitions}"))
                return step_definitions[0]
            raise self.MatchNotFoundError

        def strict_matcher(self, step_definition):
            return step_definition.type_ == self.step.type and step_definition.parser.is_matching(self.step.name)

        def liberal_matcher(self, step_definition):
            return (step_definition.type_ is None) and step_definition.parser.is_matching(self.step.name)

        def alternate_matcher(self, step_definition):
            if step_definition.liberal is None:
                if self.config.option.liberal_steps is not None:
                    is_step_definition_liberal = self.config.option.liberal_steps
                else:
                    is_step_definition_liberal = self.config.getini("liberal_steps")
            else:
                is_step_definition_liberal = step_definition.liberal

            return all(
                (
                    is_step_definition_liberal,
                    step_definition.type_ != self.step.type,
                    step_definition.parser.is_matching(self.step.name),
                )
            )

        @staticmethod
        def find_step_definition_matches(
            registry: Step.Registry | None, matchers: Sequence[Callable[[Step.Definition], bool]]
        ) -> Iterable[Step.Definition]:
            if registry:
                found_matches = False
                for matcher in matchers:
                    for step_definition in registry:
                        if matcher(step_definition):
                            found_matches = True
                            yield step_definition
                    if found_matches:
                        break
                if not found_matches:
                    with suppress(AttributeError):
                        yield from Step.Matcher.find_step_definition_matches(registry.parent, matchers)

    @attrs
    class Definition:
        func: Callable = attrib()
        type_ = attrib()
        parser: StepParser = attrib()
        converters = attrib()
        params_fixtures_mapping = attrib()
        target_fixtures = attrib()
        liberal = attrib()

        def get_parameters(self, step: Step.Model):
            parsed_arguments = self.parser.parse_arguments(step.name) or {}
            return {arg: self.converters.get(arg, lambda _: _)(value) for arg, value in parsed_arguments.items()}

    @attrs
    class Executor:
        request: FixtureRequest = attrib()
        scenario: ScenarioModel = attrib()
        step: Step.Model = attrib()
        step_params: dict = attrib(init=False)
        step_definition: Step.Definition = attrib(init=False)
        step_result: Any = attrib(init=False)

        def _inject_step_parameters_as_fixtures(
            self, step_params: dict | None = None, params_fixtures_mapping: dict | None = None
        ):
            step_params = step_params or {}
            params_fixtures_mapping = (
                DefaultMapping.instantiate_from_collection_or_bool(
                    params_fixtures_mapping or {}, warm_up_keys=self.step_params.keys()
                )
                or {}
            )

            for param, fixture_name in params_fixtures_mapping.items():
                if fixture_name is not None:
                    with suppress(KeyError):
                        inject_fixture(self.request, fixture_name, step_params[param])

        @property
        def _step_function_kwargs(self):
            for param in get_args(self.step_definition.func):
                try:
                    yield param, self.step_params[param]
                except KeyError:
                    yield param, self.request.getfixturevalue(param)

        def _inject_target_fixtures(self):
            if len(self.step_definition.target_fixtures) == 1:
                injectable_fixtures = [(self.step_definition.target_fixtures[0], self.step_result)]
            elif self.step_result is not None and len(self.step_definition.target_fixtures) != 0:
                injectable_fixtures = zip(self.step_definition.target_fixtures, self.step_result)
            else:
                injectable_fixtures = zip_longest(self.step_definition.target_fixtures, [])

            for target_fixture, return_value in injectable_fixtures:
                inject_fixture(self.request, target_fixture, return_value)

        def __call__(self):
            hook_kwargs = dict(
                request=self.request,
                feature=self.scenario.feature,
                scenario=self.scenario,
                step=self.step,
            )

            try:
                self.step_definition = self.match_to_step()
            except exceptions.StepDefinitionNotFoundError as exception:
                hook_kwargs["exception"] = exception
                self.request.config.hook.pytest_bdd_step_func_lookup_error(**hook_kwargs)
                raise
            else:
                hook_kwargs["step_func"] = self.step_definition.func

            self.request.config.hook.pytest_bdd_before_step(**hook_kwargs)

            hook_kwargs["step_func_args"] = {}
            self.step_params = self.step_definition.get_parameters(self.step)
            try:
                self._inject_step_parameters_as_fixtures(
                    step_params=self.step_params, params_fixtures_mapping=self.step_definition.params_fixtures_mapping
                )

                step_function_kwargs = dict(self._step_function_kwargs)
                hook_kwargs["step_func_args"] = step_function_kwargs

                self.request.config.hook.pytest_bdd_before_step_call(**hook_kwargs)

                # Execute the step as if it was a pytest fixture, so that we can allow "yield" statements in it
                self.step_result = call_fixture_func(
                    fixturefunc=self.step_definition.func, request=self.request, kwargs=step_function_kwargs
                )

                self._inject_target_fixtures()
                self.request.config.hook.pytest_bdd_after_step(**hook_kwargs)
            except Exception as exception:
                hook_kwargs["exception"] = exception
                self.request.config.hook.pytest_bdd_step_error(**hook_kwargs)
                raise

        execute = __call__

        def match_to_step(self):
            try:
                return self.request.config.hook.pytest_bdd_match_step_definition_to_step(
                    request=self.request, step=self.step
                )
            except Step.Matcher.MatchNotFoundError as e:
                raise exceptions.StepDefinitionNotFoundError(
                    f"Step definition is not found: {self.step}. "
                    f"Line {self.step.line_number} "
                    f'in scenario "{self.scenario.name}" '
                    f'in the feature "{self.scenario.feature.filename}"'
                ) from e

    @attrs
    class Registry:
        registry: list[Step.Definition] = attrib(default=Factory(list))
        parent: Step.Registry = attrib(default=None, init=False)

        @classmethod
        def register_step(
            cls,
            caller_locals: dict,
            func,
            type_,
            parserlike,
            converters,
            params_fixtures_mapping,
            target_fixtures,
            liberal,
        ):
            if "step_registry" not in caller_locals.keys():
                built_registry = cls()
                caller_locals["step_registry"] = built_registry.bind_pytest_bdd_step_registry_fixture()

            registry: Step.Registry = caller_locals["step_registry"].__registry__

            parser = get_parser(parserlike)
            registry.registry.append(
                Step.Definition(
                    func=func,
                    type_=type_,
                    parser=parser,
                    converters=converters,
                    params_fixtures_mapping=params_fixtures_mapping,
                    target_fixtures=target_fixtures,
                    liberal=liberal,
                )
            )

        def bind_pytest_bdd_step_registry_fixture(self):
            @pytest.fixture
            def step_registry(step_registry):
                self.parent = step_registry
                return self

            step_registry.__registry__ = self
            return step_registry

        def __iter__(self) -> Iterator[Step.Definition]:
            return iter(self.registry)

    @staticmethod
    def decorator_builder(
        step_type: str | None,
        step_parserlike: Any,
        converters: dict[str, Callable] | None = None,
        target_fixture: str | None = None,
        target_fixtures: list[str] = None,
        params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
        liberal: bool | None = None,
    ) -> Callable:
        """Step decorator for the type and the name.

        :param step_type: Step type (GIVEN, WHEN or THEN).
        :param step_parserlike: Step name as in the feature file.
        :param converters: Optional step arguments converters mapping
        :param target_fixture: Optional fixture name to replace by step definition
        :param target_fixtures: Target fixture names to be replaced by steps definition function.
        :param params_fixtures_mapping: Step parameters would be injected as fixtures
        :param liberal: Could step definition be used with other keywords

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

        def decorator(step_func: Callable) -> Callable:
            """
            Step decorator

            :param function step_func: Step definition function
            """
            Step.Registry.register_step(
                caller_locals=get_caller_module_locals(),
                func=step_func,
                type_=step_type,
                parserlike=step_parserlike,
                converters=converters,
                params_fixtures_mapping=params_fixtures_mapping,
                target_fixtures=target_fixtures,
                liberal=liberal,
            )
            return step_func

        return decorator
