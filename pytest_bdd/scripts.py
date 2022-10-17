"""pytest-bdd scripts."""
from __future__ import annotations

import argparse
import os.path

from pytest_bdd.generation import generate_code, parse_feature_files


def check_existense(file_name):
    """Check file or directory name for existence."""
    if not os.path.exists(file_name):
        raise argparse.ArgumentTypeError(f"{file_name} is an invalid file or directory name")
    return file_name


def print_generated_code(args):
    """Print generated test code for the given filenames."""
    features, scenarios, steps = parse_feature_files(args.files)
    code = generate_code(features, scenarios, steps)
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
