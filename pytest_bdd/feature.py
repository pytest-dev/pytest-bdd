"""Feature.

The way of describing the behavior is based on Gherkin language, but a very
limited version. It doesn't support any parameter tables.
If the parametrization is needed to generate more test cases it can be done
on the fixture level of the pytest.
The <variable> syntax can be used here to make a connection between steps and
it will also validate the parameters mentioned in the steps with ones
provided in the pytest parametrization table.

Syntax example:

    Feature: Articles
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
import os.path
import re
import sys
import textwrap

import glob2
import six

from . import exceptions

# Global features dictionary
features = {}

STEP_PARAM_RE = re.compile(r"\<(.+?)\>")


def force_unicode(obj, encoding="utf-8"):
    """Get the unicode string out of given object (python 2 and python 3).

    :param obj: An `object`, usually a string.

    :return: unicode string.
    """
    if sys.version_info < (3, 0):
        if isinstance(obj, str):
            return obj.decode(encoding)
        else:
            return unicode(obj)
    else:  # pragma: no cover
        return str(obj)


def force_encode(string, encoding="utf-8"):
    """Force string encoding (Python compatibility function).

    :param str string: A string value.
    :param str encoding: Encoding.

    :return: Encoded string.
    """
    if sys.version_info < (3, 0):
        if isinstance(string, unicode):
            string = string.encode(encoding)
    return string


def get_tags(line):
    """Get tags out of the given line.

    :param str line: Feature file text line.

    :return: List of tags.
    """
    if not line or not line.strip().startswith("@"):
        return set()
    return set((tag.lstrip("@") for tag in line.strip().split(" @") if len(tag) > 1))


def get_feature(base_path, filename, encoding="utf-8"):
    """Get a feature by the filename.

    :param str base_path: Base feature directory.
    :param str filename: Filename of the feature file.
    :param str encoding: Feature file encoding.

    :return: `Feature` instance from the parsed feature cache.

    :note: The features are parsed on the execution of the test and
           stored in the global variable cache to improve the performance
           when multiple scenarios are referencing the same file.
    """
    from .parser import parse_feature

    full_name = os.path.abspath(os.path.join(base_path, filename))
    feature = features.get(full_name)
    if not feature:
        feature = parse_feature(base_path, filename, encoding=encoding)
        features[full_name] = feature
    return feature


def get_features(paths, **kwargs):
    """Get features for given paths.

    :param list paths: `list` of paths (file or dirs)

    :return: `list` of `Feature` objects.
    """
    seen_names = set()
    features = []
    for path in paths:
        if path not in seen_names:
            seen_names.add(path)
            if os.path.isdir(path):
                features.extend(get_features(glob2.iglob(os.path.join(path, "**", "*.feature")), **kwargs))
            else:
                base, name = os.path.split(path)
                feature = get_feature(base, name, **kwargs)
                features.append(feature)
    features.sort(key=lambda feature: feature.name or feature.filename)
    return features


class Examples(object):

    """Example table."""

    def __init__(self):
        """Initialize examples instance."""
        self.example_params = []
        self.examples = []
        self.vertical_examples = []
        self.line_number = None
        self.name = None

    def set_param_names(self, keys):
        """Set parameter names.

        :param names: `list` of `string` parameter names.
        """
        self.example_params = [str(key) for key in keys]

    def add_example(self, values):
        """Add example.

        :param values: `list` of `string` parameter values.
        """
        self.examples.append(values)

    def add_example_row(self, param, values):
        """Add example row.

        :param param: `str` parameter name
        :param values: `list` of `string` parameter values
        """
        if param in self.example_params:
            raise exceptions.ExamplesNotValidError(
                """Example rows should contain unique parameters. "{0}" appeared more than once""".format(param)
            )
        self.example_params.append(param)
        self.vertical_examples.append(values)

    def get_params(self, converters, builtin=False):
        """Get scenario pytest parametrization table.

        :param converters: `dict` of converter functions to convert parameter values
        """
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
                example = list(example)
                for index, param in enumerate(self.example_params):
                    raw_value = example[index]
                    if converters and param in converters:
                        value = converters[param](raw_value)
                        if not builtin or value.__class__.__module__ in {"__builtin__", "builtins"}:
                            example[index] = value
                params.append(example)
            return [self.example_params, params]
        else:
            return []

    def __bool__(self):
        """Bool comparison."""
        return bool(self.vertical_examples or self.examples)

    if six.PY2:
        __nonzero__ = __bool__


class Feature(object):
    """Feature."""

    def __init__(self, scenarios, filename, rel_filename, name, tags, examples, background, line_number, description):
        self.scenarios = scenarios
        self.rel_filename = rel_filename
        self.filename = filename
        self.name = name
        self.tags = tags
        self.examples = examples
        self.name = name
        self.line_number = line_number
        self.tags = tags
        self.scenarios = scenarios
        self.description = description
        self.background = background


class Scenario(object):

    """Scenario."""

    def __init__(self, feature, name, line_number, example_converters=None, tags=None):
        """Scenario constructor.

        :param pytest_bdd.feature.Feature feature: Feature.
        :param str name: Scenario name.
        :param int line_number: Scenario line number.
        :param dict example_converters: Example table parameter converters.
        :param set tags: Set of tags.
        """
        self.feature = feature
        self.name = name
        self._steps = []
        self.examples = Examples()
        self.line_number = line_number
        self.example_converters = example_converters
        self.tags = tags or set()
        self.failed = False
        self.test_function = None

    def add_step(self, step):
        """Add step to the scenario.

        :param pytest_bdd.feature.Step step: Step.
        """
        step.scenario = self
        self._steps.append(step)

    @property
    def steps(self):
        """Get scenario steps including background steps.

        :return: List of steps.
        """
        result = []
        if self.feature.background:
            result.extend(self.feature.background.steps)
        result.extend(self._steps)
        return result

    @property
    def params(self):
        """Get parameter names.

        :return: Parameter names.
        :rtype: frozenset
        """
        return frozenset(sum((list(step.params) for step in self.steps), []))

    def get_example_params(self):
        """Get example parameter names."""
        return set(self.examples.example_params + self.feature.examples.example_params)

    def get_params(self, builtin=False):
        """Get converted example params."""
        for examples in [self.feature.examples, self.examples]:
            yield examples.get_params(self.example_converters, builtin=builtin)

    def validate(self):
        """Validate the scenario.

        :raises ScenarioValidationError: when scenario is not valid
        """
        params = self.params
        example_params = self.get_example_params()
        if params and example_params and params != example_params:
            raise exceptions.ScenarioExamplesNotValidError(
                """Scenario "{0}" in the feature "{1}" has not valid examples. """
                """Set of step parameters {2} should match set of example values {3}.""".format(
                    self.name, self.feature.filename, sorted(params), sorted(example_params)
                )
            )


@six.python_2_unicode_compatible
class Step(object):

    """Step."""

    def __init__(self, name, type, indent, line_number, keyword):
        """Step constructor.

        :param str name: step name.
        :param str type: step type.
        :param int indent: step text indent.
        :param int line_number: line number.
        :param str keyword: step keyword.
        """
        self.name = name
        self.keyword = keyword
        self.lines = []
        self.indent = indent
        self.type = type
        self.line_number = line_number
        self.failed = False
        self.start = 0
        self.stop = 0
        self.scenario = None
        self.background = None

    def add_line(self, line):
        """Add line to the multiple step.

        :param str line: Line of text - the continuation of the step name.
        """
        self.lines.append(line)

    @property
    def name(self):
        """Get step name."""
        multilines_content = textwrap.dedent("\n".join(self.lines)) if self.lines else ""

        # Remove the multiline quotes, if present.
        multilines_content = re.sub(
            pattern=r'^"""\n(?P<content>.*)\n"""$',
            repl=r"\g<content>",
            string=multilines_content,
            flags=re.DOTALL,  # Needed to make the "." match also new lines
        )

        lines = [self._name] + [multilines_content]
        return "\n".join(lines).strip()

    @name.setter
    def name(self, value):
        """Set step name."""
        self._name = value

    def __str__(self):
        """Full step name including the type."""
        return '{type} "{name}"'.format(type=self.type.capitalize(), name=self.name)

    @property
    def params(self):
        """Get step params."""
        return tuple(frozenset(STEP_PARAM_RE.findall(self.name)))


class Background(object):

    """Background."""

    def __init__(self, feature, line_number):
        """Background constructor.

        :param pytest_bdd.feature.Feature feature: Feature.
        :param int line_number: Line number.
        """
        self.feature = feature
        self.line_number = line_number
        self.steps = []

    def add_step(self, step):
        """Add step to the background."""
        step.background = self
        self.steps.append(step)
