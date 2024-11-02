from collections.abc import Iterable
from io import BufferedIOBase, TextIOBase
from pathlib import Path
from typing import Any, Optional, Union

from pytest import hookspec

from messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from messages import Pickle  # type:ignore[attr-defined]
from pytest_bdd.compatibility.pytest import Config, FixtureRequest, Mark
from pytest_bdd.model import Feature

"""Pytest-bdd pytest hooks."""


def pytest_bdd_before_scenario(request, feature, scenario):
    """Called before scenario is executed."""


def pytest_bdd_run_scenario(request, feature, scenario):
    """Execution scenario protocol"""


def pytest_bdd_after_scenario(request, feature, scenario):
    """Called after scenario is executed."""


def pytest_bdd_run_step(request, feature, scenario, step, previous_step):
    """Execution of run step protocol"""


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    """Called before step function is set up."""


def pytest_bdd_before_step_call(request, feature, scenario, step, step_func, step_func_args, step_definition):
    """Called before step function is executed."""


def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args, step_definition):
    """Called after step function is successfully executed."""


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception, step_definition):
    """Called when step function failed to execute."""


def pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception):
    """Called when step lookup failed."""


@hookspec(firstresult=True)
def pytest_bdd_convert_tag_to_marks(feature, scenario, tag) -> Optional[Iterable[Mark]]:
    """Apply a tag (from a ``.feature`` file) to the given test item.

    The default implementation does the equivalent of
    ``getattr(pytest.mark, tag)(function)``, but you can override this hook and
    return ``True`` to do more sophisticated handling of tags.
    """


@hookspec(firstresult=True)
def pytest_bdd_match_step_definition_to_step(request, feature, scenario, step, previous_step):
    """Find match between scenario step and user defined step function"""


@hookspec(firstresult=True)
def pytest_bdd_get_step_caller(request, feature, scenario, step, step_func, step_func_args, step_definition):
    """Provide alternative approach to execute step"""


@hookspec(firstresult=True)
def pytest_bdd_get_step_dispatcher(request: FixtureRequest, feature: Feature, scenario: Pickle):
    """Provide alternative approach to execute scenario steps"""


def pytest_bdd_message(config: Config, message: Message):
    """Implement cucumber message protocol https://github.com/cucumber/messages"""


@hookspec(firstresult=True)
def pytest_bdd_is_collectible(config: Config, path: Path):
    """Verifies if path could be collected by pytest_bdd"""


@hookspec(firstresult=True)
def pytest_bdd_get_parser(config: Config, mimetype: str):
    """Get parser for specific file path"""


@hookspec(firstresult=True)
def pytest_bdd_get_mimetype(config: Config, path: Path):
    """Get parser for specific file path"""


def pytest_bdd_attach(
    request: FixtureRequest,
    attachment: Union[str, bytes, bytearray, BufferedIOBase, TextIOBase, Any],
    media_type: Optional[str],
    file_name: Optional[str],
):
    """Internal hook to add attachment to a test case"""
