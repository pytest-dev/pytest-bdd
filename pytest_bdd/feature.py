"""Feature.

The way of describing the behavior is based on Gherkin language, but a very
limited version. It doesn't support any parameter tables or any variables.
If the parametrization is needed to generate more test cases it can be done
on the fixture level of the pytest.

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

from pytest_bdd.types import SCENARIO, GIVEN, WHEN, THEN


class FeatureError(Exception):
    """Feature parse error."""
    pass


# Global features dictionary
features = {}


STEP_PREFIXES = {
    'Scenario: ': SCENARIO,
    'Given ': GIVEN,
    'When ': WHEN,
    'Then ': THEN,
    'And ': None,  # Unknown step type
}

COMMENT_SYMBOLS = '#'


def get_step_type(line):
    """Detect step type by the beginning of the line.

    :param line: Line of the Feature file
    :return: SCENARIO, GIVEN, WHEN, THEN, or `None` if can't be detected.
    """
    for prefix in STEP_PREFIXES:
        if line.startswith(prefix):
            return STEP_PREFIXES[prefix]


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


class Feature(object):
    """Feature."""

    def __init__(self, filename):
        """Parse the feature file.

        :param filename: Relative path to the feature file.
        """
        self.scenarios = {}

        scenario = None
        mode = None
        prev_mode = None

        with open(filename, 'r') as f:
            content = f.read()
            for line in content.split('\n'):
                line = strip(line)
                if not line:
                    continue

                mode = get_step_type(line) or mode

                if mode == GIVEN and prev_mode not in (GIVEN, SCENARIO):
                    raise FeatureError('Given steps must be the first in withing the Scenario')

                if mode == WHEN and prev_mode not in (SCENARIO, GIVEN, WHEN):
                    raise FeatureError('When steps must be the first or follow Given steps')

                if mode == THEN and prev_mode not in (GIVEN, WHEN, THEN):
                    raise FeatureError('Then steps must follow Given or When steps')

                prev_mode = mode

                # Remove Given, When, Then, And
                line = remove_prefix(line)

                if mode == SCENARIO:
                    self.scenarios[line] = scenario = Scenario(line)
                else:
                    scenario.add_step(line)

    @classmethod
    def get_feature(cls, filename):
        feature = features.get(filename)
        if not feature:
            feature = Feature(filename)
            features[filename] = feature
        return feature


class Scenario(object):
    """Scenario."""

    def __init__(self, name):
        self.name = name
        self.steps = []

    def add_step(self, step):
        """Add step."""
        self.steps.append(step)
