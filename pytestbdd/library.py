"""Library of the step Python implementation."""

from pytestbdd.types import GIVEN, WHEN, THEN


class Library(object):
    """Library."""

    def __init__(self, request, module):
        """Library constructor.

        :param request: Pytest request object.
        :param module: Module of the current test case.
        """
        self.given = {}
        self.when = {}
        self.then = {}

        # Collect pytest fixtures
        fm = request.session._fixturemanager
        for fixture_name, fixture_defs in fm._arg2fixturedefs.iteritems():
            func = fixture_defs[-1].func
            if getattr(func, '__step_type__', None) == GIVEN:
                self.given[func.__step_name__] = fixture_name

        # Collect when and then steps
        for attr in vars(module).itervalues():
            step_type = getattr(attr, '__step_type__', None)
            if step_type is None:
                continue
            if step_type == WHEN:
                self.when[attr.__step_name__] = attr
            elif step_type == THEN:
                self.then[attr.__step_name__] = attr
