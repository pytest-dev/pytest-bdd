from __future__ import annotations

import linecache
import re
from collections import OrderedDict
from functools import partial
from itertools import chain, count, filterfalse, product, zip_longest
from operator import contains, methodcaller
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable, Collection, Iterable, Iterator, Mapping, cast

from attr import Factory, attrib, attrs, validate
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser  # type: ignore[import]
from gherkin.pickles.compiler import Compiler
from ordered_set import OrderedSet

from pytest_bdd import ast, const, exceptions
from pytest_bdd.ast import ASTSchema
from pytest_bdd.exceptions import FeatureError
from pytest_bdd.model.feature import Feature as FeatureModel
from pytest_bdd.typing.parser import ParserProtocol
from pytest_bdd.utils import SimpleMapping

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
COMMENT_RE = re.compile(r"(^|(?<=\s))#")


@attrs
class GlobMixin:
    glob: Callable[..., list[str | Path]] = attrib(default=methodcaller("rglob", "*.feature"), kw_only=True)


class ASTBuilderMixin:
    def build_feature(self, gherkin_ast_data, filename: str) -> FeatureModel:
        gherkin_ast = FeatureModel.load_ast(gherkin_ast_data)

        scenarios_data = Compiler().compile(gherkin_ast_data["gherkinDocument"])
        scenarios = FeatureModel.load_scenarios(scenarios_data)

        instance = FeatureModel(  # type: ignore[call-arg]
            gherkin_ast=gherkin_ast,
            uri=gherkin_ast.gherkin_document.uri,
            scenarios=scenarios,
            filename=filename,
        )

        for scenario in scenarios:
            scenario.bind_feature(instance)

        return instance


@attrs
class GherkinParser(CucumberIOBaseParser, ASTBuilderMixin, GlobMixin, ParserProtocol):
    ast_builder = attrib(default=None)

    def __attrs_post_init__(self):
        CucumberIOBaseParser.__init__(self, ast_builder=self.ast_builder)

    def parse(self, path: Path, uri: str, *args, **kwargs) -> FeatureModel:
        encoding = kwargs.pop("encoding", "utf-8")
        with path.open(mode="r", encoding=encoding) as feature_file:
            feature_file_data = feature_file.read()
        try:
            ast_data = CucumberIOBaseParser.parse(self, token_scanner_or_str=feature_file_data, *args, **kwargs)
        except CompositeParserException as e:
            raise FeatureError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(path), e.errors[0].location["line"]).rstrip("\n"),
                uri,
            ) from e

        ast_data["uri"] = uri
        document_ast_data = {"gherkinDocument": ast_data}

        return self.build_feature(document_ast_data, filename=str(path.as_posix()))

    def get_from_paths(self, paths: list[Path], **kwargs) -> list[FeatureModel]:
        """Get features for given paths.

        :param list paths: `list` of paths (file or dirs)

        :return: `list` of `Feature` objects.
        """
        seen_names: set[Path] = set()
        features: list[FeatureModel] = []
        features_base_dir = kwargs.pop("features_base_dir", Path.cwd())
        if not features_base_dir.is_absolute():
            features_base_dir = Path.cwd() / features_base_dir

        for rel_path in map(Path, paths):
            path = rel_path if rel_path.is_absolute() else Path(features_base_dir) / rel_path

            file_paths = list(map(Path, self.glob(path))) if path.is_dir() else [Path(path)]

            features.extend(
                map(
                    lambda path: self.parse(path, str(path.relative_to(features_base_dir).as_posix()), **kwargs),
                    filterfalse(partial(contains, seen_names), file_paths),
                )
            )

            for file_path in file_paths:
                if file_path not in seen_names:
                    seen_names.add(path)

        return sorted(features, key=lambda feature: feature.name or feature.filename)


@attrs
class Parser(ASTBuilderMixin, GlobMixin, ParserProtocol):
    def parse(self, path: Path, uri: str, *args, **kwargs):
        encoding = kwargs.pop("encoding", "utf-8")
        with path.open(mode="r", encoding=encoding) as feature_file:
            feature_file_data = feature_file.read()

        gherkin_ast_data = ASTSchema().dump(
            Feature.ASTBuilder(
                model=self.parse_content(feature_file_data, uri=uri)  # type:ignore[call-arg]
            ).build()
        )

        return self.build_feature(gherkin_ast_data, filename=str(path.as_posix()))

    @classmethod
    def parse_content(cls, content, uri) -> Feature:
        current_node: Feature | Scenario
        current_example_table: ExampleTable
        feature = current_node = Feature(  # type: ignore[call-arg]
            rel_filename=uri,
        )
        scenario: Scenario | None = None
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
            clean_line = cls.strip_comments(line)
            if not clean_line and (not prev_mode or prev_mode not in FEATURE):
                continue
            mode = cls.get_step_type(clean_line) or mode

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
                current_tags = OrderedSet(current_tags | cls.get_tags(clean_line))

            if mode == FEATURE:
                if prev_mode is None or prev_mode == TAG:
                    _, feature.name = cls.parse_line(clean_line)
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
            keyword, parsed_line = cls.parse_line(clean_line)
            if mode in [SCENARIO, SCENARIO_OUTLINE]:
                feature.scenarios[parsed_line] = scenario = current_node = Scenario(  # type: ignore[call-arg]
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
                _, table_name = cls.parse_line(clean_line)
                current_example_table = ExampleTableBuilder(  # type: ignore[call-arg]
                    name=table_name or None, line_number=line_number, node=current_node
                )
                current_node.examples += [current_example_table]
                current_example_table.tags = current_tags
                current_tags = OrderedSet()
            elif mode == EXAMPLES_HEADERS:
                mode = EXAMPLE_LINE
                current_example_table.example_params = [*cls.split_line(parsed_line)]
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
                    current_example_table.examples += [[*cls.split_line(stripped_line)]]
                    validate(current_example_table)
                except exceptions.ExamplesNotValidError as exc:
                    node_message_prefix = "Scenario" if scenario else "Feature"
                    message = f"{node_message_prefix} has not valid examples. {exc.args[0]}"
                    raise exceptions.FeatureError(message, line_number, clean_line, uri) from exc
            elif mode == EXAMPLE_LINE_VERTICAL:
                try:
                    param, *examples = cls.split_line(stripped_line)
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
                target: Background | Scenario
                if feature.background and not scenario:
                    target = feature.background
                else:
                    target = cast(Scenario, scenario)
                target.add_step(step)

        feature.description = "\n".join(description).strip()
        return feature

    @staticmethod
    def split_line(line: str) -> list[str]:
        """Split the given Examples line.

        :param str|unicode line: Feature file Examples line.

        :return: List of strings.
        """
        return [cell.replace("\\|", "|").strip() for cell in SPLIT_LINE_RE.split(line)[1:-1]]

    @staticmethod
    def parse_line(line: str) -> tuple[str, str]:
        """Parse step line to get the step prefix (Scenario, Given, When, Then or And) and the actual step name.

        :param line: Line of the Feature file.

        :return: `tuple` in form ("<prefix>", "<Line without the prefix>").
        """
        for _, prefix in STEP_PREFIXES.items():
            if line.startswith(prefix):
                return prefix.strip(), line[len(prefix) :].strip()
        return "", line

    @staticmethod
    def strip_comments(line: str) -> str:
        """Remove comments.

        :param str line: Line of the Feature file.

        :return: Stripped line.
        """
        res = COMMENT_RE.search(line)
        if res:
            line = line[: res.start()]
        return line.strip()

    @staticmethod
    def get_step_type(line: str) -> str | None:
        """Detect step type by the beginning of the line.

        :param str line: Line of the Feature file.

        :return: SCENARIO, GIVEN, WHEN, THEN, or `None` if can't be detected.
        """
        for _type, prefix in STEP_PREFIXES.items():
            if line.startswith(prefix) and _type not in CONTINUATION_STEP_TYPES:
                return _type
        return None

    @staticmethod
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


@attrs
class _ASTBuilder:
    model: Any
    id_generator = attrib(default=Factory(count), kw_only=True)

    def build(self):  # pragma: no cover
        raise NotImplementedError


@attrs
class Feature:
    node_kind = "Feature"

    name: str | None = attrib(default=None)
    description: str = attrib(default="")
    filename: str = attrib(default=None)
    rel_filename: str | None = attrib(default=None)
    tags: set = attrib(default=Factory(set))
    examples: list = attrib(default=Factory(list))
    background: Background | None = attrib(default=None)
    line_number: int = attrib(default=0)
    scenarios: OrderedDict[str, Scenario] = attrib(default=Factory(OrderedDict))

    @attrs
    class ASTBuilder(_ASTBuilder):
        model: Feature = attrib()

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
                    scenario=Scenario.ASTBuilder(model=scenario, id_generator=self.id_generator).build()
                )
                for scenario_name, scenario in self.model.scenarios.items()
            ]


@attrs
class Scenario:
    node_kind = "Scenario"

    feature: Feature = attrib()
    name: str | None = attrib(default=None)
    line_number: int = attrib(default=0)

    tags: OrderedSet = attrib(default=Factory(OrderedSet))
    steps_storage: list[Step] = attrib(default=Factory(list))
    examples: list = attrib(default=Factory(list))

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
    class ASTBuilder(_ASTBuilder):
        model: Scenario = attrib()

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
class Step:
    name: str = attrib()
    type: str = attrib()
    indent: int = attrib()
    line_number: int = attrib()
    keyword: str = attrib()

    first_name_row: str | None = attrib(default=None, init=False)
    lines: list[str] = attrib(default=Factory(list), init=False)
    failed: bool = attrib(default=False, init=False)
    scenario: Scenario | None = attrib(default=None, init=False)
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
        multilines_content = dedent("\n".join(self.lines)) if self.lines else ""

        # Remove the multiline quotes, if present.
        multilines_content = re.sub(
            pattern=r'^"""\n(?P<content>.*)\n"""$',
            repl=r"\g<content>",
            string=multilines_content,
            flags=re.DOTALL,  # Needed to make the "." match also new lines
        )

        lines = ([self.first_name_row] if self.first_name_row else []) + [multilines_content]
        self.name = "\n".join(lines).strip()

    @attrs
    class ASTBuilder(_ASTBuilder):
        model: Step = attrib()

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
    class ASTBuilder(_ASTBuilder):
        model: ExampleRowUnited = attrib()

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
    node: Feature | Scenario = attrib(default=None, kw_only=True)

    def __iter__(self) -> Iterator[ExampleRow]:
        for index, example_row in enumerate(self.examples):
            assert len(self.example_params) == len(example_row)
            yield ExampleRow(zip(self.example_params, example_row), example_table=self, index=index, kind=self.kind)  # type: ignore[call-arg]


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

    def __len__(self):  # pragma: no cover
        return len(self._list)

    def __iter__(self):
        return iter(self._list)

    def __contains__(self, item):  # pragma: no cover
        return item in self._list
