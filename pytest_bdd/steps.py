"""Step decorators.

Example:

@given("I have an article")
def article(author):
    return create_test_article(author=author)


@when("I go to the article page")
def go_to_the_article_page(browser, article):
    browser.visit(urljoin(browser.url, "/articles/{0}/".format(article.id)))


@then("I should not see the error message")
def no_error_message(browser):
    with pytest.raises(ElementDoesNotExist):
        browser.find_by_css(".message.error").first


Multiple names for the steps:

@given("I have an article")
@given("there is an article")
def article(author):
    return create_test_article(author=author)


Reusing existing fixtures for a different step name:

given("I have a beautiful article", fixture="article")
"""

from __future__ import absolute_import
from types import CodeType
import inspect
import sys

import pytest
import six

from .feature import parse_line, force_encode
from .types import GIVEN, WHEN, THEN
from .exceptions import (
    StepError,
)
from .parsers import get_parser


def given(name, fixture=None, converters=None):
    """Given step decorator.

    :param name: Given step name.
    :param fixture: Optional name of the fixture to reuse.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param parser: name of the step parser to use
    :param parser_args: optional `dict` of arguments to pass to step parser
    :raises: StepError in case of wrong configuration.
    :note: Can't be used as a decorator when the fixture is specified.
    """
    if fixture is not None:
        module = get_caller_module()
        step_func = lambda request: request.getfuncargvalue(fixture)
        step_func.step_type = GIVEN
        step_func.converters = converters
        step_func.__name__ = name
        step_func.fixture = fixture
        func = pytest.fixture(lambda: step_func)
        func.__doc__ = 'Alias for the "{0}" fixture.'.format(fixture)
        _, name = parse_line(name)
        contribute_to_module(module, name, func)
        return _not_a_fixture_decorator

    return _step_decorator(GIVEN, name, converters=converters)


def when(name, converters=None):
    """When step decorator.

    :param name: Step name.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param parser: name of the step parser to use
    :param parser_args: optional `dict` of arguments to pass to step parser

    :raises: StepError in case of wrong configuration.
    """
    return _step_decorator(WHEN, name, converters=converters)


def then(name, converters=None):
    """Then step decorator.

    :param name: Step name.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param parser: name of the step parser to use
    :param parser_args: optional `dict` of arguments to pass to step parser

    :raises: StepError in case of wrong configuration.
    """
    return _step_decorator(THEN, name, converters=converters)


def _not_a_fixture_decorator(func):
    """Function that prevents the decoration.

    :param func: Function that is going to be decorated.

    :raises: `StepError` if was used as a decorator.
    """
    raise StepError('Cannot be used as a decorator when the fixture is specified')


def _step_decorator(step_type, step_name, converters=None):
    """Step decorator for the type and the name.

    :param str step_type: Step type (GIVEN, WHEN or THEN).
    :param str step_name: Step name as in the feature file.
    :param str parser: name of the step parser to use
    :param dict parser_args: optional `dict` of arguments to pass to step parser

    :return: Decorator function for the step.

    :raise: StepError if the function doesn't take group names as parameters.

    :note: If the step type is GIVEN it will automatically apply the pytest
           fixture decorator to the step function.
    """
    def decorator(func):
        step_func = func
        parser_instance = get_parser(step_name)
        parsed_step_name = parser_instance.name

        if step_type == GIVEN:
            if not hasattr(func, "_pytestfixturefunction"):
                # Avoid multiple wrapping of a fixture
                func = pytest.fixture(func)
            step_func = lambda request: request.getfuncargvalue(func.__name__)
            step_func.__doc__ = func.__doc__
            step_func.fixture = func.__name__

        step_func.__name__ = force_encode(parsed_step_name)

        @pytest.fixture
        def lazy_step_func():
            return step_func

        step_func.step_type = step_type

        lazy_step_func = contribute_to_module(get_caller_module(), parsed_step_name, lazy_step_func)

        lazy_step_func.step_type = step_type

        # Preserve the docstring
        lazy_step_func.__doc__ = func.__doc__

        step_func.parser = lazy_step_func.parser = parser_instance
        if converters:
            step_func.converters = lazy_step_func.converters = converters

        return func

    return decorator


def recreate_function(func, module=None, name=None, add_args=[], firstlineno=None):
    """Recreate a function, replacing some info.

    :param func: Function object.
    :param module: Module to contribute to.
    :param add_args: Additional arguments to add to function.

    :return: Function copy.
    """
    def get_code(func):
        return func.__code__ if six.PY3 else func.func_code

    def set_code(func, code):
        if six.PY3:
            func.__code__ = code
        else:
            func.func_code = code

    argnames = [
        "co_argcount", "co_nlocals", "co_stacksize", "co_flags", "co_code", "co_consts", "co_names",
        "co_varnames", "co_filename", "co_name", "co_firstlineno", "co_lnotab", "co_freevars", "co_cellvars",
    ]
    if six.PY3:
        argnames.insert(1, "co_kwonlyargcount")

    for arg in inspect.getargspec(func).args:
        if arg in add_args:
            add_args.remove(arg)

    args = []
    code = get_code(func)
    for arg in argnames:
        if module is not None and arg == "co_filename":
            args.append(module.__file__)
        elif name is not None and arg == "co_name":
            args.append(name)
        elif arg == "co_argcount":
            args.append(getattr(code, arg) + len(add_args))
        elif arg == "co_varnames":
            co_varnames = getattr(code, arg)
            args.append(co_varnames[:code.co_argcount] + tuple(add_args) + co_varnames[code.co_argcount:])
        elif arg == "co_firstlineno":
            args.append(firstlineno if firstlineno else 1)
        else:
            args.append(getattr(code, arg))

    set_code(func, CodeType(*args))
    if name is not None:
        func.__name__ = name
    return func


def contribute_to_module(module, name, func):
    """Contribute a function to a module.

    :param module: Module to contribute to.
    :param name: Attribute name.
    :param func: Function object.

    :return: New function copy contributed to the module
    """
    name = force_encode(name)
    func = recreate_function(func, module=module)
    setattr(module, name, func)
    return func


def get_caller_module(depth=2):
    """Return the module of the caller."""
    frame = sys._getframe(depth)
    module = inspect.getmodule(frame)
    if module is None:
        raise Exception("empty module")
    return module


def get_caller_function(depth=2):
    """Return caller function."""
    return sys._getframe(depth)


def execute(code, g):
    exec(code, g)
