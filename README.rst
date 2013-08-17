BDD library for the py.test runner
==================================

.. |Build Status| image:: https://api.travis-ci.org/olegpidsadnyi/pytest-bdd.png
   :target: https://travis-ci.org/olegpidsadnyi/pytest-bdd
.. |Pypi| image:: https://pypip.in/v/pytest-bdd/badge.png
   :target: https://crate.io/packages/pytest-bdd/
.. |Coverrals| image:: https://coveralls.io/repos/olegpidsadnyi/pytest-bdd/badge.png?branch=master
   :target: https://coveralls.io/r/olegpidsadnyi/pytest-bdd


Install pytest-bdd
==================

::

    pip install pytest-bdd

Example
=======

publish\_article.feature:

::

    Scenario: Publishing the article
        Given I'm an author user
        And I have an article
        When I go to the article page
        And I press the publish button
        Then I should not see the error message
        And the article should be published  # Note: will query the database

test\_publish\_article.py:

::

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

::

    @given('I have an article')
    @given('there\'s an article')
    def article(author):
        return create_test_article(author=author)

Note that the given step aliases are independent and will be executed
when mentioned.

For example if you assoicate your resource to some owner or not. Admin
user can’t be an author of the article, but article should have some
default author.

::

    Scenario: I'm the author
        Given I'm an author
        And I have an article


    Scenario: I'm the admin
        Given I'm the admin
        And there is an article

Step parameters
===============

Sometimes it is hard to write good scenarios without duplicating most of
contents of existing scenario. For example if you create some object
with static param value, you might want to create another test with
different param value. By Gherkin specification it’s possible to have
parameters in steps: http://docs.behat.org/guides/1.gherkin.html
Example:

::

    Scenario: Parametrized given, when, thens
        Given there are <start> cucumbers
        When I eat <eat> cucumbers
        Then I should have <left> cucumbers

As you can see we don’t use Scenario Outline, but use just Scenario,
just because it’s simple to implement for pytest.

The code will look like:

::

    # here we use pytest power to parametrize test
    @pytest.mark.parametrize(
        ['start', 'eat', 'left'],
        [(12, 5, 7)])
    @scenario(
        'parametrized.feature',
        'Parametrized given, when, thens',
    )
    # note that we should receive same arguments in function that we use for test parametrization either directly
    # or indirectly (throught fixtures)
    def test_parametrized(start, eat, left):
        """We don't need to do anything here, everything will be managed by scenario decorator."""


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

Reuse fixtures
==============

Sometimes scenarios define new names for the fixture that can be
inherited. Fixtures can be reused with other names using given():

::

    given('I have beautiful article', fixture='article')

Reuse steps
===========

It is possible to define some common steps in the parent conftest.py and
simply expect them in the child test file.

common\_steps.feature:

::

    Scenario: All steps are declared in the conftest
        Given I have a bar
        Then bar should have value "bar"

conftest.py:

::

    from pytest_bdd import given, then


    @given('I have a bar')
    def bar():
        return 'bar'


    @then('bar should have value "bar"')
    def bar_is_bar(bar):
        assert bar == 'bar'

test\_common.py:

::

    test_conftest = scenario('common_steps.feature', 'All steps are declared in the conftest')

There are no definitions of the steps in the test file. They were
collected from the parent conftests.

Feature file paths
==================

But default, pytest-bdd will use current module’s path as base path for
finding feature files, but this behaviour can be changed by having
fixture named ‘pytestbdd\_feature\_base\_dir’ which should return the
new base path.

test\_publish\_article.py:

::

    import pytest
    from pytest_bdd import scenario


    @pytest.fixture
    def pytestbdd_feature_base_dir():
        return '/home/user/projects/foo.bar/features'

    test_publish = scenario('publish_article.feature', 'Publishing the article')

Subplugins
==========

The pytest BDD has plugin support, and the main purpose of plugins
(subplugins) is to provide useful and specialized fixtures.

List of known subplugins:

::

    *  pytest-bdd-splinter -- collection of fixtures for real browser BDD testing

License
=======

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_.

© 2013 Oleg Pidsadnyi
