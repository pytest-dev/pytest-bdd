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
import textwrap

from pytest_bdd import types  # pragma: no cover
from pytest_bdd import exceptions  # pragma: no cover


class FeatureError(Exception):  # pragma: no cover
    """Feature parse error."""

    message = u'{0}.\nLine number: {1}.\nLine: {2}.'

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self.message.format(*self.args)


# Global features dictionary
features = {}  # pragma: no cover


STEP_PREFIXES = [  # pragma: no cover
    ('Feature: ', types.FEATURE),
    ('Scenario Outline: ', types.SCENARIO_OUTLINE),
    ('Examples: Vertical', types.EXAMPLES_VERTICAL),
    ('Examples:', types.EXAMPLES),
    ('Scenario: ', types.SCENARIO),
    ('Given ', types.GIVEN),
    ('When ', types.WHEN),
    ('Then ', types.THEN),
    ('And ', None),  # Unknown step type
]

COMMENT_SYMBOLS = '#'  # pragma: no cover

STEP_PARAM_RE = re.compile('\<(.+?)\>')  # pragma: no cover


def get_step_type(line):
    """Detect step type by the beginning of the line.

    :param line: Line of the Feature file
    :return: SCENARIO, GIVEN, WHEN, THEN, or `None` if can't be detected.
    """
    for prefix, _type in STEP_PREFIXES:
        if line.startswith(prefix):
            return _type


def get_step_params(name):
    """Return step parameters."""
    return tuple(frozenset(STEP_PARAM_RE.findall(name)))


def strip_comments(line):
    """Remove comments.

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
    for prefix, _ in STEP_PREFIXES:
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

        self.filename = filename
        scenario = None
        mode = None
        prev_mode = None
        description = []

        with _open_file(filename, encoding) as f:
            content = force_unicode(f.read(), encoding)
            step = None
            multiline_step = False
            for line_number, line in enumerate(content.splitlines(), start=1):
                unindented_line = line.lstrip()
                line_indent = len(line) - len(unindented_line)
                if step and (step.indent < line_indent or ((not unindented_line) and multiline_step)):
                    multiline_step = True
                    # multiline step, so just add line and continue
                    step.add_line(line)
                    continue
                else:
                    step = None
                    multiline_step = False
                stripped_line = line.strip()
                clean_line = strip_comments(line)
                if not clean_line:
                    continue
                mode = get_step_type(clean_line) or mode

                if mode == types.GIVEN and prev_mode not in (types.GIVEN, types.SCENARIO, types.SCENARIO_OUTLINE):
                    raise FeatureError('Given steps must be the first in withing the Scenario',
                                       line_number, clean_line)

                if mode == types.WHEN and prev_mode not in (
                        types.SCENARIO, types.SCENARIO_OUTLINE, types.GIVEN, types.WHEN):
                    raise FeatureError('When steps must be the first or follow Given steps',
                                       line_number, clean_line)

                if mode == types.THEN and prev_mode not in (types.GIVEN, types.WHEN, types.THEN):
                    raise FeatureError('Then steps must follow Given or When steps',
                                       line_number, clean_line)

                if mode == types.FEATURE:
                    if prev_mode != types.FEATURE:
                        self.name = remove_prefix(clean_line)
                    else:
                        description.append(clean_line)

                prev_mode = mode

                # Remove Feature, Given, When, Then, And
                clean_line = remove_prefix(clean_line)
                if mode in [types.SCENARIO, types.SCENARIO_OUTLINE]:
                    self.scenarios[clean_line] = scenario = Scenario(self, clean_line)
                elif mode == types.EXAMPLES:
                    mode = types.EXAMPLES_HEADERS
                elif mode == types.EXAMPLES_VERTICAL:
                    mode = types.EXAMPLE_LINE_VERTICAL
                elif mode == types.EXAMPLES_HEADERS:
                    scenario.set_param_names([l.strip() for l in clean_line.split('|')[1:-1] if l.strip()])
                    mode = types.EXAMPLE_LINE
                elif mode == types.EXAMPLE_LINE:
                    scenario.add_example([l.strip() for l in stripped_line.split('|')[1:-1]])
                elif mode == types.EXAMPLE_LINE_VERTICAL:
                    clean_line = [l.strip() for l in stripped_line.split('|')[1:-1]]
                    scenario.add_example_row(clean_line[0], clean_line[1:])
                elif mode and mode != types.FEATURE:
                    step = scenario.add_step(
                        step_name=clean_line, step_type=mode, indent=line_indent, line_number=line_number)

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

    def __init__(self, feature, name, example_converters=None):
        self.feature = feature
        self.name = name
        self.params = set()
        self.steps = []
        self.example_params = []
        self.examples = []
        self.vertical_examples = []
        self.example_converters = example_converters

    def add_step(self, step_name, step_type, indent, line_number):
        """Add step to the scenario.

        :param step_name: Step name.
        :param step_type: Step type.

        """
        params = get_step_params(step_name)
        self.params.update(params)
        step = Step(
            name=step_name, type=step_type, params=params, scenario=self, indent=indent, line_number=line_number)
        self.steps.append(step)
        return step

    def set_param_names(self, keys):
        """Set parameter names.

        :param names: `list` of `string` parameter names

        """
        self.example_params = [str(key) for key in keys]

    def add_example(self, values):
        """Add example.

        :param values: `list` of `string` parameter values

        """
        self.examples.append(values)

    def add_example_row(self, param, values):
        """Add example row.

        :param param: `str` parameter name
        :param values: `list` of `string` parameter values

        """
        if param in self.example_params:
            raise exceptions.ScenarioExamplesNotValidError(
                """Scenario "{0}" in the feature "{1}" has not valid examples. """
                """Example rows should contain unique parameters. {2} appeared more than once.""".format(
                    self.name, self.feature.filename, param,
                )
            )
        self.example_params.append(param)
        self.vertical_examples.append(values)

    def get_params(self):
        """Get scenario pytest parametrization table."""
        param_count = len(self.example_params)
        if self.vertical_examples and not self.examples:
            for value_index in range(len(self.vertical_examples[0])):
                example = []
                for param_index in range(param_count):
                    example.append(self.vertical_examples[param_index][value_index])
                self.examples.append(example)

        if self.examples:
            params = []
            for example in self.examples:
                for index, param in enumerate(self.example_params):
                    if self.example_converters and param in self.example_converters:
                        example[index] = self.example_converters[param](example[index])
                params.append(example)
            return [self.example_params, params]
        else:
            return []

    def validate(self):
        """Validate the scenario.

        :raises: `ScenarioValidationError`

        """
        if self.params and self.example_params and self.params != set(self.example_params):
            raise exceptions.ScenarioExamplesNotValidError(
                """Scenario "{0}" in the feature "{1}" has not valid examples. """
                """Set of step parameters {2} should match set of example values {3}.""".format(
                    self.name, self.feature.filename, sorted(self.params), sorted(self.example_params),
                )
            )


class Step(object):
    """Step."""

    def __init__(self, name, type, params, scenario, indent, line_number):
        self.name = name
        self.lines = []
        self.indent = indent
        self.type = type
        self.params = params
        self.scenario = scenario
        self.line_number = line_number

    def add_line(self, line):
        """Add line to the multiple step."""
        self.lines.append(line)

    @property
    def name(self):
        return '\n'.join([self._name] + ([textwrap.dedent('\n'.join(self.lines))] if self.lines else []))

    @name.setter
    def name(self, value):
        self._name = value
