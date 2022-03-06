import pytest
from more_itertools import zip_equal

from pytest_bdd.new_parser import parse
from pytest_bdd.parser import Feature
from pytest_bdd.types import GIVEN, THEN, WHEN

# TODOs:
#  - test comments


def test_feature():
    feature = parse(
        """\
@atag @another_tag
@a_third_tag
Feature: a feature
"""
    )
    assert isinstance(feature, Feature)
    assert feature.name == "a feature"
    assert feature.tags == ["atag", "another_tag", "a_third_tag"]
    # TODO: assert feature.examples
    assert feature.line_number == 3
    # TODO: assert feature.description
    # TODO: assert feature.background


@pytest.mark.parametrize(
    "src, expected_scenarios",
    [
        (
            """\
Feature: a feature
""",
            0,
        ),
        (
            """\
Feature: a feature
    Scenario: scenario 1
""",
            1,
        ),
        (
            """\
Feature: a feature
    Scenario: scenario 1
    Scenario: scenario 2
""",
            2,
        ),
        #         (
        #             """\
        # Scenario: scenario 1
        # Scenario: scenario 2
        # """,
        #             2,
        #         ),  # 2 scenario, no Feature header. Not sure we want to support this, or if it's still possible
    ],
)
def test_scenario(src, expected_scenarios):
    feature = parse(src)

    assert len(feature.scenarios) == expected_scenarios
    for i, (k, scenario) in enumerate(feature.scenarios.items(), start=1):
        assert k == scenario.name == f"scenario {i}"
        assert scenario.feature == feature
        assert scenario.line_number == 1 + i
        # TODO: assert scenario.example_converters
        # TODO: assert scenario.tags


@pytest.mark.parametrize(
    "src, expected_steps",
    [
        (
            """\
Feature: a feature
    Scenario: a scenario
""",
            [],
        ),
        (
            """\
Feature: a feature
    Scenario: a scenario
        Given there is a foo
""",
            [(GIVEN, "there is a foo")],
        ),
        (
            """\
Feature: a feature
    Scenario: a scenario
        When I click the foo
""",
            [(WHEN, "I click the foo")],
        ),
        (
            """\
Feature: a feature
    Scenario: a scenario
        Then I should see a foo
""",
            [(THEN, "I should see a foo")],
        ),
        (
            """\
Feature: a feature
    Scenario: a scenario
        Given there is a foo
        When I click the foo
        Then I should see a foo
""",
            [(GIVEN, "there is a foo"), (WHEN, "I click the foo"), (THEN, "I should see a foo")],
        ),
        (
            """\
Feature: a feature
    Scenario: a scenario
        Given there is a foo
        Given there is a second foo
        And there is a third foo
        Then I should see a foo
""",
            [
                (GIVEN, "there is a foo"),
                (GIVEN, "there is a second foo"),
                (GIVEN, "there is a third foo"),
                (THEN, "I should see a foo"),
            ],
        ),
        pytest.param(
            """\
Feature: a feature
    Scenario: a scenario
        When I click the foo""",
            [
                (WHEN, "I click the foo"),
            ],
            id="no_ending_newline",
        ),
    ],
)
def test_step(src, expected_steps):
    feature = parse(src)

    [scenario] = feature.scenarios.values()
    for i, (step, expected_step) in enumerate(zip_equal(scenario.steps, expected_steps), start=3):
        expected_type, expected_name = expected_step
        assert step.type == expected_type
        assert step.name == expected_name
        assert step.line_number == i
        # TODO: assert step.name
        # TODO: assert step.keyword
        # TODO: assert step.lines
        # TODO: assert step.indent
        # TODO: assert step.type
        # TODO: assert step.line_number
        # TODO: assert step.failed
        # TODO: assert step.start
        # TODO: assert step.stop
        # TODO: assert step.scenario
        # TODO: assert step.background


@pytest.mark.xfail(reason="Not implemented yet")
def test_step_docstring_and_datatable():
    feature = parse(
        '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
            content of the docstring
            """
            |A|multiline|
            |data|table|
        When I look at the docstring
'''
    )
    [scenario] = feature.scenarios.values()
    given, when = scenario.steps
    assert given.type == GIVEN
    assert given.name == "I have a step with docstring"
    assert given.docstring == "content of the docstring"
    # fmt: off
    assert given.datatable == [
        ['A', 'multiline'],
        ['data', 'table'],
    ]
    # fmt: on

    assert when.type == WHEN
    assert when.name == "I look at the docstring"
