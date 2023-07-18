"""pytest-bdd missing test code generation."""
import argparse
import os.path
from itertools import chain, filterfalse, zip_longest
from operator import lt, methodcaller
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple, Union, cast

import py
from mako.template import Template

from messages import Pickle, PickleStep  # type:ignore[attr-defined]
from pytest_bdd.compatibility.importlib.resources import as_file, files
from pytest_bdd.compatibility.pytest import Config, ExitCode, FixtureRequest, Item, Parser, Session, wrap_session
from pytest_bdd.model import Feature, StepType
from pytest_bdd.packaging import compare_distribution_version
from pytest_bdd.parser import GherkinParser
from pytest_bdd.steps import StepHandler
from pytest_bdd.utils import make_python_name

STEP_TYPE_TO_STEP_PREFIX = {
    StepType.unknown: "*",
    StepType.outcome: "Then",
    StepType.context: "Given",
    StepType.action: "When",
}


STEP_TYPE_TO_STEP_METHOD_NAME = {
    StepType.unknown: "step",
    StepType.outcome: "then",
    StepType.context: "given",
    StepType.action: "when",
}


def check_existense(file_name):
    """Check file or directory name for existence."""
    if not os.path.exists(file_name):
        raise argparse.ArgumentTypeError(f"{file_name} is an invalid file or directory name")
    return Path(file_name)


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
        "--generate",
        action="store_true",
        dest="generate",
        default=False,
        help="Generate bdd test code for given feature files and exit.",
    )

    group._addoption(
        "--feature",
        metavar="FILE_OR_DIR",
        action="append",
        type=check_existense,
        dest="features",
        help="Feature file or directory to generate code for. Multiple allowed.",
    )


def cmdline_main(config: Config) -> Optional[int]:
    """Check config option to show missing code."""
    if config.option.generate_missing:
        return generate_and_print_missing_code(config)
    elif config.option.generate:
        return generate_and_print_code(config)
    else:
        return None  # Make mypy happy


def generate_code(
    features: Sequence[Feature],
    feature_pickles: Sequence[Tuple[Feature, Pickle]],
    feature_pickle_steps: Sequence[Tuple[Tuple[Feature, Pickle], PickleStep]],
) -> str:
    """Generate test code for the given filenames."""
    with as_file(files("pytest_bdd.template").joinpath("test.py.mak")) as path:
        template = Template(filename=str(path))
    code = template.render(
        features=features,
        feature_pickles=feature_pickles,
        feature_pickle_steps=feature_pickle_steps,
        make_python_name=make_python_name,
        make_python_docstring=make_python_docstring,
        make_string_literal=make_string_literal,
        step_type_to_method_name=STEP_TYPE_TO_STEP_METHOD_NAME,
    )
    return cast(str, code)


def generate_and_print_missing_code(config: Config) -> Union[int, ExitCode]:
    """Wrap pytest session to show missing code."""

    def _(config: Config, session: Session) -> None:
        """Preparing fixture duplicates for output."""
        tw = py.io.TerminalWriter()
        config.hook.pytest_collection(session=session)

        if config.option.features is None:
            tw.line("The --feature parameter is required.", red=True)
            session.exitstatus = 100
            return

        seen_feature_pickles_ids = set()
        non_matched_feature_pickle_steps = []

        for item in session.items:
            is_legacy_pytest = compare_distribution_version("pytest", "7.0", lt)

            method_name = "prepare" if is_legacy_pytest else "setup"
            methodcaller(method_name, item)(item.session._setupstate)

            item = cast(Item, item)
            item_request: FixtureRequest = item._request
            pickle: Pickle = item_request.getfixturevalue("scenario")
            feature: Feature = item_request.getfixturevalue("feature")

            seen_feature_pickles_ids.add((feature.uri, pickle.name))

            previous_step = None
            for step in pickle.steps:
                try:
                    item_request.config.hook.pytest_bdd_match_step_definition_to_step(
                        request=item_request, feature=feature, scenario=pickle, step=step, previous_step=previous_step
                    )
                except StepHandler.Matcher.MatchNotFoundError:
                    non_matched_feature_pickle_steps.append(((feature, pickle), step))
                finally:
                    previous_step = step

            item.session._setupstate.teardown_exact(  # type: ignore[call-arg]
                *((item,) if is_legacy_pytest else ()), None
            )

        features = GherkinParser().get_from_paths(config, list(map(Path, config.option.features)))

        seen_features_uris = set()
        for feature_uri, pickle_name in seen_feature_pickles_ids:
            if feature_uri not in seen_features_uris:
                seen_features_uris.add(feature_uri)

        non_seen_features = list(filterfalse(lambda feature: feature.uri in seen_features_uris, features))

        non_seen_feature_pickles = list(
            filter(
                lambda feature_pickle: (feature_pickle[0].uri, feature_pickle[1].name) not in seen_feature_pickles_ids,
                chain.from_iterable(map(lambda feature: zip_longest((), feature.pickles, fillvalue=feature), features)),
            )
        )

        unique_step_defs_ids = {(step.type, step.text) for _, step in non_matched_feature_pickle_steps}
        unique_non_matched_feature_pickle_steps = list(
            map(
                lambda step_def_id: next(
                    filter(
                        lambda feature_pickle_step: (
                            feature_pickle_step[1].type == step_def_id[0]
                            and feature_pickle_step[1].text == step_def_id[1]
                        ),
                        non_matched_feature_pickle_steps,
                    )
                ),
                unique_step_defs_ids,
            )
        )

        print_missing_code(
            non_seen_features,
            non_seen_feature_pickles,  # type: ignore[arg-type]
            non_matched_feature_pickle_steps,
            unique_non_matched_feature_pickle_steps,
        )

        if non_seen_feature_pickles or non_matched_feature_pickle_steps:
            session.exitstatus = 100

    return wrap_session(config=config, doit=_)


def generate_and_print_code(config: Config) -> Union[int, ExitCode]:
    """Wrap pytest session to show missing code."""

    def _(config: Config, session: Session) -> None:
        """Preparing fixture duplicates for output."""
        tw = py.io.TerminalWriter()

        if config.option.features is None:
            tw.line("The --feature parameter is required.", red=True)
            session.exitstatus = 100
            return

        features = GherkinParser().get_from_paths(config, list(map(Path, config.option.features)))

        feature_pickles: Sequence[Tuple[Feature, Pickle]] = list(
            chain.from_iterable(
                map(
                    lambda feature: cast(
                        Iterable[Tuple[Feature, Pickle]], zip_longest((), feature.pickles, fillvalue=feature)
                    ),
                    features,
                )
            )
        )

        feature_pickles_steps: Sequence[Tuple[Tuple[Feature, Pickle], PickleStep]] = list(
            chain.from_iterable(
                map(
                    lambda feature_pickle: cast(
                        Iterable[Tuple[Tuple[Feature, Pickle], PickleStep]],
                        zip_longest((), feature_pickle[1].steps, fillvalue=feature_pickle),
                    ),
                    feature_pickles,
                )
            )
        )

        unique_step_defs_ids = {(step.type, step.text) for (feature, pickle), step in feature_pickles_steps}
        unique_feature_pickle_steps = sorted(
            list(
                map(
                    lambda step_def_id: next(  # type: ignore[no-any-return]
                        filter(
                            lambda s: (s[1].type == step_def_id[0] and s[1].text == step_def_id[1]),
                            feature_pickles_steps,
                        )
                    ),
                    unique_step_defs_ids,
                )
            ),
            key=lambda feature_pickle_step: cast(str, feature_pickle_step[1].text),
        )

        code = generate_code(features, feature_pickles, unique_feature_pickle_steps)
        tw.write(code)

    verbosity = config.option.verbose
    try:
        config.option.verbose = -2
        exit_code = wrap_session(config=config, doit=_)
    finally:
        config.option.verbose = verbosity

    return exit_code


def print_missing_code(
    features,
    feature_pickles: Sequence[Tuple[Feature, Pickle]],
    feature_pickle_steps: Sequence[Tuple[Tuple[Feature, Pickle], PickleStep]],
    unique_steps,
) -> None:
    """Print missing code with TerminalWriter."""
    tw = py.io.TerminalWriter()
    scenario = step = None

    for feature, pickle in feature_pickles:
        tw.line()
        tw.line(
            f'Scenario "{pickle.name}" is not bound to any test in the feature "{feature.name}"'
            f" in the file {feature.filename}:{feature._get_pickle_line_number(pickle)}",
            red=True,
        )

    if scenario:
        tw.sep("-", red=True)

    for (feature, pickle), step in feature_pickle_steps:
        tw.line()
        step_type = STEP_TYPE_TO_STEP_PREFIX[step.type if step.type is not None else StepType.unknown]
        tw.line(
            f"""StepHandler {step_type} "{step.text}" is not defined in the scenario "{pickle.name}" in the feature"""
            f""" "{feature.name}" in the file"""
            f""" {feature.filename}:{feature._get_step_line_number(step)}""",
            red=True,
        )

    if step:
        tw.sep("-", red=True)

    tw.line("Please place the code above to the test file(s):")
    tw.line()

    code = generate_code(features, feature_pickles, unique_steps)
    tw.write(code)


def make_python_docstring(string: str) -> str:
    """Make a python docstring literal out of a given string."""
    return '"""{}."""'.format(string.replace('"""', '\\"\\"\\"'))


def make_string_literal(string: str) -> str:
    """Make python string literal out of a given string."""
    return "'{}'".format(string.replace("'", "\\'"))
