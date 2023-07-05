from contextlib import contextmanager
from inspect import signature
from itertools import count

from _pytest.config import UsageError
from _pytest.mark import MarkMatcher
from _pytest.mark.expression import Expression, ParseError
from makefun import wraps
from pytest import fixture

from pytest_bdd.compatibility.pytest import FixtureRequest

mark_expression_gen = count()


def _parse_expression(expr: str, exc_message: str) -> Expression:
    try:
        return Expression.compile(expr)
    except ParseError as e:
        raise UsageError(f"{exc_message}: {expr}: {e}") from None


def before(mark_expression):
    def decorator(func):
        func_sig = signature(func)

        @fixture(name=f"before_mark_expression_{mark_expression}_{next(mark_expression_gen)}", autouse=True)
        @wraps(func, prepend_args="request", remove_args="request")
        def before_hook(request: FixtureRequest, *args, **kwargs):
            item = request.node

            expr = _parse_expression(mark_expression, "Wrong expression passed")
            if expr.evaluate(MarkMatcher.from_item(item)):
                return func(
                    *args, **{**kwargs, **({"request": request} if "request" in func_sig.parameters.keys() else {})}
                )

        return before_hook

    return decorator


def after(mark_expression):
    def decorator(func):
        func_sig = signature(func)

        @fixture(name=f"after_mark_expression_{mark_expression}_{next(mark_expression_gen)}", autouse=True)
        @wraps(func, prepend_args="request", remove_args="request")
        def after_hook(request: FixtureRequest, *args, **kwargs):
            yield
            expr = _parse_expression(mark_expression, "Wrong expression passed")
            item = request.node
            if expr.evaluate(MarkMatcher.from_item(item)):
                func(*args, **{**kwargs, **({"request": request} if "request" in func_sig.parameters.keys() else {})})

        return after_hook

    return decorator


def around(mark_expression):
    def decorator(func):
        func_sig = signature(func)

        @fixture(name=f"around_mark_expression_{mark_expression}_{next(mark_expression_gen)}", autouse=True)
        @wraps(func, prepend_args="request", remove_args="request")
        def around_hook(request: FixtureRequest, *args, **kwargs):
            expr = _parse_expression(mark_expression, "Wrong expression passed")
            item = request.node
            if expr.evaluate(MarkMatcher.from_item(item)):
                context_manager = contextmanager(func)
                with context_manager(
                    *args, **{**kwargs, **({"request": request} if "request" in func_sig.parameters.keys() else {})}
                ):
                    yield

        return around_hook

    return decorator
