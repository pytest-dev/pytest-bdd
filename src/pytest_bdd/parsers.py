"""StepHandler parsers."""
from abc import ABCMeta, abstractmethod
from enum import Enum
from functools import partial, singledispatchmethod
from itertools import chain, filterfalse
from operator import attrgetter, contains, methodcaller
from re import Match
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import Any, Collection, Dict, Iterable, Optional, Protocol, Sequence, Type, Union, cast, runtime_checkable

import parse as base_parse
import parse_type.cfparse as base_cfparse
from cucumber_expressions.argument import Argument as CucumberExpressionArgument
from cucumber_expressions.errors import CantEscape, UndefinedParameterTypeError
from cucumber_expressions.expression import CucumberExpression
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from cucumber_expressions.regular_expression import RegularExpression as CucumberRegularExpression

from messages import ExpressionType  # type:ignore[attr-defined]
from pytest_bdd.compatibility.pytest import FixtureRequest
from pytest_bdd.model.messages_extension import ExpressionType as ExpressionTypeExtension
from pytest_bdd.utils import StringableProtocol, stringify


class ParserBuildValueError(ValueError):
    ...


@runtime_checkable
class StepParserProtocol(Protocol):
    type: Union[ExpressionType, ExpressionTypeExtension, str] = ExpressionTypeExtension.pytest_bdd_other_expression

    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Optional[Iterable[str]] = None
    ) -> Optional[Dict[str, Any]]:
        ...  # pragma: no cover

    @property
    def arguments(self) -> Collection[str]:
        ...  # pragma: no cover

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        ...  # pragma: no cover

    def __str__(self) -> str:
        ...  # pragma: no cover


class RegistryMode(Enum):
    NEW = "NEW"
    GLOBAL = "GLOBAL"
    FIXTURE = "FIXTURE"
    NOT_DEFINED = None


class StepParser(StepParserProtocol, metaclass=ABCMeta):
    """Parser of the individual step."""

    @abstractmethod
    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Optional[Iterable[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get step arguments from the given step name.

        :return: `dict` of step arguments
        """
        raise NotImplementedError()  # pragma: no cover

    @property
    @abstractmethod
    def arguments(self) -> Collection[str]:
        """Get step argument names from the given step name."""
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """Match given name with the step name."""
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def __str__(self) -> str:
        """Match given name with the step name."""
        raise NotImplementedError()  # pragma: no cover

    @classmethod
    def build(cls, parserlike: Union[str, bytes, "StepParser", StepParserProtocol]) -> "StepParser":
        """Get parser by given name.

        :param parserlike: name of the step to parse

        :return: step parser object
        :rtype: StepParser
        """

        if isinstance(parserlike, StepParserProtocol):
            parser = cast(StepParser, parserlike)
        elif isinstance(parserlike, _RePattern):
            parser = re(parserlike)
        elif isinstance(parserlike, base_parse.Parser):
            parser = parse(parserlike)
        elif isinstance(parserlike, CucumberExpression):
            parser = cucumber_expression(parserlike)
        elif isinstance(parserlike, CucumberRegularExpression):
            parser = cucumber_regular_expression(parserlike)
        else:
            parser = heuristic(parserlike)

        return parser


class re(StepParser):
    """Regex step parser."""

    type = ExpressionTypeExtension.pytest_bdd_regular_expression

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()  # pragma: no cover

    @__init__.register
    def _(self, pattern: str, *args: Any, **kwargs: Any) -> None:
        """Compile regex."""
        self.pattern = pattern
        self.regex = re_compile(self.pattern, *args, **kwargs)

    @__init__.register
    def _(self, pattern: _RePattern):
        """Compile regex."""
        self.pattern = pattern.pattern
        self.regex = pattern

    def parse_arguments(
        self,
        request: FixtureRequest,
        name,
        anonymous_group_names: Optional[Iterable[str]] = None,
    ):
        match = cast(Match, self.regex.fullmatch(name))  # Can't be None because is already matched
        group_dict = match.groupdict()
        if anonymous_group_names is not None:
            group_dict.update(
                zip(
                    anonymous_group_names,
                    map(
                        lambda span: name[slice(*span)],  # type: ignore[no-any-return] # https://github.com/python/mypy/issues/9590
                        filterfalse(
                            partial(contains, [*map(match.span, group_dict.keys())]),
                            map(match.span, range(1, len(match.groups()) + 1)),
                        ),
                    ),
                )
            )

        return {k: v for k, v in group_dict.items() if v is not None}

    @property
    def arguments(self):
        return [*self.regex.groupindex.keys()]

    def is_matching(self, request: FixtureRequest, name):
        return bool(self.regex.fullmatch(name))

    def __str__(self):
        return stringify(self.pattern)


class parse(StepParser):
    """parse step parser."""

    type = ExpressionTypeExtension.pytest_bdd_parse_expression

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, format, *args, **kwargs):
        if isinstance(format, (StringableProtocol, str, bytes)):
            self.__init_stringable__(format, *args, **kwargs)
        else:
            raise ParserBuildValueError(f"Unable build parser for format {format}")  # pragma: no cover

    def __init_stringable__(
        self, format: Union[StringableProtocol, str, bytes], *args: Any, builder=base_parse.compile, **kwargs: Any
    ) -> None:
        self.format = stringify(format)
        self.parser = builder(self.format, *args, **kwargs)

    @__init__.register
    def _(self, format: base_parse.Parser):
        self.format = format._format
        self.parser = format

    @classmethod
    def cfparse(cls, *args, **kwargs):
        kwargs.setdefault("builder", base_cfparse.Parser)
        return cls(*args, **kwargs)

    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Optional[Iterable[str]] = None
    ) -> Union[Dict[str, Any]]:
        match = self.parser.parse(name)
        group_dict = cast(dict, match.named)
        if anonymous_group_names is not None:
            group_dict.update(dict(zip(anonymous_group_names, match.fixed)))
        return group_dict

    @property
    def arguments(self) -> Collection[str]:
        return [*self.parser._match_re.groupindex.keys()]

    def is_matching(self, request: FixtureRequest, name):
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False

    def __str__(self):
        return str(self.format)


class cfparse(parse):
    """cfparse step parser."""

    type = ExpressionTypeExtension.pytest_bdd_cfparse_expression

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("builder", base_cfparse.Parser)
        super().__init__(*args, **kwargs)


class string(StepParser):
    """Exact string step parser."""

    type = ExpressionTypeExtension.pytest_bdd_string_expression

    def __init__(self, name: Union[StringableProtocol, str, bytes]) -> None:
        self.name = stringify(name)

    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Optional[Iterable[str]] = None
    ) -> Dict[str, Any]:
        """No parameters are available for simple string step.

        :return: `dict` of step arguments
        """
        return {}

    @property
    def arguments(self):
        return []

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """Match given name with the step name."""
        return bool(self.name == name)

    def __str__(self):
        return self.name


@runtime_checkable
class _CucumberExpressionProtocol(Protocol):
    def match(self, text: str) -> Optional[Sequence[CucumberExpressionArgument]]:
        ...  # pragma: no cover


class _CucumberExpression(StepParser):
    pattern: str

    expression_type: Type[Union[CucumberExpression, CucumberRegularExpression]]
    parameter_type_registry_like: Union[ParameterTypeRegistry, Any]
    parameter_type_registry = ParameterTypeRegistry()  # default registry

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        try:
            return bool(self.rebuild_expression_in_test_context(request).tree_regexp.match(name))
        except (UndefinedParameterTypeError, CantEscape):
            return False

    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Optional[Iterable[str]] = None
    ) -> Optional[Dict[str, Any]]:
        return dict(
            zip(
                anonymous_group_names or [],
                map(attrgetter("value"), self.rebuild_expression_in_test_context(request).match(name) or []),
            )
        )

    def __str__(self):
        return str(self.pattern)

    def rebuild_expression_in_test_context(self, request) -> Union[CucumberExpression, CucumberRegularExpression]:
        return self.expression_type(self.pattern, self._get_parameter_type_registry(request))

    def _get_parameter_type_registry(self, request) -> Union[ParameterTypeRegistry, Any]:
        if (
            isinstance(self.parameter_type_registry_like, (str, RegistryMode))
            or self.parameter_type_registry_like is None
        ):
            parameter_type_registry_mode = RegistryMode(self.parameter_type_registry_like)

            parameter_type_registry = {
                RegistryMode.NEW: ParameterTypeRegistry,
                RegistryMode.GLOBAL: lambda: self.parameter_type_registry,
                RegistryMode.NOT_DEFINED: lambda: self.parameter_type_registry,
                RegistryMode.FIXTURE: lambda: request.getfixturevalue("parameter_type_registry"),
            }[parameter_type_registry_mode]()
        else:
            parameter_type_registry = self.parameter_type_registry_like
        return parameter_type_registry


class cucumber_expression(_CucumberExpression):
    type = ExpressionType.cucumber_expression
    expression_type = CucumberExpression

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()  # pragma: no cover

    @__init__.register
    def _(
        self,
        expression: str,
        parameter_type_registry: Union[ParameterTypeRegistry, RegistryMode, Any] = RegistryMode.FIXTURE,
    ):
        self.pattern = expression
        self.parameter_type_registry_like = parameter_type_registry

    @__init__.register
    def _(
        self,
        expression: CucumberExpression,
    ):
        self.pattern = expression.expression
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self):
        return []


class cucumber_regular_expression(_CucumberExpression):
    type = ExpressionType.regular_expression
    expression_type = CucumberRegularExpression
    # https://bugs.python.org/issue45684

    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()  # pragma: no cover

    @__init__.register
    def _(
        self,
        expression: str,
        parameter_type_registry: Union[ParameterTypeRegistry, RegistryMode, Any] = RegistryMode.FIXTURE,
    ):
        self.pattern = expression
        self.parameter_type_registry_like = parameter_type_registry

    @__init__.register
    def _(
        self,
        expression: CucumberRegularExpression,
    ):
        self.pattern = expression.expression_regexp.pattern
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self) -> Collection[str]:
        return [*re_compile(self.pattern).groupindex.keys()]


class heuristic(StepParser):
    type = ExpressionTypeExtension.pytest_bdd_heuristic_expression

    def __init__(
        self,
        format,
        parameter_type_registry: Optional[Union[ParameterTypeRegistry, RegistryMode, Any]] = RegistryMode.FIXTURE,
    ):
        if isinstance(format, (StringableProtocol, str, bytes)):
            self.format = stringify(format)
        else:
            self.format = format
        self.parameter_type_registry = parameter_type_registry
        self.parsers_are_built = False
        self.build_parsers()

    def build_parsers(self):
        if self.parsers_are_built:
            return

        # Rework to exception groups after python 3.10 end of support
        e_cause = None
        try:
            self.string_parser: Optional[string] = string(self.format)
        except Exception as e:
            e_cause = e
            self.string_parser = None
        try:
            self.cucumber_expression_parser = cucumber_expression(
                self.format, parameter_type_registry=self.parameter_type_registry
            )
        except Exception as e:
            e.__cause__, e_cause = e_cause, e
            self.cucumber_expression_parser = None

        try:
            self.cfparse_parser: Optional[cfparse] = cfparse(self.format)
        except Exception as e:
            e.__cause__, e_cause = e_cause, e
            self.cfparse_parser = None

        try:
            self.re_parser = re(self.format)
        except Exception as e:
            e.__cause__, e_cause = e_cause, e
            self.re_parser = None

        self.parsers_are_built = True
        if not any(self.parser_by_priorities):
            raise ParserBuildValueError(
                f"Unable build parser for format {self.format}"
            ) from e_cause  # pragma: no cover

    @property
    def parser_by_priorities(self) -> Sequence[Optional[StepParser]]:
        return [self.string_parser, self.cucumber_expression_parser, self.cfparse_parser, self.re_parser]

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        return any(map(methodcaller("is_matching", request, name), filter(bool, self.parser_by_priorities)))

    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Optional[Iterable[str]] = None
    ) -> Optional[Dict[str, Any]]:
        for parser in self.parser_by_priorities:
            if parser is not None and parser.is_matching(request, name):
                arguments = parser.parse_arguments(request, name, anonymous_group_names=anonymous_group_names)
                break
        else:
            arguments = None
        return arguments

    @property
    def arguments(self) -> Collection[str]:
        return [
            *chain.from_iterable(
                map(
                    lambda parser: []  # type:ignore[no-any-return]
                    if (args := getattr(parser, "arguments")) is None
                    else args,
                    self.parser_by_priorities,
                )
            )
        ]

    def __str__(self):
        return self.format
