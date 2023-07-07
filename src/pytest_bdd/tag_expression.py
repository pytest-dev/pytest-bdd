from itertools import cycle
from typing import AbstractSet, Optional, Protocol, Type, TypeVar, runtime_checkable

from attr import attrib, attrs
from cucumber_tag_expressions import TagExpressionError, TagExpressionParser

from pytest_bdd.compatibility.pytest import PYTEST6

if PYTEST6:
    from pytest_bdd.compatibility.pytest import Expression, MarkMatcher, ParseError

TagExpressionType = TypeVar("TagExpressionType", bound="TagExpression")


@runtime_checkable
class TagExpression(Protocol):
    @classmethod
    def parse(cls: Type[TagExpressionType], expression: str) -> TagExpressionType:
        raise NotImplementedError  # pragma: no cover

    def evaluate(self, tags: AbstractSet[str]) -> bool:
        raise NotImplementedError  # pragma: no cover


@attrs
class _MarksTagExpression(TagExpression):
    expression: Optional["Expression"] = attrib()

    @classmethod
    def parse(cls, expression):
        try:
            return cls(expression=Expression.compile(expression) if expression != "" else None)
        except ParseError as e:
            raise ValueError(f"Unable parse mark expression: {expression}: {e}") from e

    def evaluate(self, tags):
        return self.expression.evaluate(MarkMatcher(tags)) if self.expression is not None else True


@attrs
class _FallbackMarksTagExpression(TagExpression):
    """Used for pytest<6.0"""

    expression: Optional[str] = attrib()

    @classmethod
    def parse(cls, expression):
        try:
            if expression != "":
                eval(expression, {})
        except SyntaxError as e:
            raise ValueError(f"Unable parse mark expression: {expression}: {e}") from e
        except NameError:
            pass
        return cls(expression=expression if expression != "" else None)

    def evaluate(self, tags):
        return eval(self.expression, {}, dict(zip(tags, cycle([True])))) if self.expression is not None else True


MarksTagExpression = _MarksTagExpression if PYTEST6 else _FallbackMarksTagExpression


@attrs
class GherkinTagExpression(TagExpression):
    expression: TagExpressionParser = attrib()

    @classmethod
    def parse(cls, expression):
        try:
            return cls(expression=TagExpressionParser.parse(expression))
        except TagExpressionError as e:
            raise ValueError(f"Unable parse tag expression: {expression}: {e}") from e

    def evaluate(self, tags):
        return self.expression.evaluate(tags)
