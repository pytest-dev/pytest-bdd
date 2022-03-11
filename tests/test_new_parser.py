import pytest
from lark import GrammarError
from more_itertools import zip_equal

from pytest_bdd.new_parser import parse
from pytest_bdd.parser import Feature
from pytest_bdd.types import GIVEN, THEN, WHEN

# TODO: Changes to document
#  - Comments are now only allowed in their own lines.
#  - "Feature:" line is always required.
#  - Other changes. Check the modifications to the tests.


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
    assert feature.tags == {"atag", "another_tag", "a_third_tag"}
    # TODO: assert feature.examples
    assert feature.line_number == 3
    # TODO: assert feature.description
    assert feature.background is None


@pytest.mark.parametrize(
    "src",
    [
        """\
@a_tag @a_second_tag @a-third-tag
Feature: a feature
""",
        """\
@a_tag
@a_second_tag
@a-third-tag
Feature: a feature
""",
        """\
@a_tag @a_second_tag
@a-third-tag
Feature: a feature
""",
        """\
@a_tag @a_second_tag @a-third-tag
Feature: a feature
""",
    ],
)
def test_feature_tags(src):
    feature = parse(src)
    assert feature.tags == {"a_tag", "a_second_tag", "a-third-tag"}


@pytest.mark.parametrize(
    "src",
    [
        """\
Feature: a feature
    @a_tag @a_second_tag @a-third-tag
    Scenario: a scenario
""",
        """\
Feature: a feature
    @a_tag
    @a_second_tag
    @a-third-tag
    Scenario: a scenario
""",
        """\
Feature: a feature
    @a_tag @a_second_tag
    @a-third-tag
    Scenario: a scenario
""",
        """\
Feature: a feature
    @a_tag @a_second_tag @a-third-tag
    Scenario: a scenario
""",
    ],
)
def test_scenario_tags(src):
    feature = parse(src)
    assert feature.tags == {}

    [scenario] = feature.scenarios.values()
    assert scenario.tags == {"a_tag", "a_second_tag", "a-third-tag"}


@pytest.mark.parametrize(
    "src",
    [
        """\
Feature: a   feature
    Scenario: a   scenario
        Given there is a   foo
""",
    ],
)
def test_whitespaces_are_kept(src):
    feature = parse(src)
    assert feature.name == "a   feature"

    [scenario] = feature.scenarios.values()
    assert scenario.name == "a   scenario"

    [given] = scenario.steps
    assert given.type == GIVEN
    assert given.name == "there is a   foo"


def test_not_a_tag():
    # TODO: Improve exception
    with pytest.raises(Exception) as e:
        feature = parse(
            """\
@ a_tag
Feature: a feature
"""
        )


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
        But I should not see more than one foo
""",
            [
                (GIVEN, "there is a foo"),
                (GIVEN, "there is a second foo"),
                (GIVEN, "there is a third foo"),
                (THEN, "I should see a foo"),
                (THEN, "I should not see more than one foo"),
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


@pytest.mark.parametrize(
    "src",
    [
        """\
Feature: a feature
    Scenario: a scenario
        Giventhere is a foo""",
        """\
Feature: a feature
    Scenario: a scenario
        Given there is a foo
        Andthere is a second foo""",
        """\
Feature: a feature
    Scenario: a scenario
        WhenI click the foo""",
        """\
Feature: a feature
    Scenario: a scenario
        Thenthere should be a foo""",
    ],
)
def test_steps_need_a_space_after_keyword(src):
    with pytest.raises(Exception) as exc:
        feature = parse(src)
    # TODO: Test the exception


@pytest.mark.parametrize(
    "src",
    [
        """\
Feature: a feature
    Scenario: a scenario
        Given there is a foo

        Then there should be a foo""",
        """\

Feature: a feature
    Scenario: a scenario
        Given there is a foo
        Then there should be a foo""",
        """\
Feature: a feature

    Scenario: a scenario
        Given there is a foo
        Then there should be a foo""",
        """\



Feature: a feature


    Scenario: a scenario

        Given there is a foo



        Then there should be a foo""",
        pytest.param(
            """\
        Feature: a feature
            Scenario: a scenario
                Given there is a foo
                # a comment
                Then there should be a foo""",
            id="new_line_and_comment",
        ),
        pytest.param(
            """\
        Feature: a feature
            Scenario: a scenario
                Given there is a foo

                Then there should be a foo""",
            id="new_line_indented",
        ),
    ],
)
def test_new_lines_are_ignored(src):
    feature = parse(src)
    assert feature.name == "a feature"
    [scenario] = feature.scenarios.values()
    assert scenario.name == "a scenario"

    given, then = scenario.steps

    assert given.name == "there is a foo"
    assert given.type == GIVEN

    assert then.name == "there should be a foo"
    assert then.type == THEN


@pytest.mark.parametrize(
    "src",
    [
        """\
Feature: Background support

    Background:
        Given there is a foo
        And I click the foo


    Scenario: a scenario
"""
    ],
)
def test_feature_background(src):
    feature = parse(src)
    assert feature.name == "Background support"

    first_given, second_given = feature.background.steps
    assert first_given.type == GIVEN
    assert first_given.name == "there is a foo"
    assert second_given.type == GIVEN
    assert second_given.name == "I click the foo"


@pytest.mark.parametrize(
    ["src", "expected"],
    [
        (
            """\
Feature: No description

    Scenario: Description
        Given I have a bar
""",
            "",
        ),
        (
            """\
Feature: A feature
    Description of the feature
    Scenario: Description
        Given I have a bar
""",
            "Description of the feature",
        ),
        (
            """\
Feature: A feature
    Description of the feature
    Background:
        Given I have a bar
""",
            "Description of the feature",
        ),
        (
            """\
Feature: A feature
    Description of the feature
    Background:
        Given I have a background bar
    Scenario: Description
        Given I have a bar
""",
            "Description of the feature",
        ),
        (
            """\
Feature: A feature
    Multiline
    description
    Background:
        Given I have a background bar
    Scenario: Description
        Given I have a bar
""",
            "Multiline\ndescription",
        ),
    ],
)
def test_feature_description(src, expected):
    feature = parse(src)
    assert feature.description == expected


# TODO: This test parametrization makes the trailing-whitespaces pre-commit hook fail.
#  Find a way to solve it somehow.
@pytest.mark.parametrize(
    "src",
    [
        """\
Feature: A feature
""",
        """\
  Feature: A feature
""",
        """\
    Feature: A feature
""",
        """\

Feature: A feature
""",
        """\

  Feature: A feature
""",
        """\

    Feature: A feature
""",
        """\
    
Feature: A feature
""",
        """\
    

Feature: A feature
""",
        """\
    
    Feature: A feature
""",
    ],
)
def test_indentation_feature(src):
    feature = parse(src)
    assert feature.name == "A feature"


@pytest.mark.parametrize(
    "src",
    [
        """\
Feature: A feature
    Scenario: A scenario
        Given there is a foo
        When I click the foo
        Then there should be a foo
""",
        """


Feature: A feature



    Scenario: A scenario


        Given there is a foo
        When I click the foo




        Then there should be a foo
""",
    ],
)
def test_empty_lines(src):
    feature = parse(src)
    assert feature.name == "A feature"
    [scenario] = feature.scenarios.values()
    assert feature.description == ""

    assert scenario.name == "A scenario"
    given, when, then = scenario.steps

    assert given.type == GIVEN
    assert given.name == "there is a foo"

    assert when.type == WHEN
    assert when.name == "I click the foo"

    assert then.type == THEN
    assert then.name == "there should be a foo"


@pytest.mark.parametrize(
    ["src", "expected"],
    [
        (
            """\
Feature: A feature
    Scenario: A scenario
        Examples:
        |  foo  |
        |  bar  |
""",
            [{"foo": "bar"}],
        ),
        (
            """\
Feature: A feature
    Scenario: A scenario
        Examples:
        | first name | last name |
        | Alessio    | Bogon     |
        | Oleg       | Pidsadnyi |
""",
            [
                {"first name": "Alessio", "last name": "Bogon"},
                {"first name": "Oleg", "last name": "Pidsadnyi"},
            ],
        ),
        (
            """\
Feature: A feature
    Scenario: A scenario
""",
            [],
        ),
        (
            """\
Feature: A feature
    Scenario: A scenario
        Examples:
        |  pipe in the \\| middle  |
        |  foo    |
""",
            [
                {"pipe in the | middle": "foo"},
            ],
        ),
    ],
)
def test_scenario_examples(src, expected):
    feature = parse(src)
    [scenario] = feature.scenarios.values()
    assert list(scenario.examples.as_contexts()) == expected


def test_comment():
    src = """\
# feature comment
Feature: Comments  # n
    # scenario comment
    Scenario: Comments can only be at start of lines  # not a comment
        # steps comment
        Given foo
        And a line without a #comment
        # mid-steps comment
        And this is not a#comment
        And this is not "#acomment"
"""
    feature = parse(src)
    assert feature.name == "Comments  # n"
    assert feature.description == ""
    [scenario] = feature.scenarios.values()

    assert scenario.name == "Comments can only be at start of lines  # not a comment"

    assert all(step.type == GIVEN for step in scenario.steps)

    step_names = [step.name for step in scenario.steps]
    assert step_names == ["foo", "a line without a #comment", "this is not a#comment", 'this is not "#acomment"']


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
