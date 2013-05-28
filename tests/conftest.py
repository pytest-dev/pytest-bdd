"""Configuration for pytest runner."""

from pytest_bdd import given, when
from pytest_bdd.plugin import pytestbdd_feature_path

pytest_plugins = 'pytester'


@given('I have a root fixture')
def root():
    return 'root'


@when('I use a when step from the parent conftest')
def global_when():
    pass
