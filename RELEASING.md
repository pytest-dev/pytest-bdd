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
