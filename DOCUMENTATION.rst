.. toctree::
   :hidden:

Advanced Features
=================

Hooks
-----

.. NOTE:: Important difference from pytest-bdd_

pytest-bdd-ng exposes several `pytest hooks <http://pytest.org/latest/plugins.html#well-specified-hooks>`_
which might be helpful building useful reporting, visualization, etc on top of it:

* pytest_bdd_before_scenario(request, feature, scenario) - Called before scenario is executed
* pytest_bdd_run_scenario(request, feature, scenario) - Execution scenario protocol
* pytest_bdd_after_scenario(request, feature, scenario) - Called after scenario is executed
  (even if one of steps has failed)
* pytest_bdd_before_step(request, feature, scenario, step, step_func) - Called before step function
  is executed and it's arguments evaluated
* pytest_bdd_run_step(request, feature, scenario, step, previous_step) - Execution step protocol
* pytest_bdd_before_step_call(request, feature, scenario, step, step_func, step_func_args) - Called before step
  function is executed with evaluated arguments
* pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args) - Called after step function
  is successfully executed
* pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception) - Called when step
  function failed to execute
* pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception) - Called when step lookup failed
* pytest_bdd_match_step_definition_to_step(request, feature, scenario, step, previous_step) - Called to match step to step definition
* pytest_bdd_get_step_caller(request, feature, scenario, step, step_func, step_func_args, step_definition) - Called to get step caller. For example could be used to make steps async
* pytest_bdd_get_step_dispatcher(request, feature, scenario) - Provide alternative approach to execute scenario steps


Default steps
-------------

Here is the list of steps that are implemented inside of the pytest-bdd:

given
    * trace - enters the `pdb` debugger via `pytest.set_trace()`
when
    * trace - enters the `pdb` debugger via `pytest.set_trace()`
then
    * trace - enters the `pdb` debugger via `pytest.set_trace()`


Fixtures
--------

pytest-bdd-ng exposes several plugin fixtures to give more testing flexibility

* bdd_example - The current scenario outline parametrization.
* attach - Fixture to allow attach files to Gherkin report
* parameter_type_registry - Contains registry of user-defined types used in Cucumber expressions
* step_registry - Contains registry of all user-defined steps
* step_matcher- Contains matcher to help find step definition for selected step of scenario
* steps_left - Current scenario steps left to execute; Allow inject steps to execute:

.. code-block:: python

    from collections import deque

    from pytest_bdd.model import UserStep
    from pytest_bdd import when

    @when('I inject step "{keyword}" "{step_text}')
    def inject_step(steps_left: deque, keyword, step_text, scenario):
        steps_left.appendleft(UserStep(text=step_text, keyword=keyword, scenario=scenario))

StructBDD
---------
Gherkin itself isn't a perfect tool to describe complex Data Driven Scenarios with alternative paths to execute test.
For example it doesn't support next things:

* Few backgrounds per scenario
* Alternative flows for scenario to setup same state
* Alternative flows to describe same behavior defined by different steps
* Usage of parameters inside Backgrounds
* Joining of parameter tables, so full Cartesian product of parameters has to be listed in Examples
* Example tables on different scenario levels

For such scenarios StructBDD DSL was developed. It independent on underlying data format, but supports most common
formats for DSL development: YAML, Hocon, TOML, JSON5, HJSON out the box.

Steps could be defined as usual, and scenarios have different options. Let see.

steps.bdd.yaml

.. code-block:: yaml

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
                    - Step:
                        Steps:
                            - And: I append 4 to the list
                            - Then: foo should have value "foo"
                            - But: the list should be [1, 2, 4]


Alternative steps produce separate test launches for every of flows. If alternative steps are defined on different
levels - there would be Cartesian product of tests for every alternative step.

Scenario could be imported as usual, but with specified parser:

.. code-block:: python

    from textwrap import dedent
    from pytest_bdd import given, when, then, scenario
    from pytest_bdd.parser import StructBDDParser
    from functools import partial

    kind = StructBDDParser.KIND.YAML

    @scenario(f"steps.bdd.{kind}", "Executed step by step", parser=partial(StructBDDParser, kind=kind)
    def test_steps(feature):
        pass


Another option is to inject built scenario directly:

.. code-block:: python

    from pytest_bdd.struct_bdd.model import Step, Table

    test_cukes = Step(
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
    )


There is also an option to build Step from dict(and use your own file format/preprocessor)

.. code-block:: python

    from pytest_bdd.struct_bdd.model import Step

    cukes = Step.parse_obj(
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

    @cukes
    def test(feature:Feature, scenario):
        assert feature.name == "Examples are substituted"


Example tables could be joined:

.. code-block:: yaml

    Tags:
      - TopTag
    Name: StepName
    Action: "Do first <HeaderA>, <HeaderB>, <HeaderC>"
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

Install StructBDD:

::

    pip install pytest-bdd-ng[struct_bdd]

Reporting
---------

It's important to have nice reporting out of your bdd tests. Cucumber introduced some kind of standard for
`json format <https://www.relishapp.com/cucumber/cucumber/docs/json-output-formatter>`_
which can be used for, for example, by `this <https://plugins.jenkins.io/cucumber-testresult-plugin/>`_ Jenkins
plugin.

To have an output in json format:

::

    pytest --cucumberjson=<path to json report>

This will output an expanded (meaning scenario outlines will be expanded to several scenarios) cucumber format.

To enable gherkin-formatted output on terminal, use

::

    pytest -vv --gherkin-terminal-reporter

Allure reporting is also in place https://docs.qameta.io/allure and based on
`allure-pytest` https://pypi.org/project/allure-pytest/ plugin. Usage is same.

To install plugin
#################

::

    pip install pytest-bdd-ng[allure]


Test code generation helpers
----------------------------

For newcomers it's sometimes hard to write all needed test code without being frustrated.
To simplify their life, simple code generator was implemented. It allows to create fully functional
but of course empty tests and step definitions for given a feature file.
It's done as a separate console script provided by pytest-bdd package:

::

    pytest --generate --feature <feature file name> .. <feature file nameN>

It will print the generated code to the standard output so you can easily redirect it to the file:

::

    pytest --generate --feature features/some.feature > tests/functional/test_some.py


Advanced code generation
------------------------

For more experienced users, there's smart code generation/suggestion feature. It will only generate the
test code which is not yet there, checking existing tests and step definitions the same way it's done during the
test execution. The code suggestion tool is called via passing additional pytest arguments:

::

    pytest --generate-missing --feature features tests/functional

The output will be like:

::

    ============================= test session starts ==============================
    platform linux2 -- Python 2.7.6 -- py-1.4.24 -- pytest-2.6.2
    plugins: xdist, pep8, cov, cache, bdd, bdd, bdd
    collected 2 items

    Scenario is not bound to any test: "Code is generated for scenarios which are not bound to any tests" in feature "Missing code generation" in /tmp/pytest-552/testdir/test_generate_missing0/tests/generation.feature
    --------------------------------------------------------------------------------

    Step is not defined: "I have a custom bar" in scenario: "Code is generated for scenario steps which are not yet defined(implemented)" in feature "Missing code generation" in /tmp/pytest-552/testdir/test_generate_missing0/tests/generation.feature
    --------------------------------------------------------------------------------
    Please place the code above to the test file(s):

    @scenario('tests/generation.feature', 'Code is generated for scenarios which are not bound to any tests')
    def test_Code_is_generated_for_scenarios_which_are_not_bound_to_any_tests():
        """Code is generated for scenarios which are not bound to any tests."""


    @given("I have a custom bar")
    def I_have_a_custom_bar():
        """I have a custom bar."""

As as side effect, the tool will validate the files for format errors, also some of the logic bugs, for example the
ordering of the types of the steps.
