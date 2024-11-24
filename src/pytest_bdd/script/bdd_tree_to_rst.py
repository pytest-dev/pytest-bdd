"""Converts directory tree containing Gherkin files into a tree which would be included into rst files

Usage:
    bdd_tree_to_rst.py [--snapshot=<snapshot_path>] <features_dir> <output_dir>

Options:
    --snapshot=<snapshot_path> Path to save snapshot on found diff between old and new documentation
"""

import io
import sys
from collections import deque
from filecmp import dircmp
from functools import partial, reduce
from itertools import chain
from operator import methodcaller, truediv
from os.path import commonpath
from pathlib import Path
from shutil import copytree, rmtree
from tempfile import TemporaryDirectory
from textwrap import dedent

import panflute as pf  # type: ignore[import-not-found]
import pycmarkgfm  # type: ignore[import-not-found]
import pypandoc  # type: ignore[import-not-found]
from docopt import docopt

SECTION_SYMBOLS = "-#!\"$%&'()*+,./:;<=>?@[\\]^_`{|}~="


def diff_folders(dcmp):
    if any(diff := [dcmp.diff_files, dcmp.left_only, dcmp.right_only]):
        dcmp.report()
        return diff
    if any(diff := list(map(diff_folders, dcmp.subdirs.values()))):
        return diff
    pass


def adjust_heading_level(elem, doc, *, level):
    if isinstance(elem, pf.Header):
        new_level = elem.level + level
        return pf.Header(*elem.content, level=new_level)
    return elem


def convert(features_path: Path, output_path: Path, temp_path: Path):
    base_output_common_path = Path(commonpath([str(features_path), str(output_path)]))
    features_path_rel_to_common_path = features_path.relative_to(base_output_common_path)
    output_path_rel_to_common_path = output_path.parent.relative_to(base_output_common_path)
    # TODO move side effect from this method
    index_file = temp_path / "features.rst"

    output_path_rel_to_features_path = (
        reduce(truediv, [".."] * len(output_path_rel_to_common_path.parts), Path()) / features_path_rel_to_common_path
    )
    processable_paths = deque([features_path])

    content = ""
    content += dedent(
        # language=rst
        """\
            Features
            ========

            .. NOTE:: Features below are part of end-to-end test suite; You always could find most specific
                      use cases of **pytest-bdd-ng** by investigation of its regression
                      test suite https://github.com/elchupanebrej/pytest-bdd-ng/tree/default/tests
        """
    )

    while processable_paths:
        processable_path = processable_paths.popleft()

        processable_rel_path = processable_path.relative_to(features_path)
        content += dedent(
            # language=rst
            f"""\
                {processable_rel_path.name}
                {SECTION_SYMBOLS[len(processable_rel_path.parts) - 1] * len(processable_rel_path.name)}

            """
        )

        gherkin_file_paths = chain(processable_path.glob("*.gherkin"), processable_path.glob("*.feature"))
        markdown_gherkin_file_paths = chain(
            processable_path.glob("*.gherkin.md"), processable_path.glob("*.feature.md")
        )
        struct_bdd_file_paths = processable_path.glob("*.bdd.yaml")

        sub_processable_paths = list(filter(methodcaller("is_dir"), processable_path.iterdir()))

        for path in markdown_gherkin_file_paths:
            rel_path = path.relative_to(features_path)
            offset = len(rel_path.parts)

            abs_path = temp_path / rel_path
            abs_path.parent.mkdir(exist_ok=True, parents=True)

            html_data = pycmarkgfm.gfm_to_html((features_path / rel_path).read_text())

            html_content = pypandoc.convert_text(html_data, "json", format="html")
            doc = pf.load(io.StringIO(html_content))

            with io.StringIO() as f:
                pf.dump(pf.run_filter(partial(adjust_heading_level, level=offset + 1), doc=doc), f)

                contents = f.getvalue()
            output_rst = pypandoc.convert_text(contents, "rst", format="json")
            abs_path.with_suffix(".rst").write_text(output_rst, encoding="utf-8")

            stemmed_path = Path(rel_path.stem).stem

            content += dedent(
                # language=rst
                f"""\
                    {stemmed_path}
                    {SECTION_SYMBOLS[offset-1]*len(stemmed_path)}

                    .. include:: {(Path('features')/ path.relative_to(features_path)).with_suffix('.rst').as_posix()}

                """
            )

        for path in gherkin_file_paths:
            rel_path = path.relative_to(features_path)
            content += dedent(
                # language=rst
                f"""\
                    {rel_path.stem}
                    {SECTION_SYMBOLS[len(rel_path.parts) - 1] * len(rel_path.stem)}

                    .. include:: {(output_path_rel_to_features_path / path.relative_to(features_path)).as_posix()}
                       :code: gherkin

                """
            )

        for path in struct_bdd_file_paths:
            rel_path = path.relative_to(features_path)
            content += dedent(
                # language=rst
                f"""\
                    {rel_path.stem}
                    {SECTION_SYMBOLS[len(rel_path.parts)-1]*len(rel_path.stem)}

                    .. include:: {(output_path_rel_to_features_path / path.relative_to(features_path)).as_posix()}
                       :code: yaml

                """
            )

        processable_paths.extendleft(sub_processable_paths)

    index_file.write_text(content.rstrip("\n") + "\n")


def main():  # pragma: no cover
    arguments = docopt(__doc__)
    features_dir = Path(arguments["<features_dir>"]).resolve()
    if not features_dir.exists() or not features_dir.is_dir():
        raise ValueError(f"Wrong input features directory {features_dir} is provided")
    output_dir = Path(arguments["<output_dir>"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir = Path(p) if (p := arguments.get("--snapshot")) else None

    with TemporaryDirectory() as temp_dirname:
        temp_dir = Path(temp_dirname)
        convert(features_dir, output_dir, temp_dir)

        if diff := diff_folders(dircmp(str(output_dir), temp_dir)):
            if snapshot_dir is not None:
                rmtree(snapshot_dir, ignore_errors=True)
                copytree(output_dir, str(snapshot_dir), dirs_exist_ok=True)

            rmtree(output_dir, ignore_errors=True)
            copytree(temp_dirname, str(output_dir), dirs_exist_ok=True)

            sys.exit(f"Documentation is generated and overwritten; Diff:{diff}")


if __name__ == "__main__":  # pragma: no cover
    main()
