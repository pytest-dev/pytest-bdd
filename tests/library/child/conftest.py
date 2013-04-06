from pytest_bdd import given


@given('I have the overriden fixture')
def overridable():
    return 'child'
