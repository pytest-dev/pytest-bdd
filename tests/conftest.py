"""Configuration for pytest runner."""

from pytest_bdd import given

pytest_plugins = 'pytester'


@given('I have a root fixture')
def root():
    return 'root'
