"""Test cucumber json output."""
import json
import os.path
import textwrap

import pytest


def runandparse(testdir, *args):
    """Run tests in testdir and parse json output."""
    resultpath = testdir.tmpdir.join("cucumber.json")
    result = testdir.runpytest('--cucumberjson={0}'.format(resultpath), '-s', *args)
    jsonobject = json.load(resultpath.open())
    return result, jsonobject


@pytest.fixture(scope='session')
def equals_any():
    """Helper object comparison to which is always 'equal'."""
    class equals_any(object):

        def __eq__(self, other):
            return True

        def __cmp__(self, other):
            return 0

    return equals_any()


def test_step_trace(testdir, equals_any):
    """Test step trace."""
    testdir.makefile('.feature', test=textwrap.dedent("""
    Feature: One passing scenario, one failing scenario

    Scenario: Passing
        Given a passing step
        And some other passing step

    Scenario: Failing
        Given a failing step
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
    assert jsonobject == [
        {
            "description": "",
            "elements": [
                {
                    "description": "",
                    "id": "test_passing",
                    "keyword": "Scenario",
                    "line": 3,
                    "name": "Passing",
                    "steps": [
                        {
                            "keyword": "Given",
                            "line": 4,
                            "match": {
                                "location": ""
                            },
                            "name": "a passing step",
                            "result": {
                                "status": "passed"
                            }
                        },
                        {
                            "keyword": "And",
                            "line": 5,
                            "match": {
                                "location": ""
                            },
                            "name": "some other passing step",
                            "result": {
                                "status": "passed"
                            }
                        }

                    ],
                    "tags": [],
                    "type": "scenario"
                },
                {
                    "description": "",
                    "id": "test_failing",
                    "keyword": "Scenario",
                    "line": 7,
                    "name": "Failing",
                    "steps": [
                        {
                            "keyword": "Given",
                            "line": 8,
                            "match": {
                                "location": ""
                            },
                            "name": "a failing step",
                            "result": {
                                "error_message": equals_any,
                                "status": "failed"
                            }
                        }
                    ],
                    "tags": [],
                    "type": "scenario"
                }
            ],
            "id": "test_step_trace0/test.feature",
            "keyword": "Feature",
            "line": 1,
            "name": "One passing scenario, one failing scenario",
            "tags": [],
            "uri": os.path.join(testdir.tmpdir.basename, 'test.feature'),
        }
    ]
