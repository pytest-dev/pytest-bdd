import pytest

from pytest_bdd.utils import run_coroutines


def regular_fn():
    return 24


async def async_fn():
    return 42


@pytest.mark.parametrize(
    ["functions_to_execute", "expected_results"],
    [
        (regular_fn(), 24),
        (async_fn(), 42),
        ((regular_fn(), regular_fn(), regular_fn()), (24, 24, 24)),
        ((async_fn(), async_fn(), async_fn()), (42, 42, 42)),
        ((regular_fn(), async_fn()), (24, 42)),
    ],
    ids=["single regular fn", "single async fn", "many regular fns", "many async fns", "mixed fns"],
)
def test_run_coroutines(request, functions_to_execute, expected_results):
    if isinstance(functions_to_execute, tuple):
        actual_results = run_coroutines(*functions_to_execute, request=request)
    else:
        actual_results = run_coroutines(functions_to_execute, request=request)

    assert actual_results == expected_results
