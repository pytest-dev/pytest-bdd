BDD Library for the pytest Runner
=================================

.. image:: https://img.shields.io/pypi/v/pytest-bdd.svg
   :target: https://pypi.python.org/pypi/pytest-bdd
.. image:: https://codecov.io/gh/pytest-dev/pytest-bdd/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/pytest-dev/pytest-bdd
.. image:: https://github.com/pytest-dev/pytest-bdd/actions/workflows/main.yml/badge.svg
   :target: https://github.com/pytest-dev/pytest-bdd/actions/workflows/main.yml
.. image:: https://readthedocs.org/projects/pytest-bdd/badge/?version=stable
   :target: https://readthedocs.org/projects/pytest-bdd/
   :alt: Documentation Status

`pytest-bdd` is a Behavior-Driven Development (BDD) library for the `pytest` runner. It uses files written in `Gherkin <https://cucumber.io/docs/gherkin/reference/>`_ to automate project requirements testing and facilitate BDD.

Unlike many other BDD tools, `pytest-bdd` does not require a separate runner and benefits from the power and flexibility of `pytest`. It unifies unit and functional tests, reduces the burden of continuous integration server configuration, and allows the reuse of test setups.

`pytest` fixtures written for unit tests can be reused for setup and actions mentioned in feature steps with dependency injection. This allows a true BDD just-enough specification of the requirements without maintaining any context object containing the side effects of Gherkin imperative declarations.

.. _behave: https://pypi.python.org/pypi/behave
.. _pytest-splinter: https://github.com/pytest-dev/pytest-splinter

Installation
------------

Install `pytest-bdd` using `pip`:

.. code-block:: bash

    pip install pytest-bdd

Example
-------

An example test for a blog hosting software could look like this. Note that pytest-splinter_ is used to get the browser fixture.

.. code-block:: gherkin

    # content of publish_article.feature

    Feature: Blog
        Scenario: Publishing the article
            Given I'm an author user
            And I have an article
            When I go to the article page
            And I press the publish button
            Then I should not see the error message
            And the article should be published

.. code-block:: python

    # test_publish_article.py

    from pytest_bdd import scenarios, given, when, then

    # Load all the scenarios
    scenarios('publish_article.feature')

    @given("I'm an author user")
    def _(auth, author):
        auth['user'] = author.user

    @given("I have an article", target_fixture="article")
    def _(author):
        return create_test_article(author=author)

    @when("I go to the article page")
    def _(article, browser):
        browser.visit(urljoin(browser.url, '/manage/articles/{0}/'.format(article.id)))

    @when("I press the publish button")
    def _(browser):
        browser.find_by_css('button[name=publish]').first.click()

    @then("I should not see the error message")
    def _(browser):
        with pytest.raises(ElementDoesNotExist):
            browser.find_by_css('.message.error').first

    @then("the article should be published")
    def _(article):
        article.refresh_from_db()
        assert article.is_published

Declaring tests in python files
-------------------------------
The recommended approach to run tests defined by feature files is to create a python test module for each feature file, and define the step implementation within the module:

.. code-block:: python

    # test_foo.py

    from pytest_bdd import scenarios, given, when, then

    scenarios("features/foo.feature")

    @given("There is an article")
    def _():
        ...

    ...

You can also decide to collect all the feature files found in a directory. For example, this will collect all the feature files from the `features` folder recursively:

.. code-block:: python

    # test_features.py

    from pytest_bdd import scenarios

    scenarios("features")

If you need fine-grained control over which scenarios to execute within a feature file, you can use the `scenario` decorator:

.. code-block:: python

    # test_feature.py

    from pytest_bdd import scenario, given, when, then

    @scenario('publish_article.feature', 'Publishing the article')
    def _(browser):
        assert article.title in browser.html

.. note:: It is encouraged to have your logic only inside the Given, When, Then steps.

Step aliases
------------

To declare the same fixtures or steps with different names for better readability, simply decorate the step function multiple times:

.. code-block:: python

    @given("I have an article")
    @given("there's an article")
    def article(author, target_fixture="article"):
        return create_test_article(author=author)

Step arguments
--------------

You can reuse steps by giving them parameters. This allows for single implementation and multiple uses, reducing code duplication.

Example
~~~~~~~

Consider the following feature file:

.. code-block:: gherkin

    Feature: Cucumber management
        Scenario: Eating cucumbers
            Given there are 12 cucumbers
            When I eat 5 cucumbers
            Then I should have 7 cucumbers

You can implement the steps with parameters as follows:

.. code-block:: python

    from pytest_bdd import scenarios, given, when, then, parsers

    # Load the feature file
    scenarios("cucumber_management.feature")

    # Define the Given step with a parameter
    @given(
        parsers.parse("there are {start:d} cucumbers"),
        target_fixture="cucumbers"
    )
    def given_cucumbers(start):
        return {"count": start}

    # Define the When step with a parameter
    @when(parsers.parse("I eat {eat:d} cucumbers"))
    def eat_cucumbers(cucumbers, eat):
        cucumbers["count"] -= eat

    # Define the Then step with a parameter
    @then(parsers.parse("I should have {left:d} cucumbers"))
    def should_have_left_cucumbers(cucumbers, left):
        assert cucumbers["count"] == left

In this example:
- The `given_cucumbers` function initializes the number of cucumbers.
- The `eat_cucumbers` function reduces the number of cucumbers.
- The `should_have_left_cucumbers` function checks the remaining number of cucumbers.

By using parameters in your step definitions, you can easily adapt the steps for different scenarios without duplicating code.

Available Parsers
~~~~~~~~~~~~~~~~~

There are several types of step parameter parsers at your disposal:

- **string** (the default): Matches the step name by equality of strings.
- **parse**: (`parse <http://pypi.python.org/pypi/parse>`_ library) Uses a readable syntax like ``{param:Type}`` for step parameters.
- **cfparse** (`parse_type <http://pypi.python.org/pypi/parse_type>`_ library): Extends `parse` with Cardinality Field support, allowing expressions like ``{values:Type+}``.
- **re**: Uses full regular expressions with named groups to define variables.

Example with `cfparse` parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pytest_bdd import parsers

    @given(
        parsers.cfparse("there are {start:Number} cucumbers",
        extra_types={"Number": int}),
        target_fixture="cucumbers",
    )
    def given_cucumbers(start):
        return {"count": start}

Example with `re` parser
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pytest_bdd import parsers

    @given(
        parsers.re(r"there are (?P<start>\d+) cucumbers"),
        converters={"start": int},
        target_fixture="cucumbers",
    )
    def given_cucumbers(start):
        return {"count": start}

Implementing a custom step parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can implement your own step parser. Its interface is quite simple. The code can look like:

.. code-block:: python

    import re
    from pytest_bdd import given, parsers


    class MyParser(parsers.StepParser):
        """Parser that uses %-interpolated strings, like `%foo%`"""
        def __init__(self, name: str) -> None:
            super().__init__(name)
            self.regex = re.compile(re.sub(r"%(.+)%", r"(?P<\1>.+)", self.name))

        def parse_arguments(self, name: str) -> dict[str, object]:
            return self.regex.match(name).groupdict()

        def is_matching(self, name: str) -> bool:
            return bool(self.regex.match(name))


    @given(parsers.parse("there are %start% cucumbers"), target_fixture="cucumbers")
    def given_cucumbers(start: str) -> dict[str, int]:
        return {"count": int(start)}

Override fixtures (injection)
-----------------------------

To imperatively change a fixture only for certain tests (scenarios), use the ``target_fixture`` parameter in the `given` decorator:


.. code-block:: gherkin

    Feature: Target fixture override
        Scenario: Test given fixture injection
            Given I have injecting given
            Then foo should be "injected foo"

.. code-block:: python

    from pytest_bdd import given

    @pytest.fixture
    def _():
        return "foo"

    @given("I have injecting given", target_fixture="foo")
    def _():
        return "injected foo"

    @then('foo should be "injected foo"')
    def _(foo):
        assert foo == "injected foo"



In this example, the existing fixture `foo` is overridden by given step `I have injecting given` only for the scenario it's used in.

Sometimes it is also useful to let `when` and `then` steps provide a fixture as well.
A common use case is when we want to access the result of an HTTP request in later steps:

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

Scenario Outlines
-----------------

Scenarios can be parameterized to cover multiple cases using `Scenario Outlines <https://cucumber.io/docs/gherkin/reference/#scenario-outline>`_.

.. code-block:: gherkin

    # content of scenario_outlines.feature

    Feature: Scenario outlines
        Scenario Outline: Eating cucumbers
            Given there are <start> cucumbers
            When I eat <eat> cucumbers
            Then I should have <left> cucumbers

            Examples:
                | start | eat | left |
                |  12   |  5  |  7   |
                |  20   |  5  |  15  |

.. code-block:: python

    # test_scenario_outlines.py

    from pytest_bdd import scenarios, given, when, then, parsers

    scenarios("scenario_outlines.feature")

    @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="cucumbers")
    def given_cucumbers(start):
        return {"count": start}

    @when(parsers.parse("I eat {eat:d} cucumbers"))
    def eat_cucumbers(cucumbers, eat):
        cucumbers["count"] -= eat

    @then(parsers.parse("I should have {left:d} cucumbers"))
    def should_have_left_cucumbers(cucumbers, left):
        assert cucumbers["count"] == left

Step Definitions and Accessing the Datatable
--------------------------------------------

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
Note that if you use pytest with the ``--strict`` option, all bdd tags mentioned in the feature files should be also in the ``markers`` setting of the ``pytest.ini`` config. Also for tags please use names which are python-compatible variable names, i.e. start with a non-number, only underscores or alphanumeric characters, etc. That way you can safely use tags for tests filtering.

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
        When        I try to post to "Expensive Therapy"
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
          The statement above applies to strict Gherkin mode, which is
          enabled by default.


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
