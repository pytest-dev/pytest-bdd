from pytest import fixture
from pytest_bdd_ng import given, when, then, parsers, step


from helper_methods.library_catalog import Catalog
from helper_methods.verification_helper_methods import verify_returned_books
@fixture
def context()
    """ Create a placeholder object to use in place of Cucumber's context object. The context object allows us to pass state between steps. """
    class dummy():
        pass


    return dummy()


@given("these books in the catalog")
def these_books_in_the_catalog(step):
    context.catalog = Catalog()
    context.catalog.add_books_to_catalog(step.data_table)


@when(parsers.re("a (?P<search_type>name|title) search is performed for " +
"(?P<search_term>.+)"))
def a_SEARCH_TYPE_is_performed_for_SEARCH_TERM(search_type, search_term):
    if search_type == "title":
        raise NotImplementedError("Title searches are not yet implemented.")
    context.search_results = context.catalog.search_by_author(search_term)


@then("only these books will be returned")
def only_these_books_will_be_returned(step):
expected_books = context.catalog.read_books_from_table(step.data_table)
verify_returned_books(context.search_results, expected_books)
