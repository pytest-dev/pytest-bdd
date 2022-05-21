"""StepHandler decorators.

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

import warnings
from contextlib import suppress
from typing import Any, Callable, Iterable, Iterator, Sequence
from warnings import warn

import pytest
from attr import Factory, attrib, attrs
from ordered_set import OrderedSet

from pytest_bdd.const import STEP_TYPE, STEP_TYPES_BY_NORMALIZED_PREFIX
from pytest_bdd.model import Feature, Scenario, Step
from pytest_bdd.parsers import StepParser, get_parser
from pytest_bdd.typing.pytest import Config, Parser, TypeAlias
from pytest_bdd.utils import get_caller_module_locals
from pytest_bdd.warning_types import PytestBDDStepDefinitionWarning


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
    param_defaults: dict | None = None,
    liberal: bool | None = None,
) -> Callable:
    """Given step decorator.

    :param parserlike: StepHandler name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords

    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        STEP_TYPE.GIVEN,
        parserlike,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
    )


def when(
    parserlike: Any,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
    param_defaults: dict | None = None,
    liberal: bool | None = None,
) -> Callable:
    """When step decorator.

    :param parserlike: StepHandler name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords

    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        STEP_TYPE.WHEN,
        parserlike,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
    )


def then(
    parserlike: Any,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
    param_defaults: dict | None = None,
    liberal: bool | None = None,
) -> Callable:
    """Then step decorator.

    :param parserlike: StepHandler name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords

    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        STEP_TYPE.THEN,
        parserlike,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
    )


def step(
    parserlike: Any,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
    param_defaults: dict | None = None,
):
    """Liberal step decorator which could be used with any keyword.

    :param parserlike: StepHandler name or a parser object.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition

    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        None,
        parserlike,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=True,
    )


class StepHandler:
    Model: TypeAlias = "Step"

    @attrs
    class Matcher:
        config: Config = attrib()
        feature: Feature = attrib(init=False)
        pickle: Scenario = attrib(init=False)
        step: Step = attrib(init=False)
        previous_step: Step | None = attrib(init=False)
        step_registry: StepHandler.Registry = attrib(init=False)
        step_type_context = attrib(default=None)

        class MatchNotFoundError(RuntimeError):
            pass

        def __call__(
            self,
            feature: Feature,
            pickle: Scenario,
            step: Step,
            previous_step: Step | None,
            step_registry: StepHandler.Registry,
        ) -> StepHandler.Definition:
            self.feature = feature
            self.pickle = pickle
            self.step = step
            self.previous_step = previous_step
            self.step_registry = step_registry

            step_type = STEP_TYPES_BY_NORMALIZED_PREFIX[self.step.prefix]

            self.step_type_context = (
                self.step_type_context
                if step_type in (STEP_TYPE.AND, STEP_TYPE.OTHER) and self.step_type_context is not None
                else step_type
            )

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
            return (
                step_definition.type_ is not None
                and step_definition.type_ == self.step_type_context
                and step_definition.parser.is_matching(self.step.text)
            )

        def liberal_matcher(self, step_definition):
            return (step_definition.type_ is None) and step_definition.parser.is_matching(self.step.text)

        def alternate_matcher(self, step_definition):
            if step_definition.liberal is None:
                # TODO Move to plugin
                if self.config.option.liberal_steps is not None:
                    is_step_definition_liberal = self.config.option.liberal_steps
                else:
                    is_step_definition_liberal = self.config.getini("liberal_steps")
            else:
                is_step_definition_liberal = step_definition.liberal

            return all(
                (
                    is_step_definition_liberal,
                    step_definition.type_ != self.step_type_context,
                    step_definition.parser.is_matching(self.step.text),
                )
            )

        @staticmethod
        def find_step_definition_matches(
            registry: StepHandler.Registry | None, matchers: Sequence[Callable[[StepHandler.Definition], bool]]
        ) -> Iterable[StepHandler.Definition]:
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
                        yield from StepHandler.Matcher.find_step_definition_matches(registry.parent, matchers)

    @attrs(auto_attribs=True)
    class Definition:
        func: Callable
        type_: str | None
        parser: StepParser
        converters: dict[str, Any]
        params_fixtures_mapping: dict[str, str]
        param_defaults: dict
        target_fixtures: list[str]
        liberal: bool

        def get_parameters(self, step: Step):
            parsed_arguments = self.parser.parse_arguments(step.name) or {}
            return {
                **self.param_defaults,
                **{arg: self.converters.get(arg, lambda _: _)(value) for arg, value in parsed_arguments.items()},
            }

    @attrs
    class Registry:
        registry: list[StepHandler.Definition] = attrib(default=Factory(list))
        parent: StepHandler.Registry = attrib(default=None, init=False)

        @classmethod
        def register_step(
            cls,
            caller_locals: dict,
            func,
            type_,
            parserlike,
            converters,
            params_fixtures_mapping,
            param_defaults,
            target_fixtures,
            liberal,
        ):
            if "step_registry" not in caller_locals.keys():
                built_registry = cls()
                caller_locals["step_registry"] = built_registry.bind_pytest_bdd_step_registry_fixture()

            registry: StepHandler.Registry = caller_locals["step_registry"].__registry__

            parser = get_parser(parserlike)
            registry.registry.append(
                StepHandler.Definition(  # type: ignore[call-arg]
                    func=func,
                    type_=type_,
                    parser=parser,
                    converters=converters,
                    params_fixtures_mapping=params_fixtures_mapping,
                    param_defaults=param_defaults,
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

        def __iter__(self) -> Iterator[StepHandler.Definition]:
            return iter(self.registry)

    @staticmethod
    def decorator_builder(
        step_type: str | None,
        step_parserlike: Any,
        converters: dict[str, Callable] | None = None,
        target_fixture: str | None = None,
        target_fixtures: list[str] = None,
        params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
        param_defaults: dict | None = None,
        liberal: bool | None = None,
    ) -> Callable:
        """StepHandler decorator for the type and the name.

        :param step_type: StepHandler type (GIVEN, WHEN or THEN).
        :param step_parserlike: StepHandler name as in the feature file.
        :param converters: Optional step arguments converters mapping
        :param target_fixture: Optional fixture name to replace by step definition
        :param target_fixtures: Target fixture names to be replaced by steps definition function.
        :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
        :param param_defaults: Default parameters for step definition
        :param liberal: Could step definition be used with other keywords

        :return: Decorator function for the step.
        """

        converters = converters or {}
        param_defaults = param_defaults or {}
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
            StepHandler decorator

            :param function step_func: StepHandler definition function
            """
            StepHandler.Registry.register_step(
                caller_locals=get_caller_module_locals(depth=2),
                func=step_func,
                type_=step_type,
                parserlike=step_parserlike,
                converters=converters,
                params_fixtures_mapping=params_fixtures_mapping,
                param_defaults=param_defaults,
                target_fixtures=target_fixtures,
                liberal=liberal,
            )
            return step_func

        return decorator
