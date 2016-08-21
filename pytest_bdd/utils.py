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
        return request._fixture_values.get(name)
    except AttributeError:
        return request._funcargs.get(name)


def set_fixture_value(request, name, value):
    """Set the given fixture value on the pytest request object."""
    try:
        request._fixture_values[name] = value
    except AttributeError:
        request._funcargs[name] = value


def get_request_fixture_defs(request):
    """Get the internal list of FixtureDefs cached into the given request object.

    Compatibility with pytest 3.0.
    """
    try:
        return request._fixture_defs
    except AttributeError:
        return getattr(request, "_fixturedefs", {})


def get_request_fixture_names(request):
    """Get list of fixture names for the given FixtureRequest.

    Get the internal and mutable list of fixture names in the enclosing scope of
    the given request object.

    Compatibility with pytest 3.0.
    """
    return request._pyfuncitem._fixtureinfo.names_closure
