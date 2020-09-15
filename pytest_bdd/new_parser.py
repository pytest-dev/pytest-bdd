import io
import os.path
import textwrap
from collections import OrderedDict

import lark
import lark.indenter
import six

from pytest_bdd.parser import Step, Scenario, Feature, Examples
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
parser = lark.Lark(grammar, start="start", parser="lalr", postlex=TreeIndenter(), maybe_placeholders=True, debug=True)


def extract_text_from_step_docstring(docstring):
    content = docstring[4:-3]
    dedented = textwrap.dedent(content)
    assert dedented[-1] == "\n"
    dedented_without_newline = dedented[:-1]
    return dedented_without_newline


class TreeToGherkin(lark.Transformer):
    def gherkin_document(self, value):
        [feature] = value
        return feature

    def string(self, value):
        # TODO: Unescape characters?
        [s] = value
        return s

    def given(self, _):
        return pytest_bdd_types.GIVEN

    def when(self, _):
        return pytest_bdd_types.WHEN

    def then(self, _):
        return pytest_bdd_types.THEN

    def step_docstring(self, value):
        # TODO: Unescape escaped characters?
        [text] = value
        content = text[4:-3]
        dedented = textwrap.dedent(content)
        assert dedented[-1] == "\n"
        dedented_without_newline = dedented[:-1]
        return dedented_without_newline

    def step_arg(self, value):
        docstring, step_datatable = value
        return docstring, step_datatable

    def data_table_row(self, cols):
        # TODO: Unescape escaped PIPE char (|)
        return [col[:-1] for col in cols]

    def data_table(self, value):
        return value

    def step(self, value):
        step_line, step_arg = value
        if step_arg is not None:
            docstring, datatable = step_arg
        else:
            docstring = datatable = None

        step_type, step_name = step_line.children

        line = step_name.line
        return Step(
            name=six.text_type(step_name),
            type=step_type,
            indent=0,
            keyword=step_name + " ",
            line_number=line,
            docstring=docstring,
            datatable=datatable,
        )

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
            examples=Examples(),
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
    # type: (six.text_type) -> Feature
    tree = parser.parse(content)
    # print(tree.pretty())
    gherkin = TreeToGherkin().transform(tree)
    return gherkin


def parse_feature(basedir, filename, encoding="utf-8"):
    """Parse the feature file.

    :param str basedir: Feature files base directory.
    :param str filename: Relative path to the feature file.
    :param str encoding: Feature file encoding (utf-8 by default).
    """
    abs_filename = os.path.abspath(os.path.join(basedir, filename))
    rel_filename = os.path.join(os.path.basename(basedir), filename)

    with io.open(abs_filename, "rt", encoding=encoding) as f:
        content = f.read()

    parsed = parse(content)
    parsed.filename = abs_filename
    parsed.rel_filename = rel_filename
    return parsed
