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

import os
import warnings
from contextlib import suppress
from inspect import getfile, getsourcelines
from typing import Any, Callable, Iterable, Iterator, Sequence, cast
from uuid import uuid4
from warnings import warn

import pytest
from attr import Factory, attrib, attrs
from ordered_set import OrderedSet

from pytest_bdd.compatibility.pytest import Config, Parser, TypeAlias, get_config_root_path
from pytest_bdd.model import Feature, StepType
from pytest_bdd.model.messages import Location, Pickle
from pytest_bdd.model.messages import PickleStep as Step
from pytest_bdd.model.messages import SourceReference, StepDefinition, StepDefinitionPattern
from pytest_bdd.parsers import StepParser
from pytest_bdd.utils import (
    PytestBDDIdGeneratorHandler,
    convert_str_to_python_name,
    get_caller_module_locals,
    setdefaultattr,
)
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
    anonymous_group_names: Iterable[str] | None = None,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] | None = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
    param_defaults: dict | None = None,
    liberal: bool | None = None,
    stacklevel=1,
) -> Callable:
    """Given step decorator.

    :param parserlike: StepHandler name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.


    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        StepType.context,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def when(
    parserlike: Any,
    anonymous_group_names: Iterable[str] | None = None,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] | None = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
    param_defaults: dict | None = None,
    liberal: bool | None = None,
    stacklevel=1,
) -> Callable:
    """When step decorator.

    :param parserlike: StepHandler name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        StepType.action,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def then(
    parserlike: Any,
    anonymous_group_names: Iterable[str] | None = None,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] | None = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
    param_defaults: dict | None = None,
    liberal: bool | None = None,
    stacklevel=1,
) -> Callable:
    """Then step decorator.

    :param parserlike: StepHandler name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        StepType.outcome,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def step(
    parserlike: Any,
    anonymous_group_names: Iterable[str] | None = None,
    converters: dict[str, Callable] | None = None,
    target_fixture: str | None = None,
    target_fixtures: list[str] | None = None,
    params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
    param_defaults: dict | None = None,
    liberal: bool | None = None,
    stacklevel=1,
):
    """Liberal step decorator which could be used with any keyword.

    :param parserlike: StepHandler name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        StepType.unknown,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


class StepHandler:
    Model: TypeAlias = "Step"

    @attrs
    class Matcher:
        config: Config = attrib()
        feature: Feature = attrib(init=False)
        pickle: Pickle = attrib(init=False)
        step: Step = attrib(init=False)
        previous_step: Step | None = attrib(init=False)
        step_registry: StepHandler.Registry = attrib(init=False)
        step_type_context = attrib(default=None)

        class MatchNotFoundError(RuntimeError):
            pass

        def __call__(
            self,
            feature: Feature,
            pickle: Pickle,
            step: Step,
            previous_step: Step | None,
            step_registry: StepHandler.Registry,
        ) -> StepHandler.Definition:
            self.feature = feature
            self.pickle = pickle
            self.step = step
            self.previous_step = previous_step
            self.step_registry = step_registry

            self.step_type_context = (
                self.step_type_context
                if self.step.type is StepType.unknown and self.step_type_context is not None
                else self.step.type
            )

            step_definitions = list(
                self.find_step_definition_matches(
                    self.step_registry, (self.strict_matcher, self.unspecified_matcher, self.liberal_matcher)
                )
            )

            if len(step_definitions) > 0:
                if len(step_definitions) > 1:
                    warn(PytestBDDStepDefinitionWarning(f"Alternative step definitions are found: {step_definitions}"))
                return step_definitions[0]
            raise self.MatchNotFoundError(self.step.text)

        def strict_matcher(self, step_definition):
            return step_definition.type_ == self.step_type_context and step_definition.parser.is_matching(
                self.step.text
            )

        def unspecified_matcher(self, step_definition):
            return (
                self.step_type_context == StepType.unknown or step_definition.type_ == StepType.unknown
            ) and step_definition.parser.is_matching(self.step.text)

        def liberal_matcher(self, step_definition):
            if step_definition.liberal is None:
                if self.config.option.liberal_steps is not None:
                    is_step_definition_liberal = self.config.option.liberal_steps
                else:
                    is_step_definition_liberal = self.config.getini("liberal_steps")
            else:
                is_step_definition_liberal = step_definition.liberal

            return all(
                (
                    not self.unspecified_matcher(step_definition),
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

    @attrs(eq=False)
    class Definition:
        func: Callable = attrib()
        type_: str | StepType | None = attrib()
        parser: StepParser = attrib()
        anonymous_group_names: Iterable[str] | None = attrib()
        converters: dict[str, Callable] = attrib()
        params_fixtures_mapping: set[str] | dict[str, str] | Any = attrib()
        param_defaults: dict = attrib()
        target_fixtures: list[str] = attrib()
        liberal: Any | None = attrib()

        id = attrib(init=False)
        __cached_message = attrib(init=False)

        def as_message(self, config: Config | PytestBDDIdGeneratorHandler):
            try:
                message = self.__cached_message
            except AttributeError:
                self.id = cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator.get_next_id()
                self.__cached_message = StepDefinition(
                    id=self.id,
                    pattern=StepDefinitionPattern(source=str(self.parser), type=self.parser.type),
                    sourceReference=SourceReference(
                        uri=os.path.relpath(
                            getfile(self.func),
                            str(get_config_root_path(cast(Config, config))),
                        ),
                        location=Location(line=getsourcelines(self.func)[1]),
                    ),
                )
                message = self.__cached_message
            return message

        def get_parameters(self, step: Step):
            parsed_arguments = (
                self.parser.parse_arguments(step.text, anonymous_group_names=self.anonymous_group_names) or {}
            )
            return {
                **self.param_defaults,
                **{arg: self.converters.get(arg, lambda _: _)(value) for arg, value in parsed_arguments.items()},
            }

    @attrs
    class Registry:
        registry: set[StepHandler.Definition] = attrib(default=Factory(set))
        parent: StepHandler.Registry = attrib(default=None, init=False)

        @classmethod
        def inject_registry_fixture_and_register_steps(cls, obj):
            steps = [
                step_candidate
                for step_candidate in obj.__dict__.values()
                if hasattr(step_candidate, "__pytest_bdd_step_definitions__")
            ]
            if steps:
                setdefaultattr(obj, "step_registry", value_factory=lambda: StepHandler.Registry().fixture)
                obj.step_registry.__registry__.register_steps(steps)

        def register_step_definition(self, step_definition):
            self.registry.add(step_definition)

        def register_steps(self, step_funcs):
            for step_func in step_funcs:
                for step_definition in step_func.__pytest_bdd_step_definitions__:
                    self.register_step_definition(step_definition)

        @property
        def fixture(self):
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
        step_type: str | StepType | None,
        step_parserlike: Any,
        anonymous_group_names: Iterable[str] | None = None,
        converters: dict[str, Callable] | None = None,
        target_fixture: str | None = None,
        target_fixtures: list[str] | None = None,
        params_fixtures_mapping: set[str] | dict[str, str] | Any = True,
        param_defaults: dict | None = None,
        liberal: Any | None = None,
        stacklevel=2,
    ) -> Callable:
        """StepHandler decorator for the type and the name.

        :param step_type: StepHandler type (CONTEXT, ACTION or OUTCOME).
        :param step_parserlike: StepHandler name as in the feature file.
        :param anonymous_group_names: Grant names for anonymous groups of parserlike
        :param converters: Optional step arguments converters mapping
        :param target_fixture: Optional fixture name to replace by step definition
        :param target_fixtures: Target fixture names to be replaced by steps definition function.
        :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
        :param param_defaults: Default parameters for step definition
        :param liberal: Could step definition be used with other keywords
        :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture

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

            step_definition = StepHandler.Definition(  # type: ignore[call-arg]
                func=step_func,
                type_=step_type,
                parser=StepParser.build(step_parserlike),
                anonymous_group_names=anonymous_group_names,
                converters=cast(dict, converters),
                params_fixtures_mapping=params_fixtures_mapping,
                param_defaults=cast(dict, param_defaults),
                target_fixtures=cast(list, target_fixtures),
                liberal=liberal,
            )

            setdefaultattr(step_func, "__pytest_bdd_step_definitions__", value_factory=set).add(step_definition)

            # Allow step function have same names, so injecting same steps with generated names into module scope
            converted_name = convert_str_to_python_name(f'step_{step_type or ""}_{step_parserlike}_{uuid4()}')
            get_caller_module_locals(stacklevel=stacklevel)[converted_name] = step_func

            return step_func

        return decorator
