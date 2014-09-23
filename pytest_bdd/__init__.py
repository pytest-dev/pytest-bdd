"""pytest-bdd public API."""

__version__ = '2.4.1'

try:
    from pytest_bdd.steps import given, when, then
    from pytest_bdd.scenario import scenario

    __all__ = [given.__name__, when.__name__, then.__name__, scenario.__name__]
except ImportError:
    # avoid import errors when only __version__ is needed (for setup.py)
    pass
