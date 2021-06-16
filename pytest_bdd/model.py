import re
import sys
import textwrap
from collections import OrderedDict
from typing import Optional, Set, Dict, Callable, List, Union

from attr import attrs, attrib, Factory

from pytest_bdd import exceptions

if (3, 7, 2) <= sys.version_info < (3, 9, 0):
    from typing import OrderedDict as OrderedDictT
else:
    from typing import Dict as OrderedDictT

STEP_PARAM_RE = re.compile(r"<(.+?)>")


@attrs
class Examples:
    """Example table."""

    examples: List[List[str]] = attrib(init=False)

    line_number = attrib(default=None)
    name = attrib(default=None)

    _example_params: List[str] = attrib(default=Factory(list), init=False)

    @property
    def example_params(self):
        return self._example_params

    @example_params.setter
    def example_params(self, value):
        self._example_params = list(map(str, value))

    def __bool__(self):
        """Bool comparison."""
        return bool(self.examples)


class ExamplesBuilder:
    class ORIENTATION:
        COLUMNS = "columns"
        ROWS = "rows"

    @classmethod
    def build(cls, *args, orientation=ORIENTATION.COLUMNS, **kwargs):
        if orientation == cls.ORIENTATION.COLUMNS:
            return ColumnExamples(*args, **kwargs)
        elif orientation == cls.ORIENTATION.ROWS:
            return RowsExamples(*args, **kwargs)
        else:
            raise RuntimeError(f"Inappropriate orientation {orientation} was provided")


@attrs
class ColumnExamples(Examples):
    examples: List[List[str]] = attrib(default=Factory(list))

    def __add__(self, other):
        self.examples.append(other)
        return self


@attrs
class RowsExamples(Examples):
    example_rows = attrib(default=Factory(list))

    def add_example_row(self, row: List[str]):
        """Add example row.

        :param List[str] row: List, first value of which is parameter name, other - parameter values
        """
        param, values = row[0], row[1:]
        if param in self.example_params:
            raise exceptions.ExamplesNotValidError(
                f"""Example rows should contain unique parameters. "{param}" appeared more than once"""
            )
        self.example_params.append(param)
        self.example_rows.append(values)
        return self

    __add__ = add_example_row

    @property
    def examples(self):
        return list(map(list, zip(*self.example_rows)))


@attrs(eq=False)
class Feature:
    """Feature

    :param Optional[OrderedDict[str, Scenario]] scenarios: List of scenarios
    :param Optional[str] filename: Absolte filename from which feature was read
    :param Optional[str] rel_filename:
    :param Optional[str] name:
    :param Set[str] tags:
    :param Examples examples:
    :param Optional['Background'] background:
    :param Optional[int] line_number:
    :param str description:
    """

    scenarios: Optional[OrderedDictT[str, "Scenario"]] = attrib(default=Factory(OrderedDict))
    filename: Optional[str] = attrib(default=None)
    rel_filename: Optional[str] = attrib(default=None)
    name: Optional[str] = attrib(default=None)
    tags: Set[str] = attrib(default=Factory(set))
    examples: Optional[Union[ColumnExamples, RowsExamples]] = attrib(default=None)
    background: Optional["Background"] = attrib(default=None)
    line_number: Optional[int] = attrib(default=None)
    description: str = attrib(default="")


@attrs
class Scenario:
    """Scenario

    :param Feature feature: Feature by which scenario is owned
    :param str name: Scenario name.
    :param Optional[int] line_number: Parsed scenario line number.
    :param Optional[Dict[str, Callable]] example_converters: Example table parameter converters.
    :param Set[str] = attrib(default=Factory(set)) tags: Set of tags.
    """

    feature: Feature = attrib()
    name: str = attrib(default=None)
    line_number: Optional[int] = attrib(default=None)
    example_converters: Optional[Dict[str, Callable]] = attrib(default=None)
    tags: Set[str] = attrib(default=Factory(set))
    examples: Optional[Union[ColumnExamples, RowsExamples]] = attrib(default=None)
    _steps: List["Step"] = attrib(default=Factory(list))

    def add_step(self, step):
        """Add step to the scenario.

        :param pytest_bdd.parser.Step step: Step.
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
        return set(
            (self.examples.example_params if self.examples is not None else [])
            + (self.feature.examples.example_params if self.feature.examples is not None else [])
        )

    @property
    def aggregated_examples(self):
        return [e for e in [self.feature.examples, self.examples] if e is not None]

    @property
    def aggregated_tags(self):
        return self.tags.union(self.feature.tags)

    def get_examples_with_applied_converters(self, builtin=False):
        """Get scenario pytest parametrization table.

        :param builtin: bypass converters which convert values to non-built-in types
        """

        for example in self.aggregated_examples:
            if example.examples:
                params = []
                for example_data in example.examples:
                    example_data = list(example_data)
                    for index, param in enumerate(example.example_params):
                        raw_value = example_data[index]
                        if self.example_converters and param in self.example_converters:
                            value = self.example_converters[param](raw_value)
                            if not builtin or value.__class__.__module__ in {"__builtin__", "builtins"}:
                                example_data[index] = value
                    params.append(example_data)
                yield [example.example_params, params]

    def validate(self):
        """Validate the scenario.

        :raises ScenarioValidationError: when scenario is not valid
        """
        params = self.params
        example_params = self.get_example_params()
        if params and example_params and params != example_params:
            raise exceptions.ScenarioExamplesNotValidError(
                """Scenario "{}" in the feature "{}" has not valid examples. """
                """Set of step parameters {} should match set of example values {}.""".format(
                    self.name, self.feature.filename, sorted(params), sorted(example_params)
                )
            )


@attrs(eq=False)
class Step:

    """Step.
    :param str name: step name.
    :param str type: step type.
    :param int indent: step text indent.
    :param int line_number: line number.
    :param str keyword: step keyword.
    """

    _name: str = attrib()
    type: str = attrib()
    indent: int = attrib()
    line_number: int = attrib()
    keyword: str = attrib()
    lines: List[str] = attrib(
        default=Factory(list),
    )
    scenario: Optional["Scenario"] = attrib(
        default=None,
    )
    background: Optional["Background"] = attrib(
        default=None,
    )

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
        return f'{self.type.capitalize()} "{self.name}"'

    @property
    def params(self):
        """Get step params."""
        return tuple(frozenset(STEP_PARAM_RE.findall(self.name)))


@attrs
class Background:
    """Background.
    :param Feature feature: Feature.
    :param int line_number: Line number.
    """

    feature: Feature = attrib()
    line_number: int = attrib()
    steps: List["Step"] = attrib(default=Factory(list))

    def add_step(self, step):
        """Add step to the background."""
        step.background = self
        self.steps.append(step)
