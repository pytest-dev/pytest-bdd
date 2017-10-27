"""Test cucumber json output."""
import json
import os.path
import textwrap

import pytest

from pytest_bdd.cucumber_json import StepNames


def runandparse(testdir, *args):
    """Run tests in testdir and parse json output."""
    resultpath = testdir.tmpdir.join("cucumber.json")
    result = testdir.runpytest('--cucumberjson={0}'.format(resultpath), '-s', *args)
    jsonobject = json.load(resultpath.open())
    return result, jsonobject


class equals_any(object):

    """Helper object comparison to which is always 'equal'."""

    def __init__(self, type=None):
        self.type = type

    def __eq__(self, other):
        return isinstance(other, self.type) if self.type else True

    def __cmp__(self, other):
        return 0 if (isinstance(other, self.type) if self.type else False) else -1


string = type(u'')


def test_step_trace(testdir):
    """Test step trace."""
    testdir.makefile('.feature', test=textwrap.dedent("""
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
    """))
    testdir.makepyfile(textwrap.dedent("""
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
    """))
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
                            "match": {
                                "location": ""
                            },
                            "name": "a passing step",
                            "result": {
                                "status": "passed",
                                "duration": equals_any(int)
                            }
                        },
                        {
                            "keyword": "And",
                            "line": 7,
                            "match": {
                                "location": ""
                            },
                            "name": "some other passing step",
                            "result": {
                                "status": "passed",
                                "duration": equals_any(int)
                            }
                        }

                    ],
                    "tags": [
                        {
                            'name': 'scenario-passing-tag',
                            'line': 4,
                        }
                    ],
                    "type": "scenario"
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
                            "match": {
                                "location": ""
                            },
                            "name": "a passing step",
                            "result": {
                                "status": "passed",
                                "duration": equals_any(int)
                            }
                        },
                        {
                            "keyword": "And",
                            "line": 12,
                            "match": {
                                "location": ""
                            },
                            "name": "a failing step",
                            "result": {
                                "error_message": equals_any(string),
                                "status": "failed",
                                "duration": equals_any(int)
                            }
                        }
                    ],
                    "tags": [
                        {
                            'name': 'scenario-failing-tag',
                            'line': 9,
                        }
                    ],
                    "type": "scenario"
                },
                {
                    "description": "",
                    "keyword": "Scenario",
                    "tags": [
                        {
                            "line": 14,
                            "name": "scenario-outline-passing-tag"
                        }
                    ],
                    "steps": [
                        {
                            "line": 16,
                            "match": {"location": ""},
                            "result": {
                                "status": "passed",
                                "duration": equals_any(int)
                            },
                            "keyword": "Given",
                            "name": "type str and value hello"
                        }
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": "test_passing_outline[str-hello]",
                    "name": "Passing outline"
                },
                {
                    "description": "",
                    "keyword": "Scenario",
                    "tags": [
                        {
                            "line": 14,
                            "name": "scenario-outline-passing-tag"
                        }
                    ],
                    "steps": [
                        {
                            "line": 16,
                            "match": {"location": ""},
                            "result": {
                                "status": "passed",
                                "duration": equals_any(int)
                            },
                            "keyword": "Given",
                            "name": "type int and value 42"
                        }
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": "test_passing_outline[int-42]",
                    "name": "Passing outline"
                },
                {
                    "description": "",
                    "keyword": "Scenario",
                    "tags": [
                        {
                            "line": 14,
                            "name": "scenario-outline-passing-tag"
                        }
                    ],
                    "steps": [
                        {
                            "line": 16,
                            "match": {"location": ""},
                            "result": {
                                "status": "passed",
                                "duration": equals_any(int)
                            },
                            "keyword": "Given",
                            "name": "type float and value 1.0"
                        }
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": "test_passing_outline[float-1.0]",
                    "name": "Passing outline"
                }
            ],
            "id": os.path.join("test_step_trace0", "test.feature"),
            "keyword": "Feature",
            "line": 2,
            "name": "One passing scenario, one failing scenario",
            "tags": [
                {
                    'name': 'feature-tag',
                    'line': 1,
                }
            ],
            "uri": os.path.join(testdir.tmpdir.basename, 'test.feature'),
        }
    ]

    assert jsonobject == expected


def test_format_step_name_none():
    sn = StepNames()
    stepname = "A step name without any replacements"
    step = {"name": stepname}
    assert sn.format_step_name(step, [], []) == stepname


def test_format_step_name_multiple():
    sn = StepNames()
    step = {"name": "A step <name> with <multiple> replacements"}
    params = ["name", "multiple"]
    example = ["NAME", "MULTIPLE"]
    assert sn.format_step_name(step, params, example) == "A step NAME with MULTIPLE replacements"


def test_generator_only_once_when_no_examples():
    sn = StepNames()
    steps = [{"name": "step 1"}, {"name": "step 2"}]
    scenario = {"name": "Simple name", "examples": [], "steps": steps}
    sn.name_generator(scenario)  # once should be ok
    with pytest.raises(StopIteration):
        sn.name_generator(scenario)  # there should be no second


def test_all_steps_all_examples():
    sn = StepNames()
    steps = [{"name": "Step <one>"}, {"name": "Step <two>"}]
    rows = [["one", "two"], [["ONE", "TWO"], ["[one]", "[two]"]]]
    scenario = {"name": "One replacement", "examples": [{"rows": rows}], "steps": steps}
    names = sn.name_generator(scenario)
    assert next(names) == "Step ONE"
    assert next(names) == "Step TWO"
    with pytest.raises(StopIteration):
        next(names)

    names = sn.name_generator(scenario)
    assert next(names) == "Step [one]"
    assert next(names) == "Step [two]"
    with pytest.raises(StopIteration):
        next(names)
