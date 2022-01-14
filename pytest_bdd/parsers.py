"""Step parsers."""


import re as base_re
import sys
from functools import partial

import parse as base_parse
from parse_type import cfparse as base_cfparse

_Re_Pattern = base_re.Pattern if sys.version_info >= (3, 7) else type(base_re.compile(""))


class StepParser:
    """Parser of the individual step."""

    def __init__(self, name):
        self.name = name

    def parse_arguments(self, name):
        """Get step arguments from the given step name.

        :return: `dict` of step arguments
        """
        raise NotImplementedError()  # pragma: no cover

    def is_matching(self, name):
        """Match given name with the step name."""
        raise NotImplementedError()  # pragma: no cover


class _CommonRe(StepParser):
    regex: _Re_Pattern

    def parse_arguments(self, name):
        """Get step arguments.

        :return: `dict` of step arguments
        """
        return self.regex.match(name).groupdict()

    def is_matching(self, name):
        """Match given name with the step name."""
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
        """Get step arguments.

        :return: `dict` of step arguments
        """
        return self.parser.parse(name).named

    def is_matching(self, name):
        """Match given name with the step name."""
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
        """Compile parse expression."""
        super().__init__(name)
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


def get_parser(step_name):
    """Get parser by given name.

    :param step_name: name of the step to parse

    :return: step parser object
    :rtype: StepArgumentParser
    """

    def does_support_parser_interface(obj):
        return all(map(partial(hasattr, obj), ["is_matching", "parse_arguments"]))

    if does_support_parser_interface(step_name):
        return step_name
    elif isinstance(step_name, _Re_Pattern):
        return _re(step_name)
    elif isinstance(step_name, base_parse.Parser):
        return _parse(step_name)
    else:
        return string(step_name)
