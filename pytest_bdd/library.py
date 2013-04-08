"""Library of the step Python implementation."""

from pytest_bdd.types import GIVEN


class LibraryError(Exception):
    pass


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
                for name in func.__step_names__:
                    if name in self.given:
                        raise LibraryError('Step with this name already registered')
                    self.given[name] = fixture_name

        # Collect when and then steps
        for attr in vars(module).itervalues():
            if getattr(attr, '__step_type__', None):
                for name in attr.__step_names__:
                    if name in self.steps:
                        raise LibraryError('Step with this name already registered')
                    self.steps[name] = attr
