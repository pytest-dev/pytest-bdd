Automatic Feature Collection
--------------------------

Starting from version 8.1, pytest-bdd can automatically collect and run feature files without requiring explicit
@scenario decorators or scenarios() calls. This behavior is disabled by default but can be enabled via
configuration.

To enable automatic feature collection, add this to your pytest.ini:

.. code-block:: ini

    [pytest]
    bdd_auto_collect_features = true

When enabled, pytest-bdd will:

1. Recursively search for .feature files in your project
2. Parse each feature file and create test cases for each scenario
3. Skip scenarios that are already bound to test functions via @scenario or scenarios()
4. Generate test function names automatically based on the scenario names

This is particularly useful for:

* Quick prototyping and exploration of BDD features
* Reducing boilerplate code in simple test cases
* Ensuring no scenarios are accidentally missed

Note that manually bound scenarios take precedence over auto-collected ones.

.. include:: ../README.rst

.. include:: ../AUTHORS.rst

.. include:: ../CHANGES.rst
