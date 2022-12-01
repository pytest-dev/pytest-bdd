from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from pathlib import Path
from uuid import uuid4

from pytest import Module as PytestModule

from pytest_bdd.model.messages import Message
from pytest_bdd.scenario import _scenarios
from pytest_bdd.steps import StepHandler
from pytest_bdd.utils import convert_str_to_python_name


class Module(PytestModule):
    def collect(self):
        StepHandler.Registry.inject_registry_fixture_and_register_steps(self.obj)
        try:
            registry = self.obj.step_registry.__registry__.registry
        except AttributeError:
            registry = set()
        config = self.session.config
        if config.option.messages_ndjson_path is not None:
            for step_definition in registry:
                config.hook.pytest_bdd_message(
                    config=config, message=Message(stepDefinition=step_definition.as_message(config=config))
                )
        return super().collect()


class FeatureFileModule(PytestModule):
    def _getobj(self):
        return self._build_test_module()

    def _build_test_module(self):
        module_name = convert_str_to_python_name(f"{Path(self.fspath).name}_{uuid4()}")

        module_spec = ModuleSpec(module_name, None)
        module = module_from_spec(module_spec)

        _scenarios(
            feature_paths=[self.fspath],
            scenario_filter_or_scenario_name=None,
            return_test_decorator=False,
            parser_type=getattr(self, "parser_type", None),
            _caller_module_locals=module.__dict__,
            _caller_module_path=self.fspath,
        )

        return module
