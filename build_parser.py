import importlib.machinery
import importlib.util
import pathlib
import sys

import tatsu
from setuptools.command.sdist import sdist as original_sdist


class sdist(original_sdist):
    def run(self) -> None:
        grammar = pathlib.Path("pytest_bdd/parser_data/gherkin.tatsu").read_text(encoding="utf-8")
        compiled_py = tatsu.to_python_sourcecode(grammar)
        pathlib.Path("pytest_bdd/_tatsu_parser.py").write_text(compiled_py, encoding="utf-8")

        return super().run()


# TODO: Remove this dev junk
class MyLoader(importlib.machinery.SourceFileLoader):
    # def __init__(self, fullname, path):
    #     self.fullname = fullname
    #     self.path = path

    # def get_filename(self, fullname):
    #     return self.path

    def get_data(self, filename):
        val = super().get_data(filename)
        decoded = val.decode("utf-8")
        # return val
        # """exec_module is already defined for us, we just have to provide a way
        # of getting the source code of the module"""
        # with open(filename) as f:
        #     data = f.read()
        compiled_py = tatsu.to_python_sourcecode(decoded)
        # do something with data ...
        # eg. ignore it... return "print('hello world')"
        return compiled_py

    def get_source(self, fullname):
        val = super().get_source(fullname)
        return val

    def exec_module(self, module) -> None:
        val = super().exec_module(module)
        return val


def load_tatsu(filename, fullpath):
    # spec = importlib.util.find_spec(name)
    # loader = importlib.util.LazyLoader(spec.loader)
    # spec.loader = loader
    # module = importlib.util.module_from_spec(spec)
    # sys.modules[name] = module
    # loader.exec_module(module)
    path = pathlib.Path(fullpath)
    loader = MyLoader(filename, path=str(path.absolute()))
    spec = importlib.util.spec_from_loader(name=loader.name, loader=loader, origin=filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[filename] = mod
    loader.exec_module(mod)
    return mod


# mod = load_tatsu("pytest_bdd.parser_data.gherkin", "pytest_bdd/parser_data/gherkin.tatsu")
# print(mod)
# print(mod.GherkinParser)
