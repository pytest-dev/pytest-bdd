import pathlib

import tatsu
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self) -> None:
        # Build the generated parser (_gherkin.py)
        grammar = pathlib.Path("src/pytest_bdd/gherkin.tatsu").read_text(encoding="utf-8")
        compiled_py = tatsu.to_python_sourcecode(grammar)
        pathlib.Path("src/pytest_bdd/_gherkin.py").write_text(compiled_py, encoding="utf-8")

        return super().run()
