# TODO: Try to remove this file


.PHONY: live-reload
live-reload:
	@echo "Listening to changes to pytest_bdd/gherkin.tatsu..."
	@which entr > /dev/null || (echo "Installing entr..."; brew install entr)
	echo "src/pytest_bdd/gherkin.tatsu" | entr -s "tatsu src/pytest_bdd/gherkin.tatsu --generate-parser > src/pytest_bdd/_gherkin.py "

src/pytest_bdd/_gherkin.py:
	tatsu pytest_bdd/gherkin.tatsu --generate-parser > pytest_bdd/_gherkin.py
