"""Datatables with fixtures collision feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    parsers
)

import pytest

@pytest.fixture
def datatable():
    return [['header'],['test body']]

@scenario('test_datatable_fixture_collision.feature', 'Ensure that there is an existing datatable fixture')
def test_ensure_existing_fixture():
    """Ensure existing fixture is used."""

@given('There is an existing fixture named datatable')
def there_is_an_existing_datatable_fixture(datatable):
    return datatable

@then(parsers.re('datatable contents (?P<negation>(don\'t |do not )?)match existing fixture'))
def check_if_contents_match_existing(negation, there_is_an_existing_datatable_fixture, datatable):
    if negation:
        assert there_is_an_existing_datatable_fixture != datatable
    else:
        assert there_is_an_existing_datatable_fixture == datatable
