"""Step parsers."""
from __future__ import annotations

import abc
import re as base_re
from typing import Any, Dict, TypeVar, cast, overload

import parse as base_parse
from parse_type import cfparse as base_cfparse


class StepParser(abc.ABC):
    """Parser of the individual step."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    def parse_arguments(self, name: str) -> dict[str, Any] | None:
        """Get step arguments from the given step name.

        :return: `dict` of step arguments
        """
        ...

    @abc.abstractmethod
    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        ...


class re(StepParser):
    """Regex step parser."""

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Compile regex."""
        super().__init__(name)
        self.regex = base_re.compile(self.name, *args, **kwargs)

    def parse_arguments(self, name: str) -> dict[str, str] | None:
        """Get step arguments.

        :return: `dict` of step arguments
        """
        match = self.regex.match(name)
        if match is None:
            return None
        return match.groupdict()

    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        return bool(self.regex.match(name))


class parse(StepParser):
    """parse step parser."""

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Compile parse expression."""
        super().__init__(name)
        self.parser = base_parse.compile(self.name, *args, **kwargs)

    def parse_arguments(self, name: str) -> dict[str, Any]:
        """Get step arguments.

        :return: `dict` of step arguments
        """
        return cast(Dict[str, Any], self.parser.parse(name).named)

    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False


class cfparse(parse):
    """cfparse step parser."""

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Compile parse expression."""
        super(parse, self).__init__(name)
        self.parser = base_cfparse.Parser(self.name, *args, **kwargs)


class string(StepParser):
    """Exact string step parser."""

    def parse_arguments(self, name: str) -> dict:
        """No parameters are available for simple string step.

        :return: `dict` of step arguments
        """
        return {}

    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        return self.name == name


TStepParser = TypeVar("TStepParser", bound=StepParser)


@overload
def get_parser(step_name: str) -> string:
    ...


@overload
def get_parser(step_name: TStepParser) -> TStepParser:
    ...


def get_parser(step_name: str | StepParser) -> StepParser:
    """Get parser by given name."""

    if isinstance(step_name, StepParser):
        return step_name

    return string(step_name)
