Changelog
=========

Unreleased
----------

- For --generate-missing, --feature parameter now correctly does the recursion (bubenkoff)


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
