"""Various utility functions."""
import base64
import pickle
import re
import typing
from inspect import getframeinfo, signature
from sys import _getframe

if typing.TYPE_CHECKING:
    from _pytest.pytester import RunResult

CONFIG_STACK = []


def get_args(func):
    """Get a list of argument names for a function.

    :param func: The function to inspect.

    :return: A list of argument names.
    :rtype: list
    """
    params = signature(func).parameters.values()
    return [param.name for param in params if param.kind == param.POSITIONAL_OR_KEYWORD]


def get_caller_module_locals(depth=2):
    """Get the caller module locals dictionary.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.
    """
    return _getframe(depth).f_locals


def get_caller_module_path(depth=2):
    """Get the caller module path.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.
    """
    frame = _getframe(depth)
    return getframeinfo(frame, context=0).filename


_DUMP_START = "_pytest_bdd_>>>"
_DUMP_END = "<<<_pytest_bdd_"


def dump_obj(*objects):
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
