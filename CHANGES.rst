Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.1.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Unreleased
----------

Added
+++++

Changed
+++++++
* Step arguments ``"datatable"`` and ``"docstring"`` are now reserved, and they can't be used as step argument names.

Deprecated
++++++++++

Removed
+++++++

Fixed
+++++
* Fixed an issue with the upcoming pytest release related to the use of ``@pytest.mark.usefixtures`` with an empty list.
* Render template variables in docstrings and datatable cells with example table entries, as we already do for steps definitions.

Security
++++++++


[8.0.0] - 2024-11-14
----------

Added
+++++
* Gherkin keyword aliases can now be used and correctly reported in json and terminal output (see `Keywords <https://cucumber.io/docs/gherkin/reference/#keywords>`_ for permitted list).
* Added localization support. The language of the feature file can be specified using the `# language: <language>` directive at the beginning of the file.
* Rule keyword can be used in feature files (see `Rule <https://cucumber.io/docs/gherkin/reference/#rule>`_)
* Added support for multiple example tables
* Added filtering by tags against example tables
* Since the 7.x series:
  * Tags can now be on multiple lines (stacked)
  * Continuation of steps using asterisks (``*``) instead of ``And``/``But`` supported.
  * Added ``datatable`` argument for steps that contain a datatable (see `Data Tables <https://cucumber.io/docs/gherkin/reference/#data-tables>`_).
  * Added ``docstring`` argument for steps that contain a docstring (see `Doc Strings <https://cucumber.io/docs/gherkin/reference/#doc-strings>`_).

Changed
+++++++
* Changelog format updated to follow `Keep a Changelog <https://keepachangelog.com/en/1.1.0/>`_.
* Text after the ``#`` character is no longer stripped from the Scenario and Feature name.
* Since the 7.x series:

  * Use the `gherkin-official <https://pypi.org/project/gherkin-official/>`_ parser, replacing the custom parsing logic. This will make pytest-bdd more compatible with the Gherkin specification.
  * Multiline steps must now always use triple-quotes for the additional lines.
  * All feature files must now use the keyword ``Feature:`` to be considered valid.
  * Tags can no longer have spaces (e.g. ``@tag one`` and ``@tag two`` are no longer valid).
  * Text after the ``#`` character is no longer stripped from the Step name.
  * Multiline strings no longer match name based on multiple lines - only on the actual step text on the step line.

Removed
+++++++
* Dropped support for python 3.8. Supported python versions: 3.9, 3.10, 3.11, 3.12, 3.13.
* Since the 7.x series:

  * Drop compatibility with pytest < 7.0.0.

Fixed
+++++
* Since the 7.x series:

  * Updated documentation to clarify that ``--gherkin-terminal-reporter`` needs to be used with ``-v`` or ``-vv``.

8.0.0b2
----------
* Updated documentation to clarify that ``--gherkin-terminal-reporter`` needs to be used with ``-v`` or ``-vv``.
* Drop compatibility with pytest < 7.0.0.
* Continuation of steps using asterisks instead of And/But supported.
* Added ``datatable`` argument for steps that contain a datatable (see `Data Tables <https://cucumber.io/docs/gherkin/reference/#data-tables>`_).
* Added ``docstring`` argument for steps that contain a docstring (see `Doc Strings <https://cucumber.io/docs/gherkin/reference/#doc-strings>`_).
* Multiline strings no longer match name based on multiple lines - only on the actual step text on the step line.

8.0.0b1
----------
* Use the `gherkin-official <https://pypi.org/project/gherkin-official/>`_ parser, replacing the custom parsing logic. This will make pytest-bdd more compatible with the Gherkin specification.
* Multiline steps must now always use triple-quotes for the additional lines.
* All feature files must now use the keyword ``Feature:`` to be considered valid.
* Tags can no longer have spaces (e.g. ``@tag one`` and ``@tag two`` are no longer valid).
* Tags can now be on multiple lines (stacked)
* Text after the ``#`` character is no longer stripped from the Step name.

7.3.0
----------
- Fix an issue when only the first Step would inject a fixture, while later steps would not be able to.
- Test against the latest versions of pytest (8.2, 8.3).

7.2.0
----------
- Fix compatibility issue with Python 3.13.
- Declare compatibility with Python 3.13.

7.1.2
----------
- Address another compatibility issue with pytest 8.1 (fixture registration). `#680 <https://github.com/pytest-dev/pytest-bdd/pull/680>`_

7.1.1
----------
- Address a bug introduced in pytest-bdd 7.1 caused by incorrect pytest version check.

7.1
----------
- Address compatibility issue with pytest 8.1. `#666 <https://github.com/pytest-dev/pytest-bdd/pull/666>`_

7.0.1
-----
- Fix errors occurring if `pytest_unconfigure` is called before `pytest_configure`. `#362 <https://github.com/pytest-dev/pytest-bdd/issues/362>`_ `#641 <https://github.com/pytest-dev/pytest-bdd/pull/641>`_

7.0.0
----------
- ⚠️ Backwards incompatible: - ``parsers.re`` now does a `fullmatch <https://docs.python.org/3/library/re.html#re.fullmatch>`_ instead of a partial match. This is to make it work just like the other parsers, since they don't ignore non-matching characters at the end of the string. `#539 <https://github.com/pytest-dev/pytest-bdd/pull/539>`_
- Drop python 3.7 compatibility, as it's no longer supported. `#627 <https://github.com/pytest-dev/pytest-bdd/pull/627>`_
- Declare official support for python 3.12 `#628 <https://github.com/pytest-dev/pytest-bdd/pull/628>`_
- Improve parser performance by 15% `#623 <https://github.com/pytest-dev/pytest-bdd/pull/623>`_ by `@dcendents <https://github.com/dcendents>`_
- Add support for Scenarios and Scenario Outlines to have descriptions. `#600 <https://github.com/pytest-dev/pytest-bdd/pull/600>`_

6.1.1
-----
- Fix regression introduced in version 6.1.0 where the ``pytest_bdd_after_scenario`` hook would be called after every step instead of after the scenario. `#577 <https://github.com/pytest-dev/pytest-bdd/pull/577>`_

6.1.0
-----
- Fix bug where steps without parsers would take precedence over steps with parsers. `#534 <https://github.com/pytest-dev/pytest-bdd/pull/534>`_
- Step functions can now be decorated multiple times with @given, @when, @then. Previously every decorator would override ``converters`` and ``target_fixture`` every at every application. `#534 <https://github.com/pytest-dev/pytest-bdd/pull/534>`_ `#544 <https://github.com/pytest-dev/pytest-bdd/pull/544>`_ `#525 <https://github.com/pytest-dev/pytest-bdd/issues/525>`_
- Require pytest>=6.2 `#534 <https://github.com/pytest-dev/pytest-bdd/pull/534>`_
- Using modern way to specify hook options to avoid deprecation warnings with pytest >=7.2.
- Add generic ``step`` decorator that will be used for all kind of steps `#548 <https://github.com/pytest-dev/pytest-bdd/pull/548>`_
- Add ``stacklevel`` param to ``given``, ``when``, ``then``, ``step`` decorators. This allows for programmatic step generation `#548 <https://github.com/pytest-dev/pytest-bdd/pull/548>`_
- Hide pytest-bdd internal method in user tracebacks `#557 <https://github.com/pytest-dev/pytest-bdd/pull/557>`_.
- Make the package PEP 561-compatible `#559 <https://github.com/pytest-dev/pytest-bdd/issues/559>`_ `#563 <https://github.com/pytest-dev/pytest-bdd/pull/563>`_.
- Configuration option ``bdd_features_base_dir`` is interpreted as relative to the `pytest root directory <https://docs.pytest.org/en/latest/reference/customize.html#rootdir>`_ (previously it was relative to the current working directory). `#573 <https://github.com/pytest-dev/pytest-bdd/pull/573>`_


6.0.1
-----
- Fix regression introduced in 6.0.0 where a step function decorated multiple using a parsers times would not be executed correctly. `#530 <https://github.com/pytest-dev/pytest-bdd/pull/530>`_ `#528 <https://github.com/pytest-dev/pytest-bdd/issues/528>`_


6.0.0
-----

This release introduces breaking changes in order to be more in line with the official gherkin specification.

- Cleanup of the documentation and tests related to parametrization (elchupanebrej) `#469 <https://github.com/pytest-dev/pytest-bdd/pull/469>`_
- Removed feature level examples for the gherkin compatibility (olegpidsadnyi) `#490 <https://github.com/pytest-dev/pytest-bdd/pull/490>`_
- Removed vertical examples for the gherkin compatibility (olegpidsadnyi) `#492 <https://github.com/pytest-dev/pytest-bdd/pull/492>`_
- Step arguments are no longer fixtures (olegpidsadnyi) `#493 <https://github.com/pytest-dev/pytest-bdd/pull/493>`_
- Drop support of python 3.6, pytest 4 (elchupanebrej) `#495 <https://github.com/pytest-dev/pytest-bdd/pull/495>`_ `#504 <https://github.com/pytest-dev/pytest-bdd/issues/504>`_
- Step definitions can have "yield" statements again (4.0 release broke it). They will be executed as normal fixtures: code after the yield is executed during teardown of the test. (youtux) `#503 <https://github.com/pytest-dev/pytest-bdd/issues/503>`_
- Scenario outlines unused example parameter validation is removed (olegpidsadnyi) `#499 <https://github.com/pytest-dev/pytest-bdd/pull/499>`_
- Add type annotations (youtux) `#505 <https://github.com/pytest-dev/pytest-bdd/pull/505>`_
- ``pytest_bdd.parsers.StepParser`` now is an Abstract Base Class. Subclasses must make sure to implement the abstract methods. (youtux) `#505 <https://github.com/pytest-dev/pytest-bdd/pull/505>`_
- Angular brackets in step definitions are only parsed in "Scenario Outline" (previously they were parsed also in normal "Scenario"s) (youtux) `#524 <https://github.com/pytest-dev/pytest-bdd/pull/524>`_.



5.0.0
-----
This release introduces breaking changes, please refer to the :ref:`Migration from 4.x.x`.

- Rewrite the logic to parse Examples for Scenario Outlines. Now the substitution of the examples is done during the parsing of Gherkin feature files. You won't need to define the steps twice like ``@given("there are <start> cucumbers")`` and ``@given(parsers.parse("there are {start} cucumbers"))``. The latter will be enough.
- Removed ``example_converters`` from ``scenario(...)`` signature. You should now use just the ``converters`` parameter for ``given``, ``when``, ``then``.
- Removed ``--cucumberjson-expanded`` and ``--cucumber-json-expanded`` options. Now the JSON report is always expanded.
- Removed ``--gherkin-terminal-reporter-expanded`` option. Now the terminal report is always expanded.

4.1.0
-----------
- `when` and `then` steps now can provide a `target_fixture`, just like `given` does. Discussion at https://github.com/pytest-dev/pytest-bdd/issues/402.
- Drop compatibility for python 2 and officially support only python >= 3.6.
- Fix error when using `--cucumber-json-expanded` in combination with `example_converters` (marcbrossaissogeti).
- Fix `--generate-missing` not correctly recognizing steps with parsers

4.0.2
-----
- Fix a bug that prevents using comments in the ``Examples:`` section. (youtux)


4.0.1
-----
- Fixed performance regression introduced in 4.0.0 where collection time of tests would take way longer than before. (youtux)


4.0.0
-----

This release introduces breaking changes, please refer to the :ref:`Migration from 3.x.x`.

- Strict Gherkin option is removed (``@scenario()`` does not accept the ``strict_gherkin`` parameter). (olegpidsadnyi)
- ``@scenario()`` does not accept the undocumented parameter ``caller_module`` anymore. (youtux)
- Given step is no longer a fixture. The scope parameter is also removed. (olegpidsadnyi)
- Fixture parameter is removed from the given step declaration. (olegpidsadnyi)
- ``pytest_bdd_step_validation_error`` hook is removed. (olegpidsadnyi)
- Fix an error with pytest-pylint plugin #374. (toracle)
- Fix pytest-xdist 2.0 compatibility #369. (olegpidsadnyi)
- Fix compatibility with pytest 6 ``--import-mode=importlib`` option. (youtux)


3.4.0
-----

- Parse multiline steps according to the gherkin specification #365.


3.3.0
-----

- Drop support for pytest < 4.3.
- Fix a Python 4.0 bug.
- Fix ``pytest --generate-missing`` functionality being broken.
- Fix problematic missing step definition from strings containing quotes.
- Implement parsing escaped pipe characters in outline parameters (Mark90) #337.
- Disable the strict Gherkin validation in the steps generation (v-buriak) #356.

3.2.1
----------

- Fix regression introduced in 3.2.0 where pytest-bdd would break in presence of test items that are not functions.

3.2.0
----------

- Fix Python 3.8 support
- Remove code that rewrites code. This should help with the maintenance of this project and make debugging easier.

3.1.1
----------

- Allow unicode string in ``@given()`` step names when using python2.
  This makes the transition of projects from python 2 to 3 easier.

3.1.0
----------

- Drop support for pytest < 3.3.2.
- Step definitions generated by ``$ pytest-bdd generate`` will now raise ``NotImplementedError`` by default.
- ``@given(...)`` no longer accepts regex objects. It was deprecated long ago.
- Improve project testing by treating warnings as exceptions.
- ``pytest_bdd_step_validation_error`` will now always receive ``step_func_args`` as defined in the signature.

3.0.2
------

- Add compatibility with pytest 4.2 (sliwinski-milosz) #288.

3.0.1
------

- Minimal supported version of `pytest` is now 2.9.0 as lower versions do not support `bool` type ini options (sliwinski-milosz) #260
- Fix RemovedInPytest4Warning warnings (sliwinski-milosz) #261.

3.0.0
------

- Fixtures `pytestbdd_feature_base_dir` and `pytestbdd_strict_gherkin` have been removed. Check the `Migration of your tests from versions 2.x.x <README.rst>`_ for more information (sliwinski-milosz) #255
- Fix step definitions not being found when using parsers or converters after a change in pytest (youtux) #257

2.21.0
------

- Gherkin terminal reporter expanded format (pauk-slon)


2.20.0
------

- Added support for But steps (olegpidsadnyi)
- Fixed compatibility with pytest 3.3.2 (olegpidsadnyi)
- MInimal required version of pytest is now 2.8.1 since it doesn't support earlier versions (olegpidsadnyi)


2.19.0
------

- Added --cucumber-json-expanded option for explicit selection of expanded format (mjholtkamp)
- Step names are filled in when --cucumber-json-expanded is used (mjholtkamp)

2.18.2
------

- Fix check for out section steps definitions for no strict gherkin feature

2.18.1
------

- Relay fixture results to recursive call of 'get_features' (coddingtonbear)

2.18.0
------

- Add gherkin terminal reporter (spinus + thedrow)

2.17.2
------

- Fix scenario lines containing an ``@`` being parsed as a tag. (The-Compiler)

2.17.1
------

- Add support for pytest 3.0

2.17.0
------

- Fix FixtureDef signature for newer pytest versions (The-Compiler)
- Better error explanation for the steps defined outside of scenarios (olegpidsadnyi)
- Add a ``pytest_bdd_apply_tag`` hook to customize handling of tags (The-Compiler)
- Allow spaces in tag names. This can be useful when using the
  ``pytest_bdd_apply_tag`` hook with tags like ``@xfail: Some reason``.


2.16.1
------

- Cleaned up hooks of the plugin (olegpidsadnyi)
- Fixed report serialization (olegpidsadnyi)


2.16.0
------

- Fixed deprecation warnings with pytest 2.8 (The-Compiler)
- Fixed deprecation warnings with Python 3.5 (The-Compiler)

2.15.0
------

- Add examples data in the scenario report (bubenkoff)

2.14.5
------

- Properly parse feature description (bubenkoff)

2.14.3
------

- Avoid potentially random collection order for xdist compartibility (bubenkoff)

2.14.1
------

- Pass additional arguments to parsers (bubenkoff)

2.14.0
------

- Add validation check which prevents having multiple features in a single feature file (bubenkoff)

2.13.1
------

- Allow mixing feature example table with scenario example table (bubenkoff, olegpidsadnyi)

2.13.0
------

- Feature example table (bubenkoff, sureshvv)

2.12.2
------

- Make it possible to relax strict Gherkin scenario validation (bubenkoff)

2.11.3
------

- Fix minimal `six` version (bubenkoff, dustinfarris)

2.11.1
------

- Mention step type on step definition not found errors and in code generation (bubenkoff, lrowe)

2.11.0
------

- Prefix step definition fixture names to avoid name collisions (bubenkoff, lrowe)

2.10.0
------

- Make feature and scenario tags to be fully compartible with pytest markers (bubenkoff, kevinastone)

2.9.1
-----

- Fixed FeatureError string representation to correctly support python3 (bubenkoff, lrowe)

2.9.0
-----

- Added possibility to inject fixtures from given keywords (bubenkoff)

2.8.0
-----

- Added hook before the step is executed with evaluated parameters (olegpidsadnyi)

2.7.2
-----

- Correct base feature path lookup for python3 (bubenkoff)

2.7.1
-----

- Allow to pass ``scope`` for ``given`` steps (bubenkoff, sureshvv)

2.7.0
-----

- Implemented `scenarios` shortcut to automatically bind scenarios to tests (bubenkoff)

2.6.2
-----

- Parse comments only in the beginning of words (santagada)

2.6.1
-----

- Correctly handle `pytest-bdd` command called without the subcommand under python3 (bubenkoff, spinus)
- Pluggable parsers for step definitions (bubenkoff, spinus)

2.5.3
-----

- Add after scenario hook, document both before and after scenario hooks (bubenkoff)

2.5.2
-----

- Fix code generation steps ordering (bubenkoff)

2.5.1
-----

- Fix error report serialization (olegpidsadnyi)

2.5.0
-----

- Fix multiline steps in the Background section (bubenkoff, arpe)
- Code cleanup (olegpidsadnyi)


2.4.5
-----

- Fix unicode issue with scenario name (bubenkoff, aohontsev)

2.4.3
-----

- Fix unicode regex argumented steps issue (bubenkoff, aohontsev)
- Fix steps timings in the json reporting (bubenkoff)

2.4.2
-----

- Recursion is fixed for the --generate-missing and the --feature parameters (bubenkoff)

2.4.1
-----

- Better reporting of a not found scenario (bubenkoff)
- Simple test code generation implemented (bubenkoff)
- Correct timing values for cucumber json reporting (bubenkoff)
- Validation/generation helpers (bubenkoff)

2.4.0
-----

- Background support added (bubenkoff)
- Fixed double collection of the conftest files if scenario decorator is used (ropez, bubenkoff)

2.3.3
-----

- Added timings to the cucumber json report (bubenkoff)

2.3.2
-----

- Fixed incorrect error message using e.argname instead of step.name (hvdklauw)

2.3.1
-----

- Implemented cucumber tags support (bubenkoff)
- Implemented cucumber json formatter (bubenkoff, albertjan)
- Added 'trace' keyword (bubenkoff)

2.1.2
-----

- Latest pytest compartibility fixes (bubenkoff)

2.1.1
-----

- Bugfixes (bubenkoff)

2.1.0
-----

- Implemented multiline steps (bubenkoff)

2.0.1
-----

- Allow more than one parameter per step (bubenkoff)
- Allow empty example values (bubenkoff)

2.0.0
-----

- Pure pytest parametrization for scenario outlines (bubenkoff)
- Argumented steps now support converters (transformations) (bubenkoff)
- scenario supports only decorator form (bubenkoff)
- Code generation refactoring and cleanup (bubenkoff)

1.0.0
-----

- Implemented scenario outlines (bubenkoff)


0.6.11
------

- Fixed step arguments conflict with the fixtures having the same name (olegpidsadnyi)

0.6.9
-----

- Implemented support of Gherkin "Feature:" (olegpidsadnyi)

0.6.8
-----

- Implemented several hooks to allow reporting/error handling (bubenkoff)

0.6.6
-----

- Fixes to unnecessary mentioning of pytest-bdd package files in py.test log with -v (bubenkoff)

0.6.5
-----

- Compartibility with recent pytest (bubenkoff)

0.6.4
-----

- More unicode fixes (amakhnach)

0.6.3
-----

- Added unicode support for feature files. Removed buggy module replacement for scenario. (amakhnach)

0.6.2
-----

- Removed unnecessary mention of pytest-bdd package files in py.test log with -v (bubenkoff)

0.6.1
-----

- Step arguments in whens when there are no given arguments used. (amakhnach, bubenkoff)

0.6.0
-----

- Added step arguments support. (curzona, olegpidsadnyi, bubenkoff)
- Added checking of the step type order. (markon, olegpidsadnyi)

0.5.2
-----

- Added extra info into output when FeatureError exception raises. (amakhnach)

0.5.0
-----

- Added parametrization to scenarios
- Coveralls.io integration
- Test coverage improvement/fixes
- Correct wrapping of step functions to preserve function docstring

0.4.7
-----

- Fixed Python 3.3 support

0.4.6
-----

- Fixed a bug when py.test --fixtures showed incorrect filenames for the steps.

0.4.5
-----

- Fixed a bug with the reuse of the fixture by given steps being evaluated multiple times.

0.4.3
-----

- Update the license file and PYPI related documentation.
