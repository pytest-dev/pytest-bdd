import textwrap

from attr import attrib, attrs
from pytest import PytestWarning


@attrs
class PytestBDDScenarioExamplesExtraParamsWarning(PytestWarning):
    __module__ = "pytest_bdd"

    scenario = attrib()
    united_example_rows = attrib()

    def __str__(self):
        n = "\n"
        breadcrumbs_with_extra_param = (
            f"{row.breadcrumb}->{set(row.keys()-self.scenario.params)}" for row in self.united_example_rows
        )
        return textwrap.dedent(
            f"""\
        Example rows have params unused in steps:
            {n.join(breadcrumbs_with_extra_param)}
        """
        )


@attrs
class PytestBDDScenarioStepsExtraPramsWarning(PytestWarning):
    __module__ = "pytest_bdd"

    scenario = attrib()
    steps_extra_params = attrib()

    def __str__(self):
        return textwrap.dedent(
            f"""\
        Scenario {self.scenario.name} have params unmatched to examples:
            {", ".join(param for param in self.steps_extra_params)}
        """
        )


class PytestBDDStepDefinitionWarning(PytestWarning):
    __module__ = "pytest_bdd"
