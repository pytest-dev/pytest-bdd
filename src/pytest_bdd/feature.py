"""Feature.

The way of describing the behavior is based on Gherkin language, but a very
limited version. It doesn't support any parameter tables.
If the parametrization is needed to generate more test cases it can be done
on the fixture level of the pytest.
The <variable> syntax can be used here to make a connection between steps and
it will also validate the parameters mentioned in the steps with ones
provided in the pytest parametrization table.

Syntax example:

    Feature: Articles
        Scenario: Publishing the article
            Given I'm an author user
            And I have an article
            When I go to the article page
            And I press the publish button
            Then I should not see the error message
            And the article should be published  # Note: will query the database

:note: The "#" symbol is used for comments.
:note: There are no multiline steps, the description of the step must fit in
one line.
"""

from __future__ import annotations

import glob
import os.path
from collections.abc import Iterable

from .parser import Feature, FeatureParser

# Global features dictionary
features: dict[str, Feature] = {}


def get_feature(base_path: str, filename: str, encoding: str = "utf-8") -> Feature:
    """Get a feature by the filename.

    :param str base_path: Base feature directory.
    :param str filename: Filename of the feature file.
    :param str encoding: Feature file encoding.

    :return: `Feature` instance from the parsed feature cache.

    :note: The features are parsed on the execution of the test and
           stored in the global variable cache to improve the performance
           when multiple scenarios are referencing the same file.
    """
    __tracebackhide__ = True
    full_name = os.path.abspath(os.path.join(base_path, filename))
    feature = features.get(full_name)
    if not feature:
        feature = FeatureParser(base_path, filename, encoding).parse()
        features[full_name] = feature
    return feature


def get_features(paths: Iterable[str], encoding: str = "utf-8") -> list[Feature]:
    """Get features for given paths.

    :param list paths: `list` of paths (file or dirs)

    :return: `list` of `Feature` objects.
    """
    seen_names = set()
    _features = []
    for path in paths:
        if path not in seen_names:
            seen_names.add(path)
            if os.path.isdir(path):
                file_paths = list(glob.iglob(os.path.join(path, "**", "*.feature"), recursive=True))
                _features.extend(get_features(file_paths, encoding=encoding))
            else:
                base, name = os.path.split(path)
                feature = get_feature(base, name, encoding=encoding)
                _features.append(feature)
    _features.sort(key=lambda _feature: _feature.name or _feature.filename)
    return _features
