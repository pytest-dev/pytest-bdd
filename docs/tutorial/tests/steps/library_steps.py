import re
from typing import Literal

from src.catalog import Book, Catalog

from messages import DataTable, Step  # type:ignore[attr-defined]
from pytest_bdd import given, step, then, when


def get_books_from_data_table(data_table: DataTable):
    # Gherkin data-tables have no title row by default, but we could use if we want.
    step_data_table_titles = [cell.value for cell in data_table.rows[0].cells]
    assert step_data_table_titles == ["Author", "Title"]

    author_and_title_list = [[cell.value for cell in row.cells] for row in data_table.rows[1:]]

    books = [Book(author, title) for author, title in author_and_title_list]
    return books


# Steps to be used in scenarios are defined with special decorators
@given(
    "these books in the catalog",
    # Steps are allowed to inject new fixtures or overwrite existing ones
    target_fixture="catalog",
)
def these_books_in_the_catalog(
    # `step` fixture is injected by pytest DI mechanism into scope of step by default
    step: Step,
):
    catalog = Catalog()

    books = get_books_from_data_table(step.data_table)
    catalog.add_books_to_catalog(books)
    yield catalog


@when(
    # Step definitions could have parameters. Here could be raw stings, cucumber expressions or regular expressions
    re.compile('a (?P<search_type>name|title) search is performed for "(?P<search_term>.+)"'),
    target_fixture="search_results",
)
def a_search_type_is_performed_for_search_term(
    # `search_results` is a usual pytest fixture defined somewhere else and injected by pytest DI mechanism.
    # In this case it will be provided by conftest.py
    search_results,
    # `search_type` and `search_term` are parameters of this step and are injected by step definition
    search_type: Literal["name", "title"],
    search_term: str,
    # `catalog` is a fixture injected by another step
    catalog: Catalog,
):
    if search_type == "title":
        search_results.extend(catalog.search_by_title(search_term))
    elif search_type == "name":
        search_results.extend(catalog.search_by_author(search_term))
    else:
        assert False, "Unknown"

    yield search_results


@then("only these books will be returned")
def only_these_books_will_be_returned(
    # fixtures persist during step execution, so usual context is not required,
    # so if you define fixture dependencies debugging becomes much easier.
    search_results,
    step: Step,
    catalog: Catalog,
):
    expected_books = get_books_from_data_table(step.data_table)
    assert all([book in catalog.storage for book in expected_books])
