from collections import defaultdict, namedtuple
from enum import Enum
from functools import partial
from inspect import getfile
from itertools import chain, product, starmap
from operator import attrgetter, eq, is_not
from pathlib import Path
from typing import Any, ClassVar, List, Literal, Optional, Sequence, Type, Union

from attr import attrib, attrs
from pydantic.v1 import BaseModel, Extra, Field, validator

from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.model.messages import KeywordType, Source
from pytest_bdd.scenario_locator import ScenarioLocatorFilterMixin
from pytest_bdd.utils import deepattrgetter


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


KEYWORD_TO_TYPE = defaultdict(
    lambda: KeywordType.unknown,
    [
        (Keyword.Given, KeywordType.context),
        (Keyword.When, KeywordType.action),
        (Keyword.Then, KeywordType.outcome),
        (Keyword.And, KeywordType.conjunction),
        (Keyword.But, KeywordType.conjunction),
        (Keyword.Star, KeywordType.unknown),
    ],
)


class Node(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    tags: Optional[Sequence[str]] = Field(default_factory=list, alias="Tags")
    name: Optional[str] = Field(None, alias="Name")
    description: Optional[str] = Field(None, alias="Description")
    comments: Optional[Sequence[str]] = Field(default_factory=list, alias="Comments")


class Table(Node):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    type: Optional[Literal["Rowed", "Columned"]] = Field("Rowed", alias="Type")
    parameters: Optional[Sequence[str]] = Field(default_factory=list, alias="Parameters")
    values: Optional[Sequence[Sequence[Any]]] = Field(default_factory=list, alias="Values")

    @property
    def columned_values(self):
        if self.type == "Columned":
            return self.values
        else:
            return list(zip(*self.values))

    @property
    def rowed_values(self):
        if self.type == "Rowed":
            return self.values
        else:
            return list(zip(*self.values))


class SubTable(Node):
    sub_table: Table = Field(..., alias="Table")


class Join(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    tables: List[Union[Table, "Join", SubTable]] = Field(default_factory=list, alias="Join")

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

    @validator("tables", each_item=True)
    def convert_sub_tables_to_tables(cls, value):
        if isinstance(value, SubTable):
            return value.sub_table
        else:
            return value


@validator("steps", pre=True, each_item=True)
def convert_to_step(cls, value):
    if isinstance(value, str):
        return Step(action=value)
    elif isinstance(value, dict) and len(value) == 1 and next(iter(value)) not in SubKeyword.__members__:
        return Step(type=next(iter(value.keys())), action=next(iter(value.values())))
    else:
        return value


@validator("type")
def select_step_keyword_type(cls, value, values, **kwargs):
    try:
        return Keyword(value)
    except:
        return value


@validator("steps", each_item=True)
def convert_sub_steps_to_steps(cls, value):
    if isinstance(value, SubStep):
        return value.sub_step
    else:
        return value


class StepPrototype(Node):
    steps: Sequence[
        Union["Alternative", "Step", "StarStep", "GivenStep", "WhenStep", "ThenStep", "AndStep", "ButStep", "SubStep"]
    ] = Field(default_factory=list, alias="Steps")

    type: Optional[Union[Keyword, str]] = Field(Keyword.Star, alias="Type")
    data: List[Union[Table, Join, SubTable]] = Field(default_factory=list, alias="Data")
    examples: List[Union[Table, Join, SubTable]] = Field(default_factory=list, alias="Examples")

    Route: ClassVar[Type] = namedtuple("Route", ["tags", "steps", "example_table"])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyword_type = KEYWORD_TO_TYPE[self.type]

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
    def build_action_first_arg(cls, action, *args, **kwargs):
        return cls(*args, **kwargs, action=action)

    @validator("examples", each_item=True)
    def convert_sub_tables_to_tables_at_examples(cls, value):
        if isinstance(value, SubTable):
            return value.sub_table
        else:
            return value

    @validator("data", each_item=True)
    def convert_sub_tables_to_tables_at_data(cls, value):
        if isinstance(value, SubTable):
            return value.sub_table
        else:
            return value

    convert_sub_steps_to_steps = convert_sub_steps_to_steps

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
            feature_source = Source(uri=self.uri, data=Path(self.filename).read_text(), media_type=self.mimetype)
            yield feature, feature_source

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
        Union["Alternative", "Step", "StarStep", "GivenStep", "WhenStep", "ThenStep", "AndStep", "ButStep", "SubStep"]
    ] = Field(default_factory=list, alias="Alternative")

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    @property
    def routes(self):
        yield from chain.from_iterable(map(attrgetter("routes"), self.steps))

    @validator("steps", pre=True, each_item=True)
    def convert_step(cls, value):
        if isinstance(value, str):
            return Step(action=value)
        else:
            return value

    convert_sub_steps_to_steps = convert_sub_steps_to_steps


class Step(StepPrototype):
    steps: Sequence[
        Union["Alternative", "Step", "StarStep", "GivenStep", "WhenStep", "ThenStep", "AndStep", "ButStep", "SubStep"]
    ] = Field(default_factory=list, alias="Steps")
    type: Union[Keyword, Optional[str]] = Field(Keyword.Star, alias="Type")
    keyword_type: Optional[KeywordType] = Field(KeywordType.unknown)
    action: Optional[str] = Field(alias="Action")

    convert_to_step = convert_to_step
    select_step_keyword_type = select_step_keyword_type


class SubStep(BaseModel):
    sub_step: Step = Field(..., alias="Step")


class StarStep(StepPrototype):
    steps: Sequence[
        Union["Alternative", "Step", "StarStep", "GivenStep", "WhenStep", "ThenStep", "AndStep", "ButStep", "SubStep"]
    ] = Field(default_factory=list, alias="Steps")

    type: Optional[Keyword] = Field(Keyword.Star, alias="Type")
    keyword_type: Optional[KeywordType] = Field(KeywordType.unknown)
    action: Optional[str] = Field(alias=Keyword.Star.value)

    convert_to_step = convert_to_step
    select_step_keyword_type = select_step_keyword_type


class GivenStep(StepPrototype):
    steps: Sequence[
        Union["Alternative", "Step", "StarStep", "GivenStep", "WhenStep", "ThenStep", "AndStep", "ButStep", "SubStep"]
    ] = Field(default_factory=list, alias="Steps")
    type: Optional[Keyword] = Field(Keyword.Given)
    keyword_type: Optional[KeywordType] = Field(KeywordType.context, alias="Type")
    action: Optional[str] = Field(alias=Keyword.Given.value)

    convert_to_step = convert_to_step
    select_step_keyword_type = select_step_keyword_type


class WhenStep(StepPrototype):
    steps: Sequence[
        Union["Alternative", "Step", "StarStep", "GivenStep", "WhenStep", "ThenStep", "AndStep", "ButStep", "SubStep"]
    ] = Field(default_factory=list, alias="Steps")
    type: Optional[Keyword] = Field(Keyword.When)
    keyword_type: Optional[KeywordType] = Field(KeywordType.action, alias="Type")
    action: Optional[str] = Field(alias=Keyword.When.value)

    convert_to_step = convert_to_step
    select_step_keyword_type = select_step_keyword_type


class ThenStep(StepPrototype):
    steps: Sequence[
        Union["Alternative", "Step", "StarStep", "GivenStep", "WhenStep", "ThenStep", "AndStep", "ButStep", "SubStep"]
    ] = Field(default_factory=list, alias="Steps")
    type: Optional[Keyword] = Field(Keyword.Then)
    keyword_type: Optional[KeywordType] = Field(KeywordType.outcome, alias="Type")
    action: Optional[str] = Field(alias=Keyword.Then.value)

    convert_to_step = convert_to_step
    select_step_keyword_type = select_step_keyword_type


class AndStep(StepPrototype):
    steps: Sequence[
        Union["Alternative", "Step", "StarStep", "GivenStep", "WhenStep", "ThenStep", "AndStep", "ButStep", "SubStep"]
    ] = Field(default_factory=list, alias="Steps")
    type: Optional[Keyword] = Field(Keyword.And)
    keyword_type: Optional[KeywordType] = Field(KeywordType.conjunction, alias="Type")
    action: Optional[str] = Field(alias=Keyword.And.value)

    convert_to_step = convert_to_step
    select_step_keyword_type = select_step_keyword_type


class ButStep(StepPrototype):
    steps: Sequence[
        Union["Alternative", "Step", "StarStep", "GivenStep", "WhenStep", "ThenStep", "AndStep", "ButStep", "SubStep"]
    ] = Field(default_factory=list, alias="Steps")
    type: Optional[Keyword] = Field(Keyword.But)
    keyword_type: Optional[KeywordType] = Field(KeywordType.conjunction, alias="Type")
    action: Optional[str] = Field(alias=Keyword.But.value)

    convert_to_step = convert_to_step
    select_step_keyword_type = select_step_keyword_type


Join.update_forward_refs()
Step.update_forward_refs()
StarStep.update_forward_refs()
GivenStep.update_forward_refs()
WhenStep.update_forward_refs()
ThenStep.update_forward_refs()
AndStep.update_forward_refs()
ButStep.update_forward_refs()
Alternative.update_forward_refs()

Given = GivenStep.build_action_first_arg
When = WhenStep.build_action_first_arg
Then = ThenStep.build_action_first_arg
And = AndStep.build_action_first_arg
But = ButStep.build_action_first_arg
