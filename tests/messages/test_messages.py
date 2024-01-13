import json
from functools import partial
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING, Iterable, Type, Union, cast

from pydantic import ValidationError

from messages import Attachment, ContentEncoding  # type:ignore[attr-defined]
from messages import Envelope as Message  # type:ignore[attr-defined]
from messages import (  # type:ignore[attr-defined]
    GherkinDocument,
    Hook,
    Meta,
    ParameterType,
    Pickle,
    Source,
    StepDefinition,
)
from messages import TestCase as _TestCase  # type:ignore[attr-defined]
from messages import TestCaseFinished as _TestCaseFinished  # type:ignore[attr-defined]
from messages import TestCaseStarted as _TestCaseStarted  # type:ignore[attr-defined]
from messages import TestRunFinished as _TestRunFinished  # type:ignore[attr-defined]
from messages import TestRunStarted as _TestRunStarted  # type:ignore[attr-defined]
from messages import TestStepFinished as _TestStepFinished  # type:ignore[attr-defined]
from messages import TestStepStarted as _TestStepStarted  # type:ignore[attr-defined]
from pytest_bdd.utils import flip

if TYPE_CHECKING:  # pragma: nocover
    from pytest_bdd.compatibility.pytest import Testdir

samples_path = Path(__file__).parent.parent.parent / "compatibility-kit/devkit/samples"


def unfold_message(message: Message):
    unfoldable_attrs = [
        "attachment",
        "gherkin_document",
        "hook",
        "meta",
        "parameter_type",
        "parse_error",
        "pickle",
        "source",
        "step_definition",
        "test_case",
        "test_case_finished",
        "test_case_started",
        "test_run_finished",
        "test_run_started",
        "test_step_finished",
        "test_step_started",
        "undefined_parameter_type",
    ]

    for attr in unfoldable_attrs:
        if (unfold := getattr(message, attr)) is not None:
            return unfold
    else:  # pragma: nocover
        raise ValueError("Empty message was given")


def list_filter_by_type(t: Union[Type, Iterable[Type]], items):
    return list(filter(partial(flip(isinstance), tuple(t) if isinstance(t, Iterable) else t), items))


class ParseError(RuntimeError):
    ...


def parse_and_unflold_messages(lines):
    errors = []
    parsed_messages = []
    for line in lines:
        try:
            parsed_messages.append(Message.model_validate(json.loads(line)))
        except ValidationError as e:  # pragma: nocover
            errors.append(e)
        if errors:  # pragma: nocover
            raise ParseError(f"Could not parse messages: {errors}")

    return list(map(unfold_message, parsed_messages))


def test_minimal_scenario_messages(testdir: "Testdir", tmp_path):
    testdir.makefile(
        ".feature",
        # language=gherkin
        minimal=(samples_path / "minimal" / "minimal.feature").read_text(),
    )

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import  given
        from parse_type.cfparse import Parser as cfparse

        @given(
            cfparse(
                "I have {cukes:Number} cukes in my belly",
                extra_types=dict(Number=int)
            )
        )
        def cukes_count(cukes):
            assert cukes
        """
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = testdir.runpytest("--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unflold_messages(ndjson_lines)

    meta_messages = messages = list_filter_by_type(Meta, unfold_messages)
    assert len(meta_messages) == 1, f"Messages: {pformat(messages)}"

    source_messages = messages = list_filter_by_type(Source, unfold_messages)
    assert len(source_messages) == 1, f"Messages: {pformat(messages)}"

    gherkin_document_messages = messages = list_filter_by_type(GherkinDocument, unfold_messages)
    assert len(gherkin_document_messages) == 1, f"Messages: {pformat(messages)}"

    pickle_messages = messages = list_filter_by_type(Pickle, unfold_messages)
    assert len(pickle_messages) == 1, f"Messages: {pformat(messages)}"

    step_definition_messages = messages = list_filter_by_type(StepDefinition, unfold_messages)
    step_definitions_defined_by_pytest_bdd_ng = 3
    step_definitions_defined_by_test = 1
    assert (
        len(step_definition_messages) == step_definitions_defined_by_pytest_bdd_ng + step_definitions_defined_by_test
    ), f"Messages: {pformat(messages)}"

    test_run_started_messages = messages = list_filter_by_type(_TestRunStarted, unfold_messages)
    assert len(test_run_started_messages) == 1, f"Messages: {pformat(messages)}"

    test_case_messages = messages = list_filter_by_type(_TestCase, unfold_messages)
    assert len(test_case_messages) == 1, f"Messages: {pformat(messages)}"

    test_case_started_messages = messages = list_filter_by_type(_TestCaseStarted, unfold_messages)
    assert len(test_case_started_messages) == 1, f"Messages: {pformat(messages)}"

    test_step_started_messages = messages = list_filter_by_type(_TestStepStarted, unfold_messages)
    assert len(test_step_started_messages) == 1, f"Messages: {pformat(messages)}"

    test_step_finished_messages = messages = list_filter_by_type(_TestStepFinished, unfold_messages)
    assert len(test_step_finished_messages) == 1, f"Messages: {pformat(messages)}"

    test_case_finished_messages = messages = list_filter_by_type(_TestCaseFinished, unfold_messages)
    assert len(test_case_finished_messages) == 1, f"Messages: {pformat(messages)}"

    test_run_finished_messages = messages = list_filter_by_type(_TestRunFinished, unfold_messages)
    assert len(test_run_finished_messages) == 1, f"Messages: {pformat(messages)}"

    messages_ids = [m.id for m in unfold_messages if hasattr(m, "id")]
    assert len(messages_ids) == len(list(set(messages_ids)))

    test_run_lifetime_messages = list_filter_by_type((_TestRunStarted, _TestRunFinished), unfold_messages)
    assert isinstance(test_run_lifetime_messages[0], _TestRunStarted)
    assert isinstance(test_run_lifetime_messages[1], _TestRunFinished)

    test_case_lifetime_messages = list_filter_by_type((_TestCaseStarted, _TestCaseFinished), unfold_messages)
    assert isinstance(test_case_lifetime_messages[0], _TestCaseStarted)
    assert isinstance(test_case_lifetime_messages[1], _TestCaseFinished)

    test_step_lifetime_messages = list_filter_by_type((_TestStepStarted, _TestStepFinished), unfold_messages)
    assert isinstance(test_step_lifetime_messages[0], _TestStepStarted)
    assert isinstance(test_step_lifetime_messages[1], _TestStepFinished)

    test_run_case_start_lifetime_messages = list_filter_by_type((_TestRunStarted, _TestCaseStarted), unfold_messages)
    assert isinstance(test_run_case_start_lifetime_messages[0], _TestRunStarted)
    assert isinstance(test_run_case_start_lifetime_messages[1], _TestCaseStarted)

    test_case_step_start_lifetime_messages = list_filter_by_type((_TestCaseStarted, _TestStepStarted), unfold_messages)
    assert isinstance(test_case_step_start_lifetime_messages[0], _TestCaseStarted)
    assert isinstance(test_case_step_start_lifetime_messages[1], _TestStepStarted)

    test_case_step_finish_lifetime_messages = list_filter_by_type(
        (_TestCaseFinished, _TestStepFinished), unfold_messages
    )
    assert isinstance(test_case_step_finish_lifetime_messages[0], _TestStepFinished)
    assert isinstance(test_case_step_finish_lifetime_messages[1], _TestCaseFinished)

    test_run_case_finish_lifetime_messages = list_filter_by_type((_TestRunFinished, _TestCaseFinished), unfold_messages)
    assert isinstance(test_run_case_finish_lifetime_messages[0], _TestCaseFinished)
    assert isinstance(test_run_case_finish_lifetime_messages[1], _TestRunFinished)


def test_parameter_type_messages(testdir: "Testdir", tmp_path):
    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from cucumber_expressions.parameter_type import ParameterType
        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

        from pytest_bdd import given
        from pytest_bdd.parsers import cucumber_expression


        class Coordinate:
            def __init__(self, x: int, y: int, z: int):
                self.x = x
                self.y = y
                self.z = z

            def __eq__(self, other):
                return (
                    isinstance(other, Coordinate)
                    and other.x == self.x
                    and self.y == other.y
                    and self.z == other.z
                )


        @pytest.fixture
        def parameter_type_registry():
            _parameter_type_registry = ParameterTypeRegistry()
            _parameter_type_registry.define_parameter_type(
                ParameterType(
                    "coordinate",
                    r"(\\d+),\\s*(\\d+),\\s*(\\d+)",
                    Coordinate,
                    lambda x, y, z: Coordinate(int(x), int(y), int(z)),
                    True,
                    False,
                )
            )

            return _parameter_type_registry


        @given(
            cucumber_expression(
                "A {int} thick line from {coordinate} to {coordinate}"
            ),
            anonymous_group_names=['thick', 'start', 'end'],
        )
        def cukes_count(thick, start, end):
            assert Coordinate(10, 20, 30) == start
            assert Coordinate(40, 50, 60) == end
            assert thick == 5

        """
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        balls="""
        Feature: minimal

          Scenario: Thick line
            Given A 5 thick line from 10,20,30 to 40,50,60

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = testdir.runpytest("--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unflold_messages(ndjson_lines)

    parameter_type_messages = messages = list_filter_by_type(ParameterType, unfold_messages)
    assert len(parameter_type_messages) == 12, f"Messages: {pformat(messages)}"


def test_attachment_type_message_as_raw_string(testdir: "Testdir", tmp_path):
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given('Attach "{value}" as string')
        def attach_as_string(attach, value):
            attach(value)
        """
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment="""
        Feature: Attachment

          Scenario: Add attachment
            Given Attach "Hello world!" as string

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = testdir.runpytest("--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unflold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Attachment, unfold_messages)
    assert len(attachment_messages) == 1, f"Messages: {pformat(messages)}"

    attachment_message: Attachment = attachment_messages[0]
    assert attachment_message.body == "Hello world!"
    assert attachment_message.media_type == "text/plain;charset=UTF-8"
    assert ContentEncoding(attachment_message.content_encoding) == ContentEncoding.identity


def test_attachment_type_messages_as_raw_string_with_content_type(testdir: "Testdir", tmp_path):
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given('Attach "{value}" as url')
        def attach_as_url(attach, value):
            attach(value, media_type='text/uri-list')
        """
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment="""
        Feature: Attachment

          Scenario: Add attachment
            Given Attach "http://https://example.com/" as url

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = testdir.runpytest("--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unflold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Attachment, unfold_messages)
    assert len(attachment_messages) == 1, f"Messages: {pformat(messages)}"

    attachment_message: Attachment = attachment_messages[0]
    assert attachment_message.body == "http://https://example.com/"
    assert attachment_message.media_type == "text/uri-list"
    assert ContentEncoding(attachment_message.content_encoding) == ContentEncoding.identity


def test_attachment_type_messages_as_bytes(testdir: "Testdir", tmp_path):
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given('Attach "{value}" as bytes')
        def attach_as_bytes(attach, value):
            attach(value.encode('utf-8'))
        """
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment="""
        Feature: Attachment

          Scenario: Add attachment
            Given Attach "Hello world!" as bytes

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = testdir.runpytest("--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unflold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Attachment, unfold_messages)
    assert len(attachment_messages) == 1, f"Messages: {pformat(messages)}"

    attachment_message: Attachment = attachment_messages[0]
    assert attachment_message.body == "SGVsbG8gd29ybGQh"
    assert ContentEncoding(attachment_message.content_encoding) == ContentEncoding.base64


def test_attachment_type_messages_from_text_file(testdir: "Testdir", tmp_path):
    file_path = tmp_path / "file.txt"
    (tmp_path / "file.txt").write_text("Hello world!")

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given
        from pathlib import Path

        @given('Attach text from {file_path} file', converters={'file_path': Path})
        def attach_from_file(attach, file_path: Path):
            with file_path.open(mode='r') as file:
                attach(file)
        """
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment=f"""
        Feature: Attachment

          Scenario: Add attachment
            Given Attach text from {file_path} file

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = testdir.runpytest("--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unflold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Attachment, unfold_messages)
    assert len(attachment_messages) == 1, f"Messages: {pformat(messages)}"

    attachment_message: Attachment = attachment_messages[0]
    assert attachment_message.body == "Hello world!"
    assert ContentEncoding(attachment_message.content_encoding) == ContentEncoding.identity


def test_attachment_type_messages_from_binary_file(testdir: "Testdir", tmp_path):
    file_path = tmp_path / "file.txt"
    (tmp_path / "file.txt").write_text("Hello world!")

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given
        from pathlib import Path

        @given('Attach bytes from {file_path} file', converters={'file_path': Path})
        def attach_bytes_from_file(attach, file_path: Path):
            with file_path.open(mode='rb') as file:
                attach(file, file_name=file_path)
        """
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment=f"""
        Feature: Attachment

          Scenario: Add attachment
            Given Attach bytes from {file_path} file

        """,
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = testdir.runpytest("--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unflold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Attachment, unfold_messages)
    assert len(attachment_messages) == 1, f"Messages: {pformat(messages)}"

    attachment_message: Attachment = attachment_messages[0]
    assert attachment_message.body == "SGVsbG8gd29ybGQh"
    assert ContentEncoding(attachment_message.content_encoding) == ContentEncoding.base64
    assert attachment_message.media_type == "application/octet-stream"
    assert Path(cast(str, attachment_message.file_name)).name == "file.txt"


def test_hook_type_messages(testdir, tmp_path):
    testdir.makefile(
        ".ini",
        # language=ini
        pytest="""\
                [pytest]
                markers =
                    tag
                """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        same_name="""\
            @tag
            Feature: Feature with tag
                Scenario: Scenario with tag
                    When Do something
            """,
    )
    testdir.makeconftest(
        # language=python
        f"""\
        from pytest import fixture
        from pytest_bdd import when
        from pytest_bdd.hook import before_tag, before_mark, after_tag, around_mark
        from pytest_bdd.compatibility.pytest import FixtureRequest
        from pytest_bdd.utils import inject_fixture


        @fixture(scope='session')
        def session_fixture():
            return 'session_fixture'

        @before_tag('@tag', name='before')
        def inject_custom_fixture(request: FixtureRequest, session_fixture):
            inject_fixture(request, 'tag_fixture', True)
            assert session_fixture == 'session_fixture'

        @before_mark('tag')
        def inject_another_custom_fixture(request: FixtureRequest):
            inject_fixture(request, 'another_tag_fixture', True)

        @after_tag('@tag', name='after')
        def check_step_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @around_mark('tag', 'around')
        def check_around_test_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert not hasattr(request.config, 'test_attr')
            yield
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @when("Do something")
        def do_something(
            tag_fixture,
            another_tag_fixture,
            request,
        ):
            assert tag_fixture
            assert another_tag_fixture
            inject_fixture(request, 'step_fixture', 'step_fixture')
            request.config.test_attr = 'test_attr'
        """
    )

    ndjson_path = tmp_path / "minimal.feature.ndjson"
    result = testdir.runpytest("--messages-ndjson", str(ndjson_path))

    result.assert_outcomes(passed=1)

    with ndjson_path.open(mode="r") as ndjson_file:
        ndjson_lines = ndjson_file.readlines()

    unfold_messages = parse_and_unflold_messages(ndjson_lines)

    attachment_messages = messages = list_filter_by_type(Hook, unfold_messages)
    assert len(attachment_messages) == 4, f"Messages: {pformat(messages)}"

    # before_mark hook
    assert any(map(lambda message: message.tag_expression == "tag" and message.name is None, attachment_messages))

    # before_tag hook
    assert any(map(lambda message: message.tag_expression == "@tag" and message.name == "before", attachment_messages))

    # after_tag hook
    assert any(map(lambda message: message.tag_expression == "@tag" and message.name == "after", attachment_messages))

    # after_tag hook
    assert any(map(lambda message: message.tag_expression == "tag" and message.name == "around", attachment_messages))
