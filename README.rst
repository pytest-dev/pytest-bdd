BDD library for the py.test runner
==================================

.. image:: https://api.travis-ci.org/olegpidsadnyi/pytest-bdd.png
   :target: https://travis-ci.org/olegpidsadnyi/pytest-bdd

.. image:: https://pypip.in/v/pytest-bdd/badge.png
   :target: https://crate.io/packages/pytest-bdd/

.. image:: https://coveralls.io/repos/olegpidsadnyi/pytest-bdd/badge.png?branch=master
   :target: https://coveralls.io/r/olegpidsadnyi/pytest-bdd

pytest-bdd implements a subset of Gherkin language for the automation of the project
requirements testing and easier behavioral driven development.

Unlike many other BDD tools it doesn't require a separate runner and benefits from
the power and flexibility of the pytest. It allows to unify your unit and functional
tests, easier continuous integration server configuration and maximal reuse of the
tests setup.

Pytest fixtures written for the unit tests can be reused for the setup and actions
mentioned in the feature steps with dependency injection, which allows a true BDD
just-enough specification of the requirements without maintaining any context object
containing the side effects of the Gherkin imperative declarations.


Install pytest-bdd
------------------

::

    pip install pytest-bdd


Example
-------

An example test for a blog hosting software could look like this.
Note that `pytest-splinter <https://github.com/paylogic/pytest-splinter>`_ is used to get the browser fixture.

publish_article.feature:

.. code-block:: gherkin

    Feature: Blog
        A site where you can publish your articles.

    Scenario: Publishing the article
        Given I'm an author user
        And I have an article
        When I go to the article page
        And I press the publish button
        Then I should not see the error message
        And the article should be published  # Note: will query the database

test_publish_article.py:

.. code-block:: python

    from pytest_bdd import scenario, given, when, then

    @scenario('publish_article.feature', 'Publishing the article')
    def test_publish():
        pass


    @given('I have an article')
    def article(author):
        return create_test_article(author=author)


    @when('I go to the article page')
    def go_to_article(article, browser):
        browser.visit(urljoin(browser.url, '/manage/articles/{0}/'.format(article.id)))


    @when('I press the publish button')
    def publish_article(browser):
        browser.find_by_css('button[name=publish]').first.click()


    @then('I should not see the error message')
    def no_error_message(browser):
        with pytest.raises(ElementDoesNotExist):
            browser.find_by_css('.message.error').first


    @then('And the article should be published')
    def article_is_published(article):
        article.refresh()  # Refresh the object in the SQLAlchemy session
        assert article.is_published


Step aliases
------------

Sometimes it is needed to declare the same fixtures or steps with the
different names for better readability. In order to use the same step
function with multiple step names simply decorate it multiple times:

.. code-block:: python

    @given('I have an article')
    @given('there\'s an article')
    def article(author):
        return create_test_article(author=author)

Note that the given step aliases are independent and will be executed
when mentioned.

For example if you associate your resource to some owner or not. Admin
user can’t be an author of the article, but articles should have a
default author.

.. code-block:: gherkin

    Scenario: I'm the author
        Given I'm an author
        And I have an article


    Scenario: I'm the admin
        Given I'm the admin
        And there is an article


Step arguments
--------------

Often it's possible to reuse steps giving them a parameter(s).
This allows to have single implementation and multiple use, so less code.
Also opens the possibility to use same step twice in single scenario and with different arguments!
Important thing that argumented step names are not just strings but regular expressions.

Example:

.. code-block:: gherkin

    Scenario: Arguments for given, when, thens
        Given there are 5 cucumbers

        When I eat 3 cucumbers
        And I eat 2 cucumbers

        Then I should have 0 cucumbers


The code will look like:

.. code-block:: python

    import re
    from pytest_bdd import scenario, given, when, then


    @scenario('arguments.feature', 'Arguments for given, when, thens')
    def test_arguments():
        pass


    @given(re.compile('there are (?P<start>\d+) cucumbers'), converters=dict(start=int))
    def start_cucumbers(start):
        return dict(start=start, eat=0)


    @when(re.compile('I eat (?P<eat>\d+) cucumbers'), converters=dict(eat=int))
    def eat_cucumbers(start_cucumbers, eat):
        start_cucumbers['eat'] += eat


    @then(re.compile('I should have (?P<left>\d+) cucumbers'), converters=dict(left=int))
    def should_have_left_cucumbers(start_cucumbers, start, left):
        assert start_cucumbers['start'] == start
        assert start - start_cucumbers['eat'] == left

Example code also shows possibility to pass argument converters which may be useful if you need argument types
different than strings.


Multiline steps
---------------

As Gherkin, pytest-bdd supports multiline steps (aka `PyStrings <http://docs.behat.org/guides/1.gherkin.html#pystrings>`_).
But in much cleaner and powerful way:

.. code-block:: gherkin

    Scenario: Multiline step using sub indentation
        Given I have a step with:
            Some
            Extra
            Lines
        Then the text should be parsed with correct indentation

Step is considered as multiline one, if the **next** line(s) after it's first line, is indented relatively
to the first line. The step name is then simply extended by adding futher lines with newlines.
In the example above, the Given step name will be:

.. code-block:: python

    """I have a step with:\nSome\nExtra\nLines"""

You can of course register step using full name (including the newlines), but it seems more practical to use
step arguments and capture lines after first line (or some subset of them) into the argument:

.. code-block:: python

    import re

    from pytest_bdd import given, then, scenario


    @scenario(
        'multiline.feature',
        'Multiline step using sub indentation',
    )
    def test_multiline():
        pass


    @given(re.compile(r'I have a step with:\n(?P<text>.+)', re.DOTALL))
    def i_have_text(text):
        return text


    @then('the text should be parsed with correct indentation')
    def eat_cucumbers(i_have_text, text):
        assert i_have_text == text == """Some
    Extra
    Lines"""

Pay attention to the re.DOTALL option used for step registration. When used, .+ will also capture newlines.


Scenario parameters
-------------------
Scenario decorator can accept such optional keyword arguments:

* ``encoding`` - decode content of feature file in specific encoding. UTF-8 is default.
* ``example_converters`` - mapping to pass functions to convert example values provided in feature files.


Scenario outlines
-----------------

Scenarios can be parametrized to cover few cases. In Gherkin the variable
templates are written using corner braces as <somevalue>.
`Scenario outlines <http://docs.behat.org/guides/1.gherkin.html#scenario-outlines>`_ are supported by pytest-bdd
exactly as it's described in be behave docs.

Example:

.. code-block:: gherkin

    Scenario Outline: Outlined given, when, thens
        Given there are <start> cucumbers
        When I eat <eat> cucumbers
        Then I should have <left> cucumbers

        Examples:
        | start | eat | left |
        |  12   |  5  |  7   |

pytest-bdd feature file format also supports example tables in different way:


.. code-block:: gherkin

    Scenario Outline: Outlined given, when, thens
        Given there are <start> cucumbers
        When I eat <eat> cucumbers
        Then I should have <left> cucumbers

        Examples: Vertical
        | start | 12 | 2 |
        | eat   | 5  | 1 |
        | left  | 7  | 1 |

This form allows to have tables with lots of columns keeping the maximum text width predictable without significant
readability change.


The code will look like:

.. code-block:: python

    from pytest_bdd import given, when, then, scenario


    @scenario(
        'outline.feature',
        'Outlined given, when, thens',
        example_converters=dict(start=int, eat=float, left=str)
    )
    def test_outlined():
        pass


    @given('there are <start> cucumbers')
    def start_cucumbers(start):
        assert isinstance(start, int)
        return dict(start=start)


    @when('I eat <eat> cucumbers')
    def eat_cucumbers(start_cucumbers, eat):
        assert isinstance(eat, float)
        start_cucumbers['eat'] = eat


    @then('I should have <left> cucumbers')
    def should_have_left_cucumbers(start_cucumbers, start, eat, left):
        assert isinstance(left, str)
        assert start - eat == int(left)
        assert start_cucumbers['start'] == start
        assert start_cucumbers['eat'] == eat

Example code also shows possibility to pass example converters which may be useful if you need parameter types
different than strings.

It's also possible to parametrize the scenario on the python side.
The reason for this is that it is sometimes not needed to mention example table for every scenario.

The code will look like:

.. code-block:: python

    import pytest
    from pytest_bdd import mark, given, when, then


    # Here we use pytest to parametrize the test with the parameters table
    @pytest.mark.parametrize(
        ['start', 'eat', 'left'],
        [(12, 5, 7)])
    @mark.scenario(
        'parametrized.feature',
        'Parametrized given, when, thens',
    )
    # Note that we should take the same arguments in the test function that we use
    # for the test parametrization either directly or indirectly (fixtures depend on them).
    def test_parametrized(start, eat, left):
        """We don't need to do anything here, everything will be managed by the scenario decorator."""


    @given('there are <start> cucumbers')
    def start_cucumbers(start):
        return dict(start=start)


    @when('I eat <eat> cucumbers')
    def eat_cucumbers(start_cucumbers, start, eat):
        start_cucumbers['eat'] = eat


    @then('I should have <left> cucumbers')
    def should_have_left_cucumbers(start_cucumbers, start, eat, left):
        assert start - eat == left
        assert start_cucumbers['start'] == start
        assert start_cucumbers['eat'] == eat

The significant downside of this approach is inability to see the test table from the feature file.


Organizing your scenarios
-------------------------

The more features and scenarios you have, the more important becomes the question about their organization.
The things you can do (and that is also a recommended way):

* organize your feature files in the folders by semantic groups:

::

    features
    │
    ├──frontend
    │  │
    │  └──auth
    │     │
    │     └──login.feature
    └──backend
       │
       └──auth
          │
          └──login.feature

This looks fine, but how do you run tests only for certain feature?
As pytest-bdd uses pytest, and bdd scenarios are actually normal tests. But test files
are separate from the feature files, the mapping is up to developers, so the test files structure can look
completely different:

::

    tests
    │
    └──functional
       │
       └──test_auth.py
          │
          └ """Authentication tests."""
            from pytest_bdd import scenario

            @scenario('frontend/auth/login.feature')
            def test_logging_in_frontend():
                pass

            @scenario('backend/auth/login.feature')
            def test_logging_in_backend():
                pass


For picking up tests to run we can use
`tests selection <http://pytest.org/latest/usage.html#specifying-tests-selecting-tests>`_ technique. The problem is that
you have to know how your tests are organized, knowing ony the feature files organization is not enough.
`cucumber tags <https://github.com/cucumber/cucumber/wiki/Tags>`_ introduce standard way of categorizing your features
and scenarios, which pytest-bdd supports. For example, we could have:

.. code-block:: gherkin

    @login @backend
    Feature: Login

      @successful
      Scenario: Successful login


pytest-bdd uses `pytest markers <http://pytest.org/latest/mark.html#mark>`_ as a `storage` of the tags for the given
scenario test, so we can use standard test selection:

.. code-block:: bash

    py.test -k "@backend and @login and @successful"

The `@` helps to separate normal markers from the bdd ones.
Note that if you use pytest `--strict` option, all bdd tags mentioned in the feature files should be also in the
`markers` setting of the `pytest.ini` config.


Test setup
----------

Test setup is implemented within the Given section. Even though these steps
are executed imperatively to apply possible side-effects, pytest-bdd is trying
to benefit of the PyTest fixtures which is based on the dependency injection
and makes the setup more declarative style.

.. code-block:: python

    @given('I have a beautiful article')
    def article():
        return Article(is_beautiful=True)

This also declares a PyTest fixture "article" and any other step can depend on it.

.. code-block:: gherkin

    Given I have a beautiful article
    When I publish this article

When step is referring the article to publish it.

.. code-block:: python

    @when('I publish this article')
    def publish_article(article):
        article.publish()

Many other BDD toolkits operate a global context and put the side effects there.
This makes it very difficult to implement the steps, because the dependencies
appear only as the side-effects in the run-time and not declared in the code.
The publish article step has to trust that the article is already in the context,
has to know the name of the attribute it is stored there, the type etc.

In pytest-bdd you just declare an argument of the step function that it depends on
and the PyTest will make sure to provide it.

Still side effects can be applied in the imperative style by design of the BDD.

.. code-block:: gherkin

    Given I have a beautiful article
    And my article is published

Functional tests can reuse your fixture libraries created for the unit-tests and upgrade
them by applying the side effects.

.. code-block:: python

    given('I have a beautiful article', fixture='article')

    @given('my article is published')
    def published_article(article):
        article.publish()
        return article

This way side-effects were applied to our article and PyTest makes sure that all
steps that require the "article" fixture will receive the same object. The value
of the "published_article" and the "article" fixtures is the same object.

Fixtures are evaluated only once within the PyTest scope and their values are cached.
In case of Given steps and the step arguments mentioning the same given step makes
no sense. It won't be executed second time.

.. code-block:: gherkin

    Given I have a beautiful article
    And some other thing
    And I have a beautiful article  # Won't be executed, exception is raised


pytest-bdd will raise an exception even in the case of the steps that use regular expression
patterns to get arguments.


.. code-block:: gherkin

    Given I have 1 cucumbers
    And I have 2 cucumbers  # Exception is raised

Will raise an exception if the step is using the regular expression pattern.

.. code-block:: python

    @given(re.compile('I have (?P<n>\d+) cucumbers'))
    def cucumbers(n):
        return create_cucumbers(n)


Backgrounds
-----------

It's often the case that to cover certain feature, you'll need multiple scenarios. And it's logical that the
setup for those scenarios will have some common parts (if not equal). For this, there are `backgrounds`.
pytest-bdd implements gherkin `backgrounds <http://docs.behat.org/en/v2.5/guides/1.gherkin.html#backgrounds>`_ for
features.

.. code-block:: gherkin

    Feature: Multiple site support

      Background:
        Given a global administrator named "Greg"
        And a blog named "Greg's anti-tax rants"
        And a customer named "Wilson"
        And a blog named "Expensive Therapy" owned by "Wilson"

      Scenario: Wilson posts to his own blog
        Given I am logged in as Wilson
        When I try to post to "Expensive Therapy"
        Then I should see "Your article was published."

      Scenario: Greg posts to a client's blog
        Given I am logged in as Greg
        When I try to post to "Expensive Therapy"
        Then I should see "Your article was published."

In this example, all steps from the background will be executed before all the scenario's own given
steps, adding possibility to prepare some common setup for multiple scenarios in a single feature.
About background best practices, please read
`here <https://github.com/cucumber/cucumber/wiki/Background#good-practices-for-using-background>`_.


Reusing fixtures
----------------

Sometimes scenarios define new names for the fixture that can be
inherited. Fixtures can be reused with other names using given():

.. code-block:: python

    given('I have beautiful article', fixture='article')


Reusing steps
-------------

It is possible to define some common steps in the parent conftest.py and
simply expect them in the child test file.

common_steps.feature:

.. code-block:: gherkin

    Scenario: All steps are declared in the conftest
        Given I have a bar
        Then bar should have value "bar"

conftest.py:

.. code-block:: python

    from pytest_bdd import given, then


    @given('I have a bar')
    def bar():
        return 'bar'


    @then('bar should have value "bar"')
    def bar_is_bar(bar):
        assert bar == 'bar'

test_common.py:

.. code-block:: python

    @scenario('common_steps.feature', 'All steps are declared in the conftest')
    def test_conftest():
        pass

There are no definitions of the steps in the test file. They were
collected from the parent conftests.


Default steps
-------------

Here is the list of steps that are implemented inside of the pytest-bdd:

given
    * trace - enters the `pdb` debugger via `pytest.set_trace()`
when
    * trace - enters the `pdb` debugger via `pytest.set_trace()`
then
    * trace - enters the `pdb` debugger via `pytest.set_trace()`


Feature file paths
------------------

But default, pytest-bdd will use current module's path as base path for
finding feature files, but this behaviour can be changed by having
fixture named ``pytestbdd_feature_base_dir`` which should return the
new base path.

test_publish_article.py:

.. code-block:: python

    import pytest
    from pytest_bdd import scenario


    @pytest.fixture
    def pytestbdd_feature_base_dir():
        return '/home/user/projects/foo.bar/features'


    @scenario('publish_article.feature', 'Publishing the article')
    def test_publish():
        pass


Avoid retyping the feature file name
------------------------------------

If you want to avoid retyping the feature file name when defining your scenarios in a test file, use functools.partial.
This will make your life much easier when defining multiple scenarios in a test file.

For example:


test_publish_article.py:

.. code-block:: python

    from functools import partial

    import pytest_bdd


    scenario = partial(pytest_bdd.scenario, '/path/to/publish_article.feature')


    @scenario('Publishing the article')
    def test_publish():
        pass


    @scenario('Publishing the article as unprivileged user')
    def test_publish_unprivileged():
        pass


You can learn more about `functools.partial <http://docs.python.org/2/library/functools.html#functools.partial>`_ in the Python docs.


Hooks
-----

pytest-bdd exposes several pytest `hooks <http://pytest.org/latest/plugins.html#well-specified-hooks>`_
which might be helpful building useful reporting, visualization, etc on top of it:

* pytest_bdd_before_step(request, feature, scenario, step, step_func) - Called before step function
  is executed and it's arguments evaluated

* pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args) - Called after step function
  is successfully executed

* pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception) - Called when step
  function failed to execute

* pytest_bdd_step_validation_error(request, feature, scenario, step, step_func, step_func_args, exception) - Called
  when step failed to validate

* pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception) - Called when step lookup failed


Browser testing
---------------

Tools recommended to use for browser testing:

* `pytest-splinter <https://github.com/paylogic/pytest-splinter>`_ - pytest `splinter <http://splinter.cobrateam.info/>`_ integration for the real browser testing


Reporting
---------

It's important to have nice reporting out of your bdd tests. Cucumber introduced some kind of standard for
`json format <https://www.relishapp.com/cucumber/cucumber/docs/json-output-formatter>`_
which can be used for `this <https://wiki.jenkins-ci.org/display/JENKINS/Cucumber+Test+Result+Plugin>`_ jenkins
plugin

To have an output in json format:

::

    py.test --cucumberjson=<path to json report>


Test code generation helpers
----------------------------

For newcomers it's sometimes hard to write all needed test code without being frustrated.
To simplify their life, simple code generator was implemented. It allows to create fully functional
but of course empty tests and step definitions for given a feature file.
It's done as a separate console script provided by pytest-bdd package:

::

    pytest-bdd generate <feature file name> .. <feature file nameN>

It will print the generated code to the standard output so you can easily redirect it to the file:

::

    pytest-bdd generate features/some.feature > tests/functional/test_some.py


Advanced code generation
------------------------

For more experienced users, there's smart code generation/suggestion feature. It will only generate the
test code which is not yet there, checking existing tests and step definitions the same way it's done during the
test execution. The code suggestion tool is called via passing additional pytest arguments:

::

    py.test --generate-missing --feature features tests/functional

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


    @given('I have a custom bar')
    def I_have_a_custom_bar():
        """I have a custom bar."""

As as side effect, the tool will validate the files for format errors, also some of the logic bugs, for example the
ordering of the types of the steps.


Migration of your tests from versions 0.x.x-1.x.x
-------------------------------------------------

In version 2.0.0, the backwards-incompartible change was introduced: scenario function can now only be used as a
decorator. Reasons for that:

* test code readability is much higher using normal python function syntax;
* pytest-bdd internals are much cleaner and shorter when using single approach instead of supporting two;
* after moving to parsing-on-import-time approach for feature files, it's not possible to detect whether it's a
  decorator more or not, so to support it along with functional approach there needed to be special parameter
  for that, which is also a backwards-incompartible change.

To help users migrate to newer version, there's migration subcommand of the `pytest-bdd` console script:

::

    # run migration script
    pytest-bdd migrate <your test folder>

Under the hood the script does the replacement from this:

.. code-block:: python

    test_function = scenario('publish_article.feature', 'Publishing the article')

to this:

.. code-block:: python

    @scenario('publish_article.feature', 'Publishing the article')
    def test_function():
        pass


License
-------

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_.

© 2013 Oleg Pidsadnyi
