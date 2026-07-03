"""Scenario implementation.

The pytest will collect the test case and the steps will be executed
line by line.

Example:

test_publish_article = scenario(
    feature_name="publish_article.feature",
    scenario_name="Publishing the article",
)
"""

from __future__ import annotations

import contextlib
import contextvars
import inspect
import logging
import os
import re
import sys
from collections.abc import Iterable, Iterator
from inspect import signature
from typing import TYPE_CHECKING, Callable, Literal, TypeVar, cast
from weakref import WeakKeyDictionary

import pytest
from _pytest.fixtures import FixtureDef, FixtureManager, FixtureRequest, call_fixture_func
from _pytest.mark.structures import Mark

from . import exceptions
from .compat import getfixturedefs, inject_fixture
from .feature import get_feature, get_features
from .steps import StepFunctionContext, get_step_fixture_name, step_function_context_registry
from .utils import (
    CONFIG_STACK,
    get_caller_module_locals,
    get_caller_module_path,
    get_required_args,
    identity,
    registry_get_safe,
)

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet
    from _pytest.nodes import Node

    from .parser import Feature, Scenario, ScenarioTemplate, Step

T = TypeVar("T")

logger = logging.getLogger(__name__)

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")

STEP_ARGUMENT_DATATABLE = "datatable"
STEP_ARGUMENT_DOCSTRING = "docstring"
STEP_ARGUMENTS_RESERVED_NAMES = {STEP_ARGUMENT_DATATABLE, STEP_ARGUMENT_DOCSTRING}

scenario_wrapper_template_registry: WeakKeyDictionary[Callable[..., object], ScenarioTemplate] = WeakKeyDictionary()


def find_fixturedefs_for_step(step: Step, fixturemanager: FixtureManager, node: Node) -> Iterable[FixtureDef[object]]:
    """Find the fixture defs that can parse a step."""
    # happens to be that _arg2fixturedefs is changed during the iteration so we use a copy
    fixture_def_by_name = list(fixturemanager._arg2fixturedefs.items())
    for fixturename, fixturedefs in fixture_def_by_name:
        for _, fixturedef in enumerate(fixturedefs):
            step_func_context = step_function_context_registry.get(fixturedef.func)
            if step_func_context is None:
                continue

            if step_func_context.type is not None and step_func_context.type != step.type:
                continue

            match = step_func_context.parser.is_matching(step.name)
            if not match:
                continue

            fixturedefs = list(getfixturedefs(fixturemanager, fixturename, node) or [])
            if fixturedef not in fixturedefs:
                continue

            yield fixturedef


# Function copied from pytest 8.0 (removed in later versions).
def iterparentnodeids(nodeid: str) -> Iterator[str]:
    """Return the parent node IDs of a given node ID, inclusive.

    For the node ID

        "testing/code/test_excinfo.py::TestFormattedExcinfo::test_repr_source"

    the result would be

        ""
        "testing"
        "testing/code"
        "testing/code/test_excinfo.py"
        "testing/code/test_excinfo.py::TestFormattedExcinfo"
        "testing/code/test_excinfo.py::TestFormattedExcinfo::test_repr_source"

    Note that / components are only considered until the first ::.
    """
    SEP = "/"
    pos = 0
    first_colons: int | None = nodeid.find("::")
    if first_colons == -1:
        first_colons = None
    # The root Session node - always present.
    yield ""
    # Eagerly consume SEP parts until first colons.
    while True:
        at = nodeid.find(SEP, pos, first_colons)
        if at == -1:
            break
        if at > 0:
            yield nodeid[:at]
        pos = at + len(SEP)
    # Eagerly consume :: parts.
    while True:
        at = nodeid.find("::", pos)
        if at == -1:
            break
        if at > 0:
            yield nodeid[:at]
        pos = at + len("::")
    # The node ID itself.
    if nodeid:
        yield nodeid


@contextlib.contextmanager
def inject_fixturedefs_for_step(step: Step, fixturemanager: FixtureManager, node: Node) -> Iterator[None]:
    """Inject fixture definitions that can parse a step.

    We fist iterate over all the fixturedefs that can parse the step.

    Then we sort them by their "path" (list of parent IDs) so that we respect the fixture scoping rules.

    Finally, we inject them into the request.
    """
    bdd_name = get_step_fixture_name(step=step)

    fixturedefs = list(find_fixturedefs_for_step(step=step, fixturemanager=fixturemanager, node=node))

    # Sort the fixture definitions by their "path", so that the `bdd_name` fixture will
    # respect the fixture scope

    def get_fixture_path(fixture_def: FixtureDef) -> list[str]:
        return list(iterparentnodeids(fixture_def.baseid))

    fixturedefs.sort(key=lambda x: get_fixture_path(x))

    if not fixturedefs:
        yield
        return

    logger.debug("Adding providers for fixture %r: %r", bdd_name, fixturedefs)
    fixturemanager._arg2fixturedefs[bdd_name] = fixturedefs

    try:
        yield
    finally:
        del fixturemanager._arg2fixturedefs[bdd_name]


def get_step_function(request: FixtureRequest, step: Step) -> StepFunctionContext | None:
    """Get the step function (context) for the given step.

    We first figure out what's the step fixture name that we have to inject.

    Then we let `patch_argumented_step_functions` find out what step definition fixtures can parse the current step,
    and it will inject them for the step fixture name.

    Finally, we let request.getfixturevalue(...) fetch the step definition fixture.
    """
    __tracebackhide__ = True
    bdd_name = get_step_fixture_name(step=step)

    with inject_fixturedefs_for_step(step=step, fixturemanager=request._fixturemanager, node=request.node):
        try:
            return cast(StepFunctionContext, request.getfixturevalue(bdd_name))
        except pytest.FixtureLookupError:
            return None


def parse_step_arguments(step: Step, context: StepFunctionContext) -> dict[str, object]:
    """Parse step arguments."""
    parsed_args = context.parser.parse_arguments(step.name)

    assert parsed_args is not None, (
        f"Unexpected `NoneType` returned from parse_arguments(...) in parser: {context.parser!r}"
    )

    reserved_args = set(parsed_args.keys()) & STEP_ARGUMENTS_RESERVED_NAMES
    if reserved_args:
        reserved_arguments_str = ", ".join(repr(arg) for arg in reserved_args)
        raise exceptions.StepImplementationError(
            f"Step {step.name!r} defines argument names that are reserved: {reserved_arguments_str}. "
            "Please use different names."
        )

    converted_args = {key: (context.converters.get(key, identity)(value)) for key, value in parsed_args.items()}

    return converted_args


def _execute_step_function(
    request: FixtureRequest, scenario: Scenario, step: Step, context: StepFunctionContext
) -> None:
    """Execute step function."""
    __tracebackhide__ = True

    func_sig = signature(context.step_func)

    kw = {
        "request": request,
        "feature": scenario.feature,
        "scenario": scenario,
        "step": step,
        "step_func": context.step_func,
        "step_func_args": {},
    }
    request.config.hook.pytest_bdd_before_step(**kw)

    try:
        parsed_args = parse_step_arguments(step=step, context=context)

        # Filter out the arguments that are not in the function signature
        kwargs = {k: v for k, v in parsed_args.items() if k in func_sig.parameters}

        if STEP_ARGUMENT_DATATABLE in func_sig.parameters and step.datatable is not None:
            kwargs[STEP_ARGUMENT_DATATABLE] = step.datatable.raw()
        if STEP_ARGUMENT_DOCSTRING in func_sig.parameters and step.docstring is not None:
            kwargs[STEP_ARGUMENT_DOCSTRING] = step.docstring

        # Fill the missing arguments requesting the fixture values
        kwargs |= {
            arg: request.getfixturevalue(arg) for arg in get_required_args(context.step_func) if arg not in kwargs
        }

        _resolve_async_arguments(request=request, context=context, kwargs=kwargs)

        kw["step_func_args"] = kwargs

        request.config.hook.pytest_bdd_before_step_call(**kw)

        if context.is_async or context.is_async_gen:
            return_value = _execute_async_step(request=request, context=context, kwargs=kwargs)
        else:
            # Execute the step as if it was a pytest fixture using `call_fixture_func`,
            # so that we can allow "yield" statements in it
            return_value = call_fixture_func(fixturefunc=context.step_func, request=request, kwargs=kwargs)
            if inspect.isawaitable(return_value):
                return_value = _await_async_result(request=request, context=context, awaitable=return_value)
            elif inspect.isasyncgen(return_value):
                return_value = _consume_async_generator_result(request=request, context=context, async_gen=return_value)

    except Exception as exception:
        request.config.hook.pytest_bdd_step_error(exception=exception, **kw)
        raise

    if context.target_fixture is not None:
        inject_fixture(request, context.target_fixture, return_value)

    request.config.hook.pytest_bdd_after_step(**kw)


def _execute_async_step(request: FixtureRequest, context: StepFunctionContext, kwargs: dict[str, object]) -> object:
    backend, marker = _resolve_async_backend_preference(request=request, step_func=context.step_func)
    pluginmanager = request.config.pluginmanager
    errors: list[str] = []

    if backend in (None, "asyncio"):
        if _has_pytest_asyncio_plugin(pluginmanager):
            try:
                return _run_async_step_with_pytest_asyncio(
                    request=request, context=context, kwargs=kwargs, asyncio_marker=marker if backend else None
                )
            except exceptions.StepImplementationError as exc:
                errors.append(str(exc))
        elif backend == "asyncio":
            errors.append(
                "Async step is marked with pytest.mark.asyncio but pytest-asyncio is not installed or not active."
            )

    if backend in (None, "anyio"):
        if pluginmanager.has_plugin("anyio"):
            try:
                return _run_async_step_with_anyio(request=request, context=context, kwargs=kwargs)
            except exceptions.StepImplementationError as exc:
                errors.append(str(exc))
        elif backend == "anyio":
            errors.append(
                "Async step is marked with pytest.mark.anyio but the anyio pytest plugin is not installed or not active."
            )

    if not errors:
        message = "Async step functions require pytest-asyncio or the anyio pytest plugin to be installed and enabled."
    else:
        # Deduplicate messages while preserving order
        message = "\n".join(dict.fromkeys(errors))

    raise exceptions.StepImplementationError(message)


def _await_async_result(request: FixtureRequest, context: StepFunctionContext, awaitable: object) -> object:
    backend, marker = _resolve_async_backend_preference(request=request, step_func=context.step_func)
    pluginmanager = request.config.pluginmanager
    errors: list[str] = []

    if backend in (None, "asyncio") and _has_pytest_asyncio_plugin(pluginmanager):
        try:
            return _await_with_pytest_asyncio(
                request=request,
                step_func=context.step_func,
                awaitable=awaitable,
                asyncio_marker=marker if backend else None,
            )
        except exceptions.StepImplementationError as exc:
            errors.append(str(exc))
    elif backend == "asyncio":
        errors.append("Awaiting async result requires pytest-asyncio, which is not installed or active.")

    if backend in (None, "anyio") and pluginmanager.has_plugin("anyio"):
        try:
            return _await_with_anyio(request=request, awaitable=awaitable)
        except exceptions.StepImplementationError as exc:
            errors.append(str(exc))
    elif backend == "anyio":
        errors.append("Awaiting async result requires the anyio pytest plugin, which is not installed or active.")

    if not errors:
        message = "Async step result requires pytest-asyncio or the anyio pytest plugin to be installed and enabled."
    else:
        message = "\n".join(dict.fromkeys(errors))

    raise exceptions.StepImplementationError(message)


def _resolve_async_arguments(
    *, request: FixtureRequest, context: StepFunctionContext, kwargs: dict[str, object]
) -> None:
    for name, value in list(kwargs.items()):
        if inspect.isawaitable(value):
            resolved = _await_async_result(request=request, context=context, awaitable=value)
            kwargs[name] = resolved
            inject_fixture(request, name, resolved)
        elif inspect.isasyncgen(value):
            resolved = _consume_async_generator_result(request=request, context=context, async_gen=value)
            kwargs[name] = resolved
            inject_fixture(request, name, resolved)


def _resolve_async_backend_preference(
    request: FixtureRequest, step_func: Callable[..., object]
) -> tuple[Literal["asyncio", "anyio"] | None, Mark | None]:
    step_marks = _collect_callable_marks(step_func)
    step_anyio = _find_mark(step_marks, "anyio")
    step_asyncio = _find_mark(step_marks, "asyncio")

    node_anyio = _first_node_marker(request, "anyio")
    node_asyncio = _first_node_marker(request, "asyncio")

    candidates: list[tuple[Literal["asyncio", "anyio"], Mark]] = []
    if step_anyio is not None:
        candidates.append(("anyio", step_anyio))
    if step_asyncio is not None:
        candidates.append(("asyncio", step_asyncio))
    if node_anyio is not None:
        candidates.append(("anyio", node_anyio))
    if node_asyncio is not None:
        candidates.append(("asyncio", node_asyncio))

    if not candidates:
        return None, None

    backend, marker = candidates[0]
    for candidate_backend, candidate_marker in candidates[1:]:
        if candidate_backend != backend:
            raise exceptions.StepImplementationError(
                "Async step has conflicting pytest markers: both 'asyncio' and 'anyio' are present."
            )
        if marker is None and candidate_marker is not None:
            marker = candidate_marker

    return backend, marker


def _collect_callable_marks(step_func: Callable[..., object]) -> list[Mark]:
    marks = getattr(step_func, "pytestmark", [])
    if isinstance(marks, Mark):
        return [marks]
    if not isinstance(marks, (list, tuple)):
        return []
    return [mark for mark in marks if isinstance(mark, Mark)]


def _find_mark(marks: Iterable[Mark], name: str) -> Mark | None:
    for mark in marks:
        if mark.name == name:
            return mark
    return None


def _first_node_marker(request: FixtureRequest, name: str) -> Mark | None:
    try:
        return next(request.node.iter_markers(name))
    except StopIteration:
        return None


def _has_pytest_asyncio_plugin(pluginmanager: pytest.PytestPluginManager) -> bool:
    return any(
        pluginmanager.has_plugin(alias)
        for alias in ("asyncio", "pytest_asyncio", "pytest-asyncio", "pytest_asyncio.plugin")
    )


def _run_async_step_with_pytest_asyncio(
    *,
    request: FixtureRequest,
    context: StepFunctionContext,
    kwargs: dict[str, object],
    asyncio_marker: Mark | None,
) -> object:
    try:
        from pytest_asyncio.plugin import _wrap_async_fixture, _wrap_asyncgen_fixture
    except ImportError as exc:  # pragma: no cover - defensive guard when plugin missing at runtime
        raise exceptions.StepImplementationError("pytest-asyncio is not importable.") from exc

    loop_scope = _determine_asyncio_loop_scope(request=request, step_func=context.step_func, marker=asyncio_marker)
    runner_fixture_name = f"_{loop_scope}_scoped_runner"

    try:
        runner = request.getfixturevalue(runner_fixture_name)
    except pytest.FixtureLookupError as exc:
        raise exceptions.StepImplementationError(
            f"Unable to obtain '{runner_fixture_name}' fixture provided by pytest-asyncio."
        ) from exc

    fixture_function = context.step_func

    if context.is_async_gen:
        wrapped = _wrap_asyncgen_fixture(fixture_function, runner, request)
    else:
        wrapped = _wrap_async_fixture(fixture_function, runner, request)

    return wrapped(**kwargs)


def _determine_asyncio_loop_scope(
    *, request: FixtureRequest, step_func: Callable[..., object], marker: Mark | None
) -> str:
    from pytest_asyncio.plugin import _get_marked_loop_scope

    default_scope = request.config.getini("asyncio_default_fixture_loop_scope")
    if not default_scope:
        default_scope = "function"

    scope = getattr(step_func, "_loop_scope", None)

    if marker is not None:
        scope = _get_marked_loop_scope(marker, default_scope)

    if scope is None:
        scope = default_scope

    assert scope in {"function", "class", "module", "package", "session"}
    return scope


def _run_async_step_with_anyio(
    *, request: FixtureRequest, context: StepFunctionContext, kwargs: dict[str, object]
) -> object:
    try:
        import anyio.pytest_plugin as anyio_pytest_plugin
    except ImportError as exc:  # pragma: no cover - defensive guard when plugin missing at runtime
        raise exceptions.StepImplementationError("anyio is not importable.") from exc

    try:
        backend_value = request.getfixturevalue("anyio_backend")
    except pytest.FixtureLookupError as exc:
        raise exceptions.StepImplementationError(
            "Async step requested anyio backend but the 'anyio_backend' fixture is not available."
        ) from exc

    backend_name, backend_options = anyio_pytest_plugin.extract_backend_and_options(backend_value)

    func_parameters = signature(context.step_func).parameters
    if "anyio_backend" in func_parameters and "anyio_backend" not in kwargs:
        kwargs["anyio_backend"] = backend_value
    if "request" in func_parameters and "request" not in kwargs:
        kwargs["request"] = request

    with anyio_pytest_plugin.get_runner(backend_name, backend_options) as runner:
        if context.is_async_gen:
            iterator = runner.run_asyncgen_fixture(context.step_func, kwargs)
            try:
                result = next(iterator)
            except StopIteration as exc:
                raise ValueError("Async step function did not yield a value") from exc

            def finalizer() -> None:
                with contextlib.suppress(StopIteration):
                    next(iterator)

            request.addfinalizer(finalizer)
            return result

        return runner.run_fixture(context.step_func, kwargs)


def _await_with_pytest_asyncio(
    *,
    request: FixtureRequest,
    step_func: Callable[..., object],
    awaitable: object,
    asyncio_marker: Mark | None,
) -> object:
    try:
        from pytest_asyncio.plugin import _apply_contextvar_changes
    except ImportError as exc:  # pragma: no cover - defensive guard
        raise exceptions.StepImplementationError("pytest-asyncio is not importable.") from exc

    loop_scope = _determine_asyncio_loop_scope(request=request, step_func=step_func, marker=asyncio_marker)
    runner_fixture_name = f"_{loop_scope}_scoped_runner"

    try:
        runner = request.getfixturevalue(runner_fixture_name)
    except pytest.FixtureLookupError as exc:
        raise exceptions.StepImplementationError(
            f"Unable to obtain '{runner_fixture_name}' fixture provided by pytest-asyncio."
        ) from exc

    if not hasattr(runner, "run"):
        raise exceptions.StepImplementationError("Unsupported pytest-asyncio runner implementation encountered.")

    ctx = contextvars.copy_context()
    result = runner.run(awaitable, context=ctx)
    reset = _apply_contextvar_changes(ctx)
    if reset is not None:
        request.addfinalizer(reset)
    return result


def _await_with_anyio(*, request: FixtureRequest, awaitable: object) -> object:
    try:
        import anyio.pytest_plugin as anyio_pytest_plugin
    except ImportError as exc:  # pragma: no cover - defensive guard
        raise exceptions.StepImplementationError("anyio is not importable.") from exc

    try:
        backend_value = request.getfixturevalue("anyio_backend")
    except pytest.FixtureLookupError as exc:
        raise exceptions.StepImplementationError(
            "Async step requested anyio backend but the 'anyio_backend' fixture is not available."
        ) from exc

    backend_name, backend_options = anyio_pytest_plugin.extract_backend_and_options(backend_value)

    async def _consume() -> object:
        return await awaitable  # type: ignore[arg-type]

    with anyio_pytest_plugin.get_runner(backend_name, backend_options) as runner:
        return runner.run_fixture(_consume, {})


def _consume_async_generator_result(request: FixtureRequest, context: StepFunctionContext, async_gen: object) -> object:
    backend, marker = _resolve_async_backend_preference(request=request, step_func=context.step_func)
    pluginmanager = request.config.pluginmanager
    errors: list[str] = []

    if backend in (None, "asyncio") and _has_pytest_asyncio_plugin(pluginmanager):
        try:
            return _consume_async_gen_with_pytest_asyncio(
                request=request,
                context=context,
                async_gen=async_gen,
                asyncio_marker=marker if backend else None,
            )
        except exceptions.StepImplementationError as exc:
            errors.append(str(exc))
    elif backend == "asyncio":
        errors.append("Async generator step requires pytest-asyncio, which is not installed or not active.")

    if backend in (None, "anyio") and pluginmanager.has_plugin("anyio"):
        try:
            return _consume_async_gen_with_anyio(request=request, async_gen=async_gen)
        except exceptions.StepImplementationError as exc:
            errors.append(str(exc))
    elif backend == "anyio":
        errors.append("Async generator step requires the anyio pytest plugin, which is not installed or not active.")

    if not errors:
        message = "Async generator steps require pytest-asyncio or the anyio pytest plugin to be installed and enabled."
    else:
        message = "\n".join(dict.fromkeys(errors))

    raise exceptions.StepImplementationError(message)


def _consume_async_gen_with_pytest_asyncio(
    *,
    request: FixtureRequest,
    context: StepFunctionContext,
    async_gen: object,
    asyncio_marker: Mark | None,
) -> object:
    try:
        from pytest_asyncio.plugin import _wrap_asyncgen_fixture
    except ImportError as exc:  # pragma: no cover - defensive guard
        raise exceptions.StepImplementationError("pytest-asyncio is not importable.") from exc

    loop_scope = _determine_asyncio_loop_scope(request=request, step_func=context.step_func, marker=asyncio_marker)
    runner_fixture_name = f"_{loop_scope}_scoped_runner"

    try:
        runner = request.getfixturevalue(runner_fixture_name)
    except pytest.FixtureLookupError as exc:
        raise exceptions.StepImplementationError(
            f"Unable to obtain '{runner_fixture_name}' fixture provided by pytest-asyncio."
        ) from exc

    def _factory() -> object:
        async def _proxy() -> object:
            async for item in async_gen:  # type: ignore[async-for]
                yield item

        return _proxy()

    wrapped = _wrap_asyncgen_fixture(_factory, runner, request)
    return wrapped()


def _consume_async_gen_with_anyio(*, request: FixtureRequest, async_gen: object) -> object:
    try:
        import anyio.pytest_plugin as anyio_pytest_plugin
    except ImportError as exc:  # pragma: no cover - defensive guard
        raise exceptions.StepImplementationError("anyio is not importable.") from exc

    try:
        backend_value = request.getfixturevalue("anyio_backend")
    except pytest.FixtureLookupError as exc:
        raise exceptions.StepImplementationError(
            "Async generator step requested anyio backend but the 'anyio_backend' fixture is not available."
        ) from exc

    backend_name, backend_options = anyio_pytest_plugin.extract_backend_and_options(backend_value)

    async def _proxy() -> object:
        async for item in async_gen:  # type: ignore[async-for]
            yield item

    runner_cm = anyio_pytest_plugin.get_runner(backend_name, backend_options)
    runner = runner_cm.__enter__()

    iterator = runner.run_asyncgen_fixture(lambda: _proxy(), {})
    try:
        result = next(iterator)
    except StopIteration as exc:
        runner_cm.__exit__(None, None, None)
        raise ValueError("Async generator step function did not yield a value") from exc
    except Exception:
        runner_cm.__exit__(*sys.exc_info())
        raise

    def finalizer() -> None:
        try:
            with contextlib.suppress(StopAsyncIteration, StopIteration):
                next(iterator)
        finally:
            runner_cm.__exit__(None, None, None)

    request.addfinalizer(finalizer)
    return result


def _execute_scenario(feature: Feature, scenario: Scenario, request: FixtureRequest) -> None:
    """Execute the scenario.

    :param feature: Feature.
    :param scenario: Scenario.
    :param request: request.
    """
    __tracebackhide__ = True
    request.config.hook.pytest_bdd_before_scenario(request=request, feature=feature, scenario=scenario)

    try:
        for step in scenario.steps:
            step_func_context = get_step_function(request=request, step=step)
            if step_func_context is None:
                exc = exceptions.StepDefinitionNotFoundError(
                    f"Step definition is not found: {step}. "
                    f'Line {step.line_number} in scenario "{scenario.name}" in the feature "{scenario.feature.filename}"'
                )
                request.config.hook.pytest_bdd_step_func_lookup_error(
                    request=request, feature=feature, scenario=scenario, step=step, exception=exc
                )
                raise exc
            _execute_step_function(request, scenario, step, step_func_context)
    finally:
        request.config.hook.pytest_bdd_after_scenario(request=request, feature=feature, scenario=scenario)


def _get_scenario_decorator(
    feature: Feature, feature_name: str, templated_scenario: ScenarioTemplate, scenario_name: str
) -> Callable[[Callable[..., T]], Callable[[FixtureRequest, dict[str, str]], T]]:
    # HACK: Ideally we would use `def decorator(fn)`, but we want to return a custom exception
    # when the decorator is misused.
    # Pytest inspect the signature to determine the required fixtures, and in that case it would look
    # for a fixture called "fn" that doesn't exist (if it exists then it's even worse).
    # It will error with a "fixture 'fn' not found" message instead.
    # We can avoid this hack by using a pytest hook and check for misuse instead.
    def decorator(*args: Callable[..., T]) -> Callable[[FixtureRequest, dict[str, str]], T]:
        if not args:
            raise exceptions.ScenarioIsDecoratorOnly(
                "scenario function can only be used as a decorator. Refer to the documentation."
            )
        [fn] = args
        func_args = get_required_args(fn)

        def scenario_wrapper(request: FixtureRequest, _pytest_bdd_example: dict[str, str]) -> T:
            __tracebackhide__ = True
            scenario = templated_scenario.render(_pytest_bdd_example)
            _execute_scenario(feature, scenario, request)
            fixture_values = [request.getfixturevalue(arg) for arg in func_args]
            return fn(*fixture_values)

        if func_args:
            # We need to tell pytest that the original function requires its fixtures,
            # otherwise indirect fixtures would not work.
            scenario_wrapper = pytest.mark.usefixtures(*func_args)(scenario_wrapper)

        example_parametrizations = collect_example_parametrizations(templated_scenario)
        if example_parametrizations is not None:
            # Parametrize the scenario outlines
            scenario_wrapper = pytest.mark.parametrize(
                "_pytest_bdd_example",
                example_parametrizations,
            )(scenario_wrapper)

        rule_tags = set() if templated_scenario.rule is None else templated_scenario.rule.tags
        for tag in templated_scenario.tags | feature.tags | rule_tags:
            config = CONFIG_STACK[-1]
            config.hook.pytest_bdd_apply_tag(tag=tag, function=scenario_wrapper)

        scenario_wrapper.__doc__ = f"{feature_name}: {scenario_name}"

        scenario_wrapper_template_registry[scenario_wrapper] = templated_scenario
        return scenario_wrapper

    return decorator


def collect_example_parametrizations(
    templated_scenario: ScenarioTemplate,
) -> list[ParameterSet] | None:
    parametrizations = []

    for examples in templated_scenario.examples:
        tags: set = examples.tags or set()

        example_marks = [getattr(pytest.mark, tag) for tag in tags]

        for context in examples.as_contexts():
            param_id = "-".join(context.values())
            parametrizations.append(
                pytest.param(
                    context,
                    id=param_id,
                    marks=example_marks,
                ),
            )

    return parametrizations or None


def scenario(
    feature_name: str,
    scenario_name: str,
    encoding: str = "utf-8",
    features_base_dir: str | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Scenario decorator.

    :param str feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param str scenario_name: Scenario name.
    :param str encoding: Feature file encoding.
    :param features_base_dir: Optional base dir location for locating feature files. If not set, it will try and resolve using property set in .ini file, then the caller_module_path.
    """
    __tracebackhide__ = True
    scenario_name = scenario_name
    caller_module_path = get_caller_module_path()

    # Get the feature
    if features_base_dir is None:
        features_base_dir = get_features_base_dir(caller_module_path)
    feature = get_feature(features_base_dir, feature_name, encoding=encoding)

    # Get the scenario
    try:
        scenario = feature.scenarios[scenario_name]
    except KeyError:
        feature_name = feature.name or "[Empty]"
        raise exceptions.ScenarioNotFound(
            f'Scenario "{scenario_name}" in feature "{feature_name}" in {feature.filename} is not found.'
        ) from None

    return _get_scenario_decorator(
        feature=feature, feature_name=feature_name, templated_scenario=scenario, scenario_name=scenario_name
    )


def get_features_base_dir(caller_module_path: str) -> str:
    d = get_from_ini("bdd_features_base_dir")
    if d is None:
        return os.path.dirname(caller_module_path)
    rootdir = CONFIG_STACK[-1].rootpath
    return os.path.join(rootdir, d)


def get_from_ini(key: str, default: str | None = None) -> str | None:
    """Get value from ini config. Return default if value has not been set.

    Use if the default value is dynamic. Otherwise, set default on addini call.
    """
    config = CONFIG_STACK[-1]
    value = config.getini(key)
    if not isinstance(value, str):
        raise TypeError(f"Expected a string for configuration option {value!r}, got a {type(value)} instead")
    return value if value != "" else default


def make_python_name(string: str) -> str:
    """Make python attribute name out of a given string."""
    string = re.sub(PYTHON_REPLACE_REGEX, "", string.replace(" ", "_"))
    return re.sub(ALPHA_REGEX, "", string).lower()


def make_python_docstring(string: str) -> str:
    """Make a python docstring literal out of a given string."""
    return '"""{}."""'.format(string.replace('"""', '\\"\\"\\"'))


def make_string_literal(string: str) -> str:
    """Make python string literal out of a given string."""
    return "'{}'".format(string.replace("'", "\\'"))


def get_python_name_generator(name: str) -> Iterable[str]:
    """Generate a sequence of suitable python names out of given arbitrary string name."""
    python_name = make_python_name(name)
    suffix = ""
    index = 0

    def get_name() -> str:
        return f"test_{python_name}{suffix}"

    while True:
        yield get_name()
        index += 1
        suffix = f"_{index}"


def scenarios(*feature_paths: str, encoding: str = "utf-8", features_base_dir: str | None = None) -> None:
    caller_locals = get_caller_module_locals()
    """Parse features from the paths and put all found scenarios in the caller module.

    :param *feature_paths: feature file paths to use for scenarios
    :param str encoding: Feature file encoding.
    :param features_base_dir: Optional base dir location for locating feature files. If not set, it will try and
      resolve using property set in .ini file, otherwise it is assumed to be relative from the caller path location.
    """
    caller_path = get_caller_module_path()

    if features_base_dir is None:
        features_base_dir = get_features_base_dir(caller_path)

    abs_feature_paths = []
    for path in feature_paths:
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(features_base_dir, path))
        abs_feature_paths.append(path)
    found = False

    module_scenarios = frozenset(
        (s.feature.filename, s.name)
        for name, attr in caller_locals.items()
        if (s := registry_get_safe(scenario_wrapper_template_registry, attr)) is not None
    )

    for feature in get_features(abs_feature_paths):
        for scenario_name, scenario_object in feature.scenarios.items():
            # skip already bound scenarios
            if (scenario_object.feature.filename, scenario_name) not in module_scenarios:

                @scenario(feature.filename, scenario_name, encoding=encoding, features_base_dir=features_base_dir)
                def _scenario() -> None:
                    pass  # pragma: no cover

                for test_name in get_python_name_generator(scenario_name):
                    if test_name not in caller_locals:
                        # found a unique test name
                        caller_locals[test_name] = _scenario
                        break
            found = True
    if not found:
        raise exceptions.NoScenariosFound(abs_feature_paths)
