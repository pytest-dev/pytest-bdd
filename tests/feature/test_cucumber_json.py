"""Test cucumber json output."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import RunResult, Testdir


def runandparse(testdir: Testdir, *args: Any) -> tuple[RunResult, list[dict[str, Any]]]:
    """Run tests in testdir and parse json output."""
    resultpath = testdir.tmpdir.join("cucumber.json")
    result = testdir.runpytest(f"--cucumberjson={resultpath}", "-s", *args)
    with resultpath.open() as f:
        jsonobject = json.load(f)
    return result, jsonobject


class OfType:
    """Helper object to help compare object type to initialization type"""

    def __init__(self, type: type = None) -> None:
        self.type = type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.type) if self.type else True


def test_step_trace(testdir):
    """Test step trace."""
    testdir.makefile(
        ".ini",
        pytest="""
        [pytest]
        markers =
            scenario-passing-tag
            scenario-failing-tag
            scenario-outline-passing-tag
            feature-tag
        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        test="""\
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
        """,
    )
    testdir.makeconftest(
        # language=python
        f"""\
        from pytest_bdd import given, parsers

        @given('a passing step')
        def a_passing_step():
            return 'pass'

        @given('some other passing step')
        def some_other_passing_step():
            return 'pass'

        @given('a failing step')
        def a_failing_step():
            raise Exception('Error')

        @given(parsers.parse('type {{type}} and value {{value}}'))
        def type_type_and_value_value():
            return 'pass'
        """
    )
    result, jsonobject = runandparse(testdir)
    result.assert_outcomes(passed=4, failed=1)

    assert result.ret
    expected = [
        {
            "description": "",
            "elements": [
                {
                    "description": "",
                    "id": "test_scenarios[file:test.feature-One passing scenario, one failing scenario-Passing]",
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
                    "id": "test_scenarios[file:test.feature-One passing scenario, one failing scenario-Failing]",
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
                            "name": "type str and value hello",
                        }
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": (
                        "test_scenarios["
                        "file:test.feature-One passing scenario, one failing scenario-"
                        "Passing outline[table_rows:[line: 20]]"
                        "]"
                    ),
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
                            "name": "type int and value 42",
                        }
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": (
                        "test_scenarios["
                        "file:test.feature-One passing scenario, one failing scenario-"
                        "Passing outline[table_rows:[line: 21]]"
                        "]"
                    ),
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
                            "name": "type float and value 1.0",
                        }
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": (
                        "test_scenarios["
                        "file:test.feature-One passing scenario, one failing scenario-"
                        "Passing outline[table_rows:[line: 22]]"
                        "]"
                    ),
                    "name": "Passing outline",
                },
            ],
            "id": "test.feature",
            "keyword": "Feature",
            "line": 2,
            "name": "One passing scenario, one failing scenario",
            "tags": [{"name": "feature-tag", "line": 1}],
            "uri": "test.feature",
        }
    ]

    assert jsonobject == expected
