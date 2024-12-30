# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from __future__ import annotations

from importlib import metadata as _metadata

project = "pytest-bdd"
copyright = "2013, Oleg Pidsadnyi"
author = "Oleg Pidsadnyi"
# The full version, including alpha/beta/rc tags.
release = _metadata.version("pytest-bdd")

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

html_sidebars = {
    "**": [
        "about.html",
        "searchfield.html",
        # 'navigation.html',
        "relations.html",
        # 'donate.html',
        "localtoc.html",
    ]
}
