import collections

import pyparsing as pp

from pytest_bdd.parser import Feature, ScenarioTemplate, Step

pp.enable_all_warnings()

any_char = pp.Regex(r"[^\n]+").set_name("any_char")

given_kw = pp.Literal("Given")
when_kw = pp.Literal("When")
then_kw = pp.Literal("Then")

step_kw = given_kw | when_kw | then_kw

scenario_kw = pp.Literal("Scenario")

step = pp.Group(step_kw("keyword") + any_char("name") + pp.LineEnd())
step.set_name("step")

steps = pp.Group(step[1, ...])("steps")

scenario = pp.Group(scenario_kw + ":" + any_char("name") + pp.LineEnd() + steps)
scenario.set_name("scenario")


scenarios = pp.Group(scenario("scenario")[1, ...])("scenarios")

start = scenarios
start.set_name("start")

start.create_diagram("/tmp/gherkin.html")

start.set_default_whitespace_chars(" \t")

input = """
Scenario: My first scenario
    Given I have a step
    When I do something
    Then I should see something else
"""

parsed = start.parse_string(input, parse_all=True)

print(parsed)


def transform(tokens: pp.ParseResults):
    res = tokens.as_dict()
    print(res)

    feature = Feature(
        scenarios=collections.OrderedDict(),
        filename="",
        rel_filename="",
        name=None,
        tags=set(),
        line_number=0,
        description="",
        background=None,
    )
    for scenario_p in tokens.scenarios:
        scenario = ScenarioTemplate(
            feature=feature,
            name=scenario_p.name,
            line_number=0,
            templated=False,
        )
        feature.scenarios[scenario.name] = scenario

        for step_p in scenario_p.steps:
            step = Step(
                name=step_p.name,
                type=step_p.keyword,
                line_number=0,
                indent=0,
                keyword=step_p.keyword.strip(),
            )
            scenario.add_step(step)
    return feature


document = transform(parsed)

print(document)


input = """
Scenario: My first scenario
    Given I have a step
    When I do something
    Then I should see something else
"""

parsed = start.parse_string(input, parse_all=True)

print(parsed.as_dict())
