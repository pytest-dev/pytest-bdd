import sys

if sys.version_info >= (3, 10):
    # noinspection PyUnresolvedReferences
    from typing import Literal, Protocol, TypeAlias
else:
    # noinspection PyUnresolvedReferences
    from typing_extensions import Literal, Protocol, TypeAlias
