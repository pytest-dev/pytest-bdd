from pytest import Module as PytestModule

from pytest_bdd.steps import StepHandler


class Module(PytestModule):
    def collect(self):
        StepHandler.Registry.inject_registry_fixture_and_register_steps(self.obj)
        return super().collect()
