"""Converts directory tree containing Gherkin files into a tree which would be included into rst files

Usage:
    bdd_tree_to_rst.py <features_dir> <output_dir>

"""

import sys
from collections import deque
from filecmp import dircmp
from functools import reduce
from itertools import chain
from operator import methodcaller, truediv
from os.path import commonpath
from pathlib import Path
from shutil import copytree, rmtree
from tempfile import TemporaryDirectory
from textwrap import dedent

import pycmarkgfm
from docopt import docopt

SECTION_SYMBOLS = "-#!\"$%&'()*+,./:;<=>?@[\\]^_`{|}~="


def same_folders(dcmp):
    if any([dcmp.diff_files, dcmp.left_only, dcmp.right_only]):
        return False
    return all(map(same_folders, dcmp.subdirs.values()))


def convert(features_path: Path, output_path: Path, temp_path: Path):
    base_output_common_path = Path(commonpath([str(features_path), str(output_path)]))
    features_path_rel_to_common_path = features_path.relative_to(base_output_common_path)
    output_path_rel_to_common_path = output_path.parent.relative_to(base_output_common_path)
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

        gherkin_file_paths = chain(processable_path.glob("*.gherkin.md"), processable_path.glob("*.feature.md"))
        struct_bdd_file_paths = processable_path.glob("*.bdd.yaml")

        sub_processable_paths = list(filter(methodcaller("is_dir"), processable_path.iterdir()))

        for path in gherkin_file_paths:
            rel_path = path.relative_to(features_path)

            (temp_path / rel_path).parent.mkdir(exist_ok=True, parents=True)
            (temp_path / rel_path).with_suffix(".html").write_text(
                pycmarkgfm.gfm_to_html((features_path / rel_path).read_text())
            )

            content += dedent(
                # language=rst
                f"""\
                    {rel_path.stem}
                    {SECTION_SYMBOLS[len(rel_path.parts)-1]*len(rel_path.stem)}

                    .. raw:: html
                       :file: {(output_path_rel_to_features_path / path.relative_to(features_path)).with_suffix('.html').as_posix()}

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

    with TemporaryDirectory() as temp_dirname:
        temp_dir = Path(temp_dirname)
        convert(features_dir, output_dir, temp_dir)

        if not same_folders(dircmp(str(output_dir), temp_dir)):
            rmtree(output_dir, ignore_errors=True)
            output_dir.mkdir(parents=True)
            copytree(temp_dirname, str(output_dir), dirs_exist_ok=True)
            sys.exit("Documentation is generated and overwritten")


if __name__ == "__main__":  # pragma: no cover
    main()
