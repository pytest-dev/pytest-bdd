"""Configuration for pytest runner."""

from pytest_bdd import when

pytest_plugins = "pytester"


@when("I use a when step from the parent conftest")
def global_when():
    pass
