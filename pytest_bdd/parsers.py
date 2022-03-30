"""Step parsers."""


import re as base_re
import sys
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Union

import parse as base_parse
import parse_type.cfparse as base_cfparse

if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable
else:
    try:
        from typing_extensions import Protocol, runtime_checkable
    except ImportError:
        Protocol, runtime_checkable = object, lambda cls: cls

_Re_Pattern = base_re.Pattern if sys.version_info >= (3, 7) else type(base_re.compile(""))


@runtime_checkable
class StepParserProtocol(Protocol):
    name: Any

    def parse_arguments(self, name) -> Dict[str, Any]:
        ...

    def is_matching(self, name) -> Union[bool, Any]:
        ...


class StepParser(StepParserProtocol, metaclass=ABCMeta):
    """Parser of the individual step."""

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def parse_arguments(self, name):
        """Get step arguments from the given step name.

        :return: `dict` of step arguments
        """
        raise NotImplemented  # pragma: no cover

    @abstractmethod
    def is_matching(self, name):
        """Match given name with the step name."""
        raise NotImplemented  # pragma: no cover


class _CommonRe(StepParser):
    regex: _Re_Pattern

    def parse_arguments(self, name):
        return self.regex.match(name).groupdict()

    def is_matching(self, name):
        return bool(self.regex.match(name))


class _re(_CommonRe):
    def __init__(self, name):
        """Compile regex."""
        super().__init__(name.pattern)
        self.regex = name


class re(_CommonRe):
    """Regex step parser."""

    def __init__(self, name, *args, **kwargs):
        """Compile regex."""
        super().__init__(name)
        self.regex = base_re.compile(self.name, *args, **kwargs)


class _CommonParse(StepParser):
    parser: base_parse.Parser

    def parse_arguments(self, name):
        return self.parser.parse(name).named

    def is_matching(self, name):
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False


class _parse(_CommonParse):
    def __init__(self, name: base_parse.Parser):
        super().__init__(name._format)
        self.parser = name


class parse(_CommonParse):
    """parse step parser."""

    def __init__(self, name, *args, **kwargs):
        """Compile parse expression."""
        super().__init__(name)
        self.parser = base_parse.compile(self.name, *args, **kwargs)


class cfparse(_CommonParse):
    """cfparse step parser."""

    def __init__(self, name, *args, **kwargs):
        """Stringify"""
        name = str(name, **({"encoding": "utf-8"} if isinstance(name, bytes) else {}))
        super().__init__(name)
        """Compile parse expression."""
        self.parser = base_cfparse.Parser(self.name, *args, **kwargs)


class string(StepParser):
    """Exact string step parser."""

    def __init__(self, name):
        """Stringify"""
        name = str(name, **({"encoding": "utf-8"} if isinstance(name, bytes) else {}))
        super().__init__(name)

    def parse_arguments(self, name):
        """No parameters are available for simple string step.

        :return: `dict` of step arguments
        """
        return {}

    def is_matching(self, name):
        """Match given name with the step name."""
        return self.name == name


def get_parser(parserlike: Union[str, StepParser, StepParserProtocol]) -> Union[StepParser, StepParserProtocol]:
    """Get parser by given name.

    :param parserlike: name of the step to parse

    :return: step parser object
    :rtype: StepArgumentParser
    """

    if isinstance(parserlike, StepParserProtocol):
        return parserlike
    elif isinstance(parserlike, _Re_Pattern):
        return _re(parserlike)
    elif isinstance(parserlike, base_parse.Parser):
        return _parse(parserlike)
    else:
        return cfparse(parserlike)
