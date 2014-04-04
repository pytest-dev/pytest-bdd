"""pytest-bdd scripts."""
import glob2
import os.path
import re
import sys


MIGRATE_REGEX = re.compile(r'\s?(\w+)\s\=\sscenario\((.+)\)', flags=re.MULTILINE)


def migrate_tests():
    """Migrate outdated tests to the most recent form."""
    if len(sys.argv) != 2:
        print('Usage: pytestbdd_migrate_tests <path>')
        sys.exit(1)
    path = sys.argv[1]
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
