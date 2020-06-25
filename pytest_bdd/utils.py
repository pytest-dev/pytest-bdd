"""Various utility functions."""
import inspect

from _pytest.fixtures import FixtureLookupError

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


def run_coroutines(*results_or_coroutines, request):
    """
    Takes provided coroutine(s) or function(s) result(s) (that can be any type) and for every one of them:
        * if it is coroutine - runs it using event_loop fixture and adds its result to the batch,
        * if it isn't coroutine - just adds it to the batch.
    Then returns batch of results (or single result).

    Example usage:
        >>> def regular_fn(): return 24
        >>> async def async_fn(): return 42
        >>>
        >>> assert run_coroutines(regular_fn(), request=request) == 24
        >>> assert run_coroutines(async_fn(), request=request) == 42
        >>> assert run_coroutines(regular_fn(), async_fn(), request=request) == (24, 42)

    :param results_or_coroutines: coroutine(s) to run or function results to let-through
    :param request: request fixture
    :return: single result (if there was single coroutine/result provided as input) or multiple results (otherwise)
    """

    def run_with_event_loop_fixture(coro):
        try:
            event_loop = request.getfixturevalue("event_loop")
        except FixtureLookupError:
            raise ValueError("Install pytest-asyncio plugin to run asynchronous steps.")

        return event_loop.run_until_complete(coro)

    results = [
        run_with_event_loop_fixture(result_or_coro) if inspect.iscoroutine(result_or_coro) else result_or_coro
        for result_or_coro in results_or_coroutines
    ]

    if len(results) == 1:
        return results[0]
    else:
        return tuple(results)
