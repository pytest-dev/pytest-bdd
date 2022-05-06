from functools import partial
from operator import methodcaller
from pathlib import Path
from typing import cast

from attr import attrib, attrs

from pytest_bdd.struct_bdd.model import Step, StepSchema
from pytest_bdd.typing.parser import ParserProtocol


@attrs
class StructBDDParser(ParserProtocol):
    class KIND:
        HOCON = "hocon"
        HJSON = "hjson"
        JSON = "json"
        JSON5 = "json5"
        TOML = "toml"
        YAML = "yaml"

    kind = attrib(kw_only=True)
    glob = attrib(kw_only=True)
    loader = attrib(kw_only=True)

    @kind.default
    def kind_default(self):
        return self.KIND.YAML if getattr(self, "loader", None) is None else None

    @glob.default
    def glob_default(self):
        return methodcaller("rglob", "*" if self.kind is None else f"*.bdd.{self.kind}")

    @loader.default
    def loader_default(self):
        return self.build_loader()

    def parse(self, path: Path, uri: str, *args, **kwargs):
        encoding = kwargs.pop("encoding", "utf-8")
        mode = kwargs.pop("mode", "r")
        with path.open(mode=mode, encoding=encoding) as feature_file:
            content = feature_file.read()

        return cast(Step, StepSchema().load(self.loader(content, *args, **kwargs))).build_feature(
            filename=str(path.as_posix()), uri=uri
        )

    def build_loader(self):
        if self.kind == self.KIND.YAML:
            from yaml import FullLoader
            from yaml import load as load_yaml

            return partial(load_yaml, Loader=FullLoader)
        elif self.kind == self.KIND.TOML:
            from tomli import loads as load_toml

            return load_toml
        elif self.kind == self.KIND.JSON:
            from json import loads as load_json

            return load_json
        elif self.kind == self.KIND.JSON5:
            from json5 import loads as load_json5

            return load_json5
        elif self.kind == self.KIND.HJSON:
            from hjson import loads as load_hjson

            return load_hjson
        elif self.kind == self.KIND.HOCON:
            from json import loads

            from pyhocon import ConfigFactory, HOCONConverter

            def load_hocon(
                s,
                hocon_parse_args=(),
                hocon_parse_kwargs=None,
                hocon_to_json_args=(),
                hocon_to_json_kwargs=None,
                json_args=(),
                json_kwargs=None,
            ):
                hocon_to_json_kwargs = hocon_to_json_kwargs or {}
                hocon_parse_kwargs = hocon_parse_kwargs or {}
                json_kwargs = json_kwargs or {}
                return loads(
                    HOCONConverter.to_json(
                        config=ConfigFactory.parse_string(s, *hocon_parse_args, **hocon_parse_kwargs),
                        *hocon_to_json_args,
                        **hocon_to_json_kwargs,
                    ),
                    *json_args,
                    **json_kwargs,
                )

            return load_hocon
