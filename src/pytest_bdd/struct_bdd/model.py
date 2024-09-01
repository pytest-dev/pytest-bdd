from collections import defaultdict, namedtuple
from enum import Enum
from functools import partial
from inspect import getfile
from itertools import chain, product, starmap
from operator import attrgetter, eq, is_not
from pathlib import Path
from typing import Any, ClassVar, List, Literal, Mapping, Optional, Sequence, Type, Union

from attr import attrib, attrs
from pydantic import (  # type:ignore[attr-defined] # migration to pydantic 2
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)

from messages import KeywordType, MediaType, Source  # type:ignore[attr-defined]
from pytest_bdd.compatibility.typing import Annotated, Self
from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.scenario_locator import ScenarioLocatorFilterMixin
from pytest_bdd.utils import deepattrgetter

# mypy: disable-error-code="typeddict-unknown-key, typeddict-item"


class Keyword(Enum):
    Given = "Given"
    When = "When"
    Then = "Then"
    And = "And"
    But = "But"
    Star = "*"


class SubKeyword(Enum):
    Step = "Step"
    Alternative = "Alternative"


KEYWORD_TO_TYPE: Mapping[Union[Keyword, str, None], KeywordType] = defaultdict(
    lambda: KeywordType.unknown,
    [
        (Keyword.Given, KeywordType.context),
        (Keyword.When, KeywordType.action),
        (Keyword.Then, KeywordType.outcome),
        (Keyword.And, KeywordType.conjunction),
        (Keyword.But, KeywordType.conjunction),
        (Keyword.Star, KeywordType.unknown),
        (None, KeywordType.unknown),
    ],
)


class Node(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    tags: Optional[Sequence[str]] = Field(default_factory=list, alias="Tags")
    name: Optional[str] = Field(None, alias="Name")
    description: Optional[str] = Field(None, alias="Description")
    comments: Optional[Sequence[str]] = Field(default_factory=list, alias="Comments")


class Table(Node):
    type: Optional[Literal["Rowed", "Columned"]] = Field("Rowed", alias="Type")
    parameters: Optional[Sequence[str]] = Field(default_factory=list, alias="Parameters")
    values: Optional[Sequence[Sequence[Any]]] = Field(default_factory=list, alias="Values")

    @property
    def columned_values(self):
        return self.values if self.type == "Columned" else list(zip(*self.values))

    @property
    def rowed_values(self):
        return self.values if self.type == "Rowed" else list(zip(*self.values))


class SubTable(Node):
    sub_table: Table = Field(..., alias="Table")


@AfterValidator
def convert_sub_tables_to_tables(value):
    return value.sub_table if isinstance(value, SubTable) else value


class Join(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    tables: List[Annotated[Union[Table, "Join", SubTable], convert_sub_tables_to_tables]] = Field(
        default_factory=list, alias="Join"
    )

    __hash__ = id

    @property
    def tags(self):
        return list(dict.fromkeys(chain.from_iterable(map(attrgetter("tags"), self.tables))))

    @property
    def name(self):
        return "\n".join(filter(partial(is_not, None), list(chain(map(attrgetter("name"), self.tables)))))

    @property
    def description(self):
        return "\n".join(
            filter(
                partial(is_not, None),
                chain.from_iterable(map(deepattrgetter("description", skip_missing=True), self.tables)),
            )
        )

    @property
    def comments(self):
        return list(chain.from_iterable(map(attrgetter("comments"), self.tables)))

    @property
    def parameters(self):
        return list(dict.fromkeys(chain.from_iterable(map(attrgetter("parameters"), self.tables))))

    @property
    def type(self):
        return "Rowed"

    @property
    def values(self):
        def _():
            filled_tables = list(filter(attrgetter("parameters"), self.tables))
            if filled_tables:
                filled_tables_parameters = list(chain.from_iterable(map(attrgetter("parameters"), self.tables)))
                for filled_tables_values in map(
                    lambda tables_values: list(chain.from_iterable(tables_values)),
                    product(*map(attrgetter("rowed_values"), filled_tables)),
                ):
                    if all(
                        [
                            all(
                                starmap(
                                    eq,
                                    product(
                                        [
                                            value
                                            for _parameter, value in zip(filled_tables_parameters, filled_tables_values)
                                            if parameter == _parameter
                                        ],
                                        repeat=2,
                                    ),
                                )
                            )
                            for parameter in self.parameters
                        ]
                    ):

                        def values_gen():
                            for parameter in self.parameters:
                                for _parameter, value in zip(filled_tables_parameters, filled_tables_values):
                                    if parameter == _parameter:
                                        yield value
                                        break

                        values = list(values_gen())
                        yield values
            else:
                yield from map(
                    lambda values_combination: list(chain.from_iterable(values_combination)),
                    product(*map(attrgetter("rowed_values"), self.tables)),
                )

        _values = list(_())
        return _values

    @property
    def columned_values(self):
        return list(zip(*self.values))

    @property
    def rowed_values(self):
        return self.values


@BeforeValidator
def before_convert_to_step(value):
    if isinstance(value, str):
        return Step(action=value)
    elif isinstance(value, dict) and len(value) == 1 and next(iter(value)) not in SubKeyword.__members__:
        return Step(type=next(iter(value.keys())), action=next(iter(value.values())))
    else:
        return value


@AfterValidator
def select_step_keyword_type(value):
    try:
        return Keyword(value)
    except ValueError:
        return value


@AfterValidator
def after_convert_sub_steps_to_steps(value):
    return value.sub_step if isinstance(value, SubStep) else value


StepKeywordType = Union[Keyword, Annotated[str, select_step_keyword_type]]


class StepPrototype(Node):
    steps: Sequence[
        Annotated[
            Annotated[Union["SubStep", "Alternative", "StepPrototype"], before_convert_to_step],
            after_convert_sub_steps_to_steps,
        ]
    ] = Field(default_factory=list, alias="Steps")

    type: Optional[StepKeywordType] = Field(default=Keyword.Star, alias="Type")
    data: List[Annotated[Union[Table, Join, SubTable], convert_sub_tables_to_tables]] = Field(
        default_factory=list, alias="Data"
    )
    examples: List[Annotated[Union[Table, Join, SubTable], convert_sub_tables_to_tables]] = Field(
        default_factory=list, alias="Examples"
    )
    keyword_type: Optional[KeywordType] = Field(KeywordType.unknown)

    Route: ClassVar[Type] = namedtuple("Route", ["tags", "steps", "example_table"])

    @model_validator(mode="after")  # type: ignore[misc] # migration to pydantic 2
    def set_keyword_type(self) -> Self:
        self.keyword_type = KEYWORD_TO_TYPE[self.type]
        return self  # type: ignore[return-value] # migration to pydantic 2

    @property
    def routes(self):
        for routes in (
            product(*map(attrgetter("routes"), self.steps))
            if self.steps
            else [[self.Route([], [], Table(parameters=[], values=[]))]]
        ):
            steps = [self, *chain.from_iterable(map(attrgetter("steps"), routes))]

            if self.examples:
                for _example_table in self.examples:
                    example_table = Join(tables=[*map(attrgetter("example_table"), routes), _example_table])
                    tags = list(
                        {*chain.from_iterable(map(attrgetter("tags"), routes)), *example_table.tags, *self.tags}
                    )

                    yield self.Route(
                        tags,
                        steps,
                        example_table,
                    )
            else:
                example_table = Join(tables=[*map(attrgetter("example_table"), routes)])
                tags = list({*chain.from_iterable(map(attrgetter("tags"), routes)), *example_table.tags, *self.tags})

                yield self.Route(
                    tags,
                    steps,
                    example_table,
                )

    @classmethod
    def build_by_action(cls, action, *args, **kwargs):
        return cls(*args, **kwargs, action=action)

    @attrs
    class Locator(ScenarioLocatorFilterMixin):
        step: "StepPrototype" = attrib()
        filename = attrib()
        uri = attrib()
        mimetype = attrib()

        def resolve_features(self, config):
            from pytest_bdd.struct_bdd.model_builder import GherkinDocumentBuilder

            feature = GherkinDocumentBuilder(self.step).build_feature(
                filename=self.filename, uri=self.uri, id_generator=config.pytest_bdd_id_generator
            )

            if isinstance(self.mimetype, MediaType):
                media_type = self.mimetype
            elif isinstance(self.mimetype, Mimetype):
                media_type = self.mimetype.value
            else:
                media_type = str(self.mimetype)
            try:
                feature_source = Source(uri=self.uri, data=Path(self.filename).read_text(), media_type=media_type)
                yield feature, feature_source
            except ValidationError:
                # Workaround because of https://github.com/cucumber/messages/issues/161
                yield feature, None

    def as_test(self, filename):
        from pytest_bdd.scenario import scenarios

        return scenarios(
            locators=[
                self.Locator(
                    self,
                    str(Path(filename).as_posix()),
                    str(Path(filename).relative_to(Path.cwd())),
                    mimetype=Mimetype.python,
                )
            ],
            return_test_decorator=False,
        )

    def as_test_decorator(self, filename):
        from pytest_bdd.scenario import scenarios

        return scenarios(
            locators=[
                self.Locator(
                    self,
                    str(Path(filename).as_posix()),
                    str(Path(filename).relative_to(Path.cwd())),
                    mimetype=Mimetype.python,
                )
            ],
            return_test_decorator=True,
        )

    def __call__(self, func):
        return self.as_test_decorator(getfile(func))(func)


class Alternative(Node):
    steps: Sequence[
        Annotated[
            Annotated[Union["SubStep", "Alternative", "StepPrototype"], before_convert_to_step],
            after_convert_sub_steps_to_steps,
        ]
    ] = Field(default_factory=list, alias="Alternative")

    @property
    def routes(self):
        yield from chain.from_iterable(map(attrgetter("routes"), self.steps))


class Step(StepPrototype):
    type: Optional[StepKeywordType] = Field(default=Keyword.Star, alias="Type")
    action: Optional[str] = Field(None, alias="Action")


class SubStep(BaseModel):
    sub_step: Step = Field(..., alias="Step")


class StarStep(StepPrototype):
    type: StepKeywordType = Field(Keyword.Star, alias="Type")
    action: Optional[str] = Field(alias=Keyword.Star.value)


class GivenStep(StepPrototype):
    type: StepKeywordType = Field(Keyword.Given, alias="Type")
    action: Optional[str] = Field(alias=Keyword.Given.value)


class WhenStep(StepPrototype):
    type: StepKeywordType = Field(Keyword.When, alias="Type")
    action: Optional[str] = Field(alias=Keyword.When.value)


class ThenStep(StepPrototype):
    type: StepKeywordType = Field(Keyword.Then, alias="Type")
    action: Optional[str] = Field(alias=Keyword.Then.value)


class AndStep(StepPrototype):
    type: StepKeywordType = Field(Keyword.And, alias="Type")
    action: Optional[str] = Field(alias=Keyword.And.value)


class ButStep(StepPrototype):
    type: StepKeywordType = Field(Keyword.But, alias="Type")
    action: Optional[str] = Field(alias=Keyword.But.value)


Join.model_rebuild()  # type:ignore[attr-defined] # migration to pydantic 2
StepPrototype.model_rebuild()  # type:ignore[attr-defined] # migration to pydantic 2
Alternative.model_rebuild()  # type:ignore[attr-defined] # migration to pydantic 2

Given = GivenStep.build_by_action
When = WhenStep.build_by_action
Then = ThenStep.build_by_action
And = AndStep.build_by_action
But = ButStep.build_by_action
