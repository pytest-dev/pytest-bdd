import io
import logging
import os.path
from collections import OrderedDict

import lark
import lark.indenter
import six

from pytest_bdd.feature import Step, Scenario, Feature
from pytest_bdd import types as pytest_bdd_types


class TreeIndenter(lark.indenter.Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 8


with io.open(os.path.join(os.path.dirname(__file__), "gherkin.grammar.lark")) as f:
    grammar = f.read()
parser = lark.Lark(grammar, start="start", parser="lalr", postlex=TreeIndenter())


test_src = '''\
@atag @asecondtag
Feature: a feature
    Scenario: scenario 1
        Given I have a bar
            """

            docstring
            dsad
            """
        When I want a bar
        Then I get a bar
    Scenario: scenario 2
'''


class TreeToGherkin(lark.Transformer):
    def gherkin_document(self, value):
        return value

    def string(self, value):
        [s] = value
        return s

    def given(self, _):
        return pytest_bdd_types.GIVEN

    def when(self, _):
        return pytest_bdd_types.WHEN

    def then(self, _):
        return pytest_bdd_types.THEN

    def step(self, value):
        step_line, *step_docstring = value
        step_type, step_name = step_line.children
        line = step_name.line
        return Step(name=six.text_type(step_name), type=step_type, indent=0, keyword=step_name + " ", line_number=line)

    def scenario(self, value):
        scenario_line, *steps = value
        [scenario_name] = scenario_line.children

        return {
            "name": six.text_type(scenario_name),
            "line_number": scenario_name.line,
            "example_converters": None,
            "tags": None,
            "steps": steps,
        }

    def feature(self, value):
        feature_header, feature_line, raw_scenarios = value
        [feature_name] = feature_line.children

        feature = Feature(
            scenarios=OrderedDict(),
            filename=None,
            rel_filename=None,
            name=six.text_type(feature_line),
            tags=None,
            examples=None,
            background=None,
            line_number=feature_name.line,
            description=None,
        )
        for raw_scenario in raw_scenarios.children:
            scenario = Scenario(feature, name=raw_scenario["name"], line_number=raw_scenario["line_number"])
            feature.scenarios[scenario.name] = scenario
            for step in raw_scenario["steps"]:
                scenario.add_step(step)
        return feature


def test():
    tree = parser.parse(test_src)
    # print(tree.pretty())
    gherkin = TreeToGherkin().transform(tree)
    print(gherkin)


if __name__ == "__main__":
    test()
