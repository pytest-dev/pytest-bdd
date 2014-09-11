"""pytest-bdd public API."""

__version__ = '2.3.3'

try:
    from pytest_bdd.steps import given, when, then  # pragma: no cover
    from pytest_bdd.scenario import scenario  # pragma: no cover

    __all__ = [given.__name__, when.__name__, then.__name__, scenario.__name__]  # pragma: no cover
except ImportError:
    # avoid import errors when only __version__ is needed (for setup.py)
    pass
