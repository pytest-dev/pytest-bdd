import re
from typing import List, Literal

from messages import DataTable, Step  # type:ignore[attr-defined]
from pytest_bdd import given, step, then, when

from ...src.catalog import Book, Catalog


def get_books_from_data_table(data_table: DataTable):
    # Gherkin data-tables have no title row by default, but we could define them if we want.
    title_row, *book_rows = data_table.rows

    step_data_table_titles = []
    for cell in title_row.cells:
        step_data_table_titles.append(cell.value)

    assert step_data_table_titles == ["Author", "Title"]

    books = []
    for row in book_rows:
        books.append(Book(row.cells[0].value, row.cells[1].value))

    return books


# Steps to be used in scenarios are defined with special decorators
@given(
    "these books in the catalog",
    # Steps are allowed to inject new fixtures or overwrite existing ones
    target_fixture="catalog",
)
def these_books_in_the_catalog(
    # `step` fixture is injected by pytest dependency injection mechanism into scope of step by default;
    # So it could be used without extra effort
    step: Step,
):
    books = get_books_from_data_table(step.data_table)

    catalog = Catalog()
    catalog.add_books_to_catalog(books)

    yield catalog


@when(
    # Step definitions could have parameters. Here could be raw stings, cucumber expressions or regular expressions
    re.compile("a (?P<search_type>name|title) search is performed for (?P<search_term>.+)"),
    target_fixture="search_results",
)
def a_search_type_is_performed_for_search_term(
    # `search_results` is a usual pytest fixture defined somewhere else (at conftest.py, plugin or module) and injected by pytest dependency injection mechanism.
    # In this case it will be provided by conftest.py
    search_results: List[Book],
    # `search_type` and `search_term` are parameters of this step and are injected by step definition
    search_type: Literal["name", "title"],
    search_term: str,
    # `catalog` is a fixture injected by another step
    catalog: Catalog,
):
    if search_type == "title":
        search = catalog.search_by_title
    elif search_type == "name":
        search = catalog.search_by_author
    else:
        assert False, "Unknown"

    found_books = search(search_term)
    search_results.extend(found_books)
    yield search_results


@then("only these books will be returned")
def only_these_books_will_be_returned(
    # Fixtures persist during step execution, so usual `context` common for behave users is not required,
    # so if you define fixture dependencies debugging becomes much easier.
    search_results: List[Book],
    step: Step,
    catalog: Catalog,
):
    expected_books = get_books_from_data_table(step.data_table)

    for book in search_results:
        if book not in expected_books:
            assert False, f"Book ${book} is not expected"
