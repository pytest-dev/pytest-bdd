from functools import partial
from operator import contains
from textwrap import dedent

from gherkin.pickles.compiler import Compiler
from yaml import FullLoader, load

from pytest_bdd import ast
from pytest_bdd.struct_bdd import ast_builder
from pytest_bdd.struct_bdd.model import Step, StepSchema


def test_load_simplest_step():
    StepSchema().load({})


def test_load_simplest_step_with_steps():
    doc = dedent(
        """\
        Steps: []
        """
    )

    data = load(doc, Loader=FullLoader)

    step = StepSchema().load(data)
    assert step.steps == []
    routes = list(step.routes)
    assert len(routes) == 1
    route = routes[0]
    assert route.tags == []
    assert len(route.steps) == 1
    step = route.steps[0]
    assert step.action is None


def test_load_simplest_step_with_text_steps():
    doc = dedent(
        """\
        Steps:
          - Do something
        """
    )

    data = load(doc, Loader=FullLoader)

    step: Step = StepSchema().load(data)
    assert step.steps[0].type is None
    assert step.steps[0].action == "Do something"

    routes = list(step.routes)
    assert len(routes) == 1
    route = routes[0]
    assert route.tags == []
    assert route.steps[0].action is None
    assert route.steps[1] == step.steps[0]


def test_load_actioned_step_with_text_steps():
    doc = dedent(
        """\
        Action: "First do"
        Steps:
          - Do something
        """
    )

    data = load(doc, Loader=FullLoader)

    step: Step = StepSchema().load(data)
    assert step.steps[0].type is None
    assert step.steps[0].action == "Do something"

    routes = list(step.routes)
    assert len(routes) == 1
    route = routes[0]
    assert route.tags == []
    assert route.steps == [step, step.steps[0]]


def test_load_actioned_step_with_alternative_text_steps():
    doc = dedent(
        """\
        Action: "First do"
        Steps:
          - Alternative:
            - Do something
            - Do something else
        """
    )

    data = load(doc, Loader=FullLoader)

    step: Step = StepSchema().load(data)

    routes = list(step.routes)
    assert len(routes) == 2
    assert routes[0].steps == [step, step.steps[0].steps[0]]
    assert routes[1].steps == [step, step.steps[0].steps[1]]


def test_load_simplest_step_with_keyworded_steps():
    doc = dedent(
        """\
        Steps:
          - Given: Do something
          - When: Do something
          - Then: Do something
          - And: Do something
          - "*": Do something
        """
    )

    data = load(doc, Loader=FullLoader)

    step = StepSchema().load(data)

    routes = list(step.routes)
    assert len(routes) == 1


def test_load_step_with_single_simplest_steps():
    try:
        doc = dedent(
            """\
            Steps:
                - Step: {}
            """
        )

        data = load(doc, Loader=FullLoader)

        StepSchema().load(data)
    except Exception as e:
        raise AssertionError from e


def test_node_module_load_for_step():
    try:
        doc = dedent(
            """\
            Name: StepName
            Tags:
              - StepTag
              - StepTag
            Description: |
                Multiline

                Step description
            Comments:
              - Very nice comment
            Steps: []
            """
        )

        data = load(doc, Loader=FullLoader)

        StepSchema().load(data)
    except Exception as e:
        raise AssertionError from e


def test_data_load():
    try:
        doc = dedent(
            """\
            Name: StepName
            Data:
              - Table:
                  Tags:
                    - StepDataTableTag
                  Name: StepDataTableName
                  Description: StepDataTableDescription
                  Type: Columned
                  Parameters:
                    - StepDataTableParametersHeader1
                    - StepDataTableParametersHeader2
                  Values:
                    - [ a, b, c ]
                    - [ d, e, f ]
            Steps: []
            """
        )

        data = load(doc, Loader=FullLoader)

        StepSchema().load(data)
    except Exception as e:
        raise AssertionError from e


def test_nested_data_load():
    try:
        doc = dedent(
            """\
            Name: StepName
            Data:
              - Table:
                  Parameters:
                    - StepDataTableParametersHeader1
                    - StepDataTableParametersHeader2
                  Values:
                    - [ a, b, c ]
                    - [ d, e, f ]
              - Table:
                  Parameters:
                    - StepDataTableParametersHeader3
                    - StepDataTableParametersHeader4
                  Values: [ ]
              - Join:
                  - Table:
                      Parameters:
                        - StepDataTableParametersHeader1
                        - StepDataTableParametersHeader2
                      Values:
                        - [ a, b, c ]
                        - [ d, e, f ]
                  - Table:
                      Parameters:
                        - StepDataTableParametersHeader3
                        - StepDataTableParametersHeader4
                      Values: [ ]
            Steps: []
            """
        )

        data = load(doc, Loader=FullLoader)

        StepSchema().load(data)
    except Exception as e:
        raise AssertionError from e


def test_nested_examples_load():
    try:
        doc = dedent(
            """\
            Name: StepName
            Examples:
              - Table:
                  Parameters:
                    - StepDataTableParametersHeader1
                    - StepDataTableParametersHeader2
                  Values:
                    - [ a, b, c ]
                    - [ d, e, f ]
              - Table:
                  Parameters:
                    - StepDataTableParametersHeader3
                    - StepDataTableParametersHeader4
                  Values: [ ]
              - Join:
                  - Table:
                      Parameters:
                        - StepDataTableParametersHeader1
                        - StepDataTableParametersHeader2
                      Values:
                        - [ a, b, c ]
                        - [ d, e, f ]
                  - Table:
                      Parameters:
                        - StepDataTableParametersHeader3
                        - StepDataTableParametersHeader4
                      Values: [ ]
            Steps: []
            """
        )

        data = load(doc, Loader=FullLoader)

        StepSchema().load(data)
    except Exception as e:
        raise AssertionError from e


def test_tags_steps_examples_load():
    doc = dedent(
        """\
        Tags:
          - TopTag
        Name: StepName
        Action: "Do first"
        Examples:
          - Table:
              Tags:
                - ExampleTag
              Parameters:
                [ Header1, Header2, Header3 ]
              Values:
                - [ a, b, c ]
                - [ d, e, f ]
        Steps:
          - Given: "Do next"
          - Step:
              Action: "Do something else"
              Tags:
                - StepTag
              Examples:
                  - Table:
                      Tags:
                        - StepExampleTag
                      Parameters:
                        [ Header4, Header5, Header6 ]
                      Values:
                        - [ g, h, i ]
                        - [ j, k, l ]
          - "Do last"
        """
    )

    data = load(doc, Loader=FullLoader)

    step = StepSchema().load(data)

    routes = list(step.routes)

    assert len(routes) == 1
    route = routes[0]
    assert all(map(partial(contains, route.tags), ["TopTag", "ExampleTag", "StepTag", "StepExampleTag"]))
    assert all(
        map(
            partial(contains, route.example_table.parameters),
            ["Header1", "Header2", "Header3", "Header4", "Header5", "Header6"],
        )
    )
    assert len(route.example_table.values) == 4

    document_ast = ast_builder.DocumentASTBuilder(step).build()
    document_ast.gherkin_document.uri = "uri"

    row_document_ast = ast.ASTSchema().dump(document_ast)
    pickles = Compiler().compile(row_document_ast["gherkinDocument"])
    assert len(pickles) == 4


def test_tags_steps_examples_load_complex():
    doc = dedent(
        """\
        Tags:
          - TopTag
        Name: StepName
        Action: "Do first"
        Examples:
          - Join:
            - Table:
                Tags:
                  - ExampleTagA
                Parameters:
                  [ HeaderA, HeaderB, HeaderC ]
                Values:
                  - [ A1, B1, C1 ]
                  - [ A2, B2, C2 ]
            - Table:
                Tags:
                  - ExampleTagB
                Parameters:
                  [ HeaderD ]
                Values:
                  - [ D1 ]
                  - [ D2 ]
                  - [ D3 ]
          - Table:
              Tags:
                - ExampleTagC
              Parameters:
                [ HeaderK ]
              Values:
                - [ K1 ]
                - [ K2 ]
                - [ K3 ]
        Steps:
          - Alternative:
              - Step:
                  Action: "Do something else"
                  Tags:
                    - StepTagA
                  Examples:
                      - Join:
                          - Table:
                              Tags:
                                - StepExampleTagA
                              Parameters:
                                [ HeaderE, HeaderF ]
                              Values:
                                - [ E1, F1 ]
                                - [ E2, F2 ]
              - Step:
                  Action: "Do next"
                  Tags:
                    - StepTagB
                  Examples:
                      - Join:
                          - Table:
                              Type: Columned
                              Tags:
                                - StepExampleTagB
                              Parameters:
                                [ HeaderG, HeaderH ]
                              Values:
                                - [ G1, G2 ]
                                - [ H1, H2 ]
                          - Table:
                              Tags:
                                - StepExampleTagC
                              Parameters:
                                [ HeaderI, HeaderJ ]
                              Values:
                                - [ I1, J1 ]
                                - [ I2, J2 ]
        """
    )

    data = load(doc, Loader=FullLoader)

    step = StepSchema().load(data)

    routes = list(step.routes)

    assert len(routes) == 4

    assert len(routes[0].example_table.values) == 12
    assert len(routes[1].example_table.values) == 6
    assert len(routes[2].example_table.values) == 24
    assert len(routes[3].example_table.values) == 12

    assert all(
        map(partial(contains, routes[0].tags), ["TopTag", "ExampleTagA", "ExampleTagB", "StepTagA", "StepExampleTagA"])
    )
    assert all(
        map(
            partial(contains, routes[0].example_table.parameters),
            ["HeaderC", "HeaderF", "HeaderA", "HeaderE", "HeaderB", "HeaderD"],
        )
    )

    assert all(map(partial(contains, routes[1].tags), ["ExampleTagC", "StepExampleTagA", "StepTagA", "TopTag"]))
    assert all(map(partial(contains, routes[1].example_table.parameters), routes[1].example_table.parameters))

    assert all(
        map(
            partial(contains, routes[2].tags),
            ["TopTag", "StepExampleTagB", "StepExampleTagC", "ExampleTagB", "StepTagB", "ExampleTagA"],
        )
    )
    assert all(
        map(
            partial(contains, routes[2].example_table.parameters),
            ["HeaderG", "HeaderC", "HeaderI", "HeaderA", "HeaderH", "HeaderB", "HeaderJ", "HeaderD"],
        )
    )

    assert all(
        map(
            partial(contains, routes[3].tags),
            ["TopTag", "StepExampleTagB", "StepExampleTagC", "ExampleTagC", "StepTagB"],
        )
    )
    assert all(
        map(
            partial(contains, routes[3].example_table.parameters),
            ["HeaderG", "HeaderK", "HeaderI", "HeaderH", "HeaderJ"],
        )
    )


def test_tags_steps_examples_joined_by_value_load():
    doc = dedent(
        """\
        Tags:
          - TopTag
        Name: StepName
        Action: "Do first"
        Examples:
          - Join:
            - Table:
                Tags:
                  - ExampleTagA
                Parameters:
                  [ HeaderA, HeaderB ]
                Values:
                  - [ A1, B1]
                  - [ A2, B2]
            - Table:
                Tags:
                  - ExampleTagB
                Parameters:
                  [ HeaderB, HeaderC ]
                Values:
                  - [ B1, C1 ]
                  - [ B2, C2 ]
                  - [ B3, C3 ]
        Steps: []
        """
    )

    data = load(doc, Loader=FullLoader)

    step = StepSchema().load(data)

    routes = list(step.routes)

    assert len(routes) == 1

    assert len(routes[0].example_table.values) == 2


def test_load_nested_steps():
    try:
        doc = dedent(
            """\
        Steps:
          - Alternative:
              - Given: Do something
              - When: Do something
              - Then: Do something
              - And: Do something
              - "*": Do something
          - Given: Do something
          - When: Do something
          - Then: Do something
          - And: Do something
          - "*": Do something
          - Step:
              Action: Do something
        """
        )

        data = load(doc, Loader=FullLoader)

        StepSchema().load(data)
    except Exception as e:
        raise AssertionError from e
