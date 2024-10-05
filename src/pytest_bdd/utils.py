"""Various utility functions."""
import base64
import pickle
import re
import sys
from collections import defaultdict
from contextlib import contextmanager, nullcontext, suppress
from enum import Enum
from functools import reduce
from inspect import getframeinfo, signature
from itertools import tee
from operator import attrgetter, getitem, itemgetter
from sys import _getframe
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Collection,
    Dict,
    Literal,
    Mapping,
    Optional,
    Pattern,
    Protocol,
    Sequence,
    Type,
    Union,
    cast,
    runtime_checkable,
)
from urllib.parse import urlparse

from _pytest.fixtures import FixtureDef, FixtureRequest

from pytest_bdd.compatibility.pytest import PYTEST8, PYTEST81, fail
from pytest_bdd.const import ALPHA_REGEX, PYTHON_REPLACE_REGEX

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import RunResult


@runtime_checkable
class PytestBDDIdGeneratorHandler(Protocol):
    pytest_bdd_id_generator: Union["IdGenerator", Any]


def get_args(func: Callable) -> Sequence[str]:
    """Get a list of argument names for a function.

    :param func: The function to inspect.

    :return: A list of argument names.
    :rtype: list
    """
    params = signature(func).parameters.values()
    return [param.name for param in params if param.kind == param.POSITIONAL_OR_KEYWORD]


def get_caller_module_locals(stacklevel: int = 1) -> Dict[str, Any]:
    """Get the caller module locals dictionary.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.
    """
    return _getframe(stacklevel).f_locals


def get_caller_module_path(stacklevel: int = 1) -> str:
    """Get the caller module path.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.
    """
    frame = _getframe(stacklevel)
    return getframeinfo(frame, context=0).filename


def convert_str_to_python_name(s: Any) -> str:
    s1: str = str(s)
    s2 = re.sub(r"[^.a-zA-Z0-9]", "_", s1)
    s3 = re.sub(r"_+", "_", s2)
    s4 = s3.strip("_")
    if re.match(r"\d.*", s4):
        result_s = f"_{s4}"
    else:
        result_s = s4
    return result_s


_DUMP_START = "_pytest_bdd_>>>"
_DUMP_END = "<<<_pytest_bdd_"


def dump_obj(*objects: Any) -> None:
    """Dump objects to stdout so that they can be inspected by the test suite."""
    for obj in objects:
        dump = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        encoded = base64.b64encode(dump).decode("ascii")
        print(f"{_DUMP_START}{encoded}{_DUMP_END}")


def collect_dumped_objects(result: "RunResult"):
    """Parse all the objects dumped with `dump_object` from the result.

    Note: You must run the result with output to stdout enabled.
    For example, using ``testdir.runpytest("-s")``.
    """
    stdout = result.stdout.str()  # pytest < 6.2, otherwise we could just do str(result.stdout)
    payloads = re.findall(rf"{_DUMP_START}(.*?){_DUMP_END}", stdout)
    return [pickle.loads(base64.b64decode(payload)) for payload in payloads]


class DefaultMapping(defaultdict):
    Skip = object()

    def __init__(self, *args, default_factory=None, warm_up_keys=(), **kwargs):
        super().__init__(default_factory, *args, **kwargs)
        self.warm_up(*warm_up_keys)

    def __missing__(self, key):
        if ... in self.keys():
            intercessor = self[...]
            if intercessor is self.Skip:
                raise KeyError(key)
            elif isinstance(intercessor, Callable):
                value = intercessor(key)
            elif intercessor is ...:
                value = key
            else:
                value = intercessor
            self[key] = value
            return value
        else:
            return super().__missing__(key)

    def warm_up(self, *items):
        for item in items:
            with suppress(KeyError):
                getitem(self, item)

    @classmethod
    def instantiate_from_collection_or_bool(
        cls, bool_or_items: Union[Collection[str], Dict[str, Any], Any] = True, *, warm_up_keys=()
    ):
        if isinstance(bool_or_items, Collection):
            if not isinstance(bool_or_items, Mapping):
                bool_or_items = zip(*tee(iter(bool_or_items)))
        else:
            bool_or_items = cast(dict, {...: ...} if bool_or_items else {...: DefaultMapping.Skip})
        return cls(bool_or_items, warm_up_keys=warm_up_keys)


def inject_fixture(request: FixtureRequest, arg: str, value: Any) -> None:
    """Inject fixture into pytest fixture request.
    :param request: pytest fixture request
    :param arg: argument name
    :param value: argument value
    """

    fd = FixtureDef(
        **({"config": request.config} if PYTEST81 else {"fixturemanager": request._fixturemanager}),
        baseid=None,
        argname=arg,
        func=lambda: value,
        scope="function",
        params=None,
        **({"_ispytest": True} if PYTEST8 else {}),
    )
    fd.cached_result = (value, 0, None)

    old_fd = request._fixture_defs.get(arg)
    add_fixturename = arg not in request.fixturenames

    def fin():
        request._fixturemanager._arg2fixturedefs[arg].remove(fd)
        request._fixture_defs[arg] = old_fd

        if add_fixturename:
            request._pyfuncitem._fixtureinfo.names_closure.remove(arg)

    request.addfinalizer(fin)

    # inject fixture definition
    request._fixturemanager._arg2fixturedefs.setdefault(arg, []).insert(0, fd)
    # inject fixture value in request cache
    request._fixture_defs[arg] = fd
    if add_fixturename:
        request._pyfuncitem._fixtureinfo.names_closure.append(arg)


def _itemgetter(*items):
    def func(obj):
        if len(items) == 0:
            return []
        elif len(items) == 1:
            return [obj[items[0]]] if items[0] != "" else []
        else:
            return itemgetter(*items)(obj)

    return func


class _NoneException(Exception):
    ...


class Empty(Enum):
    empty = None


def getitemdefault(
    obj, index, default=Empty.empty, default_factory: Optional[Callable] = None, treat_as_empty=Empty.empty
):
    if default is not Empty.empty:
        if default_factory is not None:
            raise ValueError("Both 'default' and 'default_factory' were specified")
        else:
            default_factory = lambda: default
    try:
        item = getitem(obj, index)
    except KeyError:
        if default_factory is None:
            raise
        else:
            item = default_factory()
    if item is not treat_as_empty:
        return item
    else:
        raise KeyError(f"{index}")


def deepattrgetter(*attrs, **kwargs):
    empty = object()
    default = kwargs.pop("default", empty)
    default_exception_type = AttributeError if default is not empty else _NoneException
    skip_missing = kwargs.pop("skip_missing", False)
    skip_missing_context = suppress(AttributeError) if skip_missing else nullcontext()
    if default is not empty and skip_missing:
        raise ValueError('Both "default" and "skip_missing" are specified')

    def fn(obj):
        def _():
            for attr in attrs:
                try:
                    with skip_missing_context:
                        yield attrgetter(attr)(obj)
                except default_exception_type:
                    yield default

        return tuple(_())

    return fn


def setdefaultattr(
    obj, key, value: Union[Literal[Empty.empty], Any] = Empty.empty, value_factory: Optional[Callable] = None
):
    if value is not Empty.empty and value_factory is not None:
        raise ValueError("Both 'value' and 'value_factory' were specified")
    with suppress(AttributeError):
        return getattr(obj, key)
    if value_factory is not None:
        value = value_factory()
    setattr(obj, key, value)
    return value


def compose(*funcs):
    return reduce(lambda f, g: lambda *args, **kwargs: f(g(*args, **kwargs)), funcs)


def flip(func):
    def wrapped(*args, **kwargs):
        if len(args) > 1:
            first, *other, last = args
            return func(last, *other, first, **kwargs)
        else:
            return func(*args, **kwargs)

    return wrapped


def make_python_name(string: str) -> str:
    """Make python attribute name out of a given string."""
    string = re.sub(PYTHON_REPLACE_REGEX, "", string.replace(" ", "_"))
    return re.sub(ALPHA_REGEX, "", string).lower()


@runtime_checkable
class StringableProtocol(Protocol):
    def __str__(self) -> str:
        ...  # pragma: no cover


def stringify(value: Union[StringableProtocol, str, bytes]) -> str:
    return str(value, **({"encoding": "utf-8"} if isinstance(value, bytes) else {}))


class IdGenerator:
    def __init__(self):
        self._id_counter = 0

    def __next__(self):
        try:
            return str(self._id_counter)
        finally:
            self._id_counter += 1

    get_next_id = __next__


@contextmanager
def doesnt_raise(
    expected_exception: Union[Type[Exception], Sequence[Type[Exception]]],
    *,
    match: Optional[Union[str, Pattern[str]]] = None,
    suppress_not_matched=True,
):
    """

    :param expected_exception: Expected exception/s which don't have to be raised; If it raised - test fails
    :param match: Message which will be count as failing test. If message is not matched - function passes
    :param suppress_not_matched: If specified - all non-matched exceptions will be suppressed
    :return:
    """

    try:
        yield
    except expected_exception:  # type:ignore[misc]
        ex_type, ex_value, ex_traceback = sys.exc_info()
        is_matched = True
        if match is not None:
            is_matched = bool(re.search(match, f"{ex_value}"))
        if is_matched:
            fail(f"{ex_value}")
        elif not suppress_not_matched:
            raise


def is_local_url(urllike):
    try:
        return not any(attrgetter("scheme", "netloc")(urlparse(urllike)))
    except Exception:
        return False


def is_url_parsable(urllike):
    try:
        urlparse(str(urllike))
        return True
    except ValueError:
        return False
