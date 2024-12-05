Pytest-BDD: the BDD framework for pytest
========================================

.. image:: https://img.shields.io/pypi/v/pytest-bdd.svg
   :target: https://pypi.python.org/pypi/pytest-bdd
.. image:: https://codecov.io/gh/pytest-dev/pytest-bdd/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/pytest-dev/pytest-bdd
.. image:: https://github.com/pytest-dev/pytest-bdd/actions/workflows/main.yml/badge.svg
   :target: https://github.com/pytest-dev/pytest-bdd/actions/workflows/main.yml
.. image:: https://readthedocs.org/projects/pytest-bdd/badge/?version=stable
   :target: https://readthedocs.org/projects/pytest-bdd/
   :alt: Documentation Status

pytest-bdd implements a subset of the Gherkin language to enable automating project
requirements testing and to facilitate behavioral driven development.

Unlike many other BDD tools, it does not require a separate runner and benefits from
the power and flexibility of pytest. It enables unifying unit and functional
tests, reduces the burden of continuous integration server configuration and allows the reuse of
test setups.

Pytest fixtures written for unit tests can be reused for setup and actions
mentioned in feature steps with dependency injection. This allows a true BDD
just-enough specification of the requirements without maintaining any context object
containing the side effects of Gherkin imperative declarations.

.. _behave: https://pypi.python.org/pypi/behave
.. _pytest-splinter: https://github.com/pytest-dev/pytest-splinter

Install pytest-bdd
------------------

::

    pip install pytest-bdd


Example
-------

An example test for a blog hosting software could look like this.
Note that pytest-splinter_ is used to get the browser fixture.

.. code-block:: gherkin

    # content of publish_article.feature

    Feature: Blog
        A site where you can publish your articles.

        Scenario: Publishing the article
            Given I'm an author user
            And I have an article

            When I go to the article page
            And I press the publish button

            Then I should not see the error message
            And the article should be published

Note that only one feature is allowed per feature file.

.. code-block:: python

    # content of test_publish_article.py

    from pytest_bdd import scenario, given, when, then

    @scenario('publish_article.feature', 'Publishing the article')
    def test_publish():
        pass


    @given("I'm an author user")
    def author_user(auth, author):
        auth['user'] = author.user


    @given("I have an article", target_fixture="article")
    def article(author):
        return create_test_article(author=author)


    @when("I go to the article page")
    def go_to_article(article, browser):
        browser.visit(urljoin(browser.url, '/manage/articles/{0}/'.format(article.id)))


    @when("I press the publish button")
    def publish_article(browser):
        browser.find_by_css('button[name=publish]').first.click()


    @then("I should not see the error message")
    def no_error_message(browser):
        with pytest.raises(ElementDoesNotExist):
            browser.find_by_css('.message.error').first


    @then("the article should be published")
    def article_is_published(article):
        article.refresh()  # Refresh the object in the SQLAlchemy session
        assert article.is_published


Scenario decorator
------------------

Functions decorated with the `scenario` decorator behave like a normal test function,
and they will be executed after all scenario steps.


.. code-block:: python

    from pytest_bdd import scenario, given, when, then

    @scenario('publish_article.feature', 'Publishing the article')
    def test_publish(browser):
        assert article.title in browser.html


.. NOTE:: It is however encouraged to try as much as possible to have your logic only inside the Given, When, Then steps.


Step aliases
------------

Sometimes, one has to declare the same fixtures or steps with
different names for better readability. In order to use the same step
function with multiple step names simply decorate it multiple times:

.. code-block:: python

    @given("I have an article")
    @given("there's an article")
    def article(author, target_fixture="article"):
        return create_test_article(author=author)

Note that the given step aliases are independent and will be executed
when mentioned.

For example if you associate your resource to some owner or not. Admin
user can’t be an author of the article, but articles should have a
default author.

.. code-block:: gherkin

    Feature: Resource owner
        Scenario: I'm the author
            Given I'm an author
            And I have an article


        Scenario: I'm the admin
            Given I'm the admin
            And there's an article


Using Asterisks in Place of Keywords
------------------------------------

To avoid redundancy or unnecessary repetition of keywords
such as "And" or "But" in Gherkin scenarios,
you can use an asterisk (*) as a shorthand.
The asterisk acts as a wildcard, allowing for the same functionality
without repeating the keyword explicitly.
It improves readability by making the steps easier to follow,
especially when the specific keyword does not add value to the scenario's clarity.

The asterisk will work the same as other step keywords - Given, When, Then - it follows.

For example:

.. code-block:: gherkin

    Feature: Resource owner
        Scenario: I'm the author
            Given I'm an author
            * I have an article
            * I have a pen


.. code-block:: python

    from pytest_bdd import given

    @given("I'm an author")
    def _():
        pass

    @given("I have an article")
    def _():
        pass

    @given("I have a pen")
    def _():
        pass


In the scenario above, the asterisk (*) replaces the And or Given keywords.
This allows for cleaner scenarios while still linking related steps together in the context of the scenario.

This approach is particularly useful when you have a series of steps
that do not require explicitly stating whether they are part of the "Given", "When", or "Then" context
but are part of the logical flow of the scenario.


Step arguments
--------------

Often it's possible to reuse steps giving them a parameter(s).
This allows to have single implementation and multiple use, so less code.
Also opens the possibility to use same step twice in single scenario and with different arguments!
And even more, there are several types of step parameter parsers at your disposal
(idea taken from behave_ implementation):

.. _pypi_parse: http://pypi.python.org/pypi/parse
.. _pypi_parse_type: http://pypi.python.org/pypi/parse_type

**string** (the default)
    This is the default and can be considered as a `null` or `exact` parser. It parses no parameters
    and matches the step name by equality of strings.
**parse** (based on: pypi_parse_)
    Provides a simple parser that replaces regular expressions for
    step parameters with a readable syntax like ``{param:Type}``.
    The syntax is inspired by the Python builtin ``string.format()``
    function.
    Step parameters must use the named fields syntax of pypi_parse_
    in step definitions. The named fields are extracted,
    optionally type converted and then used as step function arguments.
    Supports type conversions by using type converters passed via `extra_types`
**cfparse** (extends: pypi_parse_, based on: pypi_parse_type_)
    Provides an extended parser with "Cardinality Field" (CF) support.
    Automatically creates missing type converters for related cardinality
    as long as a type converter for cardinality=1 is provided.
    Supports parse expressions like:
    * ``{values:Type+}`` (cardinality=1..N, many)
    * ``{values:Type*}`` (cardinality=0..N, many0)
    * ``{value:Type?}``  (cardinality=0..1, optional)
    Supports type conversions (as above).
**re**
    This uses full regular expressions to parse the clause text. You will
    need to use named groups "(?P<name>...)" to define the variables pulled
    from the text and passed to your ``step()`` function.
    Type conversion can only be done via `converters` step decorator argument (see example below).

The default parser is `string`, so just plain one-to-one match to the keyword definition.
Parsers except `string`, as well as their optional arguments are specified like:

for `cfparse` parser

.. code-block:: python

    from pytest_bdd import parsers

    @given(
        parsers.cfparse("there are {start:Number} cucumbers", extra_types={"Number": int}),
        target_fixture="cucumbers",
    )
    def given_cucumbers(start):
        return {"start": start, "eat": 0}

for `re` parser

.. code-block:: python

    from pytest_bdd import parsers

    @given(
        parsers.re(r"there are (?P<start>\d+) cucumbers"),
        converters={"start": int},
        target_fixture="cucumbers",
    )
    def given_cucumbers(start):
        return {"start": start, "eat": 0}


Example:

.. code-block:: gherkin

    Feature: Step arguments
        Scenario: Arguments for given, when, then
            Given there are 5 cucumbers

            When I eat 3 cucumbers
            And I eat 2 cucumbers

            Then I should have 0 cucumbers


The code will look like:

.. code-block:: python

    from pytest_bdd import scenarios, given, when, then, parsers


    scenarios("arguments.feature")


    @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="cucumbers")
    def given_cucumbers(start):
        return {"start": start, "eat": 0}


    @when(parsers.parse("I eat {eat:d} cucumbers"))
    def eat_cucumbers(cucumbers, eat):
        cucumbers["eat"] += eat


    @then(parsers.parse("I should have {left:d} cucumbers"))
    def should_have_left_cucumbers(cucumbers, left):
        assert cucumbers["start"] - cucumbers["eat"] == left

Example code also shows possibility to pass argument converters which may be useful if you need to postprocess step
arguments after the parser.

You can implement your own step parser. It's interface is quite simple. The code can look like:

.. code-block:: python

    import re
    from pytest_bdd import given, parsers


    class MyParser(parsers.StepParser):
        """Custom parser."""

        def __init__(self, name, **kwargs):
            """Compile regex."""
            super().__init__(name)
            self.regex = re.compile(re.sub("%(.+)%", "(?P<\1>.+)", self.name), **kwargs)

        def parse_arguments(self, name):
            """Get step arguments.

            :return: `dict` of step arguments
            """
            return self.regex.match(name).groupdict()

        def is_matching(self, name):
            """Match given name with the step name."""
            return bool(self.regex.match(name))


    @given(parsers.parse("there are %start% cucumbers"), target_fixture="cucumbers")
    def given_cucumbers(start):
        return {"start": start, "eat": 0}


Override fixtures via given steps
---------------------------------

Dependency injection is not a panacea if you have complex structure of your test setup data. Sometimes there's a need
such a given step which would imperatively change the fixture only for certain test (scenario), while for other tests
it will stay untouched. To allow this, special parameter `target_fixture` exists in the `given` decorator:

.. code-block:: python

    from pytest_bdd import given

    @pytest.fixture
    def foo():
        return "foo"


    @given("I have injecting given", target_fixture="foo")
    def injecting_given():
        return "injected foo"


    @then('foo should be "injected foo"')
    def foo_is_foo(foo):
        assert foo == 'injected foo'


.. code-block:: gherkin

    Feature: Target fixture
        Scenario: Test given fixture injection
            Given I have injecting given
            Then foo should be "injected foo"


In this example, the existing fixture `foo` will be overridden by given step `I have injecting given` only for the scenario it's
used in.

Sometimes it is also useful to let `when` and `then` steps provide a fixture as well.
A common use case is when we have to assert the outcome of an HTTP request:

.. code-block:: python

    # content of test_blog.py

    from pytest_bdd import scenarios, given, when, then

    from my_app.models import Article

    scenarios("blog.feature")


    @given("there is an article", target_fixture="article")
    def there_is_an_article():
        return Article()


    @when("I request the deletion of the article", target_fixture="request_result")
    def there_should_be_a_new_article(article, http_client):
        return http_client.delete(f"/articles/{article.uid}")


    @then("the request should be successful")
    def article_is_published(request_result):
        assert request_result.status_code == 200


.. code-block:: gherkin

    # content of blog.feature

    Feature: Blog
        Scenario: Deleting the article
            Given there is an article

            When I request the deletion of the article

            Then the request should be successful


Scenarios shortcut
------------------

If you have a relatively large set of feature files, it's boring to manually bind scenarios to the tests using the scenario decorator. Of course with the manual approach you get all the power to be able to additionally parametrize the test, give the test function a nice name, document it, etc, but in the majority of the cases you don't need that.
Instead, you want to bind all the scenarios found in the ``features`` folder(s) recursively automatically, by using the ``scenarios`` helper.

.. code-block:: python

    from pytest_bdd import scenarios

    # assume 'features' subfolder is in this file's directory
    scenarios('features')

That's all you need to do to bind all scenarios found in the ``features`` folder!
Note that you can pass multiple paths, and those paths can be either feature files or feature folders.


.. code-block:: python

    from pytest_bdd import scenarios

    # pass multiple paths/files
    scenarios('features', 'other_features/some.feature', 'some_other_features')

But what if you need to manually bind a certain scenario, leaving others to be automatically bound?
Just write your scenario in a "normal" way, but ensure you do it **before** the call of ``scenarios`` helper.


.. code-block:: python

    from pytest_bdd import scenario, scenarios

    @scenario('features/some.feature', 'Test something')
    def test_something():
        pass

    # assume 'features' subfolder is in this file's directory
    scenarios('features')

In the example above, the ``test_something`` scenario binding will be kept manual, other scenarios found in the ``features`` folder will be bound automatically.


Scenario outlines
-----------------

Scenarios can be parametrized to cover multiple cases. These are called `Scenario Outlines <https://cucumber.io/docs/gherkin/reference/#scenario-outline>`_ in Gherkin, and the variable templates are written using angular brackets (e.g. ``<var_name>``).

Example:

.. code-block:: gherkin

    # content of scenario_outlines.feature

    Feature: Scenario outlines
        Scenario Outline: Outlined given, when, then
            Given there are <start> cucumbers
            When I eat <eat> cucumbers
            Then I should have <left> cucumbers

            Examples:
            | start | eat | left |
            |  12   |  5  |  7   |

.. code-block:: python

    from pytest_bdd import scenarios, given, when, then, parsers


    scenarios("scenario_outlines.feature")


    @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="cucumbers")
    def given_cucumbers(start):
        return {"start": start, "eat": 0}


    @when(parsers.parse("I eat {eat:d} cucumbers"))
    def eat_cucumbers(cucumbers, eat):
        cucumbers["eat"] += eat


    @then(parsers.parse("I should have {left:d} cucumbers"))
    def should_have_left_cucumbers(cucumbers, left):
        assert cucumbers["start"] - cucumbers["eat"] == left


Example parameters from example tables can not only be used in steps, but also embedded directly within docstrings and datatables, allowing for dynamic substitution.
This provides added flexibility for scenarios that require complex setups or validations.

Example:

.. code-block:: gherkin

    # content of docstring_and_datatable_with_params.feature

    Feature: Docstring and Datatable with example parameters
        Scenario Outline: Using parameters in docstrings and datatables
            Given the following configuration:
                """
                username: <username>
                password: <password>
                """
            When the user logs in
            Then the response should contain:
                | field     | value      |
                | username  | <username> |
                | logged_in | true       |

            Examples:
            | username  | password  |
            | user1     | pass123   |
            | user2     | 123secure |

.. code-block:: python

    from pytest_bdd import scenarios, given, when, then
    import json

    # Load scenarios from the feature file
    scenarios("docstring_and_datatable_with_params.feature")


    @given("the following configuration:")
    def given_user_config(docstring):
        print(docstring)


    @when("the user logs in")
    def user_logs_in(logged_in):
        logged_in = True


    @then("the response should contain:")
    def response_should_contain(datatable):
        assert datatable[1][1] in ["user1", "user2"]


Scenario Outlines with Multiple Example Tables
----------------------------------------------

In `pytest-bdd`, you can use multiple example tables in a scenario outline to test
different sets of input data under various conditions.
You can define separate `Examples` blocks, each with its own table of data,
and optionally tag them to differentiate between positive, negative, or any other conditions.

Example:

.. code-block:: gherkin

    # content of scenario_outline.feature

    Feature: Scenario outlines with multiple examples tables
        Scenario Outline: Outlined with multiple example tables
            Given there are <start> cucumbers
            When I eat <eat> cucumbers
            Then I should have <left> cucumbers

            @positive
            Examples: Positive results
                | start | eat | left |
                |  12   |  5  |  7   |
                |  5    |  4  |  1   |

            @negative
            Examples: Impossible negative results
                | start | eat | left |
                |  3    |  9  |  -6  |
                |  1    |  4  |  -3  |

.. code-block:: python

    from pytest_bdd import scenarios, given, when, then, parsers


    scenarios("scenario_outline.feature")


    @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="cucumbers")
    def given_cucumbers(start):
        return {"start": start, "eat": 0}


    @when(parsers.parse("I eat {eat:d} cucumbers"))
    def eat_cucumbers(cucumbers, eat):
        cucumbers["eat"] += eat


    @then(parsers.parse("I should have {left:d} cucumbers"))
    def should_have_left_cucumbers(cucumbers, left):
        assert cucumbers["start"] - cucumbers["eat"] == left


When you filter scenarios by a tag, only the examples associated with that tag will be executed.
This allows you to run a specific subset of your test cases based on the tag.
For example, in the following scenario outline, if you filter by the @positive tag,
only the examples under the "Positive results" table will be executed, and the "Negative results" table will be ignored.

.. code-block:: bash

    pytest -k "positive"


Handling Empty Example Cells
----------------------------

By default, empty cells in the example tables are interpreted as empty strings ("").
However, there may be cases where it is more appropriate to handle them as ``None``.
In such scenarios, you can use a converter with the ``parsers.re`` parser to define a custom behavior for empty values.

For example, the following code demonstrates how to use a custom converter to return ``None`` when an empty cell is encountered:

.. code-block:: gherkin

    # content of empty_example_cells.feature

    Feature: Handling empty example cells
        Scenario Outline: Using converters for empty cells
            Given I am starting lunch
            Then there are <start> cucumbers

            Examples:
            | start |
            |       |

.. code-block:: python

    from pytest_bdd import then, parsers


    # Define a converter that returns None for empty strings
    def empty_to_none(value):
        return None if value.strip() == "" else value


    @given("I am starting lunch")
    def _():
        pass


    @then(
        parsers.re("there are (?P<start>.*?) cucumbers"),
        converters={"start": empty_to_none}
    )
    def _(start):
        # Example assertion to demonstrate the conversion
        assert start is None


Here, the `start` cell in the example table is empty.
When the ``parsers.re`` parser is combined with the ``empty_to_none`` converter,
the empty cell will be converted to ``None`` and can be handled accordingly in the step definition.


Rules
-----

In Gherkin, `Rules` allow you to group related scenarios or examples under a shared context.
This is useful when you want to define different conditions or behaviours
for multiple examples that follow a similar structure.
You can use either ``Scenario`` or ``Example`` to define individual cases, as they are aliases and function identically.

Additionally, **tags** applied to a rule will be automatically applied to all the **examples or scenarios**
under that rule, making it easier to organize and filter tests during execution.

Example:

.. code-block:: gherkin

    Feature: Rules and examples

        @feature_tag
        Rule: A rule for valid cases

            @rule_tag
            Example: Valid case 1
                Given I have a valid input
                When I process the input
                Then the result should be successful

        Rule: A rule for invalid cases

            Example: Invalid case
                Given I have an invalid input
                When I process the input
                Then the result should be an error


Datatables
----------

The ``datatable`` argument allows you to utilise data tables defined in your Gherkin scenarios
directly within your test functions. This is particularly useful for scenarios that require tabular data as input,
enabling you to manage and manipulate this data conveniently.

When you use the ``datatable`` argument in a step definition, it will return the table as a list of lists,
where each inner list represents a row from the table.

For example, the Gherkin table:

.. code-block:: gherkin

    | name  | email            |
    | John  | john@example.com |

Will be returned by the ``datatable`` argument as:

.. code-block:: python

    [
        ["name", "email"],
        ["John", "john@example.com"]
    ]

.. NOTE:: When using the datatable argument, it is essential to ensure that the step to which it is applied
          actually has an associated data table. If the step does not have an associated data table,
          attempting to use the datatable argument will raise an error.
          Make sure that your Gherkin steps correctly reference the data table when defined.

Full example:

.. code-block:: gherkin

    Feature: Manage user accounts

      Scenario: Creating a new user with roles and permissions
        Given the following user details:
          | name  | email             | age |
          | John  | john@example.com  | 30  |
          | Alice | alice@example.com | 25  |

        When each user is assigned the following roles:
          | Admin       | Full access to the system |
          | Contributor | Can add content           |

        And the page is saved

        Then the user should have the following permissions:
          | permission     | allowed |
          | view dashboard | true    |
          | edit content   | true    |
          | delete content | false   |

.. code-block:: python

    from pytest_bdd import given, when, then


    @given("the following user details:", target_fixture="users")
    def _(datatable):
        users = []
        for row in datatable[1:]:
            users.append(row)

        print(users)
        return users


    @when("each user is assigned the following roles:")
    def _(datatable, users):
        roles = datatable
        for user in users:
            for role_row in datatable:
                assign_role(user, role_row)


    @when("the page is saved")
    def _():
        save_page()


    @then("the user should have the following permissions:")
    def _(datatable, users):
        expected_permissions = []
        for row in datatable[1:]:
            expected_permissions.append(row)

        assert users_have_correct_permissions(users, expected_permissions)


Docstrings
----------

The `docstring` argument allows you to access the Gherkin docstring defined in your steps as a multiline string.
The content of the docstring is passed as a single string, with each line separated by `\\n`.
Leading indentation are stripped.

For example, the Gherkin docstring:


.. code-block:: gherkin

    """
    This is a sample docstring.
    It spans multiple lines.
    """


Will be returned as:

.. code-block:: python

    "This is a sample docstring.\nIt spans multiple lines."


Full example:

.. code-block:: gherkin

    Feature: Docstring

      Scenario: Step with docstrings
        Given some steps will have docstrings

        Then a step has a docstring
        """
        This is a docstring
        on two lines
        """

        And a step provides a docstring with lower indentation
        """
    This is a docstring
        """

        And this step has no docstring

        And this step has a greater indentation
        """
            This is a docstring
        """

        And this step has no docstring

.. code-block:: python

        from pytest_bdd import given, then


        @given("some steps will have docstrings")
        def _():
            pass

        @then("a step has a docstring")
        def _(docstring):
            assert docstring == "This is a docstring\non two lines"

        @then("a step provides a docstring with lower indentation")
        def _(docstring):
            assert docstring == "This is a docstring"

        @then("this step has a greater indentation")
        def _(docstring):
            assert docstring == "This is a docstring"

        @then("this step has no docstring")
        def _():
            pass


.. note::   The ``docstring`` argument can only be used for steps that have an associated docstring.
            Otherwise, an error will be thrown.

Organizing your scenarios
-------------------------

The more features and scenarios you have, the more important the question of their organization becomes.
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

This looks fine, but how do you run tests only for a certain feature?
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


For picking up tests to run we can use the
`tests selection <https://pytest.org/en/7.1.x/how-to/usage.html#specifying-which-tests-to-run>`_ technique. The problem is that
you have to know how your tests are organized, knowing only the feature files organization is not enough.
Cucumber uses `tags <https://cucumber.io/docs/cucumber/api/#tags>`_ as a way of categorizing your features
and scenarios, which pytest-bdd supports. For example, we could have:

.. code-block:: gherkin

    @login @backend
    Feature: Login

      @successful
      Scenario: Successful login


pytest-bdd uses `pytest markers <http://pytest.org/latest/mark.html>`_ as a `storage` of the tags for the given
scenario test, so we can use standard test selection:

.. code-block:: bash

    pytest -m "backend and login and successful"

The feature and scenario markers are not different from standard pytest markers, and the ``@`` symbol is stripped out automatically to allow test selector expressions. If you want to have bdd-related tags to be distinguishable from the other test markers, use a prefix like ``bdd``.
Note that if you use pytest with the ``--strict-markers`` option, all Gherkin tags mentioned in the feature files should be also in the ``markers`` setting of the ``pytest.ini`` config. Also for tags please use names which are python-compatible variable names, i.e. start with a non-number, only underscores or alphanumeric characters, etc. That way you can safely use tags for tests filtering.

You can customize how tags are converted to pytest marks by implementing the
``pytest_bdd_apply_tag`` hook and returning ``True`` from it:

.. code-block:: python

   def pytest_bdd_apply_tag(tag, function):
       if tag == 'todo':
           marker = pytest.mark.skip(reason="Not implemented yet")
           marker(function)
           return True
       else:
           # Fall back to the default behavior of pytest-bdd
           return None

Test setup
----------

Test setup is implemented within the Given section. Even though these steps
are executed imperatively to apply possible side-effects, pytest-bdd is trying
to benefit of the PyTest fixtures which is based on the dependency injection
and makes the setup more declarative style.

.. code-block:: python

    @given("I have a beautiful article", target_fixture="article")
    def article():
        return Article(is_beautiful=True)

The target PyTest fixture "article" gets the return value and any other step can depend on it.

.. code-block:: gherkin

    Feature: The power of PyTest
        Scenario: Symbolic name across steps
            Given I have a beautiful article
            When I publish this article

The When step is referencing the ``article`` to publish it.

.. code-block:: python

    @when("I publish this article")
    def publish_article(article):
        article.publish()


Many other BDD toolkits operate on a global context and put the side effects there.
This makes it very difficult to implement the steps, because the dependencies
appear only as the side-effects during run-time and not declared in the code.
The "publish article" step has to trust that the article is already in the context,
has to know the name of the attribute it is stored there, the type etc.

In pytest-bdd you just declare an argument of the step function that it depends on
and the PyTest will make sure to provide it.

Still side effects can be applied in the imperative style by design of the BDD.

.. code-block:: gherkin

    Feature: News website
        Scenario: Publishing an article
            Given I have a beautiful article
            And my article is published

Functional tests can reuse your fixture libraries created for the unit-tests and upgrade
them by applying the side effects.

.. code-block:: python

    @pytest.fixture
    def article():
        return Article(is_beautiful=True)


    @given("I have a beautiful article")
    def i_have_a_beautiful_article(article):
        pass


    @given("my article is published")
    def published_article(article):
        article.publish()
        return article


This way side-effects were applied to our article and PyTest makes sure that all
steps that require the "article" fixture will receive the same object. The value
of the "published_article" and the "article" fixtures is the same object.

Fixtures are evaluated **only once** within the PyTest scope and their values are cached.


Backgrounds
-----------

It's often the case that to cover certain feature, you'll need multiple scenarios. And it's logical that the
setup for those scenarios will have some common parts (if not equal). For this, there are `backgrounds`.
pytest-bdd implements `Gherkin backgrounds <https://cucumber.io/docs/gherkin/reference/#background>`_ for
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
steps, adding a possibility to prepare some common setup for multiple scenarios in a single feature.
About best practices for Background, please read Gherkin's
`Tips for using Background <https://cucumber.io/docs/gherkin/reference/#tips-for-using-background>`_.

.. NOTE:: Only "Given" steps should be used in "Background" section.
          Steps "When" and "Then" are prohibited, because their purposes are
          related to actions and consuming outcomes; that is in conflict with the
          aim of "Background" - to prepare the system for tests or "put the system
          in a known state" as "Given" does it.


Reusing fixtures
----------------

Sometimes scenarios define new names for an existing fixture that can be
inherited (reused). For example, if we have the pytest fixture:


.. code-block:: python

    @pytest.fixture
    def article():
       """Test article."""
       return Article()


Then this fixture can be reused with other names using given():


.. code-block:: python

    @given('I have a beautiful article')
    def i_have_an_article(article):
       """I have an article."""


Reusing steps
-------------

It is possible to define some common steps in the parent ``conftest.py`` and
simply expect them in the child test file.

.. code-block:: gherkin

    # content of common_steps.feature

    Scenario: All steps are declared in the conftest
        Given I have a bar
        Then bar should have value "bar"

.. code-block:: python

    # content of conftest.py

    from pytest_bdd import given, then


    @given("I have a bar", target_fixture="bar")
    def bar():
        return "bar"


    @then('bar should have value "bar"')
    def bar_is_bar(bar):
        assert bar == "bar"

.. code-block:: python

    # content of test_common.py

    @scenario("common_steps.feature", "All steps are declared in the conftest")
    def test_conftest():
        pass

There are no definitions of steps in the test file. They were
collected from the parent conftest.py.


Default steps
-------------

Here is the list of steps that are implemented inside pytest-bdd:

given
    * trace - enters the `pdb` debugger via `pytest.set_trace()`
when
    * trace - enters the `pdb` debugger via `pytest.set_trace()`
then
    * trace - enters the `pdb` debugger via `pytest.set_trace()`


Feature file paths
------------------

By default, pytest-bdd will use the current module's path as the base path for finding feature files, but this behaviour can be changed in the pytest configuration file (i.e. `pytest.ini`, `tox.ini` or `setup.cfg`) by declaring the new base path in the `bdd_features_base_dir` key. The path is interpreted as relative to the `pytest root directory <https://docs.pytest.org/en/latest/reference/customize.html#rootdir>`__.
You can also override the features base path on a per-scenario basis, in order to override the path for specific tests.

pytest.ini:

.. code-block:: ini

    [pytest]
    bdd_features_base_dir = features/

tests/test_publish_article.py:

.. code-block:: python

    from pytest_bdd import scenario


    @scenario("foo.feature", "Foo feature in features/foo.feature")
    def test_foo():
        pass


    @scenario(
        "foo.feature",
        "Foo feature in tests/local-features/foo.feature",
        features_base_dir="./local-features/",
    )
    def test_foo_local():
        pass


The `features_base_dir` parameter can also be passed to the `@scenario` decorator.


Avoid retyping the feature file name
------------------------------------

If you want to avoid retyping the feature file name when defining your scenarios in a test file, use ``functools.partial``.
This will make your life much easier when defining multiple scenarios in a test file. For example:

.. code-block:: python

    # content of test_publish_article.py

    from functools import partial

    import pytest_bdd


    scenario = partial(pytest_bdd.scenario, "/path/to/publish_article.feature")


    @scenario("Publishing the article")
    def test_publish():
        pass


    @scenario("Publishing the article as unprivileged user")
    def test_publish_unprivileged():
        pass


You can learn more about `functools.partial <https://docs.python.org/3/library/functools.html#functools.partial>`_
in the Python docs.


Programmatic step generation
----------------------------
Sometimes you have step definitions that would be much easier to automate rather than writing them manually over and over again.
This is common, for example, when using libraries like `pytest-factoryboy <https://pytest-factoryboy.readthedocs.io/>`_ that automatically creates fixtures.
Writing step definitions for every model can become a tedious task.

For this reason, pytest-bdd provides a way to generate step definitions automatically.

The trick is to pass the ``stacklevel`` parameter to the ``given``, ``when``, ``then``, ``step`` decorators. This will instruct them to inject the step fixtures in the appropriate module, rather than just injecting them in the caller frame.

Let's look at a concrete example; let's say you have a class ``Wallet`` that has some amount of each currency:

.. code-block:: python

    # contents of wallet.py

    import dataclass

    @dataclass
    class Wallet:
        verified: bool

        amount_eur: int
        amount_usd: int
        amount_gbp: int
        amount_jpy: int


You can use pytest-factoryboy to automatically create model fixtures for this class:

.. code-block:: python

    # contents of wallet_factory.py

    from wallet import Wallet

    import factory
    from pytest_factoryboy import register

    class WalletFactory(factory.Factory):
        class Meta:
            model = Wallet

        amount_eur = 0
        amount_usd = 0
        amount_gbp = 0
        amount_jpy = 0

    register(Wallet)  # creates the "wallet" fixture
    register(Wallet, "second_wallet")  # creates the "second_wallet" fixture


Now we can define a function ``generate_wallet_steps(...)`` that creates the steps for any wallet fixture (in our case, it will be ``wallet`` and ``second_wallet``):

.. code-block:: python

    # contents of wallet_steps.py

    import re
    from dataclasses import fields

    import factory
    import pytest
    from pytest_bdd import given, when, then, scenarios, parsers


    def generate_wallet_steps(model_name="wallet", stacklevel=1):
        stacklevel += 1

        human_name = model_name.replace("_", " ")  # "second_wallet" -> "second wallet"

        @given(f"I have a {human_name}", target_fixture=model_name, stacklevel=stacklevel)
        def _(request):
            return request.getfixturevalue(model_name)

        # Generate steps for currency fields:
        for field in fields(Wallet):
            match = re.fullmatch(r"amount_(?P<currency>[a-z]{3})", field.name)
            if not match:
                continue
            currency = match["currency"]

            @given(
                parsers.parse(f"I have {{value:d}} {currency.upper()} in my {human_name}"),
                target_fixture=f"{model_name}__amount_{currency}",
                stacklevel=stacklevel,
            )
            def _(value: int) -> int:
                return value

            @then(
                parsers.parse(f"I should have {{value:d}} {currency.upper()} in my {human_name}"),
                stacklevel=stacklevel,
            )
            def _(value: int, _currency=currency, _model_name=model_name) -> None:
                wallet = request.getfixturevalue(_model_name)
                assert getattr(wallet, f"amount_{_currency}") == value

    # Inject the steps into the current module
    generate_wallet_steps("wallet")
    generate_wallet_steps("second_wallet")


This last file, ``wallet_steps.py``, now contains all the step definitions for our "wallet" and "second_wallet" fixtures.

We can now define a scenario like this:

.. code-block:: gherkin

    # contents of wallet.feature
    Feature: A feature

        Scenario: Wallet EUR amount stays constant
            Given I have 10 EUR in my wallet
            And I have a wallet
            Then I should have 10 EUR in my wallet

        Scenario: Second wallet JPY amount stays constant
            Given I have 100 JPY in my second wallet
            And I have a second wallet
            Then I should have 100 JPY in my second wallet


and finally a test file that puts it all together and run the scenarios:

.. code-block:: python

    # contents of test_wallet.py

    from pytest_factoryboy import scenarios

    from wallet_factory import *  # import the registered fixtures "wallet" and "second_wallet"
    from wallet_steps import *  # import all the step definitions into this test file

    scenarios("wallet.feature")


Hooks
-----

pytest-bdd exposes several `pytest hooks <https://docs.pytest.org/en/7.1.x/reference/reference.html#hooks>`_
which might be helpful building useful reporting, visualization, etc. on top of it:

* `pytest_bdd_before_scenario(request, feature, scenario)` - Called before scenario is executed

* `pytest_bdd_after_scenario(request, feature, scenario)` - Called after scenario is executed
  (even if one of steps has failed)

* `pytest_bdd_before_step(request, feature, scenario, step, step_func)` - Called before step function
  is executed and its arguments evaluated

* `pytest_bdd_before_step_call(request, feature, scenario, step, step_func, step_func_args)` - Called before step
  function is executed with evaluated arguments

* `pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args)` - Called after step function
  is successfully executed

* `pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception)` - Called when step
  function failed to execute

* `pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception)` - Called when step lookup failed


Browser testing
---------------

Tools recommended to use for browser testing:

* pytest-splinter_ - pytest `splinter <https://splinter.readthedocs.io/>`_ integration for the real browser testing


Reporting
---------

It's important to have nice reporting out of your bdd tests. Cucumber introduced some kind of standard for
`json format <https://www.relishapp.com/cucumber/cucumber/docs/json-output-formatter>`_
which can be used for, for example, by `this <https://plugins.jenkins.io/cucumber-testresult-plugin/>`_ Jenkins
plugin.

To have an output in json format:

::

    pytest --cucumberjson=<path to json report>

This will output an expanded (meaning scenario outlines will be expanded to several scenarios) Cucumber format.

To enable gherkin-formatted output on terminal, use `--gherkin-terminal-reporter` in conjunction with the `-v` or `-vv` options:

::

    pytest -v --gherkin-terminal-reporter


Test code generation helpers
----------------------------

For newcomers it's sometimes hard to write all needed test code without being frustrated.
To simplify their life, a simple code generator was implemented. It allows to create fully functional
(but of course empty) tests and step definitions for a given feature file.
It's done as a separate console script provided by pytest-bdd package:

::

    pytest-bdd generate <feature file name> .. <feature file nameN>

It will print the generated code to the standard output so you can easily redirect it to the file:

::

    pytest-bdd generate features/some.feature > tests/functional/test_some.py


Advanced code generation
------------------------

For more experienced users, there's a smart code generation/suggestion feature. It will only generate the
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


.. _Migration from 5.x.x:

Migration of your tests from versions 5.x.x
-------------------------------------------

The primary focus of the pytest-bdd is the compatibility with the latest gherkin developments
e.g. multiple scenario outline example tables with tags support etc.

In order to provide the best compatibility, it is best to support the features described in the official
gherkin reference. This means deprecation of some non-standard features that were implemented in pytest-bdd.


Removal of the feature examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The example tables on the feature level are no longer supported. If you had examples on the feature level, you should copy them to each individual scenario.


Removal of the vertical examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Vertical example tables are no longer supported since the official gherkin doesn't support them.
The example tables should have horizontal orientation.


Step arguments are no longer fixtures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Step parsed arguments conflicted with the fixtures. Now they no longer define fixture.
If the fixture has to be defined by the step, the target_fixture param should be used.


Variable templates in steps are only parsed for Scenario Outlines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In previous versions of pytest, steps containing ``<variable>`` would be parsed both by ``Scenario`` and ``Scenario Outline``.
Now they are only parsed within a ``Scenario Outline``.


.. _Migration from 4.x.x:

Migration of your tests from versions 4.x.x
-------------------------------------------

Replace usage of <parameter> inside step definitions with parsed {parameter}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Templated steps (e.g. ``@given("there are <start> cucumbers")``) should now the use step argument parsers in order to match the scenario outlines and get the values from the example tables. The values from the example tables are no longer passed as fixtures, although if you define your step to use a parser, the parameters will be still provided as fixtures.

.. code-block:: python

    # Old step definition:
    @given("there are <start> cucumbers")
    def given_cucumbers(start):
        pass


    # New step definition:
    @given(parsers.parse("there are {start} cucumbers"))
    def given_cucumbers(start):
        pass


Scenario `example_converters` are removed in favor of the converters provided on the step level:

.. code-block:: python

    # Old code:
    @given("there are <start> cucumbers")
    def given_cucumbers(start):
        return {"start": start}

    @scenario("outline.feature", "Outlined", example_converters={"start": float})
    def test_outline():
        pass


    # New code:
    @given(parsers.parse("there are {start} cucumbers"), converters={"start": float})
    def given_cucumbers(start):
        return {"start": start}

    @scenario("outline.feature", "Outlined")
    def test_outline():
        pass


Refuse combining scenario outline and pytest parametrization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The significant downside of combining scenario outline and pytest parametrization approach was an inability to see the
test table from the feature file.


.. _Migration from 3.x.x:

Migration of your tests from versions 3.x.x
-------------------------------------------


Given steps are no longer fixtures. In case it is needed to make given step setup a fixture,
the target_fixture parameter should be used.


.. code-block:: python

    @given("there's an article", target_fixture="article")
    def there_is_an_article():
        return Article()


Given steps no longer have the `fixture` parameter. In fact the step may depend on multiple fixtures.
Just normal step declaration with the dependency injection should be used.

.. code-block:: python

    @given("there's an article")
    def there_is_an_article(article):
        pass


Strict gherkin option is removed, so the ``strict_gherkin`` parameter can be removed from the scenario decorators
as well as ``bdd_strict_gherkin`` from the ini files.

Step validation handlers for the hook ``pytest_bdd_step_validation_error`` should be removed.

License
-------

This software is licensed under the `MIT License <https://opensource.org/licenses/MIT>`_.

© 2013 Oleg Pidsadnyi, Anatoly Bubenkov and others
