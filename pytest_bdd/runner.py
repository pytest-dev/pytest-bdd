from __future__ import annotations

from collections import deque
from contextlib import suppress
from functools import partial
from itertools import zip_longest
from operator import attrgetter

from pytest import hookimpl

from pytest_bdd import exceptions
from pytest_bdd.model import Feature, Scenario
from pytest_bdd.steps import StepHandler
from pytest_bdd.typing.pytest import FixtureRequest, Item, call_fixture_func
from pytest_bdd.utils import DefaultMapping, get_args, inject_fixture


class ScenarioRunner:
    def __init__(self):
        self.request: FixtureRequest | None = None
        self.feature = None
        self.scenario = None
        self.plugin_manager = None

    def pytest_runtest_call(self, item: Item):
        if "pytest_bdd_scenario" in list(map(attrgetter("name"), item.iter_markers())):
            self.request = item._request
            self.feature = self.request.getfixturevalue("feature")
            self.scenario = self.request.getfixturevalue("scenario")
            self.plugin_manager = self.request.config.hook
            self.plugin_manager.pytest_bdd_before_scenario(
                request=self.request, feature=self.feature, scenario=self.scenario
            )
            try:
                self.plugin_manager.pytest_bdd_run_scenario(
                    request=self.request,
                    feature=self.feature,
                    scenario=self.scenario,
                )
            finally:
                self.plugin_manager.pytest_bdd_after_scenario(
                    request=self.request, feature=self.feature, scenario=self.scenario
                )

    def pytest_bdd_run_scenario(self, request: FixtureRequest, feature: Feature, scenario: Scenario):
        """Execute the scenarios.

        :param feature: Feature.
        :param scenario: Scenario.
        :param request: request.
        """
        previous_step = None
        left_steps: deque = request.getfixturevalue("steps_left")
        left_steps.extend(scenario.steps)
        while left_steps:
            step = left_steps.popleft()
            self.plugin_manager.pytest_bdd_run_step(
                request=request, feature=feature, scenario=scenario, step=step, previous_step=previous_step
            )  # type: ignore[call-arg]
            previous_step = step

    def pytest_bdd_run_step(self, request, feature, scenario, step, previous_step):
        hook_kwargs = dict(
            request=request,
            feature=feature,
            scenario=scenario,
            step=step,
            previous_step=previous_step,
        )

        try:
            step_definition = self._match_to_step(step, previous_step)
        except exceptions.StepDefinitionNotFoundError as exception:
            hook_kwargs["exception"] = exception
            self.request.config.hook.pytest_bdd_step_func_lookup_error(**hook_kwargs)
            raise
        else:
            hook_kwargs["step_func"] = step_definition.func
            hook_kwargs["step_definition"] = step_definition

        self.request.config.hook.pytest_bdd_before_step(**hook_kwargs)

        hook_kwargs["step_func_args"] = {}
        step_params = step_definition.get_parameters(step)
        try:
            self._inject_step_parameters_as_fixtures(
                step_params=step_params, params_fixtures_mapping=step_definition.params_fixtures_mapping
            )

            step_function_kwargs = dict(self._get_step_function_kwargs(step, step_definition, step_params))
            hook_kwargs["step_func_args"] = step_function_kwargs

            self.request.config.hook.pytest_bdd_before_step_call(**hook_kwargs)

            step_caller = self.request.config.hook.pytest_bdd_get_step_caller(**hook_kwargs)
            step_result = step_caller()

            self._inject_target_fixtures(step_definition, step_result)
            self.request.config.hook.pytest_bdd_after_step(**hook_kwargs)
        except Exception as exception:
            hook_kwargs["exception"] = exception
            self.request.config.hook.pytest_bdd_step_error(**hook_kwargs)
            raise

    @hookimpl(trylast=True)
    def pytest_bdd_get_step_caller(self, request, feature, scenario, step, step_func, step_func_args, step_definition):
        # Execute the step as if it was a pytest fixture, so that we can allow "yield" statements in it
        return partial(call_fixture_func, fixturefunc=step_definition.func, request=request, kwargs=step_func_args)

    def _inject_step_parameters_as_fixtures(
        self, step_params: dict | None = None, params_fixtures_mapping: dict | None = None
    ):
        step_params = step_params or {}
        params_fixtures_mapping = (
            DefaultMapping.instantiate_from_collection_or_bool(
                params_fixtures_mapping or {}, warm_up_keys=step_params.keys()
            )
            or {}
        )

        for param, fixture_name in params_fixtures_mapping.items():
            if fixture_name is not None:
                with suppress(KeyError):
                    inject_fixture(self.request, fixture_name, step_params[param])

    def _get_step_function_kwargs(self, step, step_definition, step_params):
        for param in get_args(step_definition.func):
            try:
                yield param, step_params[param]
            except KeyError:
                try:
                    yield param, dict(step=step)[param]
                except KeyError:
                    yield param, self.request.getfixturevalue(param)

    def _inject_target_fixtures(self, step_definition, step_result):
        if len(step_definition.target_fixtures) == 1:
            injectable_fixtures = [(step_definition.target_fixtures[0], step_result)]
        elif step_result is not None and len(step_definition.target_fixtures) != 0:
            injectable_fixtures = zip(step_definition.target_fixtures, step_result)
        else:
            injectable_fixtures = zip_longest(step_definition.target_fixtures, [])

        for target_fixture, return_value in injectable_fixtures:
            inject_fixture(self.request, target_fixture, return_value)

    def _match_to_step(self, step, previous_step):
        try:
            return self.request.config.hook.pytest_bdd_match_step_definition_to_step(
                request=self.request,
                feature=self.feature,
                scenario=self.scenario,
                step=step,
                previous_step=previous_step,
            )
        except StepHandler.Matcher.MatchNotFoundError as e:
            raise exceptions.StepDefinitionNotFoundError(
                f'Step definition is not found: "{step.name}". '
                f'Step keyword: "{step.keyword}". '
                f"Line {step.line_number} "
                f'in scenario "{self.scenario.name}" '
                f'in the feature "{self.feature.filename}"'
            ) from e
