from configparser import ConfigParser
from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from pathlib import Path
from typing import Optional, Tuple, cast
from urllib.parse import urlparse
from uuid import uuid4

from pytest_bdd.compatibility.pytest import Module as PytestModule
from pytest_bdd.scenario import FeaturePathType as PathType
from pytest_bdd.scenario import scenarios
from pytest_bdd.steps import StepHandler
from pytest_bdd.utils import convert_str_to_python_name
from pytest_bdd.webloc import read as webloc_read


class Module(PytestModule):
    def collect(self):
        StepHandler.Registry.inject_registry_fixture_and_register_steps(self.obj)
        return super().collect()


class FeatureFileModule(Module):
    def _getobj(self):
        path: Path = self.get_path()
        if ".url" == path.suffixes[-1]:
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_url_file(path)
        elif ".desktop" == path.suffixes[-1]:
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_desktop_file(path)
        elif ".webloc" == path.suffixes[-1]:
            feature_pathlike, features_path_type, base_dir = self.get_feature_pathlike_from_weblock_file(path)
        else:
            feature_pathlike, features_path_type, base_dir = path, PathType.PATH, None
        return self._build_test_module(feature_pathlike, features_path_type, base_dir)

    def _build_test_module(self, path: Optional[Path], features_path_type: PathType, base_dir: Optional[Path]):
        module_name = convert_str_to_python_name(f"{path}_{uuid4()}")

        module_spec = ModuleSpec(module_name, None)
        module = module_from_spec(module_spec)

        module.test_scenarios = scenarios(  # type:ignore[attr-defined]
            *((path,) if path is not None else []),
            filter_=None,
            return_test_decorator=False,
            parser_type=getattr(self, "parser_type", None),
            features_base_dir=base_dir,
            features_path_type=features_path_type,
        )

        return module

    @staticmethod
    def detect_uri_pathtype(path) -> Tuple[str, PathType]:
        try:
            parsed_url = urlparse(path)
        except Exception:
            features_path_type = PathType.UNDEFINED
        else:
            if parsed_url.scheme == "file":
                features_path_type = PathType.PATH
                path = parsed_url.path
            elif parsed_url.scheme:
                features_path_type = PathType.URL
            else:
                features_path_type = PathType.UNDEFINED
        return path, features_path_type

    @classmethod
    def get_feature_pathlike_from_url_file(cls, path: Path) -> Tuple[str, PathType, Optional[str]]:
        config_parser = ConfigParser()
        config_parser.read(path)

        config_data = config_parser["InternetShortcut"]
        working_dir = config_data.get("WorkingDirectory", None)
        url = config_data.get("URL", None)
        return *cls.detect_uri_pathtype(url), working_dir  # type: ignore[return-value]

    @classmethod
    def get_feature_pathlike_from_desktop_file(cls, path: Path) -> Optional[str]:
        config_parser = ConfigParser()
        config_parser.read(path)

        config_data = config_parser["Desktop Entry"]
        return *cls.detect_uri_pathtype(config_data["URL"] if config_data["Type"] == "Link" else None), None  # type: ignore[return-value]

    @classmethod
    def get_feature_pathlike_from_weblock_file(cls, path: Path) -> str:
        return *cls.detect_uri_pathtype(cast(str, webloc_read(str(path)))), None  # type: ignore[return-value]
