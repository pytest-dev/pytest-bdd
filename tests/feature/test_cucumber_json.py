"""Test cucumber json output."""
import json
import os.path
import textwrap


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

        @scenario('test.feature', 'Passing')
        def test_passing():
            pass

        @scenario('test.feature', 'Failing')
        def test_failing():
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
                            'name': '@scenario-passing-tag',
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
                            'name': '@scenario-failing-tag',
                            'line': 9,
                        }
                    ],
                    "type": "scenario"
                }
            ],
            "id": "test_step_trace0/test.feature",
            "keyword": "Feature",
            "line": 2,
            "name": "One passing scenario, one failing scenario",
            "tags": [
                {
                    'name': '@feature-tag',
                    'line': 1,
                }
            ],
            "uri": os.path.join(testdir.tmpdir.basename, 'test.feature'),
        }
    ]

    assert jsonobject == expected
