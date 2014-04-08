"""Test cucumber json output."""
import json
import textwrap


def runandparse(testdir, *args):
    """Run tests in testdir and parse json output."""
    resultpath = testdir.tmpdir.join("cucumber.json")
    result = testdir.runpytest('--cucumberjson={0}'.format(resultpath), *args)
    jsonobject = json.loads(result)
    return result, jsonobject


def test_step_trace(testdir):
    """Test step trace."""
    testdir.makefile('.feature', test=textwrap.dedent("""
    Feature: One passing scenario, one failing scenario

    Scenario: Passing
        Given a passing step

    Scenario: Failing
        Given a failing step
    """))
    testdir.makepyfile(textwrap.dedent("""
        import pytest
        from pytest_bdd import given, when, scenario

        @given('a passing step')
        def a_passing_step():
            return 'pass'

        @given('a failing step')
        def a_passing_step():
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
                    "id": "one-passing-scenario,-one-failing-scenario;passing",
                    "keyword": "Scenario",
                    "line": 5,
                    "name": "Passing",
                    "steps": [
                        {
                            "keyword": "Given ",
                            "line": 6,
                            "match": {
                                "location": "features/step_definitions/steps.rb:1"
                            },
                            "name": "a passing step",
                            "result": {
                                "status": "passed"
                            }
                        }
                    ],
                    "tags": [
                        {
                            "line": 4,
                            "name": "@b"
                        }
                    ],
                    "type": "scenario"
                },
                {
                    "description": "",
                    "id": "one-passing-scenario,-one-failing-scenario;failing",
                    "keyword": "Scenario",
                    "line": 9,
                    "name": "Failing",
                    "steps": [
                        {
                            "keyword": "Given ",
                            "line": 10,
                            "match": {
                                "location": "features/step_definitions/steps.rb:5"
                            },
                            "name": "a failing step",
                            "result": {
                                "error_message": " (RuntimeError)\n./features/step_definitions/steps.rb:6:in /a "
                                "failing step/'\nfeatures/one_passing_one_failing.feature:10:in Given a failing step'",
                                "status": "failed"
                            }
                        }
                    ],
                    "tags": [
                        {
                            "line": 8,
                            "name": "@c"
                        }
                    ],
                    "type": "scenario"
                }
            ],
            "id": "one-passing-scenario,-one-failing-scenario",
            "keyword": "Feature",
            "line": 2,
            "name": "One passing scenario, one failing scenario",
            "tags": [
                {
                    "line": 1,
                    "name": "@a"
                }
            ],
            "uri": "features/one_passing_one_failing.feature"
        }
    ]
