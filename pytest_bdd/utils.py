"""Various utility functions."""

import inspect

CONFIG_STACK = []


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
    """Set the given raw fixture value from the pytest request object.

    :note: Compatibility with pytest < 3.3.2
    """
    try:
        return request._fixture_values.get(name)
    except AttributeError:
        try:
            return request._funcargs.get(name)
        except AttributeError:
            pass


def set_fixture_value(request, name, value):
    """Set the given fixture value on the pytest request object.

    :note: Compatibility with pytest < 3.3.2
    """
    try:
        request._fixture_values[name] = value
    except AttributeError:
        try:
            request._funcargs[name] = value
        except AttributeError:
            pass


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


def get_parametrize_markers_args(node):
    """In pytest 3.6 new API to access markers has been introduced and it deprecated
    MarkInfo objects.

    This function uses that API if it is available otherwise it uses MarkInfo objects.
    """
    mark_name = 'parametrize'
    try:
        return get_markers_args_using_iter_markers(node, mark_name)
    except AttributeError:
        return get_markers_args_using_get_marker(node, mark_name)


def get_markers_args_using_iter_markers(node, mark_name):
    """Recommended on pytest>=3.6"""
    args = []
    for mark in node.iter_markers(mark_name):
        args += mark.args
    return tuple(args)


def get_markers_args_using_get_marker(node, mark_name):
    """Deprecated on pytest>=3.6"""
    return getattr(node.get_marker(mark_name), 'args', ())


def get_parametrize_params(parametrize_args):
    """Group parametrize markers arguments names and values.

    :param parametrize_args: parametrize markers arguments.
    :return: `list` of `dict` in the form of:
        [
            {
                "names": ["name1", "name2", ...],
                "values": [value1, value2, ...],
            },
            ...
        ]
    """
    params = []
    for i in range(0, len(parametrize_args), 2):
        params.append({
            'names': _coerce_list(parametrize_args[i]),
            'values': parametrize_args[i+1]
        })
    return params


def _coerce_list(names):
    if not isinstance(names, (tuple, list)):
        # As pytest.mark.parametrize has only one param name,
        # it is not returned as a list. Convert it to list:
        names = [names]
    return list(names)
