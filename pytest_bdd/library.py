"""Library of the step Python implementation."""

from pytest_bdd.types import GIVEN


class Library(object):
    """Library."""

    def __init__(self, request, module):
        """Library constructor.

        :param request: Pytest request object.
        :param module: Module of the current test case.
        """
        self.given = {}
        self.steps = {}

        # Collect pytest fixtures
        fm = request.session._fixturemanager
        for fixture_name, fixture_defs in fm._arg2fixturedefs.iteritems():
            faclist = list(fm._matchfactories(fixture_defs, request._parentid))
            if not faclist:
                continue

            func = faclist[-1].func
            if getattr(func, '__step_type__', None) == GIVEN:
                self.given[func.__step_name__] = fixture_name

        # Collect when and then steps
        for attr in vars(module).itervalues():
            if getattr(attr, '__step_type__', None):
                self.steps[attr.__step_name__] = attr
