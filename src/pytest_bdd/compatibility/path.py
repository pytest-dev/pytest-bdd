import os
import sys


def relpath(path, start=os.curdir):
    try:
        return os.path.relpath(path, start)
    except ValueError:
        if sys.platform == "win32":
            return path
        else:
            raise
