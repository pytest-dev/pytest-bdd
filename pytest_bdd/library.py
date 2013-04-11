"""Library of the step Python implementation."""

from itertools import chain
from pytest_bdd.types import GIVEN


class LibraryError(Exception):
    pass


class Library(object):
    """Library."""

    def __init__(self, request):
        """Library constructor.

        :param request: Pytest request object.
        """
        self.given = {}
        self.steps = {}

        self._collect_given(request)
        self._collect_steps(request)

    def _collect_given(self, request):
        """Collect given steps/fixtures.

        :param request: Pytest request object.
        """
        # Collect pytest fixtures
        fm = request.session._fixturemanager
        for fixture_name, fixture_defs in fm._arg2fixturedefs.iteritems():
            faclist = list(fm._matchfactories(fixture_defs, request._parentid))
            if not faclist:
                continue

            func = faclist[-1].func
            if getattr(func, '__step_type__', None) == GIVEN:
                for name in func.__step_names__:
                    if name in self.given:
                        raise LibraryError('Step with this name already registered')
                    self.given[name] = fixture_name

    def _collect_steps(self, request):
        """Collect other steps.

        :param request: Pytest request object.
        :param module: Current test module.

        It will look into the current module and also all the plugins.
        """
        plugins = request.config.pluginmanager.getplugins()
        #import pytest; pytest.set_trace()

        for module in chain([request.module], plugins):
            for attr in vars(module).itervalues():
                step_type = getattr(attr, '__step_type__', None)

                if step_type and step_type != GIVEN:
                    for name in attr.__step_names__:
                        if name in self.steps:
                            raise LibraryError('Step with this name already registered')
                        self.steps[name] = attr
