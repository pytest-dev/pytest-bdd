import io
import os.path
from collections import OrderedDict

import lark
import lark.indenter
import six

from pytest_bdd.parser import Step, Scenario, Feature
from pytest_bdd import types as pytest_bdd_types


class TreeIndenter(lark.indenter.Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 8


with io.open(os.path.join(os.path.dirname(__file__), "parser_data/gherkin.grammar.lark")) as f:
    grammar = f.read()
parser = lark.Lark(grammar, start="start", parser="lalr", postlex=TreeIndenter())


class TreeToGherkin(lark.Transformer):
    def gherkin_document(self, value):
        [feature] = value
        return feature

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

    def tag(self, value):
        [tag] = value
        return tag

    def feature(self, value):
        try:
            feature_header = next(el for el in value if el.data == "feature_header")
            tag_lines = [el for el in feature_header.children if el.data == "tag_line"]
            tags = [el for tag_line in tag_lines for el in tag_line.children]
        except StopIteration:
            tags = []

        feature_line = next((el for el in value if el.data == "feature_line"))
        raw_scenarios = next((el for el in value if el.data == "scenarios"))

        [feature_name] = feature_line.children

        feature = Feature(
            scenarios=OrderedDict(),
            filename=None,
            rel_filename=None,
            name=six.text_type(feature_name),
            tags=tags,
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


def parse(content):
    tree = parser.parse(content)
    # print(tree.pretty())
    gherkin = TreeToGherkin().transform(tree)
    return gherkin
