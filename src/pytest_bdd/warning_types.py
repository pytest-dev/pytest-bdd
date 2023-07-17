from pytest import PytestWarning


class PytestBDDStepDefinitionWarning(PytestWarning):
    __module__ = "pytest_bdd"
