# How to setup development environment
- Install poetry: https://python-poetry.org/docs/#installation
- (Optional) Install pre-commit: https://pre-commit.com/#install
- Run `poetry install` to install dependencies
- Run `pre-commit install` to install pre-commit hooks

# How to run tests
- Run `poetry run pytest`
- or run `tox`
# How to make a release

```shell
python -m pip install --upgrade build twine

# cleanup the ./dist folder
rm -rf ./dist

# Build the distributions
python -m build

# Upload them

twine upload dist/*
```
