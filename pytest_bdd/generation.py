"""pytest-bdd missing test code generation."""
from __future__ import annotations

import itertools
import os.path
from functools import reduce
from operator import lt, methodcaller
from pathlib import Path
from typing import Any, cast

import py
from mako.lookup import TemplateLookup
from pytest import ExitCode

from pytest_bdd.const import STEP_TYPES_BY_NORMALIZED_PREFIX
from pytest_bdd.model import Feature, Scenario, Step
from pytest_bdd.packaging import compare_distribution_version
from pytest_bdd.parser import GherkinParser
from pytest_bdd.steps import StepHandler
from pytest_bdd.typing.pytest import Config, FixtureRequest, Item, Parser, Session, wrap_session
from pytest_bdd.utils import make_python_name

template_lookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__), "templates")])


def add_options(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Generation")

    group._addoption(
        "--generate-missing",
        action="store_true",
        dest="generate_missing",
        default=False,
        help="Generate missing bdd test code for given feature files and exit.",
    )

    group._addoption(
        "--feature",
        metavar="FILE_OR_DIR",
        action="append",
        dest="features",
        help="Feature file or directory to generate missing code for. Multiple allowed.",
    )


def cmdline_main(config: Config) -> int | None:
    """Check config option to show missing code."""
    if config.option.generate_missing:
        return show_missing_code(config)
    return None  # Make mypy happy


def generate_code(features: list[Feature], scenarios: list[Scenario], steps: list[Step]) -> str:
    """Generate test code for the given filenames."""
    grouped_steps = group_steps(steps)
    template = template_lookup.get_template("test.py.mak")
    code = template.render(
        features=features,
        scenarios=scenarios,
        steps=grouped_steps,
        make_python_name=make_python_name,
        make_python_docstring=make_python_docstring,
        make_string_literal=make_string_literal,
    )
    return cast(str, code)


def show_missing_code(config: Config) -> int | ExitCode:
    """Wrap pytest session to show missing code."""

    return wrap_session(config, _show_missing_code_main)


def print_missing_code(scenarios: list[Scenario], steps: list[Step]) -> None:
    """Print missing code with TerminalWriter."""
    tw = py.io.TerminalWriter()
    scenario = step = None

    for scenario in scenarios:
        tw.line()
        tw.line(
            f'Scenario "{scenario.name}" is not bound to any test in the feature "{scenario.feature.name}"'
            f" in the file {scenario.feature.filename}:{scenario.line_number}",
            red=True,
        )

    if scenario:
        tw.sep("-", red=True)

    for step in steps:
        tw.line()
        tw.line(
            f"""StepHandler {step.keyword} "{step.name}" is not defined in the scenario "{step.scenario.name}" in the feature"""
            f""" "{step.scenario.feature.name}" in the file"""
            f""" {step.scenario.feature.filename}:{step.line_number}""",
            red=True,
        )

    if step:
        tw.sep("-", red=True)

    tw.line("Please place the code above to the test file(s):")
    tw.line()

    features: list[Feature] = sorted(
        reduce(
            lambda list_, item: cast(list, list_) + [item] if item not in list_ else list_,
            [scenario.feature for scenario in scenarios],
            [],
        ),
        key=lambda feature: feature.uri,  # type: ignore[no-any-return]  # https://github.com/python/typing/issues/760
    )
    code = generate_code(features, scenarios, steps)
    tw.write(code)


def parse_feature_files(paths: list[str], **kwargs: Any) -> tuple[list[Feature], list[Scenario], list[Step]]:
    """Parse feature files of given paths.

    :param paths: `list` of paths (file or dirs)

    :return: `list` of `tuple` in form:
             (`list` of `Feature` objects, `list` of `Scenario` objects, `list` of `StepHandler` objects).
    """
    features = GherkinParser().get_from_paths(list(map(Path, paths)), **kwargs)
    _, scenarios = zip(
        *sorted(
            itertools.chain.from_iterable(
                itertools.zip_longest([], feature.scenarios, fillvalue=feature) for feature in features
            ),
            key=lambda item: (item[0].uri, item[1].id, item[1].name),
        )
    )

    seen = set()
    steps: list[Step] = sorted(
        (
            seen.add(step.name) or step  # type: ignore[func-returns-value]
            for step in itertools.chain.from_iterable(scenario.steps for scenario in scenarios)
            if step.name not in seen
        ),
        key=lambda step: step.name,  # type: ignore[no-any-return]  # https://github.com/python/typing/issues/760
    )
    return features, scenarios, steps


def group_steps(steps: list[Step]) -> list[Step]:
    """Group steps by type."""
    steps = sorted(steps, key=lambda step: STEP_TYPES_BY_NORMALIZED_PREFIX[step.prefix])
    seen_steps = set()
    grouped_steps: list[Step] = []
    for step in itertools.chain.from_iterable(
        sorted(group, key=lambda step: step.name)  # type: ignore[no-any-return]  # https://github.com/python/typing/issues/760
        for _, group in itertools.groupby(
            steps, lambda step: sorted(steps, key=lambda step: STEP_TYPES_BY_NORMALIZED_PREFIX[step.prefix])
        )
    ):
        if step.name not in seen_steps:
            grouped_steps.append(step)
            seen_steps.add(step.name)
    grouped_steps.sort(key=lambda step: step.prefix)  # type: ignore[no-any-return]  # https://github.com/python/typing/issues/760
    return grouped_steps


def _show_missing_code_main(config: Config, session: Session) -> None:
    """Preparing fixture duplicates for output."""
    tw = py.io.TerminalWriter()
    config.hook.pytest_collection(session=session)

    if config.option.features is None:
        tw.line("The --feature parameter is required.", red=True)
        session.exitstatus = 100
        return

    features, scenarios, steps = parse_feature_files(config.option.features)
    scenarios = list(scenarios)

    for item in session.items:

        is_legacy_pytest = compare_distribution_version("pytest", "7.0", lt)

        method_name = "prepare" if is_legacy_pytest else "setup"
        methodcaller(method_name, item)(item.session._setupstate)

        item = cast(Item, item)
        item_request: FixtureRequest = item._request
        scenario: Scenario = item_request.getfixturevalue("scenario")
        feature: Feature = scenario.feature

        for i, s in enumerate(scenarios):
            if s.id == scenario.id and s.uri == scenario.uri:
                scenarios.remove(s)
                break

        previous_step = None
        for step in scenario.steps:
            try:
                item_request.config.hook.pytest_bdd_match_step_definition_to_step(
                    request=item_request, feature=feature, scenario=scenario, step=step, previous_step=previous_step
                )
            except StepHandler.Matcher.MatchNotFoundError:
                pass
            else:
                steps = [non_found_steps for non_found_steps in steps if non_found_steps.name != step.name]
            finally:
                previous_step = step

        item.session._setupstate.teardown_exact(*((item,) if is_legacy_pytest else ()), None)  # type: ignore[call-arg]

    grouped_steps = group_steps(steps)
    print_missing_code(scenarios, grouped_steps)

    if scenarios or steps:
        session.exitstatus = 100


def make_python_docstring(string: str) -> str:
    """Make a python docstring literal out of a given string."""
    return '"""{}."""'.format(string.replace('"""', '\\"\\"\\"'))


def make_string_literal(string: str) -> str:
    """Make python string literal out of a given string."""
    return "'{}'".format(string.replace("'", "\\'"))
