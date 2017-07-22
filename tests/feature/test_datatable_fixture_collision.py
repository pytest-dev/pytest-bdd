"""Datatables with fixtures collision feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    parsers
)

import pytest


# Existing fixture
@pytest.fixture
def datatable():
    return [['header'], ['test body']]


# Scenarios
@scenario('test_datatable_fixture_collision.feature', 'Ensure that there is an existing datatable fixture')
def test_ensure_existing_fixture():
    """Ensure existing fixture is used."""


@scenario('test_datatable_fixture_collision.feature', 'Ensure that datatable does not conflict with existing fixture')
def test_datatable_does_not_conflict_with_existing_fixture():
    """Ensure that there is no collision between existing fixture and datatable"""


# Steps
@given('There is an existing fixture named datatable')
def there_is_an_existing_datatable_fixture(datatable):
    return datatable


@given('I have the following cars:')
def i_have_the_following_cars(datatable):
    return datatable[:]


@then("datatable contents match existing fixture")
def check_that_contents_match(there_is_an_existing_datatable_fixture, datatable):
    assert there_is_an_existing_datatable_fixture == datatable


@then("datatable contents don't match existing fixture")
def check_that_contents_dont_match(i_have_the_following_cars, datatable):
    import pdb; pdb.set_trace()
    assert i_have_the_following_cars != datatable


@then('I should see the following existing datatable')
def i_should_see_the_following_existing_datatable(there_is_an_existing_datatable_fixture, datatable):
    column = there_is_an_existing_datatable_fixture[0][0]
    import pdb; pdb.set_trace()
    body = there_is_an_existing_datatable_fixture[1][0]


@then('I should see the following models:')
def i_should_see_following_models(i_have_the_following_cars, datatable):
    column = i_have_the_following_cars[0][1]
    assert column == 'model'
