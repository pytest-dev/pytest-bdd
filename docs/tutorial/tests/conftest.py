"""
    conftest.py is local per-directory plugin of pytest.
    Its mission is to define fixtures, steps, and hooks which will be used
    by tests gathered by pytest from directory structure below

    https://docs.pytest.org/en/latest/how-to/writing_plugins.html#conftest-py-local-per-directory-plugins
    https://docs.pytest.org/en/latest/explanation/goodpractices.html#test-discovery
"""

from pytest import fixture

from .steps.library_steps import (
    a_search_type_is_performed_for_search_term,
    only_these_books_will_be_returned,
    these_books_in_the_catalog,
)


@fixture
def search_results() -> list:
    return []
