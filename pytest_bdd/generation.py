"""pytest-bdd missing test code generation."""
import os.path
import itertools
import py

from _pytest.python import getlocation
from collections import defaultdict

tw = py.io.TerminalWriter()
verbose = 1

from .feature import Feature
from .scenario import (
    _find_argumented_step_fixture_name,
    force_encode
)


def pytest_addoption(parser):
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd")
    group._addoption(
        '--generate-missing',
        action="store_true", dest="generate_missing",
        default=False,
        help="Generate missing bdd test code for given feature files")
    group._addoption(
        '--feature-file',
        action="append", dest="features",
        help="Feature file(s) to generate missing code for.")


def pytest_cmdline_main(config):
    """Check config option to show missing code."""
    if config.option.generate_missing:
        return show_missing_code(config)


def show_missing_code(config):
    """Wrap pytest session to show missing code."""
    from _pytest.main import wrap_session
    return wrap_session(config, _show_missing_code_main)


def print_missing_code(scenarios, steps):
    """Print missing code with TerminalWriter."""
    curdir = py.path.local()

    scenario = step = None

    for scenario in sorted(scenarios, key=lambda scenario: scenario.name):
        tw.line()
        tw.line(
            'Scenario is not bound to any test: "{scenario.name}" in feature "{scenario.feature.name}"'
            ' in {scenario.feature.filename}'.format(scenario=scenario), red=True)

    if scenario:
        tw.sep('-', red=True)

    for step in sorted(steps, key=lambda step: step.name):
        tw.line()
        tw.line(
            'Step is not defined: "{step.name}" in scenario: "{step.scenario.name}" in feature'
            ' "{step.scenario.feature.name}" in {step.scenario.feature.filename}'.format(step=step), red=True)

    if step:
        tw.sep('-', red=True)

    # if len(fixtures) > 1:
    #     fixtures = sorted(fixtures, key=lambda key: key[2])

    #     for baseid, module, bestrel, fixturedef in fixtures:

    #         if previous_argname != argname:
    #             tw.line()
    #             tw.sep("-", argname)
    #             previous_argname = argname

    #         if verbose <= 0 and argname[0] == "_":
    #             continue

    #         funcargspec = bestrel

    #         tw.line(funcargspec)


def _find_step_fixturedef(fixturemanager, item, name, encoding='utf-8'):
    """Find step fixturedef.

    :param request: PyTest Item object.
    :param step: `Step`.

    :return: Step function.
    """
    fixturedefs = fixturemanager.getfixturedefs(force_encode(name, encoding), item.nodeid)
    if not fixturedefs:
        name = _find_argumented_step_fixture_name(name, fixturemanager)
        if name:
            return _find_step_fixturedef(fixturemanager, item, name, encoding)
    else:
        return fixturedefs


def _show_missing_code_main(config, session):
    """Preparing fixture duplicates for output."""
    session.perform_collect()

    fm = session._fixturemanager

    features = [Feature.get_feature(*os.path.split(feature_file)) for feature_file in config.option.features]
    scenarios = list(itertools.chain.from_iterable(feature.scenarios.values() for feature in features))
    steps = list(itertools.chain.from_iterable(scenario.steps for scenario in scenarios))
    for item in session.items:
        scenario = getattr(item.obj, '__scenario__', None)
        if scenario:
            if scenario in scenarios:
                scenarios.remove(scenario)
            for step in scenario.steps:
                fixturedefs = _find_step_fixturedef(fm, item, step.name, )
                if fixturedefs:
                    try:
                        steps.remove(step)
                    except ValueError:
                        pass
            # assert fixturedefs is not None
            # if not fixturedefs:
            #     continue

            # for fixturedef in fixturedefs:
            #     loc = getlocation(fixturedef.func, curdir)

            #     fixture = (
            #         len(fixturedef.baseid),
            #         fixturedef.func.__module__,
            #         curdir.bestrelpath(loc),
            #         fixturedef
            #     )
            #     if fixture[2] not in [f[2] for f in available[argname]]:
            #         available[argname].append(fixture)
    for scenario in scenarios:
        for step in scenario.steps:
            steps.remove(step)
    print_missing_code(scenarios, steps)
    if scenarios or steps:
        session.exitstatus = 100
