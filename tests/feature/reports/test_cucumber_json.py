"""Test cucumber json output."""

from __future__ import annotations

import json
import os.path
from typing import Any

from _pytest.pytester import Pytester, RunResult

from .cucumber_helper import OfType, create_test


def run_and_parse(pytester: Pytester, *args: Any) -> tuple[RunResult, list[dict[str, Any]]]:
    """Run tests in test-dir and parse json output."""
    result_path = pytester.path.joinpath("cucumber.json")
    result = pytester.runpytest(f"--cucumberjson={result_path}", "-s", *args)
    with result_path.open() as f:
        jsonobject = json.load(f)
    return result, jsonobject


def test_step_trace(pytester):
    """Test step trace."""
    create_test(pytester)
    result, jsonobject = run_and_parse(pytester)
    result.assert_outcomes(passed=4, failed=1)

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
                    "keyword": "Scenario Outline",
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
                    "id": "test_passing_outline[str-hello]",
                    "name": "Passing outline",
                },
                {
                    "description": "",
                    "keyword": "Scenario Outline",
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
                    "id": "test_passing_outline[int-42]",
                    "name": "Passing outline",
                },
                {
                    "description": "",
                    "keyword": "Scenario Outline",
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
                    "id": "test_passing_outline[float-1.0]",
                    "name": "Passing outline",
                },
            ],
            "id": os.path.join("test_step_trace0", "test.feature"),
            "keyword": "Feature",
            "line": 2,
            "name": "One passing scenario, one failing scenario",
            "tags": [{"name": "feature-tag", "line": 1}],
            "uri": os.path.join(pytester.path.name, "test.feature"),
        }
    ]

    assert jsonobject == expected
