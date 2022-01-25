import os.path
import re
import textwrap
import typing
from collections import OrderedDict
from functools import reduce
from itertools import chain, product, zip_longest
from operator import or_
from warnings import warn

from _pytest.warning_types import PytestCollectionWarning
from attr import Factory, attrib, attrs, validate
from ordered_set import OrderedSet

from . import exceptions, types
from .utils import SimpleMapping
from .warning_types import PytestBDDScenarioExamplesExtraParamsWarning, PytestBDDScenarioStepsExtraPramsWarning

SPLIT_LINE_RE = re.compile(r"(?<!\\)\|")
STEP_PARAM_RE = re.compile(r"<(.+?)>")
COMMENT_RE = re.compile(r"(^|(?<=\s))#")
STEP_PREFIXES = [
    ("Feature: ", types.FEATURE),
    ("Scenario Outline: ", types.SCENARIO_OUTLINE),
    ("Examples: Vertical", types.EXAMPLES_VERTICAL),
    ("Examples:", types.EXAMPLES),
    ("Scenario: ", types.SCENARIO),
    ("Background:", types.BACKGROUND),
    ("Given ", types.GIVEN),
    ("When ", types.WHEN),
    ("Then ", types.THEN),
    ("@", types.TAG),
    # Continuation of the previously mentioned step type
    ("And ", None),
    ("But ", None),
]


def split_line(line):
    """Split the given Examples line.

    :param str|unicode line: Feature file Examples line.

    :return: List of strings.
    """
    return [cell.replace("\\|", "|").strip() for cell in SPLIT_LINE_RE.split(line)[1:-1]]


def parse_line(line):
    """Parse step line to get the step prefix (Scenario, Given, When, Then or And) and the actual step name.

    :param line: Line of the Feature file.

    :return: `tuple` in form ("<prefix>", "<Line without the prefix>").
    """
    for prefix, _ in STEP_PREFIXES:
        if line.startswith(prefix):
            return prefix.strip(), line[len(prefix) :].strip()
    return "", line


def strip_comments(line):
    """Remove comments.

    :param str line: Line of the Feature file.

    :return: Stripped line.
    """
    res = COMMENT_RE.search(line)
    if res:
        line = line[: res.start()]
    return line.strip()


def get_step_type(line):
    """Detect step type by the beginning of the line.

    :param str line: Line of the Feature file.

    :return: SCENARIO, GIVEN, WHEN, THEN, or `None` if can't be detected.
    """
    for prefix, _type in STEP_PREFIXES:
        if line.startswith(prefix):
            return _type


def parse_feature(basedir: str, filename: str, encoding: str = "utf-8") -> "Feature":
    """Parse the feature file.

    :param str basedir: Feature files base directory.
    :param str filename: Relative path to the feature file.
    :param str encoding: Feature file encoding (utf-8 by default).
    """
    abs_filename = os.path.abspath(os.path.join(basedir, filename))
    rel_filename = os.path.join(os.path.basename(basedir), filename)
    current_node: typing.Union[Feature, ScenarioTemplate]
    current_example_table: typing.Optional[ExampleTable] = None
    feature = current_node = Feature(
        scenarios=OrderedDict(),
        filename=abs_filename,
        rel_filename=rel_filename,
        line_number=1,
        name=None,
        tags=set(),
        examples=Examples(),
        background=None,
        description="",
    )
    scenario: typing.Optional[ScenarioTemplate] = None
    mode = None
    prev_mode = None
    description: typing.List[str] = []
    step = None
    multiline_step = False
    current_tags = OrderedSet()

    with open(abs_filename, encoding=encoding) as f:
        content = f.read()

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
        if not clean_line and (not prev_mode or prev_mode not in types.FEATURE):
            continue
        mode = get_step_type(clean_line) or mode

        allowed_prev_mode = (types.BACKGROUND, types.GIVEN, types.WHEN)

        if not scenario and prev_mode not in allowed_prev_mode and mode in types.STEP_TYPES:
            raise exceptions.FeatureError(
                "Step definition outside of a Scenario or a Background", line_number, clean_line, filename
            )

        allowed_prev_mode = (
            types.EXAMPLE_LINE,
            types.EXAMPLE_LINE_VERTICAL,
            types.TAG,
            *types.STEP_TYPES,
            types.FEATURE,
        )

        if mode == types.TAG and prev_mode and prev_mode not in allowed_prev_mode:
            raise exceptions.FeatureError(
                "Tag not around Feature, Scenario or Examples ", line_number, clean_line, filename
            )
        else:
            current_tags |= get_tags(clean_line)

        if mode == types.FEATURE:
            if prev_mode is None or prev_mode == types.TAG:
                _, feature.name = parse_line(clean_line)
                feature.line_number = line_number
                feature.tags = current_tags
                current_tags = OrderedSet()
            elif prev_mode == types.FEATURE:
                description.append(clean_line)
            else:
                raise exceptions.FeatureError(
                    "Multiple features are not allowed in a single feature file",
                    line_number,
                    clean_line,
                    filename,
                )

        prev_mode = mode

        # Remove Feature, Given, When, Then, And
        keyword, parsed_line = parse_line(clean_line)
        if mode in [types.SCENARIO, types.SCENARIO_OUTLINE]:
            feature.scenarios[parsed_line] = scenario = current_node = ScenarioTemplate(
                feature=feature, name=parsed_line, line_number=line_number, tags=current_tags
            )
            current_tags = OrderedSet()
        elif mode == types.BACKGROUND:
            feature.background = Background(feature=feature, line_number=line_number)
        elif mode in [types.EXAMPLES, types.EXAMPLES_VERTICAL]:
            if mode == types.EXAMPLES:
                mode, ExampleTableBuilder = types.EXAMPLES_HEADERS, ExampleTableRows
            else:
                mode, ExampleTableBuilder = types.EXAMPLE_LINE_VERTICAL, ExampleTableColumns
            _, table_name = parse_line(clean_line)
            current_example_table = ExampleTableBuilder(
                name=table_name or None, line_number=line_number, node=current_node
            )
            current_node.examples += [current_example_table]
            current_example_table.tags = current_tags
            current_tags = OrderedSet()
        elif mode == types.EXAMPLES_HEADERS:
            mode = types.EXAMPLE_LINE
            current_example_table.example_params = [l for l in split_line(parsed_line) if l]
            try:
                validate(current_example_table)
            except exceptions.ExamplesNotValidError as exc:
                raise exceptions.FeatureError(
                    f"{current_node.node_kind} has not valid examples. {exc.args[0]}", line_number, clean_line, filename
                ) from exc
        elif mode == types.EXAMPLE_LINE:
            try:
                current_example_table.examples += [[*split_line(stripped_line)]]
                validate(current_example_table)
            except exceptions.ExamplesNotValidError as exc:
                node_message_prefix = "Scenario" if scenario else "Feature"
                message = f"{node_message_prefix} has not valid examples. {exc.args[0]}"
                raise exceptions.FeatureError(message, line_number, clean_line, filename) from exc
        elif mode == types.EXAMPLE_LINE_VERTICAL:
            try:
                param, *examples = split_line(stripped_line)
            except ValueError:
                pass
            else:
                try:
                    current_example_table: ExampleTableColumns
                    current_example_table.example_params += [param]
                    current_example_table.examples_transposed += [examples]
                    validate(current_example_table)
                except exceptions.ExamplesNotValidError as exc:
                    raise exceptions.FeatureError(
                        f"{current_node.node_kind} has not valid examples. {exc.args[0]}",
                        line_number,
                        clean_line,
                        filename,
                    ) from exc
        elif mode and mode not in (types.FEATURE, types.TAG):
            step = Step(name=parsed_line, type=mode, indent=line_indent, line_number=line_number, keyword=keyword)
            if feature.background and not scenario:
                target = feature.background
            else:
                target = scenario
            target.add_step(step)

    feature.description = "\n".join(description).strip()
    return feature


class Feature:
    """Feature."""

    node_kind = "Feature"

    def __init__(self, scenarios, filename, rel_filename, name, tags, examples, background, line_number, description):
        self.scenarios: typing.Dict[str, ScenarioTemplate] = scenarios
        self.rel_filename = rel_filename
        self.filename = filename
        self.tags = tags
        self.examples = examples
        self.name = name
        self.line_number = line_number
        self.description = description
        self.background = background


class ScenarioTemplate:
    """A scenario template.

    Created when parsing the feature file, it will then be combined with the examples to create a Scenario."""

    node_kind = "Scenario"

    def __init__(self, feature: Feature, name: str, line_number: int, tags=None):
        """

        :param str name: Scenario name.
        :param int line_number: Scenario line number.
        :param OrderedSet tags: Set of tags.
        """
        self.feature = feature
        self.name = name
        self._steps: typing.List[Step] = []
        self.examples = Examples()
        self.line_number = line_number
        self.tags = tags or OrderedSet()

    def add_step(self, step):
        """Add step to the scenario.

        :param pytest_bdd.parser.Step step: Step.
        """
        step.scenario = self
        self._steps.append(step)

    @property
    def steps(self):
        background = self.feature.background
        return (background.steps if background else []) + self._steps

    def render(self, context: typing.Mapping[str, typing.Any]) -> "Scenario":
        steps = [
            Step(
                name=templated_step.render(context),
                type=templated_step.type,
                indent=templated_step.indent,
                line_number=templated_step.line_number,
                keyword=templated_step.keyword,
            )
            for templated_step in self.steps
        ]
        return Scenario(feature=self.feature, name=self.name, line_number=self.line_number, steps=steps, tags=self.tags)

    @property
    def params(self):
        return reduce(or_, map(set, (step.params for step in self.steps)), set())

    def validate(self, external_join_keys: typing.Set[str] = ()):
        """Validate the scenario.

        :raises ScenarioValidationError: when scenario is not valid
        """
        params = self.params
        united_example_rows = list(self.united_example_rows)
        example_rows_with_extra_params = [
            row for row in united_example_rows if set(row.keys()) - params - row.join_params - external_join_keys
        ]
        external_defined_step_params = reduce(
            or_,
            (
                params - set(row.keys()) - external_join_keys
                for row in united_example_rows
                if params - set(row.keys()) - external_join_keys
            ),
            set(),
        )

        if example_rows_with_extra_params:
            warn(PytestBDDScenarioExamplesExtraParamsWarning(self, example_rows_with_extra_params))

        if external_defined_step_params:
            warn(PytestBDDScenarioStepsExtraPramsWarning(self, external_defined_step_params))

    @property
    def example_table_combinations(self) -> typing.Iterable["ExampleTableCombination"]:
        if self.feature.examples and self.examples:
            example_table_combinations = product(self.feature.examples, self.examples)
        else:
            example_table_combinations = ([example_table] for example_table in self.feature.examples or self.examples)
        yield from map(ExampleTableCombination, example_table_combinations)

    @property
    def united_example_rows(self) -> typing.Iterable["ExampleRowUnited"]:
        for example_table_combination in self.example_table_combinations:
            yield from example_table_combination.united_example_rows


class Scenario:

    """Scenario."""

    def __init__(self, feature: Feature, name: str, line_number: int, steps: "typing.List[Step]", tags=None):
        """Scenario constructor.

        :param pytest_bdd.parser.Feature feature: Feature.
        :param str name: Scenario name.
        :param int line_number: Scenario line number.
        :param set tags: Set of tags.
        """
        self.feature = feature
        self.name = name
        self.steps = steps
        self.line_number = line_number
        self.tags = tags or set()
        self.failed = False


class Step:

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
        return f'{self.type.capitalize()} "{self.name}"'

    @property
    def params(self):
        """Get step params."""
        return tuple(frozenset(STEP_PARAM_RE.findall(self.name)))

    def render(self, context: typing.Mapping[str, typing.Any]):
        def replacer(m: typing.Match):
            varname = m.group(1)
            try:
                return str(context[varname])
            except KeyError:
                warn(
                    PytestCollectionWarning(f'Name "{varname}" wasn\'t found between examples and fixtures, left as is')
                )
                return f"<{varname}>"

        return STEP_PARAM_RE.sub(replacer, self.name)


class Background:

    """Background."""

    def __init__(self, feature, line_number):
        """Background constructor.

        :param pytest_bdd.parser.Feature feature: Feature.
        :param int line_number: Line number.
        """
        self.feature = feature
        self.line_number = line_number
        self.steps = []

    def add_step(self, step):
        """Add step to the background."""
        step.background = self
        self.steps.append(step)


class Examples(list):
    @property
    def example_params(self):
        return reduce(or_, (set(example_table.example_params) for example_table in self), set())


@attrs
class ExampleRow(SimpleMapping):
    mapping = attrib()
    index = attrib(kw_only=True, default=None)
    kind = attrib(kw_only=True, default=None)
    tags = attrib(default=Factory(OrderedSet), kw_only=True)
    example_table: "ExampleTable" = attrib(kw_only=True, default=None)

    def __attrs_post_init__(self):
        self._dict = dict(self.mapping)

    @property
    def breadcrumb(self):
        node = self.example_table.node
        example_table = self.example_table
        if node:
            return (
                f"[{node.node_kind}:{node.name or '[Empty]'}:line_no:{node.line_number}]>"
                f"[Examples:{example_table.name or '[Empty]'}:line_no:{example_table.line_number}]>"
                f"[{self.kind or '[Empty]'}:{self.index if self.index is not None else '[Empty]'}]"
            )
        else:
            raise AttributeError


@attrs
class ExampleRowUnited(SimpleMapping):
    example_rows: typing.List[ExampleRow] = attrib()
    join_params = attrib(default=Factory(set), kw_only=True)
    tags = attrib(default=Factory(OrderedSet), kw_only=True)

    class BuildError(ValueError):
        ...

    def __attrs_post_init__(self):
        combined_row = ExampleRow({})
        join_params = set()
        built = False
        for example_row in self.example_rows:
            combined_row, extra_join_params = self._combine_two_rows(combined_row, example_row)
            if combined_row is None:
                break
            join_params |= extra_join_params
        else:
            built = True
            self._dict = combined_row
            self.tags = combined_row.tags
            self.join_params = join_params
        if not built:
            raise self.BuildError

    @staticmethod
    def _combine_two_rows(
        row1: ExampleRow, row2: ExampleRow
    ) -> typing.Tuple[typing.Optional["ExampleRow"], typing.Optional[typing.Set]]:
        common_param_names = set(row1.keys()) & set(row2.keys())
        if all(row1[param_name] == row2[param_name] for param_name in common_param_names):
            return (
                ExampleRow(
                    {**row1, **row2},
                    tags=OrderedSet(
                        chain(
                            row1.tags,
                            *((row1.example_table.tags,) if row1.example_table is not None else ()),
                            row2.tags,
                            *((row2.example_table.tags,) if row2.example_table is not None else ()),
                        )
                    ),
                ),
                common_param_names,
            )
        else:
            return None, None

    @property
    def breadcrumb(self):
        return ">>".join(map(lambda example_row: example_row.breadcrumb, self.example_rows))


@attrs
class ExampleTable:
    """Example table."""

    examples: list
    examples_transposed: list
    kind: str
    example_params = attrib(default=Factory(list))

    @example_params.validator
    def unique(self, attribute, value):
        unique_items = set()
        for item in value:
            if item in unique_items:
                raise exceptions.ExamplesNotValidError(
                    f"""Example rows should contain unique parameters. "{item}" appeared more than once"""
                )
            unique_items.add(item)
        return True

    line_number = attrib(default=None)
    name = attrib(default=None)
    tags = attrib(default=Factory(OrderedSet), kw_only=True)
    node: typing.Union[Feature, ScenarioTemplate] = attrib(default=None, kw_only=True)

    def __iter__(self) -> typing.Iterable[ExampleRow]:
        for index, example_row in enumerate(self.examples):
            assert len(self.example_params) == len(example_row)
            yield ExampleRow(zip(self.example_params, example_row), example_table=self, index=index, kind=self.kind)

    def __bool__(self):
        """Bool comparison."""
        return bool(self.examples)


@attrs
class ExampleTableColumns(ExampleTable):
    examples_transposed = attrib(default=Factory(list))

    kind = "Column"

    @examples_transposed.validator
    def each_row_contains_same_count_of_values(self, attribute, value):
        if value:
            item_len = len(value[0])
            if not all(item_len == len(item) for item in value):
                raise exceptions.ExamplesNotValidError(
                    f"""All example columns in Examples: Vertical must have same count of values"""
                )
        return True

    @property
    def examples(self):
        return list(zip_longest(*self.examples_transposed))


@attrs
class ExampleTableRows(ExampleTable):
    examples = attrib(default=Factory(list))

    kind = "Row"

    @examples.validator
    def each_row_contains_same_count_of_values(self, attribute, value):
        if value:
            item_len = len(self.example_params)
            if not (all(item_len == len(item) for item in value) and len(value[0])):
                raise exceptions.ExamplesNotValidError(f"""All example rows must have same count of values""")
        return True


@attrs
class ExampleTableCombination(typing.Collection):
    iterable = attrib()

    def __attrs_post_init__(self):
        self._list = list(self.iterable)

    @property
    def united_example_rows(self) -> typing.Iterable[ExampleRowUnited]:
        def get_rows_or_build_default_row(example_table: ExampleTable):
            rows = iter(example_table)
            try:
                yield next(rows)
            except StopIteration:
                yield ExampleRow({}, example_table=example_table)
            yield from rows

        for rows in product(*map(get_rows_or_build_default_row, self)):
            try:
                yield ExampleRowUnited(rows)
            except ExampleRowUnited.BuildError:
                pass

    def __len__(self):
        return len(self._list)

    def __iter__(self):
        return iter(self._list)

    def __contains__(self, item):
        return item in self._list


def get_tags(line) -> typing.Set[str]:
    """Get tags out of the given line.

    :param str line: Feature file text line.

    :return: List of tags.
    """
    if not line or not line.strip().startswith("@"):
        return set()
    return {tag.lstrip("@") for tag in line.strip().split(" @") if len(tag) > 1}
