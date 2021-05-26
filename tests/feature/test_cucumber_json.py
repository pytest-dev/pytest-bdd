"""Test cucumber json output."""
import json
import os.path
import textwrap


def runandparse(testdir, *args):
    """Run tests in testdir and parse json output."""
    resultpath = testdir.tmpdir.join("cucumber.json")
    result = testdir.runpytest(f"--cucumberjson={resultpath}", "-s", *args)
    with resultpath.open() as f:
        jsonobject = json.load(f)
    return result, jsonobject


class OfType:
    """Helper object to help compare object type to initialization type"""

    def __init__(self, type=None):
        self.type = type

    def __eq__(self, other):
        return isinstance(other, self.type) if self.type else True


def test_step_trace(testdir):
    """Test step trace."""
    testdir.makefile(
        ".ini",
        pytest=textwrap.dedent(
            """
    [pytest]
    markers =
        scenario-passing-tag
        scenario-failing-tag
        scenario-outline-passing-tag
        feature-tag
    """
        ),
    )
    testdir.makefile(
        ".feature",
        test=textwrap.dedent(
            """
    @feature-tag
    Feature: One passing scenario, one failing scenario

        @scenario-passing-tag
        Scenario: Passing
            Given a passing step
            And some other passing step

        @scenario-failing-tag
        Scenario: Failing
            Given a passing step
            And a failing step

        @scenario-outline-passing-tag
        Scenario: Passing outline
            Given type <type> and value <value>

            Examples: example1
            | type    | value  |
            | str     | hello  |
            | int     | 42     |
            | float   | 1.0    |
    """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """
        import pytest
        from pytest_bdd import given, when, scenario

        @given('a passing step')
        def a_passing_step():
            return 'pass'

        @given('some other passing step')
        def some_other_passing_step():
            return 'pass'

        @given('a failing step')
        def a_failing_step():
            raise Exception('Error')

        @given('type <type> and value <value>')
        def type_type_and_value_value():
            return 'pass'

        @scenario('test.feature', 'Passing')
        def test_passing():
            pass

        @scenario('test.feature', 'Failing')
        def test_failing():
            pass

        @scenario('test.feature', 'Passing outline')
        def test_passing_outline():
            pass
    """
        )
    )
    result, jsonobject = runandparse(testdir)
    assert result.ret
    expected = [
        {
            "description": "",
            "elements": [
                {
                    "description": "",
                    "id": "test_passing",
                    "keyword": "Scenario",
                    "line": 5,
                    "name": "Passing",
                    "steps": [
                        {
                            "keyword": "Given",
                            "line": 6,
                            "match": {"location": ""},
                            "name": "a passing step",
                            "result": {"status": "passed", "duration": OfType(int)},
                        },
                        {
                            "keyword": "And",
                            "line": 7,
                            "match": {"location": ""},
                            "name": "some other passing step",
                            "result": {"status": "passed", "duration": OfType(int)},
                        },
                    ],
                    "tags": [{"name": "scenario-passing-tag", "line": 4}],
                    "type": "scenario",
                },
                {
                    "description": "",
                    "id": "test_failing",
                    "keyword": "Scenario",
                    "line": 10,
                    "name": "Failing",
                    "steps": [
                        {
                            "keyword": "Given",
                            "line": 11,
                            "match": {"location": ""},
                            "name": "a passing step",
                            "result": {"status": "passed", "duration": OfType(int)},
                        },
                        {
                            "keyword": "And",
                            "line": 12,
                            "match": {"location": ""},
                            "name": "a failing step",
                            "result": {"error_message": OfType(str), "status": "failed", "duration": OfType(int)},
                        },
                    ],
                    "tags": [{"name": "scenario-failing-tag", "line": 9}],
                    "type": "scenario",
                },
                {
                    "description": "",
                    "keyword": "Scenario",
                    "tags": [{"line": 14, "name": "scenario-outline-passing-tag"}],
                    "steps": [
                        {
                            "line": 16,
                            "match": {"location": ""},
                            "result": {"status": "passed", "duration": OfType(int)},
                            "keyword": "Given",
                            "name": "type <type> and value <value>",
                        }
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": "test_passing_outline[str-hello]",
                    "name": "Passing outline",
                },
                {
                    "description": "",
                    "keyword": "Scenario",
                    "tags": [{"line": 14, "name": "scenario-outline-passing-tag"}],
                    "steps": [
                        {
                            "line": 16,
                            "match": {"location": ""},
                            "result": {"status": "passed", "duration": OfType(int)},
                            "keyword": "Given",
                            "name": "type <type> and value <value>",
                        }
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": "test_passing_outline[int-42]",
                    "name": "Passing outline",
                },
                {
                    "description": "",
                    "keyword": "Scenario",
                    "tags": [{"line": 14, "name": "scenario-outline-passing-tag"}],
                    "steps": [
                        {
                            "line": 16,
                            "match": {"location": ""},
                            "result": {"status": "passed", "duration": OfType(int)},
                            "keyword": "Given",
                            "name": "type <type> and value <value>",
                        }
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": "test_passing_outline[float-1.0]",
                    "name": "Passing outline",
                },
            ],
            "id": os.path.join("test_step_trace0", "test.feature"),
            "keyword": "Feature",
            "line": 2,
            "name": "One passing scenario, one failing scenario",
            "tags": [{"name": "feature-tag", "line": 1}],
            "uri": os.path.join(testdir.tmpdir.basename, "test.feature"),
        }
    ]

    assert jsonobject == expected


def test_step_trace_with_expand_option(testdir):
    """Test step trace."""
    testdir.makefile(
        ".ini",
        pytest=textwrap.dedent(
            """
    [pytest]
    markers =
        feature-tag
        scenario-outline-passing-tag
    """
        ),
    )
    testdir.makefile(
        ".feature",
        test=textwrap.dedent(
            """
    @feature-tag
    Feature: One scenario outline, expanded to multiple scenarios

        @scenario-outline-passing-tag
        Scenario: Passing outline
            Given type <type> and value <value>

            Examples: example1
            | type    | value  |
            | str     | hello  |
            | int     | 42     |
            | float   | 1.0    |
    """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """
        import pytest
        from pytest_bdd import given, scenario

        @given('type <type> and value <value>')
        def type_type_and_value_value():
            return 'pass'

        @scenario('test.feature', 'Passing outline')
        def test_passing_outline():
            pass
    """
        )
    )
    result, jsonobject = runandparse(testdir, "--cucumber-json-expanded")
    result.assert_outcomes(passed=3)

    assert jsonobject[0]["elements"][0]["steps"][0]["name"] == "type str and value hello"
    assert jsonobject[0]["elements"][1]["steps"][0]["name"] == "type int and value 42"
    assert jsonobject[0]["elements"][2]["steps"][0]["name"] == "type float and value 1.0"


def test_converters_dict_with_expand_option(testdir):
    """Test that `--cucumber-json-expanded` works correctly when using `example_converters`."""
    testdir.makefile(
        ".feature",
        test=textwrap.dedent(
            """
    Feature: Expanded option with example converters
        Scenario: Passing outline
            Given there is an intvalue <intvalue> and stringvalue <stringvalue> and floatvalue <floatvalue>

            Examples: example1
            | intvalue | stringvalue | floatvalue |
            | 1        | hello       | 1.0        |
    """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """
        import pytest
        from pytest_bdd import given, scenario

        @given('there is an intvalue <intvalue> and stringvalue <stringvalue> and floatvalue <floatvalue>')
        def type_type_and_value_value():
            pass

        @scenario(
            'test.feature',
            'Passing outline',
            example_converters={"intvalue":int, "stringvalue":str, "floatvalue":float},
        )
        def test_passing_outline():
            pass
    """
        )
    )
    result, jsonobject = runandparse(testdir, "--cucumber-json-expanded")
    assert result.ret == 0

    expanded_step_name = jsonobject[0]["elements"][0]["steps"][0]["name"]
    assert expanded_step_name == "there is an intvalue 1 and stringvalue hello and floatvalue 1.0"
