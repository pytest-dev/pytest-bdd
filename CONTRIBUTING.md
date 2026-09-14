# How to setup development environment
- Install uv: https://docs.astral.sh/uv/getting-started/installation/
- (Optional) Install pre-commit: https://pre-commit.com/#install
- Run `uv sync` to install dependencies
- Run `pre-commit install` to install pre-commit hooks

# How to run tests
- Run `uv run pytest`
- or run `tox` (or `uv run tox`)

# How to make a release

```shell
# cleanup the ./dist folder
rm -rf ./dist

# Build the distributions
uv build

# Upload them
uv run --group build twine upload dist/*
```
