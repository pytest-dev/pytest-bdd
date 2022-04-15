# create virtual environment
PATH := .env/bin:$(PATH)

.env:
	virtualenv .env


.PHONY: dependencies
dependencies:
	.env/bin/pip install -e . -r requirements-testing.txt tox python-coveralls


.PHONY: develop
develop: | .env dependencies pytest_bdd/_gherkin.py


.PHONY: live-reload
live-reload:
	@echo "Listening to changes to pytest_bdd/gherkin.tatsu..."
	@which entr > /dev/null || (echo "Installing entr..."; brew install entr)
	echo "pytest_bdd/gherkin.tatsu" | entr -s "tatsu pytest_bdd/gherkin.tatsu --generate-parser > pytest_bdd/_gherkin.py "

pytest_bdd/_gherkin.py:
	tatsu pytest_bdd/gherkin.tatsu --generate-parser > pytest_bdd/_gherkin.py

.PHONY: coverage
coverage: develop
	coverage run --source=pytest_bdd .env/bin/pytest tests
	coverage report -m

.PHONY: test
test: develop
	tox

.PHONY: coveralls
coveralls: coverage
	coveralls


.PHONY: clean
clean:
	-rm -rf .env
