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
    if hasattr(inspect, "signature"):
        params = inspect.signature(func).parameters.values()
        return [param.name for param in params if param.kind == param.POSITIONAL_OR_KEYWORD]
    else:
        return inspect.getargspec(func).args


def get_parametrize_markers_args(node):
    """In pytest 3.6 new API to access markers has been introduced and it deprecated
    MarkInfo objects.

    This function uses that API if it is available otherwise it uses MarkInfo objects.
    """
    return tuple(arg for mark in node.iter_markers("parametrize") for arg in mark.args)
