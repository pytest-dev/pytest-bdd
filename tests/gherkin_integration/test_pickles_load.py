import json
from pathlib import Path

from messages import Pickle  # type:ignore[attr-defined]
from pytest import mark, param

test_data = Path(__file__).parent.parent.parent / "gherkin" / "testdata"


@mark.parametrize(
    "pickle_path",
    map(
        lambda file: param(file, id=file.name),  # type: ignore[no-any-return]
        (test_data / "good").glob("*.pickles.ndjson"),
    ),
)
def test_simple_load_pickle(pickle_path: Path):
    with pickle_path.open(mode="r") as pickle_file:
        for pickle_line in pickle_file:
            pickle_data = json.loads(pickle_line)["pickle"]
            pickle = Pickle.model_validate(pickle_data)  # type: ignore[attr-defined] # migration to pydantic2
            assert isinstance(pickle, Pickle)

            dumped_pickle_data = json.loads(pickle.model_dump_json(by_alias=True, exclude_none=True))  # type: ignore[attr-defined] # migration to pydantic2

            assert pickle_data == dumped_pickle_data
