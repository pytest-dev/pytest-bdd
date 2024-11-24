import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import TYPE_CHECKING

from pytest import mark

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Testdir


@mark.skipif(sys.version_info < (3, 12), reason="Verify only on the latest version")
def test_doc_generation(testdir: "Testdir"):
    from pytest_bdd.script.bdd_tree_to_rst import convert

    features_path = Path(testdir.tmpdir) / "features"
    features_path.mkdir()
    (features_path / "simple.gherkin").write_text(
        # language=gherkin
        """
        Feature: Do nothing
        """
    )
    (features_path / "simple_markdown.gherkin.md").write_text(
        # language=gherkin
        """
        # Feature: Simple gherkin markdown
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

    with TemporaryDirectory() as temp_dirname:
        temp_path = Path(temp_dirname)
        convert(features_path.resolve(), output_path.resolve(), temp_path)

        assert (temp_path / "features.rst").read_text() == dedent(
            # language=rst
            """\
                Features
                ========

                .. NOTE:: Features below are part of end-to-end test suite; You always could find most specific
                          use cases of **pytest-bdd-ng** by investigation of its regression
                          test suite https://github.com/elchupanebrej/pytest-bdd-ng/tree/default/tests



                simple_markdown
                ---------------

                .. include:: features/simple_markdown.gherkin.rst

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
