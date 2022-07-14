import json
from pathlib import Path

from marshmallow.utils import RAISE
from pytest import mark, param

from pytest_bdd.ast import AST, ASTSchema

resources = Path(__file__).parent / "resources"
test_data = resources / "testdata"


@mark.parametrize(
    "ast_path",
    map(
        lambda file: param(file, id=file.name),  # type: ignore[no-any-return]
        (test_data / "good").glob("*.ast.ndjson"),
    ),
)
def test_simple_load_ast(ast_path: Path):
    with ast_path.open(mode="r") as ast_file:
        for ast_line in ast_file:
            ast_datum = json.loads(ast_line)
            ast = ASTSchema().load(data=ast_datum, unknown=RAISE)
            assert isinstance(ast, AST)

            dumped_ast_datum = ASTSchema().dump(ast)

            assert ast_datum == dumped_ast_datum
