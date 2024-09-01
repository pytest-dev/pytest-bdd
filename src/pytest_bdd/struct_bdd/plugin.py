from contextlib import suppress
from functools import partial
from inspect import getmembers
from pathlib import Path

import pytest

from pytest_bdd.compatibility.pytest import PYTEST7, Config, Module
from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.struct_bdd.model import StepPrototype
from pytest_bdd.struct_bdd.parser import StructBDDParser


class StructBDDPlugin:
    extension_to_mimetype = {
        StructBDDParser.KIND.YAML: Mimetype.struct_bdd_yaml,
        StructBDDParser.KIND.HOCON: Mimetype.struct_bdd_hocon,
        StructBDDParser.KIND.JSON5: Mimetype.struct_bdd_json5,
        StructBDDParser.KIND.JSON: Mimetype.struct_bdd_json,
        StructBDDParser.KIND.HJSON: Mimetype.struct_bdd_hjson,
        StructBDDParser.KIND.TOML: Mimetype.struct_bdd_toml,
    }

    def pytest_bdd_get_parser(self, config: Config, mimetype: str):
        with suppress(KeyError):
            return partial(
                StructBDDParser,
                kind={
                    Mimetype.struct_bdd_yaml.value: StructBDDParser.KIND.YAML.value,
                    Mimetype.struct_bdd_hocon.value: StructBDDParser.KIND.HOCON.value,
                    Mimetype.struct_bdd_json5.value: StructBDDParser.KIND.JSON5.value,
                    Mimetype.struct_bdd_json.value: StructBDDParser.KIND.JSON.value,
                    Mimetype.struct_bdd_hjson.value: StructBDDParser.KIND.HJSON.value,
                    Mimetype.struct_bdd_toml.value: StructBDDParser.KIND.TOML.value,
                }[mimetype],
            )

    def pytest_bdd_get_mimetype(self, config: Config, path: Path):
        for extension_suffix, mimetype in self.extension_to_mimetype.items():
            if str(path).endswith(f".bdd.{extension_suffix.value}"):
                return mimetype.value

    def pytest_bdd_is_collectible(self, config: Config, path: Path):
        for extension_suffix, mimetype in self.extension_to_mimetype.items():
            if str(path).endswith(f".bdd.{extension_suffix.value}"):
                return True

    def _pytest_pycollect_makemodule(self):
        outcome = yield
        res = outcome.get_result()
        if isinstance(res, Module):
            for member_name, member in getmembers(res.module):
                if isinstance(member, StepPrototype) and member_name.startswith("test_"):
                    setattr(res.module, member_name, member.as_test(res.module.__file__))

    if PYTEST7:

        @pytest.hookimpl(hookwrapper=True)
        def pytest_pycollect_makemodule(self, parent, module_path):
            yield from self._pytest_pycollect_makemodule()

    else:

        @pytest.hookimpl(hookwrapper=True)
        def pytest_pycollect_makemodule(self, path, parent):
            yield from self._pytest_pycollect_makemodule()
