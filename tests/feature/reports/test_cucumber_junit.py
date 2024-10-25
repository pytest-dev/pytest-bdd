"""Test cucumber junit output."""

from __future__ import annotations

import xml.dom.minidom
from typing import Any

from _pytest.pytester import Pytester, RunResult

from .cucumber_helper import create_test

FEATURE_NAME = "One passing scenario, one failing scenario"


def run_and_parse(pytester: Pytester, *args: Any) -> tuple[RunResult, xml.dom.minidom.Document]:
    """Run tests in test-dir and parse xml output."""
    result_path = pytester.path.joinpath("cucumber.xml")
    result = pytester.runpytest(f"--cucumberjunit={result_path}", "-s", *args)
    with result_path.open() as f:
        xmlobject = xml.dom.minidom.parseString(f.read())
    return result, xmlobject


def test_step_trace(pytester):
    """Test step trace."""
    create_test(pytester)
    result, xmlobject = run_and_parse(pytester)
    result.assert_outcomes(passed=4, failed=1, skipped=1)

    assert result.ret

    test_suite = xmlobject.firstChild
    assert test_suite.localName == "testsuite"

    test_suite_attributes = dict(test_suite.attributes.items())
    assert test_suite_attributes["name"] == "pytest-bdd.cucumber.junit"
    assert test_suite_attributes["tests"] == "4"
    assert test_suite_attributes["skipped"] == "1"
    assert test_suite_attributes["errors"] == "0"
    assert test_suite_attributes["failures"] == "1"
    assert isinstance(float(test_suite_attributes["time"]), float)

    test_cases = [test_case for test_case in test_suite.childNodes if isinstance(test_case, xml.dom.minidom.Element)]
    assert all(test_case.localName == "testcase" for test_case in test_cases)
    assert all(test_case.attributes["classname"].value == FEATURE_NAME for test_case in test_cases)
    assert all(isinstance(float(test_case.attributes["time"].value), float) for test_case in test_cases)

    assert test_cases[0].attributes["name"].value == "Passing"
    assert test_cases[1].attributes["name"].value == "Failing"
    assert test_cases[2].attributes["name"].value == "Passing outline - (str-hello)"
    assert test_cases[3].attributes["name"].value == "Passing outline - (int-42)"
    assert test_cases[4].attributes["name"].value == "Passing outline - (float-1.0)"

    [test_output] = [child for child in test_cases[0].childNodes if isinstance(child, xml.dom.minidom.Element)]
    assert test_output.nodeName == "system-out"
    assert test_output.firstChild.data == (
        "\n"
        "      Given a passing step...................................passed\n"
        "      And some other passing step............................passed\n"
        "\n"
    )

    test_outputs = [child for child in test_cases[1].childNodes if isinstance(child, xml.dom.minidom.Element)]
    assert test_outputs[0].nodeName == "failure"

    assert "Exception: Error" in test_outputs[0].firstChild.data
    assert "test_step_trace.py:14: Exception" in test_outputs[0].firstChild.data

    assert test_outputs[1].nodeName == "system-out"
    assert test_outputs[1].firstChild.data == (
        "\n"
        "      Given a passing step...................................passed\n"
        "      And a failing step.....................................failed\n"
        "\n"
    )
