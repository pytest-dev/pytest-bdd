.. toctree::
   :hidden:

Changelog
=========

In-progress
-----------

Planned
-------
- API doc
- Add struct_bdd autoload
- Move tox.ini, pytest.ini into pyproject.toml
- Review report generation to be conform with official tools
- Add tests about linked files and features autoload (feature autoload must not be disabled on linked files)
- Check using Path globs on the feature loading via scenario/scenarios
- Rework extended_step_context method usage
- Remove tests targeting Feature parsing

  - https://github.com/pytest-dev/pytest-bdd/issues/488
- Nested Rules support

  - Review after fix https://github.com/cucumber/gherkin/issues/126
- Implement support of \*.md files

  - Waiting for upstream issue https://github.com/cucumber/gherkin/pull/64
  - Use js implementation for such feature
- Support of messages:

  - Pending:

    - parse_error
    - undefined_parameter_type

- Add mode to execute scenarios with missing/failing steps
- Remove

  - Hide traceback for pytest code "__tracebackhide__ = True"
- Generate documentation via https://github.com/jolly-good-toolbelt/sphinx_gherkindoc instead of direct use

  - Move sphinx-gherkindoc to official parser

    - Documentation is ugly when contains injected code
- Rework generation code to include new features directly

  - Generate code into dir structure aligned with proposed project layout

- Test messages against

  - pytest-xdist at workers on different machines (sending back ndjson info https://codespeak.net/execnet/example/test_info.html#sending-channels-over-channels)

    - Investigate https://smarie.github.io/python-pytest-harvest/
  - pytest-rerunfailures
  - Parametrize step execution by different step realizations using https://smarie.github.io/python-pytest-cases/
- Switch testdir to pytester after pytest<6.2 get EOL (python 3.8 and 3.9 get EOL)
- Use Poetry

  - Wait for https://github.com/python-poetry/roadmap/issues/3
- Contribute to messages repository with python model
- Add support of native legacy cucumber-json
- Test against https://github.com/cucumber/json-formatter

Unreleased
----------

2.2.0
-----
- Move documentation to Gherkin itself
- Fixed pytest.ini option "disable_feature_autoload"
- Improved fixture injection by adding seamless fixtures on plugin/module collection

2.1.4
-----
- Add support for Python 3.12 in CI
- Add support for pytest 8
- Switch to the official Gherkin package: https://pypi.org/project/ci-environment/
- Fix other compatibility issues

2.1.0
-----
- Add validation for legacy cucumber.json output
- Migrated to Pydantic 2
- Add tests for PyPy
- Using tox4
- Added support of conditional hooks https://cucumber.io/docs/cucumber/api/?lang=java#conditional-hooks
- Support of messages:

  - Done:

    - meta
    - gherkin_document
    - pickle
    - source
    - step_definition
    - test_case
    - test_case_finished
    - test_case_started
    - test_run_finished
    - test_run_started
    - test_step_finished
    - test_step_started
    - parameter_type
    - attachment
    - hook

2.0.0
-----
- Reviewed StructBdd step collection; no more ``as_test`` / ``as_test_decorator`` Step methods are needed directly used
- Drop python 3.7
- Move StructBDD model to Pydantic
- Remove ast module usage by StructBDD
- Test filters in scenario/scenarios to filter out not needed scenarios
- ``.url``, ``.desktop`` and ``.webloc`` files are collected from test directories, so scenario/scenarios usages is not necessary
- Load features/scenarios by url
- Features are autoloaded by default; Feature autoload could be disabled by ``--disable-feature-autoload`` cli option
- Relative feature paths are counted from pytest rootpath
- No more injection of tests into module space; Tests have to be registered directly
- Separate generation scripts were moved to pytest environment
- ``scenario`` no more override collected scenarios; They have to be registered independently. Scenarios could be filtered out if needed.
- Added support of messages
- Added support of cucumber expressions https://github.com/cucumber/cucumber-expressions#readme
- It possible to name anonymous groups during step parsing
- Remove legacy feature parser (and surplus features of it)
- Remove outdated migration script

1.2.3
-----
- Features could be autoloaded by --feature-autoload cli option
- Remove possibility to manually register imported steps; They are registered automatically

1.2.2
-----
- Add possibility to register imported steps

1.2.0
-----
- Make liberal step definitions conform with

  - `Change messages and Gherkin parser/pickle compiler to retain step keyword (#1741) <https://github.com/cucumber/common/pull/1741>`_
  - `Proposal: Unambiguous Keywords (#768) <https://github.com/cucumber/common/issues/768>`_

1.1.2
-----
- Fixups

1.1.1
-----
- Added hook to alter scenario steps execution protocol

1.1.0
-----
- Added allure plugin extension for allure-pytest
- Added StructBDD DSL

1.0.0
-----
- Default step parameter parser is switched to cfparse. String step name is compiled to cfparse
- Step functions could get compiled instances of parse, cfparse and re.compile directly
- Drop pytest 4
- Drop python 3.6
- Added tags support for Examples sections for original parser
- Added joining by parameters between examples sections on different levels (and with fixtures) for original feature parser
- Step could override multiple fixtures using ``target_fixtures`` parameter
- Default step parameters injection as fixtures behavior could be changed by ``params_fixtures_mapping`` step parameter
- Step definitions can have "yield" statements again (4.0 release broke it). They will be executed as normal fixtures: code after the yield is executed during teardown of the test. (youtux)
- Show pass/fail status per step in Gherkin terminal reporter
- Step definitions could be used independently from keyword by ``step`` decorator

  - https://github.com/pytest-dev/pytest-bdd/issues/450
- ``pytest_bdd_apply_tag`` was removed; ``pytest_bdd_convert_tag_to_marks`` was added instead
- Feature parser switched to official one

  - https://github.com/pytest-dev/pytest-bdd/issues/394
  - https://github.com/pytest-dev/pytest-bdd/issues/511
- Changes ``scenario`` and ``scenarios`` function/decorator feature registration order. Both could be used as decorators
- Move scenario execution & step matching to hooks
- Added possibility to operate steps stack via fixture
- Other

  - https://github.com/pytest-dev/pytest-bdd/issues/464
  - https://github.com/pytest-dev/pytest-bdd/issues/474
  - https://github.com/pytest-dev/pytest-bdd/issues/512


Pre pytest-bdd-ng era
---------------------

5.0.0
#####
This release introduces breaking changes, please refer to the `Migration from 4.x.x`.

- Rewrite the logic to parse Examples for Scenario Outlines. Now the substitution of the examples is done during the parsing of Gherkin feature files. You won't need to define the steps twice like ``@given("there are <start> cucumbers")`` and ``@given(parsers.parse("there are {start} cucumbers"))``. The latter will be enough.
- Removed ``example_converters`` from ``scenario(...)`` signature. You should now use just the ``converters`` parameter for ``given``, ``when``, ``then``.
- Removed ``--cucumberjson-expanded`` and ``--cucumber-json-expanded`` options. Now the JSON report is always expanded.
- Removed ``--gherkin-terminal-reporter-expanded`` option. Now the terminal report is always expanded.

4.1.0
#####
- `when` and `then` steps now can provide a `target_fixture`, just like `given` does. Discussion at https://github.com/pytest-dev/pytest-bdd/issues/402.
- Drop compatibility for python 2 and officially support only python >= 3.6.
- Fix error when using `--cucumber-json-expanded` in combination with `example_converters` (marcbrossaissogeti).
- Fix `--generate-missing` not correctly recognizing steps with parsers

4.0.2
#####
- Fix a bug that prevents using comments in the ``Examples:`` section. (youtux)


4.0.1
#####
- Fixed performance regression introduced in 4.0.0 where collection time of tests would take way longer than before. (youtux)


4.0.0
#####
This release introduces breaking changes, please refer to the `Migration from 3.x.x`.

- Strict Gherkin option is removed (``@scenario()`` does not accept the ``strict_gherkin`` parameter). (olegpidsadnyi)
- ``@scenario()`` does not accept the undocumented parameter ``caller_module`` anymore. (youtux)
- Given step is no longer a fixture. The scope parameter is also removed. (olegpidsadnyi)
- Fixture parameter is removed from the given step declaration. (olegpidsadnyi)
- ``pytest_bdd_step_validation_error`` hook is removed. (olegpidsadnyi)
- Fix an error with pytest-pylint plugin #374. (toracle)
- Fix pytest-xdist 2.0 compatibility #369. (olegpidsadnyi)
- Fix compatibility with pytest 6 ``--import-mode=importlib`` option. (youtux)


3.4.0
#####
- Parse multiline steps according to the gherkin specification #365.


3.3.0
#####
- Drop support for pytest < 4.3.
- Fix a Python 4.0 bug.
- Fix ``pytest --generate-missing`` functionality being broken.
- Fix problematic missing step definition from strings containing quotes.
- Implement parsing escaped pipe characters in outline parameters (Mark90) #337.
- Disable the strict Gherkin validation in the steps generation (v-buriak) #356.

3.2.1
#####
- Fix regression introduced in 3.2.0 where pytest-bdd would break in presence of test items that are not functions.

3.2.0
#####
- Fix Python 3.8 support
- Remove code that rewrites code. This should help with the maintenance of this project and make debugging easier.

3.1.1
#####
- Allow unicode string in ``@given()`` step names when using python2.
  This makes the transition of projects from python 2 to 3 easier.

3.1.0
#####
- Drop support for pytest < 3.3.2.
- Step definitions generated by ``$ pytest-bdd generate`` will now raise ``NotImplementedError`` by default.
- ``@given(...)`` no longer accepts regex objects. It was deprecated long ago.
- Improve project testing by treating warnings as exceptions.
- ``pytest_bdd_step_validation_error`` will now always receive ``step_func_args`` as defined in the signature.

3.0.2
#####
- Add compatibility with pytest 4.2 (sliwinski-milosz) #288.

3.0.1
#####
- Minimal supported version of `pytest` is now 2.9.0 as lower versions do not support `bool` type ini options (sliwinski-milosz) #260
- Fix RemovedInPytest4Warning warnings (sliwinski-milosz) #261.

3.0.0
#####
- Fixtures `pytestbdd_feature_base_dir` and `pytestbdd_strict_gherkin` have been removed. Check the `Migration of your tests from versions 2.x.x <README.rst>`_ for more information (sliwinski-milosz) #255
- Fix step definitions not being found when using parsers or converters after a change in pytest (youtux) #257

2.21.0
######
- Gherkin terminal reporter expanded format (pauk-slon)


2.20.0
######
- Added support for But steps (olegpidsadnyi)
- Fixed compatibility with pytest 3.3.2 (olegpidsadnyi)
- MInimal required version of pytest is now 2.8.1 since it doesn't support earlier versions (olegpidsadnyi)


2.19.0
######
- Added --cucumber-json-expanded option for explicit selection of expanded format (mjholtkamp)
- Step names are filled in when --cucumber-json-expanded is used (mjholtkamp)

2.18.2
######
- Fix check for out section steps definitions for no strict gherkin feature

2.18.1
######
- Relay fixture results to recursive call of 'get_features' (coddingtonbear)

2.18.0
######
- Add gherkin terminal reporter (spinus + thedrow)

2.17.2
######
- Fix scenario lines containing an ``@`` being parsed as a tag. (The-Compiler)

2.17.1
######
- Add support for pytest 3.0

2.17.0
######
- Fix FixtureDef signature for newer pytest versions (The-Compiler)
- Better error explanation for the steps defined outside of scenarios (olegpidsadnyi)
- Add a ``pytest_bdd_apply_tag`` hook to customize handling of tags (The-Compiler)
- Allow spaces in tag names. This can be useful when using the
  ``pytest_bdd_apply_tag`` hook with tags like ``@xfail: Some reason``.


2.16.1
######
- Cleaned up hooks of the plugin (olegpidsadnyi)
- Fixed report serialization (olegpidsadnyi)


2.16.0
######
- Fixed deprecation warnings with pytest 2.8 (The-Compiler)
- Fixed deprecation warnings with Python 3.5 (The-Compiler)

2.15.0
######
- Add examples data in the scenario report (bubenkoff)

2.14.5
######
- Properly parse feature description (bubenkoff)

2.14.3
######
- Avoid potentially random collection order for xdist compartibility (bubenkoff)

2.14.1
######
- Pass additional arguments to parsers (bubenkoff)

2.14.0
######
- Add validation check which prevents having multiple features in a single feature file (bubenkoff)

2.13.1
######
- Allow mixing feature example table with scenario example table (bubenkoff, olegpidsadnyi)

2.13.0
######
- Feature example table (bubenkoff, sureshvv)

2.12.2
######
- Make it possible to relax strict Gherkin scenario validation (bubenkoff)

2.11.3
######
- Fix minimal `six` version (bubenkoff, dustinfarris)

2.11.1
######
- Mention step type on step definition not found errors and in code generation (bubenkoff, lrowe)

2.11.0
######
- Prefix step definition fixture names to avoid name collisions (bubenkoff, lrowe)

2.10.0
######
- Make feature and scenario tags to be fully compartible with pytest markers (bubenkoff, kevinastone)

2.9.1
#####
- Fixed FeatureError string representation to correctly support python3 (bubenkoff, lrowe)

2.9.0
#####
- Added possibility to inject fixtures from given keywords (bubenkoff)

2.8.0
#####
- Added hook before the step is executed with evaluated parameters (olegpidsadnyi)

2.7.2
#####
- Correct base feature path lookup for python3 (bubenkoff)

2.7.1
#####
- Allow to pass ``scope`` for ``given`` steps (bubenkoff, sureshvv)

2.7.0
#####
- Implemented `scenarios` shortcut to automatically bind scenarios to tests (bubenkoff)

2.6.2
#####
- Parse comments only in the beginning of words (santagada)

2.6.1
#####
- Correctly handle `pytest-bdd` command called without the subcommand under python3 (bubenkoff, spinus)
- Pluggable parsers for step definitions (bubenkoff, spinus)

2.5.3
#####
- Add after scenario hook, document both before and after scenario hooks (bubenkoff)

2.5.2
#####
- Fix code generation steps ordering (bubenkoff)

2.5.1
#####
- Fix error report serialization (olegpidsadnyi)

2.5.0
#####
- Fix multiline steps in the Background section (bubenkoff, arpe)
- Code cleanup (olegpidsadnyi)


2.4.5
#####
- Fix unicode issue with scenario name (bubenkoff, aohontsev)

2.4.3
#####
- Fix unicode regex argumented steps issue (bubenkoff, aohontsev)
- Fix steps timings in the json reporting (bubenkoff)

2.4.2
#####
- Recursion is fixed for the --generate-missing and the --feature parameters (bubenkoff)

2.4.1
#####
- Better reporting of a not found scenario (bubenkoff)
- Simple test code generation implemented (bubenkoff)
- Correct timing values for cucumber json reporting (bubenkoff)
- Validation/generation helpers (bubenkoff)

2.4.0
#####
- Background support added (bubenkoff)
- Fixed double collection of the conftest files if scenario decorator is used (ropez, bubenkoff)

2.3.3
#####
- Added timings to the cucumber json report (bubenkoff)

2.3.2
#####
- Fixed incorrect error message using e.argname instead of step.name (hvdklauw)

2.3.1
#####
- Implemented cucumber tags support (bubenkoff)
- Implemented cucumber json formatter (bubenkoff, albertjan)
- Added 'trace' keyword (bubenkoff)

2.1.2
#####
- Latest pytest compartibility fixes (bubenkoff)

2.1.1
#####
- Bugfixes (bubenkoff)

2.1.0
#####
- Implemented multiline steps (bubenkoff)

2.0.1
#####
- Allow more than one parameter per step (bubenkoff)
- Allow empty example values (bubenkoff)

2.0.0
#####
- Pure pytest parametrization for scenario outlines (bubenkoff)
- Argumented steps now support converters (transformations) (bubenkoff)
- scenario supports only decorator form (bubenkoff)
- Code generation refactoring and cleanup (bubenkoff)

1.0.0
#####
- Implemented scenario outlines (bubenkoff)


0.6.11
######
- Fixed step arguments conflict with the fixtures having the same name (olegpidsadnyi)

0.6.9
#####
- Implemented support of Gherkin "Feature:" (olegpidsadnyi)

0.6.8
#####
- Implemented several hooks to allow reporting/error handling (bubenkoff)

0.6.6
#####
- Fixes to unnecessary mentioning of pytest-bdd package files in py.test log with -v (bubenkoff)

0.6.5
#####
- Compatibility with recent pytest (bubenkoff)

0.6.4
#####
- More unicode fixes (amakhnach)

0.6.3
#####
- Added unicode support for feature files. Removed buggy module replacement for scenario. (amakhnach)

0.6.2
#####
- Removed unnecessary mention of pytest-bdd package files in py.test log with -v (bubenkoff)

0.6.1
#####
- Step arguments in whens when there are no given arguments used. (amakhnach, bubenkoff)

0.6.0
#####
- Added step arguments support. (curzona, olegpidsadnyi, bubenkoff)
- Added checking of the step type order. (markon, olegpidsadnyi)

0.5.2
#####
- Added extra info into output when FeatureError exception raises. (amakhnach)

0.5.0
#####
- Added parametrization to scenarios
- Coveralls.io integration
- Test coverage improvement/fixes
- Correct wrapping of step functions to preserve function docstring

0.4.7
#####
- Fixed Python 3.3 support

0.4.6
#####
- Fixed a bug when py.test --fixtures showed incorrect filenames for the steps.

0.4.5
#####
- Fixed a bug with the reuse of the fixture by given steps being evaluated multiple times.

0.4.3
#####
- Update the license file and PYPI related documentation.
