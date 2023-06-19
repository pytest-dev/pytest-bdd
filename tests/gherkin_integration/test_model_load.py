import json
from pathlib import Path

from pytest import mark, param

from pytest_bdd.model.messages import Message

test_data = Path(__file__).parent.parent.parent / "testdata"


@mark.parametrize(
    "ast_path",
    map(
        lambda file: param(file, id=file.name),  # type: ignore[no-any-return]
        (test_data / "good").glob("*.ast.ndjson"),
    ),
)
def test_simple_load_model(ast_path: Path):
    with ast_path.open(mode="r") as ast_file:
        for ast_line in ast_file:
            model_datum = json.loads(ast_line)
            model = Message.parse_obj(model_datum)
            assert isinstance(model, Message)

            dumped_ast_datum = json.loads(model.json(by_alias=True, exclude_none=True))

            assert model_datum == dumped_ast_datum
