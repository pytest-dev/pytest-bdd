# create virtual environment
PATH := .env/bin:$(PATH)

.env:
	virtualenv .env

# install all needed for development
develop: .env
	.env/bin/pip install -e . -r requirements-testing.txt tox python-coveralls

develop-grammar:
	echo "Listening to changes to pytest_bdd/gherkin.tatsu..."
	echo "pytest_bdd/gherkin.tatsu" | entr -s "tatsu pytest_bdd/gherkin.tatsu --generate-parser > pytest_bdd/_gherkin.py "

coverage: develop
	coverage run --source=pytest_bdd .env/bin/pytest tests
	coverage report -m

test: develop
	tox

coveralls: coverage
	coveralls

# clean the development environment
clean:
	-rm -rf .env
