from functools import partial
from textwrap import dedent

from pytest import mark, param

from pytest_bdd.struct_bdd.parser import StructBDDParser


@mark.parametrize(
    "kind,file_content",
    [
        partial(param, id="plain-yaml")(
            StructBDDParser.KIND.YAML.value,
            # language=yaml
            """\
            Name: Steps are executed one by one
            Description: |
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.
            Steps:
                - Step:
                    Name: Executed step by step
                    Description: Scenario description
                    Steps:
                        - Given: I have a foo fixture with value "foo"
                        - And: there is a list
                        - When: I append 1 to the list
                        - And: I append 2 to the list
                        - And: I append 3 to the list
                        - Then: foo should have value "foo"
                        - But: the list should be [1, 2, 3]
            """,
        ),
        partial(param, id="plain-hocon")(
            StructBDDParser.KIND.HOCON.value,
            # language=hocon
            r"""
              Name = Steps are executed one by one
              Description: "Steps are executed one by one. Given and When sections\nare not mandatory in some cases.\n",
              Steps: [
                {
                  Step: {
                    "Name": "Executed step by step",
                    "Description": "Scenario description",
                    "Steps": [
                      {"Given": "I have a foo fixture with value \"foo\""}
                      {"And": "there is a list"}
                      {"When": "I append 1 to the list"},
                      {"And": I append 2 to the list},
                      {"And": "I append 3 to the list"},
                      {"Then": "foo should have value \"foo\""},
                      {"But": "the list should be [1, 2, 3]"}
                    ]
                  }
                }
              ]
            """,
        ),
        partial(param, id="plain-json")(
            StructBDDParser.KIND.JSON.value,
            # language=json
            r"""{
              "Name": "Steps are executed one by one",
              "Description": "Steps are executed one by one. Given and When sections\nare not mandatory in some cases.\n",
              "Steps": [
                {
                  "Step": {
                    "Name": "Executed step by step",
                    "Description": "Scenario description",
                    "Steps": [
                      {"Given": "I have a foo fixture with value \"foo\""},
                      {"And": "there is a list"},
                      {"When": "I append 1 to the list"},
                      {"And": "I append 2 to the list"},
                      {"And": "I append 3 to the list"},
                      {"Then": "foo should have value \"foo\""},
                      {"But": "the list should be [1, 2, 3]"}
                    ]
                  }
                }
              ]
            }
            """,
        ),
        partial(param, id="plain-hjson")(
            StructBDDParser.KIND.HJSON.value,
            # language=hjson
            r"""{
              Name: Steps are executed one by one
              Description:
                '''
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                '''
              Steps: [
                {
                  Step: {
                    Name: Executed step by step
                    Description: 'Scenario description'
                    Steps: [
                      {Given: 'I have a foo fixture with value "foo"',}
                      {
                        And: there is a list
                      }
                      {When: 'I append 1 to the list'}
                      {And: 'I append 2 to the list',}
                      {And: 'I append 3 to the list',}
                      {Then: 'foo should have value "foo"',}
                      {But: 'the list should be [1, 2, 3]',}
                    ],
                  },
                },
              ],
            }
            """,
        ),
        partial(param, id="plain-json5")(
            StructBDDParser.KIND.JSON5.value,
            # language=json5
            r"""{
              Name: 'Steps are executed one by one',
              Description: 'Steps are executed one by one. Given and When sections\nare not mandatory in some cases.\n',
              Steps: [
                {
                  Step: {
                    Name: 'Executed step by step',
                    Description: 'Scenario description',
                    Steps: [
                      {Given: 'I have a foo fixture with value "foo"',},
                      {And: 'there is a list',},
                      {When: 'I append 1 to the list',},
                      {And: 'I append 2 to the list',},
                      {And: 'I append 3 to the list',},
                      {Then: 'foo should have value "foo"',},
                      {But: 'the list should be [1, 2, 3]',},
                    ],
                  },
                },
              ],
            }
            """,
        ),
        partial(param, id="plain-toml")(
            StructBDDParser.KIND.TOML.value,
            # language=toml
            """\
            Name = "Steps are executed one by one"
            Description='''
            Steps are executed one by one. Given and When sections
            are not mandatory in some cases.
            '''
            [[Steps]]
                [Steps.Step]
                Name = "Executed step by step"
                Description = "Scenario description"
                Steps = [
                    {Given = 'I have a foo fixture with value "foo"'},
                    {And = 'there is a list'},
                    {When = 'I append 1 to the list'},
                    {And = 'I append 2 to the list'},
                    {And = 'I append 3 to the list'},
                    {Then = 'foo should have value "foo"'},
                    {But = 'the list should be [1, 2, 3]'}
                ]
            """,
        ),
        partial(param, id="complex-yaml")(
            StructBDDParser.KIND.YAML.value,
            # language=yaml
            """\
            Name: Steps are executed one by one
            Description: |
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.
            Steps:
                - Step:
                    Name: Executed step by step
                    Description: Scenario description
                    Steps:
                        - I have a foo fixture with value "foo"
                        - And: there is a list
                        - When: I append 1 to the list
                        - Step:
                            Action: I append 2 to the list
                            Type: And
                        - Alternative:
                            - Step:
                                Steps:
                                    - And: I append 3 to the list
                                    - Then: foo should have value "foo"
                                    - But: the list should be [1, 2, 3]
            """,
        ),
        partial(param, id="complex-toml")(
            StructBDDParser.KIND.TOML.value,
            # language=toml
            """\
            Name = "Steps are executed one by one"
            Description='''
            Steps are executed one by one. Given and When sections
            are not mandatory in some cases.
            '''
            [[Steps]]
                [Steps.Step]
                Name = "Executed step by step"
                Description = "Scenario description"
                [[Steps.Step.Steps]]
                    Given = 'I have a foo fixture with value "foo"'
                [[Steps.Step.Steps]]
                    And = 'there is a list'
                [[Steps.Step.Steps]]
                    When = 'I append 1 to the list'
                [[Steps.Step.Steps]]
                    [Steps.Step.Steps.Step]
                        Action = 'I append 2 to the list'
                        Type = 'And'
                [[Steps.Step.Steps]]
                    [[Steps.Step.Steps.Alternative]]
                        [Steps.Step.Steps.Alternative.Step]
                            Steps = [
                                {And = 'I append 3 to the list'},
                                {Then = 'foo should have value "foo"'},
                                {But = 'the list should be [1, 2, 3]'}
                            ]
            """,
        ),
    ],
)
def test_steps(testdir, kind, file_content, tmp_path):
    (tmp_path / f"steps.bdd.{kind}").write_text(dedent(file_content))

    testdir.makeini(
        f"""\
        [pytest]
        bdd_features_base_dir={tmp_path}
        """
    )

    testdir.makepyfile(
        # language=python
        """\
        from textwrap import dedent
        from pytest_bdd import given, when, then, scenario, step

        @scenario("steps.bdd.{kind}", "Executed step by step")
        def test_steps(feature):
            assert feature.description == dedent('''\\
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.
                '''
            )

        @step('I have a foo fixture with value "foo"', target_fixture="foo", liberal=True)
        def foo():
            return "foo"

        @given("there is a list", target_fixture="results", liberal=True)
        def results():
            return []

        @when("I append 1 to the list")
        def append_1(results):
            results.append(1)

        @when("I append 2 to the list")
        def append_2(results):
            results.append(2)

        @when("I append 3 to the list")
        def append_3(results):
            results.append(3)

        @then('foo should have value "foo"')
        def foo_is_foo(foo):
            assert foo == "foo"

        @then("the list should be [1, 2, 3]")
        def check_results(results):
            assert results == [1, 2, 3]
        """.format(
            kind=kind
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


@mark.parametrize(
    "kind,file_content",
    [
        partial(param, id="plain-yaml")(
            StructBDDParser.KIND.YAML.value,
            """\
            Name: Steps are executed one by one
            Description: |
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.
            Steps:
                - Step:
                    Name: Executed step by step
                    Description: Scenario description
                    Steps:
                        - Given: I have a foo fixture with value "foo"
                        - And: there is a list
                        - When: I append 1 to the list
                        - And: I append 2 to the list
                        - And: I append 3 to the list
                        - Then: foo should have value "foo"
                        - But: the list should be [1, 2, 3]
            """,
        ),
    ],
)
def test_default_loader(testdir, kind, file_content):
    testdir.makefile(
        f".bdd.{kind}",
        steps=file_content,
    )

    testdir.makepyfile(
        # language=python
        """\
        from textwrap import dedent
        from pytest_bdd import given, when, then, scenario

        @scenario("steps.bdd.{kind}", "Executed step by step")
        def test_steps(feature):
            assert feature.description == dedent('''\\
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.
                '''
            )

        @given('I have a foo fixture with value "foo"', target_fixture="foo")
        def foo():
            return "foo"


        @given("there is a list", target_fixture="results")
        def results():
            return []


        @when("I append 1 to the list")
        def append_1(results):
            results.append(1)


        @when("I append 2 to the list")
        def append_2(results):
            results.append(2)


        @when("I append 3 to the list")
        def append_3(results):
            results.append(3)


        @then('foo should have value "foo"')
        def foo_is_foo(foo):
            assert foo == "foo"


        @then("the list should be [1, 2, 3]")
        def check_results(results):
            assert results == [1, 2, 3]
        """.format(
            kind=kind
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


@mark.parametrize(
    "kind,file_content",
    [
        partial(param, id="plain-yaml")(
            StructBDDParser.KIND.YAML.value,
            # language=yaml
            """\
            Name: Steps are executed one by one
            Description: |
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.
            Steps:
                - Step:
                    Name: Executed step by step
                    Description: Scenario description
                    Steps:
                        - Given: I have a foo fixture with value "foo"
                        - And: there is a list
                        - When: I append 1 to the list
                        - And: I append 2 to the list
                        - And: I append 3 to the list
                        - Then: foo should have value "foo"
                        - But: the list should be [1, 2, 3]
            """,
        ),
    ],
)
def test_autoload_feature_yaml(testdir, kind, file_content):
    testdir.makefile(
        f".bdd.feature.{kind}",
        steps=file_content,
    )

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, when, then

        @given('I have a foo fixture with value "foo"', target_fixture="foo")
        def foo():
            return "foo"

        @given("there is a list", target_fixture="results")
        def results():
            return []

        @when("I append 1 to the list")
        def append_1(results):
            results.append(1)

        @when("I append 2 to the list")
        def append_2(results):
            results.append(2)

        @when("I append 3 to the list")
        def append_3(results):
            results.append(3)

        @then('foo should have value "foo"')
        def foo_is_foo(foo):
            assert foo == "foo"

        @then("the list should be [1, 2, 3]")
        def check_results(results):
            assert results == [1, 2, 3]
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


@mark.parametrize(
    "file_content",
    [
        partial(param, id="simple")(
            # language=yaml
            """\
            Name: Examples are substituted
            Steps:
                - Given: I have <have> cucumbers
                - And: I eat <eat> cucumbers
                - Then: I have <left> cucumbers
            Examples:
                - Table:
                    Parameters: [ have, eat, left ]
                    Values:
                        - [ "12", 5, 7.0 ]
                        - [ "8.0", 3.0, "5" ]
            """,
        ),
    ],
)
def test_examples(testdir, file_content):
    testdir.makefile(
        ".bdd.yaml",
        steps=file_content,
    )

    testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import given, then, scenarios

        test_scenarios = scenarios("steps.bdd.yaml")

        @given('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count):
            return count

        @given('I eat {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            return cucumbers - count

        @then('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            assert count == cucumbers
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2, failed=0)


def test_dsl(testdir):
    testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import given, then
        from pytest_bdd.struct_bdd.model import Step, Table

        test_scenarios = Step(
            name="Examples are substituted",
            steps=[
                Step(type='Given', action='I have <have> cucumbers'),
                Step(type='And', action='I eat <eat> cucumbers'),
                Step(type='Then', action='I have <left> cucumbers')
            ],
            examples=[
                Table(
                    parameters=['have', 'eat', 'left'],
                    values=[
                        ['12', 5, 7.0],
                        ["8.0", 3.0, "5"]
                    ]
                )
            ]
        ).as_test(filename=__file__)


        @given('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count):
            return count

        @given('I eat {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            return cucumbers - count

        @then('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            assert count == cucumbers
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2, failed=0)


def test_dsl_decorator(testdir):
    testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import given, then
        from pytest_bdd.struct_bdd.model import Step, Table
        from pytest_bdd.model import Feature

        step = Step(
            name="Examples are substituted",
            steps=[
                Step(type='Given', action='I have <have> cucumbers'),
                Step(type='And', action='I eat <eat> cucumbers'),
                Step(type='Then', action='I have <left> cucumbers')
            ],
            examples=[
                Table(
                    type='Columned',
                    parameters=['have', 'eat', 'left'],
                    values=[
                        ['12', 8],
                        [5, 3.0],
                        ["7.0", "5"],
                    ]
                )
            ]
        )

        @step.as_test_decorator(filename=__file__)
        def test(feature:Feature, scenario):
            assert feature.name == "Examples are substituted"

        @given('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count):
            return count

        @given('I eat {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            return cucumbers - count

        @then('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            assert count == cucumbers
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2, failed=0)


def test_dsl_as_dict(testdir):
    testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import given, then
        from pytest_bdd.struct_bdd.model import Step

        step = Step.from_dict(
            dict(
                Name="Examples are substituted",
                Steps=[
                    dict(Given='I have <have> cucumbers'),
                    dict(And='I eat <eat> cucumbers'),
                    dict(Then='I have <left> cucumbers')
                ],
                Examples=[
                    dict(
                        Table=dict(
                            Parameters=['have', 'eat', 'left'],
                            Values=[
                                ['12', 5, 7.0],
                                ["8.0", 3.0, "5"]
                            ]
                        )
                    )
                ]
            )
        )

        test_sceanrios = step.as_test(filename=__file__)

        @given('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count):
            return count

        @given('I eat {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            return cucumbers - count

        @then('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            assert count == cucumbers
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2, failed=0)


def test_dsl_keyworded_steps(testdir):
    testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import given, then
        from pytest_bdd.struct_bdd.model import Step, Given, And, Then, Table

        step = Step(
            name="Examples are substituted",
            steps=[
                Given('I have <have> cucumbers'),
                And('I eat <eat> cucumbers'),
                Then('I have <left> cucumbers')
            ],
            examples=[
                Table(
                    parameters=['have', 'eat', 'left'],
                    values=[
                        ['12', 5, 7.0],
                        ["8.0", 3.0, "5"]
                    ]
                )
            ]
        )

        test_scenarios = step.as_test(filename=__file__)

        @given('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count):
            return count

        @given('I eat {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            return cucumbers - count

        @then('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            assert count == cucumbers
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2, failed=0)


def test_dsl_alternative_steps(testdir):
    testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import given, then, step
        from pytest_bdd.struct_bdd.model import Step, Given, And, Then, Table, Alternative, When

        test_scenarios = Step(
            name="Alternative steps",
            steps=[
                Given('I have <have> cucumbers'),
                Alternative(
                    steps=[
                        And('I eat <first_spend> cucumbers'),
                        And('I corrupt <first_spend> cucumbers'),
                    ]
                ),
                Alternative(
                    steps=[
                        When('I corrupt <second_spend> cucumbers'),
                        Given('I eat <second_spend> cucumbers'),
                    ]
                ),
                Then('I have <left> cucumbers')
            ],
            examples=[
                Table(
                    parameters=['have', 'first_spend', 'second_spend', 'left'],
                    values=[
                        ['12', 5, 2, 5.0],
                        ["8.0", 3.0, 4, "1"]
                    ]
                )
            ]
        ).as_test(filename=__file__)

        @given('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count):
            return count

        @given('I eat {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            return cucumbers - count

        @step('I corrupt {count:g} cucumbers', target_fixture="cucumbers", liberal=True)
        def foo(count, cucumbers):
            return cucumbers - count

        @then('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            assert count == cucumbers
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=8, failed=0)


def test_dsl_joined_tables(testdir):
    testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import given, then, step
        from pytest_bdd.struct_bdd.model import Step, Given, And, Then, Table, Join

        test_scenarios = Step(
            name="Alternative steps",
            steps=[
                Given('I have <have> cucumbers'),
                And('I <first_action> <first_spend> cucumbers'),
                Given('I <second_action> <second_spend> cucumbers'),
                Then('I have <left> cucumbers')
            ],
            examples=[
                Join(
                    tables=[
                        Table(
                            parameters=['have', 'first_spend', 'second_spend', 'left'],
                            values=[
                                ['12', 5, 2, 5.0],
                                ["8.0", 3.0, 4, "1"]
                            ]
                        ),
                        Table(
                            parameters=['first_action'],
                            values=[
                                ['eat'],
                                ["corrupt"]
                            ]
                        ),
                        Table(
                            parameters=['first_action', 'second_action'],
                            comments=["I don't like to eat corrupted cucumbers"],
                            values=[
                                ['eat', 'eat'],
                                ['eat', 'corrupt'],
                                ["corrupt", 'corrupt']
                            ]
                        ),
                    ]
                )
            ]
        ).as_test(filename=__file__)

        @given('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count):
            return count

        @given('I eat {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            return cucumbers - count

        @step('I corrupt {count:g} cucumbers', target_fixture="cucumbers", liberal = True)
        def foo(count, cucumbers):
            return cucumbers - count

        @then('I have {count:g} cucumbers', target_fixture="cucumbers")
        def foo(count, cucumbers):
            assert count == cucumbers
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=6, failed=0)
