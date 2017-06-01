"""Datatables feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
)


@scenario('test_datatable.feature', 'I use datatables')
def test_i_use_datatables():
    """I use datatables."""

@scenario('test_datatable.feature', 'I use datatables for emails')
def test_i_use_datatables_for_emails():
    """I use datatables for emails."""

@given('the following users exist:')
def the_following_users_exist(datatable):
    """the following users exist:."""
    return datatable[1]


@then('I should see the following names:')
def i_should_see(datatable, the_following_users_exist):
    names = [row[0] for row in the_following_users_exist]
    assert names == sum(datatable[1], [])

@then('I should see the following emails:')
def i_should_see(datatable, the_following_users_exist):
    emails = [row[1] for row in the_following_users_exist]
    assert emails == sum(datatable[1], [])
