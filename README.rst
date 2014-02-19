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
==================

::

    pip install pytest-bdd

Example
=======

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

    test_publish = scenario('publish_article.feature', 'Publishing the article')


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
============

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
==============

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

    test_arguments = scenario('arguments.feature', 'Arguments for given, when, thens')

    @given(re.compile('there are (?P<start>\d+) cucumbers'))
    def start_cucumbers(start):
        # note that you always get step arguments as strings, convert them on demand
        start = int(start)
        return dict(start=start, eat=0)


    @when(re.compile('I eat (?P<eat>\d+) cucumbers'))
    def eat_cucumbers(start_cucumbers, eat):
        eat = int(eat)
        start_cucumbers['eat'] += eat


    @then(re.compile('I should have (?P<left>\d+) cucumbers'))
    def should_have_left_cucumbers(start_cucumbers, start, left):
        start, left = int(start), int(left)
        assert start_cucumbers['start'] == start
        assert start - start_cucumbers['eat'] == left

Scenario parameters
===================
Scenario can accept `encoding` param to decode content of feature file in specific encoding. UTF-8 is default.

Step parameters
===============

Scenarios can be parametrized to cover few cases. In Gherkin the variable
templates are written using corner braces as <somevalue>.

Example:

.. code-block:: gherkin

    Scenario: Parametrized given, when, thens
        Given there are <start> cucumbers
        When I eat <eat> cucumbers
        Then I should have <left> cucumbers

Unlike other tools, pytest-bdd implements the scenario outline not in the
feature files, but in the python code using pytest parametrization.
The reason for this is that it is very often that some simple pythonic type
is needed in the parameters like a datetime or a dictionary, which makes it
more difficult to express in the text files and preserve the correct format.

The code will look like:

.. code-block:: python

    import pytest
    from pytest_bdd import scenario, given, when, then

    # Here we use pytest to parametrize the test with the parameters table
    @pytest.mark.parametrize(
        ['start', 'eat', 'left'],
        [(12, 5, 7)])
    @scenario(
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

Test setup
==========

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


Reusing fixtures
================

Sometimes scenarios define new names for the fixture that can be
inherited. Fixtures can be reused with other names using given():

.. code-block:: python

    given('I have beautiful article', fixture='article')

Reusing steps
=============

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

    test_conftest = scenario('common_steps.feature', 'All steps are declared in the conftest')

There are no definitions of the steps in the test file. They were
collected from the parent conftests.

Feature file paths
==================

But default, pytest-bdd will use current module’s path as base path for
finding feature files, but this behaviour can be changed by having
fixture named ‘pytestbdd_feature_base_dir’ which should return the
new base path.

test_publish_article.py:

.. code-block:: python

    import pytest
    from pytest_bdd import scenario


    @pytest.fixture
    def pytestbdd_feature_base_dir():
        return '/home/user/projects/foo.bar/features'

    test_publish = scenario('publish_article.feature', 'Publishing the article')


Avoid retyping the feature file name
====================================

If you want to avoid retyping the feature file name when defining your scenarios in a test file, use functools.partial.
This will make your life much easier when defining multiple scenarios in a test file.

For example:


test_publish_article.py:

.. code-block:: python

    from functools import partial

    import pytest_bdd


    scenario = partial(pytest_bdd.scenario, '/path/to/publish_article.feature')

    test_publish = scenario('Publishing the article')
    test_publish_unprivileged = scenario('Publishing the article as unprivileged user')


You can learn more about `functools.partial <http://docs.python.org/2/library/functools.html#functools.partial>`_ in the Python docs.

Hooks
=====

pytest-bdd exposes several pytest `hooks <http://pytest.org/latest/plugins.html#well-specified-hooks>`_
which might be helpful building useful reporting, visualization, etc on top of it:

    * pytest_bdd_before_step(request, feature, scenario, step, step_func, step_func_args) - Called before step function
      is executed

    * pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args) - Called after step function
      is successfully executed

    * pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception) - Called when step
      function failed to execute

    * pytest_bdd_step_validation_error(request, feature, scenario, step, step_func, step_func_args, exception) - Called
      when step failed to validate

    * pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception) - Called when step lookup failed


Subplugins
==========

The pytest BDD has plugin support, and the main purpose of plugins
(subplugins) is to provide useful and specialized fixtures.

List of known subplugins:

    *  pytest-bdd-splinter - collection of fixtures for the real browser BDD testing

License
=======

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_.

© 2013 Oleg Pidsadnyi
