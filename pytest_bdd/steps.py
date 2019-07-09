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
try:
    from _pytest import fixtures as pytest_fixtures
except ImportError:
    from _pytest import python as pytest_fixtures
import six

from .feature import parse_line, force_encode
from .types import GIVEN, WHEN, THEN
from .exceptions import (
    StepError,
)
from .parsers import get_parser
from .utils import get_args


def get_step_fixture_name(name, type_, encoding=None):
    """Get step fixture name.

    :param name: unicode string
    :param type: step type
    :param encoding: encoding
    :return: step fixture name
    :rtype: string
    """
    return "pytestbdd_{type}_{name}".format(
        type=type_, name=force_encode(name, **(dict(encoding=encoding) if encoding else {})))


def given(name, fixture=None, converters=None, scope='function', target_fixture=None):
    """Given step decorator.

    :param name: Given step name.
    :param fixture: Optional name of the fixture to reuse.
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :scope: Optional fixture scope
    :param target_fixture: Target fixture name to replace by steps definition function
    :raises: StepError in case of wrong configuration.
    :note: Can't be used as a decorator when the fixture is specified.
    """
    if fixture is not None:
        module = get_caller_module()

        def step_func(request):
            return request.getfixturevalue(fixture)

        step_func.step_type = GIVEN
        step_func.converters = converters
        step_func.__name__ = force_encode(name, 'ascii')
        step_func.fixture = fixture
        func = pytest.fixture(scope=scope)(lambda: step_func)
        func.__doc__ = 'Alias for the "{0}" fixture.'.format(fixture)
        _, name = parse_line(name)
        contribute_to_module(module, get_step_fixture_name(name, GIVEN), func)
        return _not_a_fixture_decorator

    return _step_decorator(GIVEN, name, converters=converters, scope=scope, target_fixture=target_fixture)


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


def _step_decorator(step_type, step_name, converters=None, scope='function', target_fixture=None):
    """Step decorator for the type and the name.

    :param str step_type: Step type (GIVEN, WHEN or THEN).
    :param str step_name: Step name as in the feature file.
    :param dict converters: Optional step arguments converters mapping
    :param str scope: Optional step definition fixture scope
    :param target_fixture: Optional fixture name to replace by step definition

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
                func = pytest.fixture(scope=scope)(func)

            def step_func(request):
                result = request.getfixturevalue(func.__name__)
                if target_fixture:
                    inject_fixture(request, target_fixture, result)
                return result

            step_func.__doc__ = func.__doc__
            step_func.fixture = func.__name__

        step_func.__name__ = force_encode(parsed_step_name)

        def lazy_step_func():
            return step_func

        step_func.step_type = step_type
        lazy_step_func.step_type = step_type

        # Preserve the docstring
        lazy_step_func.__doc__ = func.__doc__

        step_func.parser = lazy_step_func.parser = parser_instance
        if converters:
            step_func.converters = lazy_step_func.converters = converters

        lazy_step_func = pytest.fixture(scope=scope)(lazy_step_func)
        contribute_to_module(
            module=get_caller_module(),
            name=get_step_fixture_name(parsed_step_name, step_type),
            func=lazy_step_func,
        )

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

    for arg in get_args(func):
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
        return get_caller_module(depth=depth)
    return module


def get_caller_function(depth=2):
    """Return caller function."""
    return sys._getframe(depth)


def execute(code, g):
    """Execute given code in given globals environment."""
    exec(code, g)


def inject_fixture(request, arg, value):
    """Inject fixture into pytest fixture request.

    :param request: pytest fixture request
    :param arg: argument name
    :param value: argument value
    """
    fd_kwargs = {
        'fixturemanager': request._fixturemanager,
        'baseid': None,
        'argname': arg,
        'func': lambda: value,
        'scope': "function",
        'params': None,
    }

    if 'yieldctx' in get_args(pytest_fixtures.FixtureDef.__init__):
        fd_kwargs['yieldctx'] = False

    fd = pytest_fixtures.FixtureDef(**fd_kwargs)
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
