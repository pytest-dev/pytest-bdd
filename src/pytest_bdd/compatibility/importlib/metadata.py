import sys

if sys.version_info >= (3, 10):
    from importlib.metadata import *
    from importlib.metadata import version
else:
    from importlib_metadata import *
    from importlib_metadata import version

__all__ = ["version"]
