import json
from functools import partial
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING, Iterable, Type, Union

from pydantic import ValidationError

from pytest_bdd.model.messages import GherkinDocument, Message, Meta, ParameterType, Pickle, Source, StepDefinition
from pytest_bdd.model.messages import TestCase as _TestCase
from pytest_bdd.model.messages import TestCaseFinished as _TestCaseFinished
from pytest_bdd.model.messages import TestCaseStarted as _TestCaseStarted
from pytest_bdd.model.messages import TestRunFinished as _TestRunFinished
from pytest_bdd.model.messages import TestRunStarted as _TestRunStarted
from pytest_bdd.model.messages import TestStepFinished as _TestStepFinished
from pytest_bdd.model.messages import TestStepStarted as _TestStepStarted
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


def test_minimal_scenario_messages(testdir: "Testdir", tmp_path):
    """Test comments inside scenario."""
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

    errors = []
    parsed_messages = []
    for ndjson_line in ndjson_lines:
        try:
            parsed_messages.append(Message.parse_obj(json.loads(ndjson_line)))
        except ValidationError as e:  # pragma: nocover
            errors.append(e)
        assert errors == [], f"Could not parse messages: {errors}"

    unfold_messages = list(map(unfold_message, parsed_messages))

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
    """Test comments inside scenario."""
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

    errors = []
    parsed_messages = []
    for ndjson_line in ndjson_lines:
        try:
            parsed_messages.append(Message.parse_obj(json.loads(ndjson_line)))
        except ValidationError as e:  # pragma: nocover
            errors.append(e)
        assert errors == [], f"Could not parse messages: {errors}"

    unfold_messages = list(map(unfold_message, parsed_messages))

    parameter_type_messages = messages = list_filter_by_type(ParameterType, unfold_messages)
    assert len(parameter_type_messages) == 12, f"Messages: {pformat(messages)}"
