from contextlib import contextmanager
from enum import Enum
from inspect import isfunction, isgeneratorfunction, signature
from itertools import count, product, starmap
from operator import attrgetter
from typing import Optional, Union

from makefun import wraps
from pytest import fixture

from pytest_bdd.compatibility.pytest import FixtureRequest
from pytest_bdd.tag_expression import GherkinTagExpression, MarksTagExpression, TagExpression

expression_count_gen = count()


class HookKind(Enum):
    mark = "mark"
    tag = "tag"


class HookConjunction(Enum):
    before = "before"
    after = "after"
    around = "around"


def decorator_builder(conjunction: Union[str, HookConjunction], kind: Union[str, HookKind]):
    _conjunction = HookConjunction(conjunction) if isinstance(conjunction, str) else conjunction
    _kind = HookKind(kind) if isinstance(kind, str) else kind

    def decorator_wrapper(expression: str, name: Optional[str] = None):
        def decorator(func):
            func_sig = signature(func)

            @fixture(
                name=f"{_conjunction.value}_{_kind.value}_expression_{expression}_{next(expression_count_gen)}",
                autouse=True,
            )
            @wraps(func, prepend_args="request", remove_args="request")
            def hook(request: FixtureRequest, *args, **kwargs):
                _expression = {
                    HookKind.mark: MarksTagExpression,
                    HookKind.tag: GherkinTagExpression,
                }[_kind]

                # mypy@Python 3.8 complains "ABCMeta" has no attribute "parse"  [attr-defined] what is wrong
                parsed_expression: TagExpression = _expression.parse(expression)  # type: ignore[attr-defined]

                get_tags = {
                    HookKind.mark: lambda: {mark.name for mark in request.node.iter_markers()},
                    HookKind.tag: lambda: set(map(attrgetter("name"), request.getfixturevalue("scenario").tags)),
                }[_kind]

                is_matching = parsed_expression.evaluate(get_tags())

                is_function = isfunction(func)
                is_generator_function = isgeneratorfunction(func)
                if any(
                    [
                        _conjunction is HookConjunction.around and not is_generator_function,
                        _conjunction in {HookConjunction.before, HookConjunction.after} and not is_function,
                    ]
                ):
                    raise ValueError(f"_{_conjunction.value}")

                _args, _kwargs = args, {
                    **kwargs,
                    **({"request": request} if "request" in func_sig.parameters.keys() else {}),
                }

                if is_matching:
                    if _conjunction is HookConjunction.before:
                        yield func(*_args, **_kwargs)
                    elif _conjunction is HookConjunction.after:
                        yield
                        func(*_args, **_kwargs)
                    elif _conjunction is HookConjunction.around:
                        with contextmanager(func)(*_args, **_kwargs):
                            yield
                    else:  # pragma: no cover
                        yield
                else:
                    yield

            return hook

        return decorator

    return decorator_wrapper


before_mark, before_tag, after_mark, after_tag, around_mark, around_tag = starmap(
    decorator_builder, product(HookConjunction, HookKind)
)
