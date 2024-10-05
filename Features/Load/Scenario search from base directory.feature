Feature: Feature files search is started from base directory
  By default, pytest-bdd-ng will use current module's path as base path for finding feature files,
  but this behaviour can be changed in the pytest configuration file (i.e. `pytest.ini`, `tox.ini` or `setup.cfg`)
  by declaring the new base path in the `bdd_features_base_dir` key.
  The path is interpreted as relative to the pytest root directory.
  You can also override features base path on a per-scenario basis,
  in order to override the path for specific tests.

  Background:
      Given File "Passing.feature" in the temporary path with content:
        # Feature is out testing directory, so won't be automatically collected
        """gherkin
        Feature: Passing feature
          Scenario: Passing scenario
            Given Passing step
          Scenario: Failing scenario
            Given Failing step
        """
      And File "conftest.py" with content:
        """python
        from pytest_bdd import step
        from pytest_bdd.compatibility.pytest import fail

        @step('Passing step')
        def _():
          ...

        @step('Failing step')
        def _():
          fail('Intentional')
        """
      And File "test_feature.py" with content:
        """python
        from pytest_bdd import scenarios

        test = scenarios('Passing.feature')
        """
    Scenario:
      Given File "pytest.ini" with fixture templated content:
        """ini
        [pytest]
        bdd_features_base_dir={tmp_path}
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     1|
