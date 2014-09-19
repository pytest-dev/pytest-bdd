"""pytest-bdd scripts."""
import argparse
import itertools
import os.path
import re

import glob2
from mako.lookup import TemplateLookup

import pytest_bdd
from pytest_bdd.feature import Feature

template_lookup = TemplateLookup(directories=[os.path.join(os.path.dirname(pytest_bdd.__file__), 'templates')])

MIGRATE_REGEX = re.compile(r'\s?(\w+)\s\=\sscenario\((.+)\)', flags=re.MULTILINE)

PYTHON_REPLACE_REGEX = re.compile('\W')

ALPHA_REGEX = re.compile('^\d+_*')


def make_python_name(string):
    """Make python attribute name out of a given string."""
    string = re.sub(PYTHON_REPLACE_REGEX, '', string.replace(' ', '_'))
    return re.sub(ALPHA_REGEX, '', string)


def migrate_tests(args):
    """Migrate outdated tests to the most recent form."""
    path = args.path
    for file_path in glob2.iglob(os.path.join(os.path.abspath(path), '**', '*.py')):
        migrate_tests_in_file(file_path)


def migrate_tests_in_file(file_path):
    """Migrate all bdd-based tests in the given test file."""
    try:
        with open(file_path, 'r+') as fd:
            content = fd.read()
            new_content = MIGRATE_REGEX.sub(r'\n\n@scenario(\2)\ndef \1():\n    pass\n', content)
            if new_content != content:
                fd.seek(0)
                fd.write(new_content)
                print('migrated: {0}'.format(file_path))
            else:
                print('skipped: {0}'.format(file_path))
    except IOError:
        pass


def check_existense(file_name):
    """Check filename for existense."""
    if not os.path.isfile(file_name):
        raise argparse.ArgumentTypeError('{0} is an invalid file name'.format(file_name))
    return file_name


def generate_code(args):
    """Generate test code for the given filename."""
    features = []
    scenarios = []
    seen_names = set()
    for file_name in args.files:
        if file_name in seen_names:
            continue
        seen_names.add(file_name)
        base, name = os.path.split(file_name)
        feature = Feature.get_feature(base, name)
        features.append(feature)
        scenarios.extend(feature.scenarios.values())

    steps = itertools.chain.from_iterable(
        scenario.steps for scenario in scenarios)
    steps = sorted(steps, key=lambda step: step.type)
    seen_steps = set()
    grouped_steps = []
    for step in (itertools.chain.from_iterable(
            sorted(group, key=lambda step: step.name)
            for _, group in itertools.groupby(steps, lambda step: step.type))):
        if step.name not in seen_steps:
            grouped_steps.append(step)
            seen_steps.add(step.name)

    print(template_lookup.get_template('test.py.mak').render(
        feature=features[0], scenarios=scenarios, steps=grouped_steps, make_python_name=make_python_name))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(prog='pytest-bdd')
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_generate = subparsers.add_parser('generate', help='generate help')
    parser_generate.add_argument(
        'files', metavar='FEATURE_FILE', type=check_existense, nargs='+',
        help='Feature files to generate test code with')
    parser_generate.set_defaults(func=generate_code)

    parser_migrate = subparsers.add_parser('migrate', help='migrate help')
    parser_migrate.add_argument(
        'path', metavar='PATH',
        help='Migrate outdated tests to the most recent form')
    parser_migrate.set_defaults(func=migrate_tests)

    args = parser.parse_args()
    args.func(args)
