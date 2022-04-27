from __future__ import annotations

import re
import textwrap
from collections import OrderedDict
from functools import reduce
from itertools import chain, count, product, zip_longest
from operator import or_
from typing import TYPE_CHECKING, Collection, Iterator, Mapping, Match, cast
from warnings import warn

from _pytest.warning_types import PytestCollectionWarning
from attr import Factory, attrib, attrs, validate
from gherkin.parser import Parser as CucumberIOBaseParser  # type: ignore[import]
from ordered_set import OrderedSet

import pytest_bdd.steps
from pytest_bdd import const

from . import ast, exceptions
from .ast import ASTSchema
from .utils import SimpleMapping
from .warning_types import PytestBDDScenarioExamplesExtraParamsWarning, PytestBDDScenarioStepsExtraPramsWarning

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Iterable

FEATURE = "feature"
SCENARIO_OUTLINE = "scenario outline"
EXAMPLES = "examples"
EXAMPLES_VERTICAL = "examples vertical"
SCENARIO = "scenario"
BACKGROUND = "background"
EXAMPLES_HEADERS = "example headers"
EXAMPLE_LINE = "example line"
EXAMPLE_LINE_VERTICAL = "example line vertical"

GIVEN = "given"
WHEN = "when"
THEN = "then"
AND_AND = "and_and"
AND_BUT = "and_but"
AND_STAR = "and_star"
TAG = "tag"
CONTINUATION_STEP_TYPES = (AND_AND, AND_BUT, AND_STAR)
STEP_TYPES = (GIVEN, WHEN, THEN, *CONTINUATION_STEP_TYPES)


STEP_PREFIXES = {
    **const.STEP_PREFIXES,
    # Continuation of the previously mentioned step type
    AND_AND: "And ",
    AND_BUT: "But ",
    AND_STAR: "* ",
}

SPLIT_LINE_RE = re.compile(r"(?<!\\)\|")
STEP_PARAM_RE = re.compile(r"<(.+?)>")
COMMENT_RE = re.compile(r"(^|(?<=\s))#")


def split_line(line: str) -> list[str]:
    """Split the given Examples line.

    :param str|unicode line: Feature file Examples line.

    :return: List of strings.
    """
    return [cell.replace("\\|", "|").strip() for cell in SPLIT_LINE_RE.split(line)[1:-1]]


def parse_line(line: str) -> tuple[str, str]:
    """Parse step line to get the step prefix (Scenario, Given, When, Then or And) and the actual step name.

    :param line: Line of the Feature file.

    :return: `tuple` in form ("<prefix>", "<Line without the prefix>").
    """
    for _, prefix in STEP_PREFIXES.items():
        if line.startswith(prefix):
            return prefix.strip(), line[len(prefix) :].strip()
    return "", line


def strip_comments(line: str) -> str:
    """Remove comments.

    :param str line: Line of the Feature file.

    :return: Stripped line.
    """
    res = COMMENT_RE.search(line)
    if res:
        line = line[: res.start()]
    return line.strip()


def get_step_type(line: str) -> str | None:
    """Detect step type by the beginning of the line.

    :param str line: Line of the Feature file.

    :return: SCENARIO, GIVEN, WHEN, THEN, or `None` if can't be detected.
    """
    for _type, prefix in STEP_PREFIXES.items():
        if line.startswith(prefix) and _type not in CONTINUATION_STEP_TYPES:
            return _type
    return None


def get_tags(line: str | None) -> OrderedSet[str]:
    """Get tags out of the given line.

    :param str line: Feature file text line.

    :return: List of tags.
    """
    if not line or not line.strip().startswith(STEP_PREFIXES[TAG]):
        return OrderedSet()
    return OrderedSet(
        [tag.lstrip(STEP_PREFIXES[TAG]) for tag in line.strip().split(f" {STEP_PREFIXES[TAG]}") if len(tag) > 1]
    )


class GherkinParser(CucumberIOBaseParser):
    def parse(self, *args, uri=None, **kwargs):
        ast = super().parse(*args, **kwargs)
        if uri is not None:
            ast["uri"] = uri
        return {"gherkinDocument": ast}


class Parser:
    def parse(self, content, uri=None):
        feature = Feature.parse(content, uri=uri)

        feature_ast = Feature.ASTBuilder(feature).build()
        return ASTSchema().dump(feature_ast)


@attrs
class Feature:
    node_kind = "Feature"

    scenarios: OrderedDict = attrib()
    rel_filename: str = attrib()
    name: str | None = attrib()
    tags: set = attrib()
    examples = attrib()
    background: Background | None = attrib()
    line_number: int = attrib()
    description: str = attrib()
    filename: str = attrib(default=None)

    @staticmethod
    def parse(content, uri) -> Feature:
        current_node: Feature | ScenarioTemplate
        current_example_table: ExampleTable
        feature = current_node = Feature(  # type: ignore[call-arg]
            scenarios=OrderedDict(),
            rel_filename=uri,
            line_number=1,
            name=None,
            tags=set(),
            examples=Examples(),
            background=None,
            description="",
        )
        scenario: ScenarioTemplate | None = None
        mode: str | None = None
        prev_mode = None
        description: list[str] = []
        step = None
        multiline_step = False
        current_tags: OrderedSet = OrderedSet()

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
            if not clean_line and (not prev_mode or prev_mode not in FEATURE):
                continue
            mode = get_step_type(clean_line) or mode

            allowed_prev_mode: tuple[str, ...] = (BACKGROUND, GIVEN, WHEN)

            if not scenario and prev_mode not in allowed_prev_mode and mode in STEP_TYPES:
                raise exceptions.FeatureError(
                    "Step definition outside of a Scenario or a Background", line_number, clean_line, uri
                )

            allowed_prev_mode = (
                EXAMPLES,
                EXAMPLES_VERTICAL,
                EXAMPLE_LINE,
                EXAMPLE_LINE_VERTICAL,
                TAG,
                *STEP_TYPES,
                FEATURE,
            )

            if mode == TAG and prev_mode and prev_mode not in allowed_prev_mode:
                raise exceptions.FeatureError(
                    "Tag not around Feature, Scenario or Examples ", line_number, clean_line, uri
                )
            else:
                current_tags = OrderedSet(current_tags | get_tags(clean_line))

            if mode == FEATURE:
                if prev_mode is None or prev_mode == TAG:
                    _, feature.name = parse_line(clean_line)
                    feature.line_number = line_number
                    feature.tags = set(current_tags)
                    current_tags: OrderedSet = OrderedSet()  # type: ignore[no-redef]
                elif prev_mode == FEATURE:
                    description.append(clean_line)
                else:
                    raise exceptions.FeatureError(
                        "Multiple features are not allowed in a single feature file",
                        line_number,
                        clean_line,
                        uri,
                    )

            prev_mode = mode

            # Remove Feature, Given, When, Then, And
            keyword, parsed_line = parse_line(clean_line)
            if mode in [SCENARIO, SCENARIO_OUTLINE]:
                feature.scenarios[parsed_line] = scenario = current_node = ScenarioTemplate(  # type: ignore[call-arg]
                    feature=feature, name=parsed_line, line_number=line_number, tags=current_tags
                )
                current_tags = OrderedSet()
            elif mode == BACKGROUND:
                feature.background = Background(feature=feature, line_number=line_number)  # type: ignore[call-arg]
            elif mode in [EXAMPLES, EXAMPLES_VERTICAL]:
                ExampleTableBuilder: type[ExampleTable]
                if mode == EXAMPLES:
                    mode, ExampleTableBuilder = EXAMPLES_HEADERS, ExampleTableRows
                else:
                    mode, ExampleTableBuilder = EXAMPLE_LINE_VERTICAL, ExampleTableColumns  # type: ignore[no-redef]
                _, table_name = parse_line(clean_line)
                current_example_table = ExampleTableBuilder(  # type: ignore[call-arg]
                    name=table_name or None, line_number=line_number, node=current_node
                )
                current_node.examples += [current_example_table]
                current_example_table.tags = current_tags
                current_tags = OrderedSet()
            elif mode == EXAMPLES_HEADERS:
                mode = EXAMPLE_LINE
                current_example_table.example_params = [*split_line(parsed_line)]
                try:
                    validate(current_example_table)
                except exceptions.ExamplesNotValidError as exc:
                    raise exceptions.FeatureError(
                        f"{current_node.node_kind} has not valid examples. {exc.args[0]}",
                        line_number,
                        clean_line,
                        uri,
                    ) from exc
            elif mode == EXAMPLE_LINE:
                try:
                    current_example_table.examples += [[*split_line(stripped_line)]]
                    validate(current_example_table)
                except exceptions.ExamplesNotValidError as exc:
                    node_message_prefix = "Scenario" if scenario else "Feature"
                    message = f"{node_message_prefix} has not valid examples. {exc.args[0]}"
                    raise exceptions.FeatureError(message, line_number, clean_line, uri) from exc
            elif mode == EXAMPLE_LINE_VERTICAL:
                try:
                    param, *examples = split_line(stripped_line)
                except ValueError:
                    pass
                else:
                    try:
                        cast(ExampleTableColumns, current_example_table).example_params += [param]
                        current_example_table.examples_transposed += [examples]
                        validate(current_example_table)
                    except exceptions.ExamplesNotValidError as exc:
                        raise exceptions.FeatureError(
                            f"{current_node.node_kind} has not valid examples. {exc.args[0]}",
                            line_number,
                            clean_line,
                            uri,
                        ) from exc
            elif mode and mode not in (FEATURE, TAG):
                step = Step(
                    name=parsed_line, type=mode, indent=line_indent, line_number=line_number, keyword=keyword
                )  # type: ignore[call-arg]
                target: Background | ScenarioTemplate
                if feature.background and not scenario:
                    target = feature.background
                else:
                    target = cast(ScenarioTemplate, scenario)
                target.add_step(step)

        feature.description = "\n".join(description).strip()
        return feature

    @attrs
    class ASTBuilder:
        model: Feature = attrib()
        id_generator = attrib(default=Factory(count))

        def build(self):
            return ast.AST(
                gherkin_document=ast.GherkinDocument(
                    comments=[],
                    uri=self.model.rel_filename,
                ).setattrs(feature=self._build_feature()),
            )

        def _build_feature(self):
            return ast.Feature(
                children=self._build_feature_children(),
                description=self.model.description,
                language="EN",
                location=ast.Location(column=-1, line=self.model.line_number),
                tags=self._build_feature_tags(),
                name=self.model.name,
            ).setattrs(keyword="Feature")

        def _build_feature_tags(self):
            def _():
                for tag_name in self.model.tags:
                    yield ast.Tag(
                        name=tag_name,
                        identifier=next(self.id_generator),
                        location=ast.Location(column=-1, line=self.model.line_number - 1),
                    )

            return list(_())

        def _build_feature_children(self):
            return [
                ast.NodeContainerChild().setattrs(
                    scenario=ScenarioTemplate.ASTBuilder(model=scenario, id_generator=self.id_generator).build()
                )
                for scenario_name, scenario in self.model.scenarios.items()
            ]


@attrs
class ScenarioTemplate:
    """A scenario template.

    Created when parsing the feature file, it will then be combined with the examples to create a Scenario."""

    node_kind = "Scenario"

    feature: Feature = attrib()
    name = attrib()
    line_number = attrib()

    tags: OrderedSet = attrib(default=Factory(OrderedSet))
    steps_storage: list[Step] = attrib(default=Factory(list))
    examples = attrib(default=Factory(lambda *args, **kwargs: Examples(*args, **kwargs)))

    def add_step(self, step: Step) -> None:
        """Add step to the scenario.

        :param pytest_bdd.parser.Step step: Step.
        """
        step.scenario = self
        self.steps_storage.append(step)

    @property
    def steps(self) -> list[Step]:
        background = self.feature.background
        return (background.steps if background else []) + self.steps_storage

    def render(self, context: Mapping[str, Any]) -> Scenario:
        steps = [
            Step(  # type: ignore[call-arg]
                name=templated_step.render(context),
                type=templated_step.type,
                indent=templated_step.indent,
                line_number=templated_step.line_number,
                keyword=templated_step.keyword,
            )
            for templated_step in self.steps
        ]
        return Scenario(  # type: ignore[call-arg]
            feature=self.feature, name=self.name, line_number=self.line_number, steps=steps, tags=set(self.tags)
        )

    @property
    def params(self):
        return reduce(or_, map(set, (step.params for step in self.steps)), set())

    def validate(self, external_join_keys: set[str] | tuple = ()):
        """Validate the scenario.

        :raises ScenarioValidationError: when scenario is not valid
        """
        params = self.params
        united_example_rows = list(self.united_example_rows)
        example_rows_with_extra_params = [
            row for row in united_example_rows if set(row.keys()) - params - row.join_params - external_join_keys
        ]
        external_defined_step_params: set[ExampleRowUnited] = reduce(
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
    def example_table_combinations(self) -> Iterable[ExampleTableCombination]:
        example_table_combinations: Iterable
        if self.feature.examples and self.examples:
            example_table_combinations = product(self.feature.examples, self.examples)
        else:
            example_table_combinations = ([example_table] for example_table in self.feature.examples or self.examples)
        # https://github.com/python/mypy/issues/6811
        yield from map(ExampleTableCombination, example_table_combinations)  # type: ignore[arg-type]

    @property
    def united_example_rows(self) -> Iterable[ExampleRowUnited]:
        for example_table_combination in self.example_table_combinations:
            yield from example_table_combination.united_example_rows

    @attrs
    class ASTBuilder:
        model: ScenarioTemplate = attrib()
        id_generator = attrib(default=Factory(count))

        def build(self):
            return ast.Scenario(
                identifier=next(self.id_generator),
                name=self.model.name,
                examples=self._build_scenario_examples(),
                tags=self._build_scenario_tags(),
                steps=self._build_scenario_steps(),
                location=ast.Location(column=-1, line=self.model.line_number),
                keyword="Scenario",
                description="",
            )

        def _build_scenario_tags(self):
            def _():
                for tag_name in self.model.tags:
                    yield ast.Tag(
                        name=tag_name,
                        identifier=next(self.id_generator),
                        location=ast.Location(column=-1, line=self.model.line_number - 1),
                    )

            return list(_())

        def _build_scenario_examples(self):
            return [
                ExampleRowUnited.ASTBuilder(model=example_row, id_generator=self.id_generator).build()
                for example_row in self.model.united_example_rows
            ]

        def _build_scenario_steps(self):
            return [Step.ASTBuilder(model=step, id_generator=self.id_generator).build() for step in self.model.steps]


@attrs
class Scenario:

    feature: Feature = attrib()
    name: str = attrib()
    line_number: int = attrib()
    steps: list[Step] = attrib()
    tags: set | None = attrib(default=Factory(set))
    failed: bool = attrib(default=False)


@attrs
class Step:
    name: str = attrib()
    type: str = attrib()
    indent: int = attrib()
    line_number: int = attrib()
    keyword: str = attrib()

    first_name_row: str | None = attrib(default=None, init=False)
    lines: list[str] = attrib(default=Factory(list), init=False)
    failed: bool = attrib(default=False, init=False)
    scenario: ScenarioTemplate | None = attrib(default=None, init=False)
    background: Background | None = attrib(default=None, init=False)

    def add_line(self, line: str) -> None:
        """Add line to the multiple step.

        :param str line: Line of text - the continuation of the step name.
        """
        if not self.lines:
            self.first_name_row = self.name
        self.lines.append(line)
        self._update_name()

    def _update_name(self) -> None:
        """Get step name."""
        multilines_content = textwrap.dedent("\n".join(self.lines)) if self.lines else ""

        # Remove the multiline quotes, if present.
        multilines_content = re.sub(
            pattern=r'^"""\n(?P<content>.*)\n"""$',
            repl=r"\g<content>",
            string=multilines_content,
            flags=re.DOTALL,  # Needed to make the "." match also new lines
        )

        lines = ([self.first_name_row] if self.first_name_row else []) + [multilines_content]
        self.name = "\n".join(lines).strip()

    def __str__(self) -> str:
        """Full step name including the type."""
        return f'{self.type.capitalize()} "{self.name}"'

    @property
    def params(self) -> tuple[str, ...]:
        """Get step params."""
        return tuple(frozenset(STEP_PARAM_RE.findall(self.name)))

    def render(self, context: Mapping[str, Any]):
        def replacer(m: Match):
            varname = m.group(1)
            try:
                return str(context[varname])
            except KeyError:
                warn(
                    PytestCollectionWarning(f'Name "{varname}" wasn\'t found between examples and fixtures, left as is')
                )
                return f"<{varname}>"

        return STEP_PARAM_RE.sub(replacer, self.name)

    @attrs
    class ASTBuilder:
        model: Step = attrib()
        id_generator = attrib(default=Factory(count))

        def build(self):
            return ast.Step(
                identifier=next(self.id_generator),
                location=ast.Location(column=-1, line=self.model.line_number),
                keyword=self.model.keyword,
                text=self.model.name,
            ).setattrs(
                **(
                    {
                        "doc_string": ast.DocString(
                            content="\n".join(self.model.lines),
                            delimiter="\n",
                            location=ast.Location(column=-1, line=self.model.line_number + 1),
                        )
                    }
                    if self.model.lines
                    else {}
                )
            )


@attrs
class Background:
    feature: Feature = attrib()
    line_number: int = attrib()
    steps: list[Step] = attrib(default=Factory(list))

    def add_step(self, step: Step) -> None:
        """Add step to the background."""
        step.background = self
        self.steps.append(step)


class Examples(list):
    @property
    def example_params(self):
        return reduce(or_, (set(example_table.example_params) for example_table in self), set())


@attrs
class ExampleRow(SimpleMapping):
    mapping: Mapping | Iterable = attrib()
    index = attrib(kw_only=True, default=None)
    kind = attrib(kw_only=True, default=None)
    tags = attrib(default=Factory(OrderedSet), kw_only=True)
    example_table: ExampleTable = attrib(kw_only=True, default=None)

    def __attrs_post_init__(self):
        self._dict = {}
        mapping = self.mapping.items() if isinstance(self.mapping, Mapping) else self.mapping
        for key, value in mapping:
            if key == STEP_PREFIXES[TAG]:
                self.tags |= {value}
            else:
                self._dict[key] = value

    @property
    def breadcrumb(self) -> str:
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
    example_rows: list[ExampleRow] = attrib()
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
    def _combine_two_rows(row1: ExampleRow, row2: ExampleRow) -> tuple[ExampleRow | None, set | None]:
        common_param_names = set(row1.keys()) & set(row2.keys())
        if all(row1[param_name] == row2[param_name] for param_name in common_param_names):
            return (
                ExampleRow(
                    {**row1, **row2},
                    tags=OrderedSet(  # type: ignore[call-arg]
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
    class ASTBuilder:
        model: ExampleRowUnited = attrib()
        id_generator = attrib(default=Factory(count))

        def build(self):
            return ast.Example(
                identifier=next(self.id_generator),
                keyword="Examples",
                description="",
                name=self.model.breadcrumb,
                location=ast.Location(column=-1, line=-1),
                tags=self._build_example_tags(),
                table_body=self._build_table_body(),
            ).setattrs(
                table_header=self._build_table_header(),
            )

        def _build_example_tags(self):
            def _():
                for tag_name in self.model.tags:
                    yield ast.Tag(
                        name=tag_name,
                        identifier=next(self.id_generator),
                        location=ast.Location(column=-1, line=-1),
                    )

            return list(_())

        def _build_table_body(self):
            return [
                ast.TableRow(
                    identifier=next(self.id_generator),
                    location=ast.Location(column=-1, line=-1),
                    cells=[
                        ast.TableCell(location=ast.Location(column=-1, line=-1), value=cell_value)
                        for cell_value in self.model.values()
                    ],
                )
            ]

        def _build_table_header(self):
            return ast.ExampleTableHeader(
                identifier=next(self.id_generator),
                location=ast.Location(column=-1, line=-1),
                cells=[
                    ast.TableCell(location=ast.Location(column=-1, line=-1), value=cell_value)
                    for cell_value in self.model.keys()
                ],
            )


@attrs
class ExampleTable:
    examples: list
    examples_transposed: list
    kind: str
    example_params: list[str] = attrib(default=Factory(list))

    @example_params.validator  # type: ignore[attr-defined]
    def unique(self, attribute, value):
        unique_items = set()
        excluded_items = {STEP_PREFIXES[TAG]}
        for item in value:
            if item not in excluded_items and item in unique_items:
                raise exceptions.ExamplesNotValidError(
                    f"""Example rows should contain unique parameters. "{item}" appeared more than once"""
                )
            unique_items.add(item)
        return True

    line_number = attrib(default=None)
    name = attrib(default=None)
    tags = attrib(default=Factory(OrderedSet), kw_only=True)
    node: Feature | ScenarioTemplate = attrib(default=None, kw_only=True)

    def __iter__(self) -> Iterator[ExampleRow]:
        for index, example_row in enumerate(self.examples):
            assert len(self.example_params) == len(example_row)
            yield ExampleRow(zip(self.example_params, example_row), example_table=self, index=index, kind=self.kind)  # type: ignore[call-arg]

    def __bool__(self) -> bool:
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
class ExampleTableCombination(Collection):
    iterable = attrib()

    def __attrs_post_init__(self):
        self._list = list(self.iterable)

    @property
    def united_example_rows(self) -> Iterable[ExampleRowUnited]:
        def get_rows_or_build_default_row(example_table: ExampleTable):
            rows = iter(example_table)
            try:
                yield next(rows)
            except StopIteration:
                yield ExampleRow({}, example_table=example_table)  # type: ignore[call-arg]
            yield from rows

        for rows in product(*map(get_rows_or_build_default_row, self)):
            try:
                yield ExampleRowUnited(rows)  # type: ignore[call-arg]
            except ExampleRowUnited.BuildError:
                pass

    def __len__(self):
        return len(self._list)

    def __iter__(self):
        return iter(self._list)

    def __contains__(self, item):
        return item in self._list
