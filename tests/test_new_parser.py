import logging

import pytest
from more_itertools import zip_equal  # add requirement

from pytest_bdd.new_parser import (
    GherkinInvalidDocstring,
    GherkinInvalidTable,
    GherkinMissingFeatureDefinition,
    GherkinMissingFeatureName,
    GherkinMultipleFeatures,
    GherkinUnexpectedInput,
    parse,
)
from pytest_bdd.parser import Feature, Step
from pytest_bdd.tatsu_parser import parse
from pytest_bdd.types import GIVEN, THEN, WHEN

# TODO: Changes to document
#  - Comments are now only allowed in their own lines.
#  - "Feature:" line is always required.
#  - Other changes. Check the modifications to the tests.
#  - Tags can only be "valid" identifiers, e.g. no spaces.
#  - Must use "Scenario Outline" (or "Scenario Template") for outlined scenarios. "Scenario" will not work anymore
#  - Background can only contain "Given" steps (according to gherkin spec)
#  - Test error reporting when filename is passed
#  - Multiline steps are removed


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
    assert feature.line_number == 3
    assert feature.background is None


@pytest.mark.parametrize(
    ["src", "line", "column"],
    [
        (
            """\
Feature: a feature
    Scenario: a scenario
Feature: a second feature
    Scenario: another scenario
""",
            3,
            1,
        ),
        (
            """\
Feature: a feature
    Scenario: a scenario
        Given foo
Feature: a second feature
""",
            4,
            1,
        ),
        (
            """\
Feature: a feature
    Scenario: a scenario
        Given foo
Feature: a second feature
    Scenario: foo
Feature: a third feature
""",
            4,
            1,
        ),
        (
            """\
Feature: a feature
Feature: a second feature
""",
            2,
            1,
        ),
    ],
)
def test_no_more_than_one_feature_allowed(src, line, column):
    with pytest.raises(GherkinMultipleFeatures) as exc:
        parse(src)

    message = str(exc.value)
    assert message.startswith(
        f"""\
Multiple features found at line {line}, column {column}:

Feature: a second feature
"""
    )
    assert message.endswith("File: <unknown>")


@pytest.mark.parametrize(
    ["src", "line", "column"],
    [
        (
            "Feature:",
            1,
            9,
        ),
        (
            "Feature: ",
            1,
            9 + 1,  # There is a space after "Feature:",
        ),
        (
            """\
Feature:\t \t
invalid text
""",
            1,
            9 + 3,  # 3 whitespaces after "Feature:"
        ),
        (
            """\
Feature:
    Scenario: foo
        Given foo
""",
            1,
            9,
        ),
    ],
)
def test_missing_feature_name(src, line, column):
    with pytest.raises(GherkinMissingFeatureName) as exc:
        parse(src)

    message = str(exc.value)
    assert message.startswith(
        f"""\
Missing feature name at line {line}, column {column}:

Feature:"""
    )
    assert message.endswith("File: <unknown>")


@pytest.mark.parametrize(
    "src",
    [
        """\
@a_tag @a_second_tag @a-third-tag @1.tag-with?punctuation!
Feature: a feature
""",
        """\
@a_tag
@a_second_tag
@a-third-tag
@1.tag-with?punctuation!
Feature: a feature
""",
        """\
@a_tag @a_second_tag
@a-third-tag
@1.tag-with?punctuation!
Feature: a feature
""",
        """\
@a_tag @a_second_tag @a-third-tag @1.tag-with?punctuation!
Feature: a feature
""",
    ],
)
def test_feature_tags(src):
    feature = parse(src)
    assert feature.tags == {"a_tag", "a_second_tag", "a-third-tag", "1.tag-with?punctuation!"}


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
    assert feature.tags == set()

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
    ],
)
def test_scenario(src, expected_scenarios):
    feature = parse(src)

    assert len(feature.scenarios) == expected_scenarios
    for i, (k, scenario) in enumerate(feature.scenarios.items(), start=1):
        assert k == scenario.name == f"scenario {i}"
        assert scenario.feature == feature
        assert scenario.line_number == 1 + i


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
            [Step(GIVEN, "there is a foo", 3, 9, "Given")],
        ),
        (
            """\
Feature: a feature
    Scenario: a scenario
        When I click the foo
""",
            [Step(WHEN, "I click the foo", 3, 9, "When")],
        ),
        (
            """\
Feature: a feature
    Scenario: a scenario
        Then I should see a foo
""",
            [Step(THEN, "I should see a foo", 3, 9, "Then")],
        ),
        (
            """\
Feature: a feature
    Scenario: a scenario
        Given there is a foo
        When I click the foo
        Then I should see a foo
""",
            [
                Step(GIVEN, "there is a foo", 3, 9, "Given"),
                Step(WHEN, "I click the foo", 4, 9, "When"),
                Step(THEN, "I should see a foo", 5, 9, "Then"),
            ],
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
                Step(GIVEN, "there is a foo", 3, 9, "Given"),
                Step(GIVEN, "there is a second foo", 4, 9, "Given"),
                Step(GIVEN, "there is a third foo", 5, 9, "And"),
                Step(THEN, "I should see a foo", 6, 9, "Then"),
                Step(THEN, "I should not see more than one foo", 7, 9, "But"),
            ],
        ),
        pytest.param(
            """\
Feature: a feature
    Scenario: a scenario
        Given there is a foo
        And there is a second foo
        When I click a foo
        Then I should see a foo
        When I click the second foo
        Then I should see the second foo
        But I should not see the foo
        When I click the first foo
        Then I should see the first foo
""",
            [
                Step(GIVEN, "there is a foo", 3, 9, "Given"),
                Step(GIVEN, "there is a second foo", 4, 9, "And"),
                Step(WHEN, "I click a foo", 5, 9, "When"),
                Step(THEN, "I should see a foo", 6, 9, "Then"),
                Step(WHEN, "I click the second foo", 7, 9, "When"),
                Step(THEN, "I should see the second foo", 8, 9, "Then"),
                Step(THEN, "I should not see the foo", 9, 9, "But"),
                Step(WHEN, "I click the first foo", 10, 9, "When"),
                Step(THEN, "I should see the first foo", 11, 9, "Then"),
            ],
            id="interleaved_when_then",
        ),
        pytest.param(
            """\
Feature: a feature
    Scenario: a scenario
        When I do nothing
        And I do nothing
        When I click a foo
        Then I should see a foo
        When I click the second foo
        Then I should see the second foo
        But I should not see the foo
        When I click the first foo
        Then I should see the first foo
""",
            [
                Step(WHEN, "I do nothing", 3, 9, "When"),
                Step(WHEN, "I do nothing", 4, 9, "And"),
                Step(WHEN, "I click a foo", 5, 9, "When"),
                Step(THEN, "I should see a foo", 6, 9, "Then"),
                Step(WHEN, "I click the second foo", 7, 9, "When"),
                Step(THEN, "I should see the second foo", 8, 9, "Then"),
                Step(THEN, "I should not see the foo", 9, 9, "But"),
                Step(WHEN, "I click the first foo", 10, 9, "When"),
                Step(THEN, "I should see the first foo", 11, 9, "Then"),
            ],
            id="interleaved_when_then_without_givens",
        ),
        pytest.param(
            """\
Feature: a feature
    Scenario: a scenario
        When I click the foo""",
            [
                Step(WHEN, "I click the foo", 3, 9, "When"),
            ],
            id="no_ending_newline",
        ),
    ],
)
def test_step(src, expected_steps):
    feature = parse(src)

    [scenario] = feature.scenarios.values()
    for step, expected_step in zip_equal(scenario.steps, expected_steps):
        assert step.type == expected_step.type
        assert step.name == expected_step.name
        assert step.line_number == expected_step.line_number
        assert step.indent == expected_step.indent
        assert step.keyword == expected_step.keyword

        assert step.failed is False
        assert step.scenario == scenario


def test_step_background():
    src = """\
Feature: a feature
    Background:
        Given I have a foo
    Scenario: a scenario
        When I click the foo"""
    feature = parse(src)
    [background_step] = feature.background.steps

    assert background_step.name == "I have a foo"
    assert background_step.background is not None
    assert background_step.background == feature.background

    [scenario] = feature.scenarios.values()
    [given, when] = scenario.steps

    assert given is background_step
    assert when.name == "I click the foo"


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
    "src",
    [
        """\
Feature: Background support

    Background:
        Given there is a foo
        When I click the foo


    Scenario: a scenario
""",
        """\
Feature: Background support

    Background:
        Given there is a foo
        Then I click the foo


    Scenario: a scenario
""",
        """\
Feature: Background support
    Background:
        Then I click the foo
    Scenario: a scenario
""",
    ],
)
def test_feature_background_can_only_have_given_steps(src):
    # TODO: Check exception
    with pytest.raises(Exception, match=r"expecting .Given") as exc:
        feature = parse(src)


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
def test_whitespaces_feature(src):
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
        pytest.param(
            """\
Feature: A feature
    Scenario Outline: A scenario
        Examples:
        |  foo  |
        |  bar  |
""",
            [{"foo": "bar"}],
            id="basic",
        ),
        pytest.param(
            """\
Feature: A feature
    Scenario Template: A scenario
        Examples:
        |  foo  |
        |  bar  |
""",
            [{"foo": "bar"}],
            id="scenario_template_instead_of_scenario_outline_keyword",
        ),
        pytest.param(
            """\
Feature: A feature
    Scenario Outline: A scenario
        Scenarios:
        |  foo  |
        |  bar  |
""",
            [{"foo": "bar"}],
            id="scenarios_instead_of_examples_keyword",
        ),
        (
            """\
Feature: A feature
    Scenario Outline: A scenario
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
    Scenario Outline: A scenario
""",
            [],
        ),
        (
            """\
Feature: A feature
    Scenario Outline: A scenario
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


@pytest.mark.parametrize(
    ["src", "line"],
    [
        (
            """\
Feature: A feature
    Scenario Outline: A scenario
        Examples:
        |  backslash at the end of a header\\|
        |  foo    |
""",
            4,
        ),
        (
            """\
Feature: A feature
    Scenario Outline: A scenario
        Examples:
        |  foo    |
        |  backslash at the end of a cell\\|
""",
            5,
        ),
        (
            """\
Feature: A feature
    Scenario Outline: A scenario
        Examples:
        | foo |
        | bar |
        | backslash at the end of the third cell\\|
""",
            6,
        ),
        (
            """\
Feature: A feature
    Scenario Outline: A scenario
        Examples:
        | header |
        | bar |
        | baz | 
        | backslash at the end of the fourth cell\\|
""",
            7,
        ),
        (
            """\
Feature: A feature
    Scenario Outline: A scenario
        Examples:
        | header |
        | bar |
        | baz |
        | lam | 
        | backslash at the end of the fifth cell\\|
""",
            8,
        ),
        (
            """\
Feature: A feature
    Scenario Outline: A scenario
        Examples:
        | header |
        | bar |
        | baz |
        | backslash at the end of a cell in the middle\\|
        | lam |
""",
            7,
        ),
        (
            """\
Feature: A feature
    Scenario Outline: A scenario
        Given foo
        Examples:
        | backslash at the end of a cell in the middle\\|
""",
            7,
        ),
        (
            """\
Feature: A feature
    Scenario Outline: Mismatching number of cells
        Examples:
        | first name |
        | Alessio | Bogon |
""",
            4,
        ),
        (
            """\
Feature: A feature
    Scenario Outline: Mismatching number of cells
        Examples:
        | first name | last name |
        | Alessio |
""",
            4,
        ),
    ],
)
def test_invalid_examples_table(src, line):
    with pytest.raises(GherkinInvalidTable) as exc:
        parse(src)

    message = str(exc.value)
    assert message.startswith(f"Invalid table at line {line}")
    # TODO: we should use the appropriate exception


@pytest.mark.parametrize(
    ["src", "expected"],
    [
        (
            """\
Feature: A feature
    Scenario: A scenario
        Given foo is <foo>
        Examples:
        |  foo  |
        |  bar  |
""",
            [{"foo": "bar"}],
        ),
    ],
)
def test_examples_not_allowed_in_scenario(src, expected):
    """Test that "Examples:" are not allowed in scenarios (only in scenario outlines)"""
    with pytest.raises(Exception):
        feature = parse(src)
    # TODO: Test exception


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
    assert step_names == [
        "foo",
        "a line without a #comment",
        "this is not a#comment",
        'this is not "#acomment"',
    ]


@pytest.mark.parametrize(
    ["src", "expected"],
    [
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
            A simple docstring
            """
''',
            "A simple docstring",
            id="triple_double_quotes",
        ),
        pytest.param(
            """\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            '''
            A simple docstring
            '''
""",
            "A simple docstring",
            id="triple_single_quotes",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
                    """
                    A simple docstring
                    """
''',
            "A simple docstring",
            id="a_lot_of_indentation",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
"""
A simple docstring
"""
''',
            "A simple docstring",
            id="no_indentation",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
            Multiline
            docstring
            """
''',
            "Multiline\ndocstring",
            id="multiline",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
                Indented
                docstring
            """
''',
            "    Indented\n    docstring",
            id="preserves_indentation_difference",
        ),
    ],
)
def test_step_docstring(src, expected):
    feature = parse(src)
    [scenario] = feature.scenarios.values()
    [given] = scenario.steps
    assert given.type == GIVEN
    assert given.name == "I have a step with docstring"
    assert given.docstring == expected


def test_step_after_docstring():
    src = '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
            A docstring
            """
        When I click the foo
'''
    feature = parse(src)
    [scenario] = feature.scenarios.values()
    [given, when] = scenario.steps
    assert given.type == GIVEN
    assert given.name == "I have a step with docstring"
    assert given.docstring == "A docstring"

    assert when.type == WHEN
    assert when.name == "I click the foo"


@pytest.mark.parametrize(
    "src",
    [
        """\
Scenario: foo
    Given foo
Scenario: bar
    Given foo
"""
    ],
)
def test_missing_feature_definition(src):
    with pytest.raises(GherkinMissingFeatureDefinition) as exc:
        parse(src)

    message = str(exc.value)
    assert message.startswith(f"Missing feature definition at line 1, column 1:\n\nScenario: foo")


@pytest.mark.parametrize(
    "src",
    [
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
            Invalid quotes
            \'\'\'
''',
            id="mixed_quotes",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
Invalid indent
            """
''',
            id="invalid_indentation",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
        Invalid indent
            """
''',
            id="invalid_indentation",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
                Invalid
        indent
            """
''',
            id="invalid_indentation",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """Invalid quote indent"""
''',
            id="invalid_quotes_indentation",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
            Invalid quote indent"""
''',
            id="invalid_quotes_indentation",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
            Invalid quote indent
        """
''',
            id="invalid_quotes_indentation",
        ),
        pytest.param(
            '''\
Feature: a feature
    Scenario: a scenario
        Given I have a step with docstring
            """
            Invalid quote indent
                """
''',
            id="invalid_quotes_indentation",
        ),
    ],
)
def test_step_invalid_docstring(src):
    with pytest.raises(GherkinInvalidDocstring) as exc:
        parse(src)
    message = str(exc.value)
    assert message.startswith("Invalid docstring at line 4")


def test_step_datatable():
    feature = parse(
        """\
Feature: a feature
    Scenario: a scenario
        Given I have a step with a datatable
            |A|multiline|
            |data|table|
        When I look at the docstring
"""
    )
    [scenario] = feature.scenarios.values()
    given, when = scenario.steps
    assert given.type == GIVEN
    assert given.name == "I have a step with a datatable"
    # fmt: off
    assert given.datatable == [
        ('A', 'multiline'),
        ('data', 'table'),
    ]
    # fmt: on

    assert when.type == WHEN
    assert when.name == "I look at the docstring"


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
        ('A', 'multiline'),
        ('data', 'table'),
    ]
    # fmt: on

    assert when.type == WHEN
    assert when.name == "I look at the docstring"
