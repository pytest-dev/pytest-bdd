"""pytest-bdd scripts."""
from __future__ import annotations

import argparse
import os.path
from itertools import chain, zip_longest
from pathlib import Path

from pytest_bdd.generation import generate_code
from pytest_bdd.parser import GherkinParser


def check_existense(file_name):
    """Check file or directory name for existence."""
    if not os.path.exists(file_name):
        raise argparse.ArgumentTypeError(f"{file_name} is an invalid file or directory name")
    return file_name


def print_generated_code(args):
    """Print generated test code for the given filenames."""
    features = GherkinParser().get_from_paths(None, list(map(Path, args.files)))

    feature_pickles = list(
        chain.from_iterable(map(lambda feature: zip_longest((), feature.pickles, fillvalue=feature), features))
    )

    feature_pickles_steps = list(
        chain.from_iterable(
            map(
                lambda feature_pickle: zip_longest((), feature_pickle[1].steps, fillvalue=feature_pickle),
                feature_pickles,
            )
        )
    )

    unique_step_defs_ids = {(step.type, step.text) for (feature, pickle), step in feature_pickles_steps}
    unique_feature_pickle_steps = sorted(
        list(
            map(
                lambda step_def_id: next(
                    filter(
                        lambda s: (s[1].type == step_def_id[0] and s[1].text == step_def_id[1]), feature_pickles_steps
                    )
                ),
                unique_step_defs_ids,
            )
        ),
        key=lambda feature_pickle_step: feature_pickle_step[1].text,
    )

    code = generate_code(features, feature_pickles, unique_feature_pickle_steps)
    print(code)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(prog="pytest-bdd")
    subparsers = parser.add_subparsers(help="sub-command help", dest="command")
    subparsers.required = True
    parser_generate = subparsers.add_parser("generate", help="generate help")
    parser_generate.add_argument(
        "files",
        metavar="FEATURE_FILE",
        type=check_existense,
        nargs="+",
        help="Feature files to generate test code with",
    )
    parser_generate.set_defaults(func=print_generated_code)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
