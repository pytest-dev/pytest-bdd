import re
from pytest_bdd import when


@when(re.compile(r'I append (?P<n>\d+) to the list'))
def append_to_list(results, n):
    results.append(int(n))
