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
