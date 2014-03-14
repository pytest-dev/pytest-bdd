"""pytest-bdd scripts."""
import glob
import os.path
import re
import sys


MIGRATE_REGEX = re.compile(r'(\w+)\s\=\sscenario\((.+)\)')


def migrate_tests():
    """Migrate outdated tests to the most recent form."""
    if len(sys.argv) != 2:
        print 'Usage: pytestbdd_migrate_tests <path>'
        sys.exit(1)
    path = sys.argv[1]
    for file_path in glob.iglob(os.path.join(os.path.abspath(path), '**', '*.py')):
        migrate_tests_in_file(file_path)


def migrate_tests_in_file(file_path):
    """Migrate all bdd-based tests in the given test file."""
    re.sub(MIGRATE_REGEX, '@scenario(2)\ndef 1():\n    pass', open(file_path), flags=re.MULTILINE)
