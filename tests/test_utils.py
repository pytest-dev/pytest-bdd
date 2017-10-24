import pytest

from pytest_bdd import types
from pytest_bdd.feature import Step
from pytest_bdd.utils import format_step_name


@pytest.fixture
def single():
    return "SINGLE"


@pytest.fixture()
def second():
    return "SECOND"


def test_format_step_name_without_format(request):
    step = Step(
        name="without any formats",
        type=types.GIVEN,
        indent=0,
        line_number=0,
        keyword="",
    )
    assert format_step_name(request, step) == "without any formats"


def test_format_step_name_with_single_format(request, single):
    step = Step(
        name="with a <single> format",
        type=types.WHEN,
        indent=0,
        line_number=0,
        keyword="",
    )
    assert format_step_name(request, step) == "with a SINGLE format"


def test_format_step_name_with_multiple_formats(request, single, second):
    step = Step(
        name="with not only a <single>, but a <second> format",
        type=types.THEN,
        indent=0,
        line_number=0,
        keyword="",
    )
    assert format_step_name(request, step) == "with not only a SINGLE, but a SECOND format"
