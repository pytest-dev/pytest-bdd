Changelog
=========


0.6.11
-----

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
