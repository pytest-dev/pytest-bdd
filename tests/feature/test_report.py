"""Test scenario reporting."""

import textwrap
from typing import Optional

import pytest


class OfType:
    """Helper object comparison to which is always 'equal'."""

    def __init__(self, type: Optional[type] = None) -> None:
        self.type = type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.type) if self.type else True


def test_step_trace(pytester):
    """Test step trace."""
    pytester.makefile(
        ".ini",
        pytest=textwrap.dedent(
            """
    [pytest]
    markers =
        feature-tag
        scenario-passing-tag
        scenario-failing-tag
    """
        ),
    )
    feature = pytester.makefile(
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

        Scenario Outline: Outlined
            Given there are <start> cucumbers
            When I eat <eat> cucumbers
            Then I should have <left> cucumbers

            Examples:
            | start | eat | left |
            |  12   |  5  |  7   |
            |  5    |  4  |  1   |
    """
        ),
    )
    relpath = feature.relative_to(pytester.path.parent)
    pytester.makepyfile(
        textwrap.dedent(
            """
        import pytest
        from pytest_bdd import given, when, then, scenarios, parsers

        @given('a passing step')
        def _():
            return 'pass'

        @given('some other passing step')
        def _():
            return 'pass'

        @given('a failing step')
        def _():
            raise Exception('Error')

        @given(parsers.parse('there are {start:d} cucumbers'), target_fixture="cucumbers")
        def _(start):
            assert isinstance(start, int)
            return {"start": start}


        @when(parsers.parse('I eat {eat:g} cucumbers'))
        def _(cucumbers, eat):
            assert isinstance(eat, float)
            cucumbers['eat'] = eat


        @then(parsers.parse('I should have {left} cucumbers'))
        def _(cucumbers, left):
            assert isinstance(left, str)
            assert cucumbers['start'] - cucumbers['eat'] == int(left)


        scenarios('test.feature')
    """
        )
    )
    result = pytester.inline_run("-vvl")
    assert result.ret
    report = result.matchreport("test_passing", when="call").scenario
    expected = {
        "feature": {
            "description": "",
            "filename": str(feature),
            "line_number": 2,
            "name": "One passing scenario, one failing scenario",
            "rel_filename": str(relpath),
            "tags": ["feature-tag"],
        },
        "line_number": 5,
        "name": "Passing",
        "steps": [
            {
                "duration": OfType(float),
                "failed": False,
                "keyword": "Given",
                "line_number": 6,
                "name": "a passing step",
                "type": "given",
            },
            {
                "duration": OfType(float),
                "failed": False,
                "keyword": "And",
                "line_number": 7,
                "name": "some other passing step",
                "type": "given",
            },
        ],
        "tags": ["scenario-passing-tag"],
    }

    assert report == expected

    report = result.matchreport("test_failing", when="call").scenario
    expected = {
        "feature": {
            "description": "",
            "filename": str(feature),
            "line_number": 2,
            "name": "One passing scenario, one failing scenario",
            "rel_filename": str(relpath),
            "tags": ["feature-tag"],
        },
        "line_number": 10,
        "name": "Failing",
        "steps": [
            {
                "duration": OfType(float),
                "failed": False,
                "keyword": "Given",
                "line_number": 11,
                "name": "a passing step",
                "type": "given",
            },
            {
                "duration": OfType(float),
                "failed": True,
                "keyword": "And",
                "line_number": 12,
                "name": "a failing step",
                "type": "given",
            },
        ],
        "tags": ["scenario-failing-tag"],
    }
    assert report == expected

    report = result.matchreport("test_outlined[12-5-7]", when="call").scenario
    expected = {
        "feature": {
            "description": "",
            "filename": str(feature),
            "line_number": 2,
            "name": "One passing scenario, one failing scenario",
            "rel_filename": str(relpath),
            "tags": ["feature-tag"],
        },
        "line_number": 14,
        "name": "Outlined",
        "steps": [
            {
                "duration": OfType(float),
                "failed": False,
                "keyword": "Given",
                "line_number": 15,
                "name": "there are 12 cucumbers",
                "type": "given",
            },
            {
                "duration": OfType(float),
                "failed": False,
                "keyword": "When",
                "line_number": 16,
                "name": "I eat 5 cucumbers",
                "type": "when",
            },
            {
                "duration": OfType(float),
                "failed": False,
                "keyword": "Then",
                "line_number": 17,
                "name": "I should have 7 cucumbers",
                "type": "then",
            },
        ],
        "tags": [],
    }
    assert report == expected

    report = result.matchreport("test_outlined[5-4-1]", when="call").scenario
    expected = {
        "feature": {
            "description": "",
            "filename": str(feature),
            "line_number": 2,
            "name": "One passing scenario, one failing scenario",
            "rel_filename": str(relpath),
            "tags": ["feature-tag"],
        },
        "line_number": 14,
        "name": "Outlined",
        "steps": [
            {
                "duration": OfType(float),
                "failed": False,
                "keyword": "Given",
                "line_number": 15,
                "name": "there are 5 cucumbers",
                "type": "given",
            },
            {
                "duration": OfType(float),
                "failed": False,
                "keyword": "When",
                "line_number": 16,
                "name": "I eat 4 cucumbers",
                "type": "when",
            },
            {
                "duration": OfType(float),
                "failed": False,
                "keyword": "Then",
                "line_number": 17,
                "name": "I should have 1 cucumbers",
                "type": "then",
            },
        ],
        "tags": [],
    }
    assert report == expected


def test_complex_types(pytester, pytestconfig):
    """Test serialization of the complex types."""
    if not pytestconfig.pluginmanager.has_plugin("xdist"):
        pytest.skip("Execnet not installed")

    import execnet.gateway_base

    pytester.makefile(
        ".feature",
        test=textwrap.dedent(
            """
    Feature: Report serialization containing parameters of complex types

    Scenario Outline: Complex
        Given there is a coordinate <point>

        Examples:
        |  point  |
        |  10,20  |
    """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """
        import pytest
        from pytest_bdd import given, when, then, scenario, parsers

        class Point:

            def __init__(self, x, y):
                self.x = x
                self.y = y

            @classmethod
            def parse(cls, value):
                return cls(*(int(x) for x in value.split(',')))

        class Alien(object):
            pass

        @given(
            parsers.parse('there is a coordinate {point}'),
            target_fixture="point",
            converters={"point": Point.parse},
        )
        def given_there_is_a_point(point):
            assert isinstance(point, Point)
            return point


        @pytest.mark.parametrize('alien', [Alien()])
        @scenario('test.feature', 'Complex')
        def test_complex(alien):
            pass

    """
        )
    )
    result = pytester.inline_run("-vvl")
    report = result.matchreport("test_complex[10,20-alien0]", when="call")
    assert report.passed
    assert execnet.gateway_base.dumps(report.item)
    assert execnet.gateway_base.dumps(report.scenario)
