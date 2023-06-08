# Implement CI meta message
from __future__ import annotations

from pathlib import Path
from time import time_ns
from typing import cast

from _pytest.fixtures import FixtureRequest
from _pytest.main import Session
from attr import attrib, attrs
from pytest import ExitCode

from pytest_bdd.compatibility.pytest import Config, Parser
from pytest_bdd.model.messages import (
    Duration,
    Message,
    Status,
    TestCase,
    TestCaseFinished,
    TestRunFinished,
    TestRunStarted,
    TestStep,
    TestStepFinished,
    TestStepResult,
    TestStepStarted,
    Timestamp,
)
from pytest_bdd.steps import StepHandler
from pytest_bdd.utils import PytestBDDIdGeneratorHandler, deepattrgetter


@attrs(eq=False)
class MessagePlugin:
    config: Config = attrib()
    current_test_case = attrib(default=None)
    current_test_case_step_to_definition_mapping = attrib(default=None)

    def get_timestamp(self):
        timestamp = time_ns()
        test_run_started_seconds = timestamp // 10**9
        test_run_started_nanos = timestamp - test_run_started_seconds * 10**9
        return Timestamp(seconds=test_run_started_seconds, nanos=test_run_started_nanos)

    @staticmethod
    def add_options(parser: Parser) -> None:
        """Add pytest-bdd options."""
        group = parser.getgroup("bdd", "Cucumber NDJSON")
        group.addoption(
            "--messagesndjson",
            "--messages-ndjson",
            action="store",
            dest="messages_ndjson_path",
            metavar="path",
            default=None,
            help="messages ndjson report file at given path.",
        )

    def pytest_bdd_message(self, config: Config, message: Message):
        if config.option.messages_ndjson_path is None:
            return
        with Path(self.config.option.messages_ndjson_path).open(mode="a+") as f:
            f.write(message.json(exclude_none=True))
            f.write("\n")

    def pytest_runtestloop(self, session: Session):
        config = session.config
        if config.option.messages_ndjson_path is None:
            return
        hook_handler = config.hook

        # TODO check messaging of step definitions; seems outdated

        # Message plugins step definitions (test module step definitions are messaged separately)
        for plugin in session.config.pluginmanager._plugin2hookcallers.keys():
            registry = deepattrgetter("step_registry.__registry__.registry", default=set())(plugin)[0]
            for step_definition in registry:
                hook_handler.pytest_bdd_message(
                    config=config, message=Message(stepDefinition=step_definition.as_message(config=config))
                )

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(testRunStarted=TestRunStarted(timestamp=self.get_timestamp())),
        )

    def pytest_sessionfinish(self, session, exitstatus):
        config = session.config
        if config.option.messages_ndjson_path is None:
            return
        hook_handler = config.hook

        is_testrun_success = (isinstance(exitstatus, int) and exitstatus == 0) or exitstatus is ExitCode.OK
        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(
                testRunFinished=TestRunFinished(
                    timestamp=self.get_timestamp(),
                    success=is_testrun_success,
                )
            ),
        )

    def pytest_bdd_before_scenario(self, request: FixtureRequest, feature, scenario):
        config: Config | PytestBDDIdGeneratorHandler = request.config  # https://github.com/python/typing/issues/213
        if cast(Config, config).option.messages_ndjson_path is None:
            return
        hook_handler = cast(Config, config).hook

        test_steps = []
        previous_step = None
        self.current_test_case_step_id_to_step_mapping = {}
        for step in scenario.steps:
            try:
                step_definition = hook_handler.pytest_bdd_match_step_definition_to_step(
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    previous_step=previous_step,
                )
            except StepHandler.Matcher.MatchNotFoundError as e:
                pass
            else:
                test_step = TestStep(
                    id=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator.get_next_id(),
                    pickleStepId=step.id,
                    stepDefinitionIds=[step_definition.id]
                    # TODO Check step_match_arguments_lists
                )
                test_steps.append(test_step)
                self.current_test_case_step_id_to_step_mapping[id(step)] = test_step
            finally:
                previous_step = step

        self.current_test_case = TestCase(
            id=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator.get_next_id(),
            pickleId=scenario.id,
            testSteps=test_steps,
        )

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(testCase=self.current_test_case),
        )

    def pytest_bdd_after_scenario(self, request, feature, scenario):
        config = request.config
        if config.option.messages_ndjson_path is None:
            return

        hook_handler = config.hook

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(
                testCaseFinished=TestCaseFinished(
                    testCaseStartedId=self.current_test_case.id,
                    timestamp=self.get_timestamp(),
                    # TODO check usage
                    willBeRetried=False,
                )
            ),
        )
        self.current_test_case = None

    def pytest_bdd_before_step(self, request, feature, scenario, step, step_func):
        config = request.config
        if config.option.messages_ndjson_path is None:
            return
        hook_handler = config.hook

        # TODO check behaviour if missing
        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]

        self.current_test_case_step_start_timestamp = self.get_timestamp()

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(
                testStepStarted=TestStepStarted(
                    testCaseStartedId=self.current_test_case.id,
                    timestamp=self.current_test_case_step_start_timestamp,
                    testStepId=step_definition.id,
                )
            ),
        )

    def pytest_bdd_after_step(self, request, feature, scenario, step, step_func):
        config = request.config
        if config.option.messages_ndjson_path is None:
            return
        hook_handler = config.hook

        # TODO check behaviour if missing
        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]
        self.current_test_case_step_finish_timestamp = self.get_timestamp()

        current_test_case_step_duration_total_nanos = (
            self.current_test_case_step_finish_timestamp.seconds * 10**9
            + self.current_test_case_step_finish_timestamp.nanos
        ) - (
            self.current_test_case_step_start_timestamp.seconds * 10**9
            + self.current_test_case_step_start_timestamp.nanos
        )
        current_test_case_step_duration_seconds = current_test_case_step_duration_total_nanos // 10**9
        current_test_case_step_duration_nanos = (
            current_test_case_step_duration_total_nanos - current_test_case_step_duration_seconds * 10**9
        )
        current_test_case_step_duration = Duration(
            seconds=current_test_case_step_duration_seconds, nanos=current_test_case_step_duration_nanos
        )

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(
                testStepFinished=TestStepFinished(
                    testCaseStartedId=self.current_test_case.id,
                    timestamp=self.current_test_case_step_finish_timestamp,
                    testStepId=step_definition.id,
                    testStepResult=TestStepResult(duration=current_test_case_step_duration, status=Status.passed),
                )
            ),
        )

    def pytest_bdd_step_error(
        self, request, feature, scenario, step, step_func, step_func_args, exception, step_definition
    ):
        config = request.config
        if config.option.messages_ndjson_path is None:
            return
        hook_handler = config.hook

        # TODO check behaviour if missing
        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]
        self.current_test_case_step_finish_timestamp = self.get_timestamp()

        current_test_case_step_duration_total_nanos = (
            self.current_test_case_step_finish_timestamp.seconds * 10**9
            + self.current_test_case_step_finish_timestamp.nanos
        ) - (
            self.current_test_case_step_start_timestamp.seconds * 10**9
            + self.current_test_case_step_start_timestamp.nanos
        )
        current_test_case_step_duration_seconds = current_test_case_step_duration_total_nanos // 10**9
        current_test_case_step_duration_nanos = (
            current_test_case_step_duration_total_nanos - current_test_case_step_duration_seconds * 10**9
        )
        current_test_case_step_duration = Duration(
            seconds=current_test_case_step_duration_seconds, nanos=current_test_case_step_duration_nanos
        )

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(
                testStepFinished=TestStepFinished(
                    testCaseStartedId=self.current_test_case.id,
                    timestamp=self.current_test_case_step_finish_timestamp,
                    testStepId=step_definition.id,
                    testStepResult=TestStepResult(duration=current_test_case_step_duration, status=Status.failed),
                )
            ),
        )
