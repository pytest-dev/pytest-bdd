"""Various utility functions."""

import inspect


def get_args(func):
    """Get a list of argument names for a function.

    This is a wrapper around inspect.getargspec/inspect.signature because
    getargspec got deprecated in Python 3.5 and signature isn't available on
    Python 2.

    :param func: The function to inspect.

    :return: A list of argument names.
    :rtype: list
    """
    if hasattr(inspect, 'signature'):
        params = inspect.signature(func).parameters.values()
        return [param.name for param in params
                if param.kind == param.POSITIONAL_OR_KEYWORD]
    else:
        return inspect.getargspec(func).args


def get_fixture_value(request, name):
    """Get the given fixture from the pytest request object.

    getfuncargvalue() is deprecated in pytest 3.0, so we need to use
    getfixturevalue() there.
    """
    try:
        getfixturevalue = request.getfixturevalue
    except AttributeError:
        getfixturevalue = request.getfuncargvalue
    return getfixturevalue(name)


def get_fixture_value_raw(request, name):
    """Set the given raw fixture value from the pytest request object."""
    try:
        return request._fixture_values.get((name, request.scope))
    except AttributeError:
        return request._funcargs.get(name)


def set_fixture_value(request, name, value):
    """Set the given fixture value on the pytest request object."""
    try:
        request._fixture_values[(name, request.scope)] = value
    except AttributeError:
        request._funcargs[name] = value
