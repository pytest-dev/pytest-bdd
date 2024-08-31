from itertools import cycle
from operator import attrgetter
from typing import AbstractSet, List, Optional, Protocol, Type, TypeVar, Union, runtime_checkable

from _pytest.mark import Mark
from attr import attrib, attrs
from cucumber_tag_expressions import TagExpressionError, TagExpressionParser

from pytest_bdd.compatibility.pytest import PYTEST6, PYTEST83

if PYTEST6:
    from pytest_bdd.compatibility.pytest import Expression, MarkMatcher, ParseError

TagExpressionType = TypeVar("TagExpressionType", bound="TagExpression")


@runtime_checkable
class TagExpression(Protocol):
    @classmethod
    def parse(cls: Type[TagExpressionType], expression: str) -> TagExpressionType:
        raise NotImplementedError  # pragma: no cover

    def evaluate(self, marks: List[Mark]) -> bool:
        raise NotImplementedError  # pragma: no cover


@attrs
class _ModernTagExpression(TagExpression):
    expression: Optional["Expression"] = attrib()

    @classmethod
    def parse(cls, expression):
        try:
            return cls(expression=Expression.compile(expression) if expression != "" else None)
        except ParseError as e:
            raise ValueError(f"Unable parse mark expression: {expression}: {e}") from e


@attrs
class _EnhancedMarksTagExpression(_ModernTagExpression):
    """Used for 8.3<=pytest"""

    def evaluate(self, marks):
        return self.expression.evaluate(MarkMatcher.from_markers(marks)) if self.expression is not None else True


@attrs
class _MarksTagExpression(_ModernTagExpression):
    """Used for 6.0<=pytest<8.3"""

    def evaluate(self, marks):
        return (
            self.expression.evaluate(MarkMatcher(map(attrgetter("name"), marks)))
            if self.expression is not None
            else True
        )


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

    def evaluate(self, marks):
        return (
            eval(self.expression, {}, dict(zip(map(attrgetter("name"), marks), cycle([True]))))
            if self.expression is not None
            else True
        )


MarksTagExpression: Type[Union[_EnhancedMarksTagExpression, _MarksTagExpression, _FallbackMarksTagExpression]]
if PYTEST83:
    MarksTagExpression = _EnhancedMarksTagExpression
elif PYTEST6:
    MarksTagExpression = _MarksTagExpression
else:
    MarksTagExpression = _FallbackMarksTagExpression


@attrs
class GherkinTagExpression(TagExpression):
    expression: TagExpressionParser = attrib()

    @classmethod
    def parse(cls, expression):
        try:
            return cls(expression=TagExpressionParser.parse(expression))
        except TagExpressionError as e:
            raise ValueError(f"Unable parse tag expression: {expression}: {e}") from e

    def evaluate(self, marks):
        return self.expression.evaluate(map(attrgetter("name"), marks))
