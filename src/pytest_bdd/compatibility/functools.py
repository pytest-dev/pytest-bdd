import sys

if sys.version_info < (3, 8):
    from singledispatchmethod import singledispatchmethod
else:
    from functools import singledispatchmethod

__all__ = ["singledispatchmethod"]
