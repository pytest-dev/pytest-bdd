import pathlib

import tatsu
from setuptools.command.build_py import build_py as original_build_py
from setuptools.command.sdist import sdist as original_sdist


# TODO: Figure out if we need sdist or build_py
class sdist(original_sdist):
    def run(self) -> None:
        # Build the generated parser (_gherkin.py)
        grammar = pathlib.Path("pytest_bdd/gherkin.tatsu").read_text(encoding="utf-8")
        compiled_py = tatsu.to_python_sourcecode(grammar)
        pathlib.Path("pytest_bdd/_gherkin.py").write_text(compiled_py, encoding="utf-8")

        return super().run()


class build_py(original_build_py):
    def run(self) -> None:
        # Build the generated parser (_gherkin.py)
        grammar = pathlib.Path("pytest_bdd/gherkin.tatsu").read_text(encoding="utf-8")
        compiled_py = tatsu.to_python_sourcecode(grammar)
        pathlib.Path("pytest_bdd/_gherkin.py").write_text(compiled_py, encoding="utf-8")

        return super().run()
