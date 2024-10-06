BDD library for the pytest runner
=================================

.. image:: http://img.shields.io/pypi/v/pytest-bdd-ng.svg
    :target: https://pypi.python.org/pypi/pytest-bdd-ng
.. image:: https://codecov.io/gh/elchupanebrej/pytest-bdd-ng/branch/default/graph/badge.svg
    :target: https://app.codecov.io/gh/elchupanebrej/pytest-bdd-ng
.. image:: https://readthedocs.org/projects/pytest-bdd-ng/badge/?version=default
    :target: https://pytest-bdd-ng.readthedocs.io/en/default/?badge=default
    :alt: Documentation Status
.. image:: https://badgen.net/badge/stand%20with/UKRAINE/?color=0057B8&labelColor=FFD700
    :target: https://savelife.in.ua/en/

.. _behave: https://pypi.python.org/pypi/behave
.. _pytest: https://docs.pytest.org
.. _Gherkin: https://cucumber.io/docs/gherkin/reference
.. _pytest-bdd-ng: https://pytest-bdd-ng.readthedocs.io/en/default/
.. _pytest-bdd: https://github.com/pytest-dev/pytest-bdd

**pytest-bdd-ng** combine descriptive clarity of Gherkin_ language
with power and fullness of pytest_ infrastructure.
It enables unifying unit and functional
tests, reduces the burden of continuous integration server configuration and allows the reuse of
test setups.

Pytest fixtures written for unit tests can be reused for setup and actions
mentioned in feature steps with dependency injection. This allows a true BDD
just-enough specification of the requirements without obligatory maintaining any context object
containing the side effects of Gherkin imperative declarations.

.. NOTE:: Project documentation on readthedocs: pytest-bdd-ng_


Why ``NG`` ?
------------

The current pytest plugin for cucumber is pytest-bdd_ , a popular project with 1.2k stars and used in 3k public repos and maintained by the pytest community. The upstream open-cucumber project does not have an official python release, so the current cucumber specs include features not available in pytest-bdd_ . This project is an effort to bridge the gap and also make it easier for pytest users to access new cucumber features.

.. list-table::
   :widths: 30 10 10 50
   :header-rows: 1

   * - Feature
     - original
     - NG
     - Description
   * - `Official parser support <https://github.com/cucumber/gherkin>`_
     - \-
     - \+
     - All features of Feature files are supported from the "box" (localisation, Rules, Examples, Data tables, etc.)
   * - Steps definitions via `Cucumber expressions <https://github.com/cucumber/cucumber-expressions>`_
     - \-
     - \+
     - Easy migration between implementations
   * - Reporting using `Messages <https://github.com/cucumber/messages>`_
     - \-
     - \+
     - Possible to use all collection of Cucumber community tools for reporting
   * - `Pickles <https://github.com/cucumber/gherkin>`_ internal protocol
     - \-
     - \+
     - Allows to implement parsers based on other file types/principles
   * - Heuristic step matching
     - \-/+
     - \+
     - Steps ease of use / amount of needed boilerplate code
   * - Step execution context. Step types and variants of definition
     - \-/+
     - \+
     - Dispatching steps by kind. Steps injecting multiple fixtures. Default injecting behaviors. Steps could be used on import automatically. It's possible to define default values for step variables.
   * - Automatic collection of Feature files
     - \-
     - \+
     - No boilerplate code / No mix between steps definition and feature files
   * - Load of Feature files by HTTP
     - \-
     - \+
     - Allows to integrate the library into external Feature storages
   * - Stability and bugfixes
     - \+
     - \+/-
     -
   * - Supported python/pytest versions
     - \+/-
     - \+
     - NG supports wider and elder pytest&python version. Tested also for PyPy
   * - Active community
     - \+
     - \-/+
     -


Install pytest-bdd-ng
---------------------

::

    pip install pytest-bdd-ng

Project layout
--------------
**pytest-bdd-ng** automatically collects ``*.feature`` files from pytest_ tests directory.
Important to remember, that feature files are used by other team members as live documentation,
so it's not a very good idea to mix documentation and test code.

The more features and scenarios you have, the more important becomes the question about
their organization. So the recommended way is to organize your feature files in the folders by
semantic groups:

::

    features
    ├──frontend
    │  └──auth
    │     └──login.feature
    └──backend
       └──auth
          └──login.feature

And tests for these features would be organized in the following manner:

::

    tests
    └──conftest.py
    └──functional
    │     └──__init__.py
    │     └──conftest.py
    │     │     └── "User step library used by descendant tests"
    │     │
    │     │         from steps.auth.given import *
    │     │         from steps.auth.when import *
    │     │         from steps.auth.then import *
    │     │
    │     │         from steps.order.given import *
    │     │         from steps.order.when import *
    │     │         from steps.order.then import *
    │     │
    │     │         from steps.browser.given import *
    │     │         from steps.browser.when import *
    │     │         from steps.browser.then import *
    │     │
    │     └──frontend_auth.feature -> ../../features/frontend/auth.feature
    │     └──backend_auth.feature -> ../../features/backend/auth.feature
    ...

The step definitions would then be organized like this:

::

    steps
    └──auth
    │     └── given.py
    │     │      └── """User auth step definitions"""
    │     │          from pytest import fixture
    │     │          from pytest_bdd import given, when, then, step
    │     │
    │     │          @fixture
    │     │          def credentials():
    │     │             return 'test_login', 'test_very_secure_pass'
    │     │
    │     │          @given('User login into application')
    │     │          def user_login(credentials):
    │     │             ...
    │     └── when.py
    │     └── then.py
    └──order
    │     └── given.py
    │     └── when.py
    │     └── then.py
    └──browser
    │     └── ...
    ...

To make links between feature files at features directory and test directory there are few options
(for more information please examine the project's tests):

#. Symlinks
#. `.desktop` files
#. `.webloc` files
#. `.url` files

.. NOTE:: Link files also could be used to load features by http://


How to Contribute
-----------------

The project is now open to contributions. Please open an issue for more details.
