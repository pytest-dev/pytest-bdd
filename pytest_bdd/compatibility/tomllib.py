import sys

if sys.version_info < (3, 11):
    # noinspection PyUnresolvedReferences
    from tomli import *
else:
    # noinspection PyUnresolvedReferences
    from tomllib import *
