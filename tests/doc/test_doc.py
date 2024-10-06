from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from pytest_bdd.script.bdd_tree_to_rst import convert

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Testdir


def test_doc_generation(testdir: "Testdir"):
    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    (features_path / "simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do nothing
        """
    )
    (features_path / "extra").mkdir()
    (features_path / "extra" / "other_simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do other nothing
        """
    )

    output_path = Path(testdir.tmpdir) / "output"
    output_path.mkdir()

    output = convert(features_path.resolve(), output_path.resolve())
    assert output == dedent(
        # language=rst
        """\
            Features
            ========

            .. NOTE:: Features below are part of end-to-end test suite; You always could find most specific
                      use cases of **pytest-bdd-ng** by investigation of its regression
                      test suite https://github.com/elchupanebrej/pytest-bdd-ng/tree/default/tests



            simple
            ------

            .. include:: features/simple.gherkin
               :code: gherkin

            extra
            -----

            other_simple
            ############

            .. include:: features/extra/other_simple.gherkin
               :code: gherkin
        """
    )
