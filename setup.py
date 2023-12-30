from pathlib import Path

from setuptools import setup

root_path = Path(__file__).parent

setup(
    # This is needed until ci-environment&messages become regular PyPi packages
    install_requires=[
        f"ci-environment@file://{root_path}/ci-environment/python",
        f"messages@file://{root_path}/messages/python",
        "aiohttp",
        "attrs",
        "certifi",
        "cucumber-expressions",
        "decopatch",
        "docopt-ng",
        "filelock",
        "gherkin-official>=24",
        "importlib-metadata;python_version<'3.10.0'",
        "importlib-resources",
        "makefun",
        "Mako",
        "ordered_set",
        "packaging",
        "parse",
        "parse_type>=0.6.0",
        "py",
        "pydantic>=2.0.3",
        "pytest>=5.0",
        "setuptools>=58",
        "six>=1.16;python_version~='3.8'",
        "cucumber-tag-expressions",
        "typing-extensions;python_version<'3.11.0'",
    ],
)
