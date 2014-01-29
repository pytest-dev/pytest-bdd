"""Feature.

The way of describing the behavior is based on Gherkin language, but a very
limited version. It doesn't support any parameter tables.
If the parametrization is needed to generate more test cases it can be done
on the fixture level of the pytest.
The <variable> syntax can be used here to make a connection between steps and
it will also validate the parameters mentioned in the steps with ones
provided in the pytest parametrization table.

Syntax example:

    Scenario: Publishing the article
        Given I'm an author user
        And I have an article
        When I go to the article page
        And I press the publish button
        Then I should not see the error message
        And the article should be published  # Note: will query the database

:note: The "#" symbol is used for comments.
:note: There're no multiline steps, the description of the step must fit in
one line.

"""
import re  # pragma: no cover
import sys  # pragma: no cover

from pytest_bdd.types import FEATURE, SCENARIO, GIVEN, WHEN, THEN  # pragma: no cover


class FeatureError(Exception):  # pragma: no cover
    """Feature parse error."""

    message = u'{0}.\nLine number: {1}.\nLine: {2}.'

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self.message.format(*self.args)


# Global features dictionary
features = {}  # pragma: no cover


STEP_PREFIXES = {  # pragma: no cover
    'Feature: ': FEATURE,
    'Scenario: ': SCENARIO,
    'Given ': GIVEN,
    'When ': WHEN,
    'Then ': THEN,
    'And ': None,  # Unknown step type
}

COMMENT_SYMBOLS = '#'  # pragma: no cover

STEP_PARAM_RE = re.compile('\<(.+?)\>')  # pragma: no cover


def get_step_type(line):
    """Detect step type by the beginning of the line.

    :param line: Line of the Feature file
    :return: SCENARIO, GIVEN, WHEN, THEN, or `None` if can't be detected.
    """
    for prefix in STEP_PREFIXES:
        if line.startswith(prefix):
            return STEP_PREFIXES[prefix]


def get_step_params(name):
    """Return step parameters."""
    params = STEP_PARAM_RE.search(name)
    if params:
        return params.groups()
    return ()


def strip(line):
    """Remove leading and trailing whitespaces and comments.

    :param line: Line of the Feature file.
    :return: Stripped line.
    """
    try:
        line = line[:line.index(COMMENT_SYMBOLS)]
    except ValueError:
        pass
    return line.strip()


def remove_prefix(line):
    """Remove the step prefix (Scenario, Given, When, Then or And).

    :param line: Line of the Feature file.

    :return: Line without the prefix.

    """
    for prefix in STEP_PREFIXES:
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return line


def _open_file(filename, encoding):
    if sys.version_info < (3, 0):
        return open(filename, 'r')
    else:
        return open(filename, 'r', encoding=encoding)


def force_unicode(string, encoding='utf-8'):
    if sys.version_info < (3, 0) and isinstance(string, str):
        return string.decode(encoding)
    else:
        return string


def force_encode(string, encoding='utf-8'):
    if sys.version_info < (3, 0):
        return string.encode(encoding)
    else:
        return string


class Feature(object):
    """Feature."""

    def __init__(self, filename, encoding='utf-8'):
        """Parse the feature file.

        :param filename: Relative path to the feature file.

        """
        self.scenarios = {}

        scenario = None
        mode = None
        prev_mode = None
        description = []

        with _open_file(filename, encoding) as f:
            content = force_unicode(f.read(), encoding)
            for line_number, line in enumerate(content.split('\n')):
                line = strip(line)
                if not line:
                    continue

                mode = get_step_type(line) or mode

                if mode == GIVEN and prev_mode not in (GIVEN, SCENARIO):
                    raise FeatureError('Given steps must be the first in withing the Scenario',
                                       line_number, line)

                if mode == WHEN and prev_mode not in (SCENARIO, GIVEN, WHEN):
                    raise FeatureError('When steps must be the first or follow Given steps',
                                       line_number, line)

                if mode == THEN and prev_mode not in (GIVEN, WHEN, THEN):
                    raise FeatureError('Then steps must follow Given or When steps',
                                       line_number, line)

                if mode == FEATURE:
                    if prev_mode != FEATURE:
                        self.name = remove_prefix(line)
                    else:
                        description.append(line)

                prev_mode = mode

                # Remove Feature, Given, When, Then, And
                line = remove_prefix(line)

                if mode == SCENARIO:
                    self.scenarios[line] = scenario = Scenario(line)
                elif mode and mode != FEATURE:
                    scenario.add_step(step_name=line, step_type=mode)

        self.description = u'\n'.join(description)

    @classmethod
    def get_feature(cls, filename, encoding='utf-8'):
        """Get a feature by the filename.

        :param filename: Filename of the feature file.

        :return: `Feature` instance from the parsed feature cache.

        :note: The features are parsed on the execution of the test and
            stored in the global variable cache to improve the performance
            when multiple scenarios are referencing the same file.

        """
        feature = features.get(filename)
        if not feature:
            feature = Feature(filename, encoding=encoding)
            features[filename] = feature
        return feature


class Scenario(object):
    """Scenario."""

    def __init__(self, name):
        self.name = name
        self.params = set()
        self.steps = []

    def add_step(self, step_name, step_type):
        """Add step to the scenario.

        :param step_name: Step name.
        :param step_type: Step type.

        """
        self.params.update(get_step_params(step_name))
        self.steps.append(Step(name=step_name, type=step_type))


class Step(object):
    """Step."""

    def __init__(self, name, type):
        self.name = name
        self.type = type
