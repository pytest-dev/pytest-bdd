"""Pytest plugin entry point. Used for any fixtures needed."""

import pytest

from . import given, when, then
from . import cucumber_json
from . import generation
from . import gherkin_terminal_reporter


# Import hook handlers:
from .reporting import *
from .cucumber_json import *
from .generation import *
from .gherkin_terminal_reporter import *

from .fixtures import *


def pytest_addhooks(pluginmanager):
    """Register plugin hooks."""
    from pytest_bdd import hooks
    try:
        # pytest >= 2.8
        pluginmanager.add_hookspecs(hooks)
    except AttributeError:
        # pytest < 2.8
        pluginmanager.addhooks(hooks)


@given('trace')
@when('trace')
@then('trace')
def trace():
    """Enter pytest's pdb trace."""
    pytest.set_trace()


def pytest_addoption(parser):
    """Add pytest-bdd options."""
    cucumber_json.add_options(parser)
    generation.add_options(parser)
    gherkin_terminal_reporter.add_options(parser)
