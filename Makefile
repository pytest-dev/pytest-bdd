# create virtual environment
PATH := .env/bin:$(PATH)

.env:
	virtualenv .env

# install all needed for development
develop: .env
	pip install -e . -r requirements-testing.txt tox python-coveralls

translate:
	msgfmt pytest_bdd/locales/en/LC_MESSAGES/step-prefixes.po \
		-o pytest_bdd/locales/en/LC_MESSAGES/step-prefixes.mo
	msgfmt pytest_bdd/locales/pt_BR/LC_MESSAGES/step-prefixes.po \
		-o pytest_bdd/locales/pt_BR/LC_MESSAGES/step-prefixes.mo

coverage: develop translate
	coverage run --source=pytest_bdd .env/bin/py.test tests
	coverage report -m

test: develop
	tox

coveralls: coverage
	coveralls

# clean the development envrironment
clean:
	-rm -rf .env
