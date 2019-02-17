Changelog
=========

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

- Parse comments only in the begining of words (santagada)

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
