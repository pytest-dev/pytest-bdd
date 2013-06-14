BDD library for the py.test runner
===================================

[![Build Status](https://api.travis-ci.org/olegpidsadnyi/pytest-bdd.png)](https://travis-ci.org/olegpidsadnyi/pytest-bdd)


Install pytest-bdd
=================

	pip install pytest-bdd


Example
=======

publish_article.feature:

    Scenario: Publishing the article
        Given I'm an author user
        And I have an article
        When I go to the article page
        And I press the publish button
        Then I should not see the error message
        And the article should be published  # Note: will query the database


test_publish_article.py:

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

Sometimes it is needed to declare the same fixtures or steps with the different names
for better readability.
In order to use the same step function with multiple step names simply
decorate it multiple times:


	@given('I have an article')
	@given('there\'s an article')
	def article(author):
		return create_test_article(author=author)

Note that the given step aliases are independent and will be executed when mentioned.

For example if you assoicate your resource to some owner or not. Admin user can't be an
author of the article, but article should have some default author.

	Scenario: I'm the author
		Given I'm an author
		And I have an article


	Scenario: I'm the admin
		Given I'm the admin
		And there is an article


Reuse fixtures
================

Sometimes scenarios define new names for the fixture that can be inherited.
Fixtures can be reused with other names using given():

	given('I have beautiful article', fixture='article')


Reuse steps
===========

It is possible to define some common steps in the parent conftest.py and simply
expect them in the child test file.

common_steps.feature:

	Scenario: All steps are declared in the conftest
	    Given I have a bar
	    Then bar should have value "bar"


conftest.py:

	from pytest_bdd import given, then


	@given('I have a bar')
	def bar():
	    return 'bar'


	@then('bar should have value "bar"')
	def bar_is_bar(bar):
	    assert bar == 'bar'

test_common.py:

	test_conftest = scenario('common_steps.feature', 'All steps are declared in the conftest')


There are no definitions of the steps in the test file. They were collected from the parent
conftests.


Feature file paths
==================

But default, pytest-bdd will use current module's path as base path for finding feature files, but this behaviour can
be changed by having fixture named 'pytestbdd_feature_base_dir' which should return the new base path.

test_publish_article.py:

    import pytest
    from pytest_bdd import scenario


    @pytest.fixture
    def pytestbdd_feature_base_dir():
        return '/home/user/projects/foo.bar/features'

    test_publish = scenario('publish_article.feature', 'Publishing the article')


Subplugins
==========

The pytest BDD has plugin support, and the main purpose of plugins (subplugins) is to provide useful and specialized
fixtures.

List of known subplugins:

    *  pytest-bdd-splinter -- collection of fixtures for real browser BDD testing


License
=======

This software is licensed under the [MIT license](http://en.wikipedia.org/wiki/MIT_License>).

© 2013 Oleg Pidsadnyi