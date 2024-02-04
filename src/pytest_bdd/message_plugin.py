import json
import logging
import os
import sys
from base64 import b64encode
from inspect import getfile, getsourcelines
from io import BufferedIOBase, TextIOBase
from pathlib import Path
from platform import machine, processor, system, version
from pprint import pformat
from queue import Empty, Queue
from threading import Event, Thread
from time import sleep, time_ns
from typing import Callable, Set, Union, cast

from attr import attrib, attrs
from ci_environment import detect_ci_environment
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from filelock import FileLock
from pydantic import ValidationError
from pytest import ExitCode, Session, hookimpl

from messages import Attachment, Ci, ContentEncoding, Duration  # type:ignore[attr-defined]
from messages import Envelope as Message  # type:ignore[attr-defined]
from messages import (  # type:ignore[attr-defined]
    Hook,
    Location,
    Meta,
    ParameterType,
    Product,
    Source,
    SourceReference,
    Status,
    TestCase,
    TestCaseFinished,
    TestCaseStarted,
    TestRunFinished,
    TestRunStarted,
    TestStep,
    TestStepFinished,
    TestStepResult,
    TestStepStarted,
    Timestamp,
)
from pytest_bdd.compatibility.pytest import (
    Config,
    FixtureDef,
    FixtureRequest,
    Parser,
    get_config_root_path,
    get_metafunc_call_arg,
    is_set,
)
from pytest_bdd.packaging import get_distribution_version
from pytest_bdd.steps import StepHandler
from pytest_bdd.utils import PytestBDDIdGeneratorHandler, deepattrgetter


@attrs(eq=False)
class MessagePlugin:
    config: Config = attrib()
    current_test_case = attrib(default=None)
    current_test_case_step_to_definition_mapping = attrib(default=None)
    parameter_type_registry: Set[int] = set()
    hook_registry: Set[int] = set()

    def __attrs_post_init__(self):
        self.is_disabled = self.config.option.messages_ndjson_path is None

        if not self.is_disabled:
            self.process_messages_io_queue = Queue()
            self.process_messages_stop_event = Event()
            self.process_messages_thread = Thread(
                target=type(self).process_messages,
                args=(
                    self.process_messages_io_queue,
                    self.process_messages_stop_event,
                    self.config.option.messages_ndjson_path,
                ),
                daemon=True,
            )
            self.process_messages_thread.start()
            sleep(0)

    @staticmethod
    def process_messages(queue: Queue, stop_event: Event, messages_file_path: Union[str, Path]):
        last_enter = False
        while not (stop_event.is_set() and last_enter):  # give one more enter to take all left messages
            if stop_event.is_set():
                last_enter = True
            lock = FileLock(f"{messages_file_path}.lock")
            with lock:
                with Path(messages_file_path).open(mode="at+", buffering=1) as f:
                    lines = []
                    while not queue.empty():
                        try:
                            message_json = queue.get(timeout=1)
                        except Empty:
                            sleep(0)
                            continue

                        try:
                            Message.model_validate(json.loads(message_json))  # type: ignore[attr-defined] # migration to pydantic2
                        except ValidationError:
                            logging.exception(f"Failed to parse:\n{pformat(message_json)}\n", exc_info=True)
                        else:
                            lines.append(f"{message_json}\n")
                        finally:
                            queue.task_done()
                        sleep(0)
                    f.writelines(lines)
                    f.flush()

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

    @hookimpl(hookwrapper=True)
    def pytest_generate_tests(self, metafunc):
        yield
        if self.is_disabled:
            return

        if all(
            [
                "feature" in metafunc.fixturenames,
                "scenario" in metafunc.fixturenames,
                "feature_source" in metafunc.fixturenames,
                metafunc._calls,
            ]
        ):
            config = metafunc.config

            feature_registry = set()
            pickle_registry = set()
            for call in metafunc._calls:
                feature = get_metafunc_call_arg(call, "feature")
                pickle = get_metafunc_call_arg(call, "scenario")
                feature_source: Source = get_metafunc_call_arg(call, "feature_source")

                if is_set(feature) and feature_source.uri not in feature_registry:
                    feature_registry.add(feature_source.uri)
                    cast(Config, config).hook.pytest_bdd_message(config=config, message=Message(source=feature_source))

                    cast(Config, config).hook.pytest_bdd_message(
                        config=config, message=Message(gherkin_document=feature.gherkin_document)
                    )
                if is_set(pickle) and id(pickle) not in pickle_registry:
                    cast(Config, config).hook.pytest_bdd_message(config=config, message=Message(pickle=pickle))

    def pytest_bdd_message(self, config: Config, message: Message):
        if self.is_disabled:
            return

        message_json = message.model_dump_json(exclude_none=True, by_alias=True)  # type: ignore[attr-defined] # migration to pydantic2
        self.process_messages_io_queue.put_nowait(message_json)

    def pytest_runtestloop(self, session: Session):
        if self.is_disabled:
            return

        config = session.config
        hook_handler = config.hook

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(test_run_started=TestRunStarted(timestamp=self.get_timestamp())),
        )

    def pytest_sessionstart(self, session):
        if self.is_disabled:
            return

        config = session.config
        hook_handler = config.hook

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(
                meta=Meta(
                    protocol_version="22.0.0",
                    implementation=Product(
                        name="pytest-bdd-ng", version=str(get_distribution_version("pytest-bdd-ng"))
                    ),
                    runtime=Product(name="Python", version=sys.version),
                    os=Product(name=system(), version=version()),
                    cpu=Product(name=machine(), version=processor()),
                    ci=Ci.model_validate(obj) if (obj := detect_ci_environment(os.environ)) is not None else None,
                ),
            ),
        )

    def pytest_sessionfinish(self, session, exitstatus):
        if self.is_disabled:
            return

        config = session.config
        hook_handler = config.hook

        is_testrun_success = (isinstance(exitstatus, int) and exitstatus == 0) or exitstatus is ExitCode.OK
        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(
                test_run_finished=TestRunFinished(
                    timestamp=self.get_timestamp(),
                    success=is_testrun_success,
                )
            ),
        )
        self.process_messages_io_queue.join()
        self.process_messages_stop_event.set()
        self.process_messages_thread.join()

    @hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef: FixtureDef, request):
        func = fixturedef.func
        func_id = id(func)

        if self.is_disabled or func_id in self.hook_registry:
            yield
            return

        config = request.config
        hook_handler = config.hook

        if hasattr(func, "__pytest_bdd_is_hook__"):
            self.hook_registry.add(func_id)

            hook_name = getattr(func, "__pytest_bdd_hook_name__", None)
            hook_expression = getattr(func, "__pytest_bdd_hook_expression__", None)

            hook_handler.pytest_bdd_message(
                config=config,
                message=Message(
                    hook=Hook(
                        id=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator.get_next_id(),
                        **({"name": hook_name} if hook_name is not None else {}),
                        source_reference=SourceReference(
                            uri=os.path.relpath(
                                getfile(func),
                                str(get_config_root_path(cast(Config, config))),
                            ),
                            location=Location(line=getsourcelines(func)[1]),
                        ),
                        **({"tag_expression": hook_expression} if hook_expression is not None else {}),
                    )
                ),
            )

        yield

    @hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        yield

        if self.is_disabled:
            return

        session = item.session
        config: Union[
            Config, PytestBDDIdGeneratorHandler
        ] = session.config  # https://github.com/python/typing/issues/213

        hook_handler = cast(Config, config).hook

        request = item._request
        scenario = request.getfixturevalue("scenario")
        feature = request.getfixturevalue("feature")

        step_registry = request.getfixturevalue("step_registry")
        seen_steps = set()
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    seen_steps.add(id(step_definition))
                    config.hook.pytest_bdd_message(
                        config=config, message=Message(step_definition=step_definition.as_message(config=config))
                    )
            step_registry = step_registry.parent

        step_registry = request.getfixturevalue("step_registry")
        seen_steps = set()
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    parameter_type_registry_getter: Callable[[FixtureRequest], ParameterTypeRegistry] = deepattrgetter(
                        "_get_parameter_type_registry", default=None
                    )(step_definition.parser)[0]

                    if parameter_type_registry_getter is None:
                        break

                    parameter_type_registry = parameter_type_registry_getter(request)

                    parameter_types = dict(
                        map(
                            lambda parameter_type: (id(parameter_type), parameter_type),
                            parameter_type_registry.parameter_types,
                        )
                    )

                    not_yet_registered_parameter_types = {
                        key: parameter_type
                        for key, parameter_type in parameter_types.items()
                        if key not in self.parameter_type_registry
                    }

                    for parameter_type in not_yet_registered_parameter_types.values():
                        hook_handler.pytest_bdd_message(
                            config=config,
                            message=Message(
                                parameter_type=ParameterType(
                                    name=parameter_type.name,
                                    regular_expressions=parameter_type.regexps,
                                    prefer_for_regular_expression_match=parameter_type._prefer_for_regexp_match,
                                    use_for_snippets=parameter_type._use_for_snippets,
                                    id=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator.get_next_id(),
                                ),
                            ),
                        )
                    self.parameter_type_registry |= not_yet_registered_parameter_types.keys()
            step_registry = step_registry.parent

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
                    pickle_step_id=step.id,
                    step_definition_ids=[step_definition.as_message(config).id]
                    # TODO Check step_match_arguments_lists
                )
                test_steps.append(test_step)
                self.current_test_case_step_id_to_step_mapping[id(step)] = test_step
            finally:
                previous_step = step

        self.current_test_case = TestCase(
            id=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator.get_next_id(),
            pickle_id=scenario.id,
            test_steps=test_steps,
        )

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(test_case=self.current_test_case),
        )

    def pytest_bdd_before_scenario(self, request, feature, scenario):
        if self.is_disabled:
            return

        config = request.config
        hook_handler = config.hook

        self.current_test_case_start = TestCaseStarted(
            attempt=getattr(request.node, "execution_count", 0),
            id=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator.get_next_id(),
            test_case_id=self.current_test_case.id,
            worker_id=os.environ.get("PYTEST_XDIST_WORKER", "master"),
            timestamp=self.get_timestamp(),
        )

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(test_case_started=self.current_test_case_start),
        )

    def pytest_bdd_after_scenario(self, request, feature, scenario):
        if self.is_disabled:
            return

        config = request.config

        hook_handler = config.hook

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(
                test_case_finished=TestCaseFinished(
                    test_case_started_id=self.current_test_case_start.id,
                    timestamp=self.get_timestamp(),
                    # TODO check usage
                    will_be_retried=False,
                )
            ),
        )
        self.current_test_case = None

    def pytest_bdd_before_step(self, request, feature, scenario, step, step_func):
        if self.is_disabled:
            return

        config = request.config
        hook_handler = config.hook

        # TODO check behaviour if missing
        step_definition = self.current_test_case_step_id_to_step_mapping[id(step)]

        self.current_test_case_step_start_timestamp = self.get_timestamp()

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(
                test_step_started=TestStepStarted(
                    test_case_started_id=self.current_test_case.id,
                    timestamp=self.current_test_case_step_start_timestamp,
                    test_step_id=step_definition.id,
                )
            ),
        )

    def pytest_bdd_after_step(self, request, feature, scenario, step, step_func):
        if self.is_disabled:
            return

        config = request.config
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
                test_step_finished=TestStepFinished(
                    test_case_started_id=self.current_test_case.id,
                    timestamp=self.current_test_case_step_finish_timestamp,
                    test_step_id=step_definition.id,
                    test_step_result=TestStepResult(duration=current_test_case_step_duration, status=Status.passed),
                )
            ),
        )

    def pytest_bdd_step_error(
        self, request, feature, scenario, step, step_func, step_func_args, exception, step_definition
    ):
        if self.is_disabled:
            return

        config = request.config
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
                test_step_finished=TestStepFinished(
                    test_case_started_id=self.current_test_case.id,
                    timestamp=self.current_test_case_step_finish_timestamp,
                    test_step_id=step_definition.id,
                    test_step_result=TestStepResult(duration=current_test_case_step_duration, status=Status.failed),
                )
            ),
        )

    def pytest_bdd_attach(self, request, attachment, media_type, file_name):
        if self.is_disabled:
            return

        config = request.config
        hook_handler = config.hook

        if isinstance(attachment, (str, TextIOBase)):
            content_encoding = ContentEncoding.identity
            _media_type = "text/plain;charset=UTF-8" if media_type is None else media_type
        elif isinstance(attachment, (bytes, bytearray, BufferedIOBase)):
            content_encoding = ContentEncoding.base64
            _media_type = "application/octet-stream" if media_type is None else media_type
        else:
            content_encoding = ContentEncoding.identity
            _media_type = "text/plain;charset=UTF-8" if media_type is None else media_type

        if isinstance(attachment, str):
            body = attachment
        elif isinstance(attachment, TextIOBase):
            body = attachment.read()
        elif isinstance(attachment, (bytes, bytearray, BufferedIOBase)):
            if isinstance(attachment, bytes):
                body_bytes = attachment
            elif isinstance(attachment, bytearray):
                body_bytes = bytes(attachment)
            elif isinstance(attachment, BufferedIOBase):
                body_bytes = attachment.read()
            else:  # pragma: no cover
                body_bytes = b""

            body = b64encode(body_bytes).decode("ascii")
        else:
            body = str(attachment)

        hook_handler.pytest_bdd_message(
            config=config,
            message=Message(
                attachment=Attachment(
                    test_step_id=self.current_test_case.id,
                    test_case_started_id=self.current_test_case.id,
                    # TODO find a specification when it useful
                    # source=,
                    media_type=_media_type,
                    **(dict(file_name=str(file_name)) if file_name is not None else {}),
                    content_encoding=content_encoding,
                    body=body,
                )
            ),
        )
