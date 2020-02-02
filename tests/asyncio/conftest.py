from tests.asyncio.dummy_app import *


# TODO: remove below functions and add test to them instead
async def pytest_bdd_before_scenario(request, feature, scenario):
    print ("i'm in before scenario")


async def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    print ("i'm in before step")


async def pytest_bdd_before_step_call(request, feature, scenario, step, step_func, step_func_args):
    print ("i'm in before step call")


async def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    print ("i'm in after step")


async def pytest_bdd_after_scenario(request, feature, scenario):
    print ("i'm in after scenario")


async def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    print ("i'm in step error")


async def pytest_bdd_step_validation_error(request, feature, scenario, step, step_func, step_func_args, exception):
    print ("i'm in step validation")


async def pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception):
    print ("i'm in step func lookup error")
