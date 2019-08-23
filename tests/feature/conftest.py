from pytest_bdd import given, then


@given("I have a bar")
def bar():
    return "bar"


@then('bar should have value "bar"')
def bar_is_bar(bar):
    assert bar == "bar"
