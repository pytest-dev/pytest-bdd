from pytest_bdd import given


@given('I have parent fixture')
def parent():
    return 'parent'


@given('I have overridable parent fixture')
def overridable():
    return 'parent'
