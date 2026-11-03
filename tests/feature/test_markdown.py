"""Test Markdown with Gherkin (MDG) feature files."""

from __future__ import annotations

import textwrap
from importlib.metadata import version

import pytest
from packaging.version import parse as parse_version

MARKDOWN_SUPPORTED = parse_version(version("gherkin-official")) >= parse_version("32.2.0")

requires_markdown = pytest.mark.skipif(
    not MARKDOWN_SUPPORTED, reason="Markdown with Gherkin requires gherkin-official>=32.2.0"
)

STEPS = """\
import json

from pytest_bdd import given, parsers, then


@given("I have a bar", target_fixture="bar")
def _():
    return "bar"


@given("the payload", target_fixture="payload")
def _(docstring):
    return json.loads(docstring)


@given("the cheeses", target_fixture="cheeses")
def _(datatable):
    return [row[0] for row in datatable[1:]]


@given(parsers.parse("I have {count:d} cucumbers"), target_fixture="count")
def _(count):
    return count


@then("I have a bar")
def _(bar):
    assert bar == "bar"


@then(parsers.parse('the payload name is "{name}"'))
def _(payload, name):
    assert payload["name"] == name


@then("I have gouda and edam")
def _(cheeses):
    assert cheeses == ["gouda", "edam"]


@then(parsers.parse("I have {count:d} cucumbers left"))
def _(count):
    assert count > 0
"""

MARKDOWN_FEATURE = """\
`@bdd`
# Feature: Markdown with Gherkin

This prose documents the behaviour and is not part of any scenario.

| term | meaning          |
| ---- | ---------------- |
| bar  | something to own |

```mermaid
flowchart LR
  given --> then
```

## Background:

* Given I have a bar

`@slow`
## Scenario: Tagged scenario

Prose between the heading and the first step.

* Then I have a bar

## Scenario: Doc string argument

* Given the payload
  ```json
  {"name": "cucumber"}
  ```
* Then the payload name is "cucumber"

## Scenario: Data table argument

* Given the cheeses
  | name  |
  | gouda |
  | edam  |
* Then I have gouda and edam

## Scenario Outline: Examples table

* Given I have <count> cucumbers
* Then I have <count> cucumbers left

### Examples:

  | count |
  | ----- |
  | 1     |
  | 2     |
"""


@requires_markdown
def test_scenarios_collect_markdown_feature_files(pytester):
    """`scenarios()` collects `.feature.md` files beside `.feature` files and ignores other Markdown."""
    pytester.makeconftest(STEPS)
    features = pytester.mkdir("features")
    features.joinpath("plain.feature").write_text(
        textwrap.dedent(
            """\
            Feature: Plain Gherkin
                Scenario: Plain scenario
                    Given I have a bar
                    Then I have a bar
            """
        ),
        "utf-8",
    )
    features.joinpath("markdown.feature.md").write_text(MARKDOWN_FEATURE, "utf-8")
    features.joinpath("README.md").write_text(
        "# Feature: Not a feature file\n\n## Scenario: Must not be collected\n\n* Given I have a bar\n",
        "utf-8",
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios

        scenarios("features")
        """
    )

    result = pytester.runpytest("-v")

    result.assert_outcomes(passed=6)
    result.stdout.no_fnmatch_line("*must_not_be_collected*")


@requires_markdown
def test_markdown_tags_become_markers(pytester):
    """Inline code tags above a heading are applied to the scenario as markers."""
    pytester.makeini(
        """
        [pytest]
        markers =
            bdd
            slow
        """
    )
    pytester.makeconftest(STEPS)
    pytester.path.joinpath("markdown.feature.md").write_text(MARKDOWN_FEATURE, "utf-8")
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios

        scenarios("markdown.feature.md")
        """
    )

    result = pytester.runpytest("-v", "-m", "slow")

    result.assert_outcomes(passed=1, deselected=4)
    result.stdout.fnmatch_lines(["*test_tagged_scenario PASSED*"])


@requires_markdown
def test_scenario_decorator_binds_markdown_scenario(pytester):
    """`@scenario` binds a scenario from a `.feature.md` file by name."""
    pytester.makeconftest(STEPS)
    pytester.path.joinpath("markdown.feature.md").write_text(MARKDOWN_FEATURE, "utf-8")
    pytester.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("markdown.feature.md", "Doc string argument")
        def test_doc_string():
            pass
        """
    )

    result = pytester.runpytest()

    result.assert_outcomes(passed=1)


@requires_markdown
def test_markdown_parse_error_reports_line(pytester):
    """A Markdown with Gherkin syntax error reports the offending line."""
    pytester.path.joinpath("broken.feature.md").write_text(
        "# Feature: Broken\n\n`@orphan`\n* Given I have a bar\n",
        "utf-8",
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios

        scenarios("broken.feature.md")
        """
    )

    result = pytester.runpytest()

    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*Line number: 4*", "*Line: * Given I have a bar*"])


@pytest.mark.skipif(MARKDOWN_SUPPORTED, reason="gherkin-official supports Markdown with Gherkin")
def test_markdown_requires_recent_gherkin(pytester):
    """Older gherkin-official releases are rejected with an actionable error."""
    pytester.path.joinpath("markdown.feature.md").write_text(MARKDOWN_FEATURE, "utf-8")
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios

        scenarios("markdown.feature.md")
        """
    )

    result = pytester.runpytest()

    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*Markdown with Gherkin requires gherkin-official>=32.2.0*"])
