"""Configuration for pytest runner."""

from pytest_bdd import given, when
from pytest_bdd.fixtures import *

pytest_plugins = "pytester"


@given("I have a root fixture")
def root():
    return "root"


@when("I use a when step from the parent conftest")
def global_when():
    pass
