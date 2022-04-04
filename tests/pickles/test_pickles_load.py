import json
from pathlib import Path

from _pytest.mark import param
from pytest import mark

from pytest_bdd.pickle import Pickle

resources = Path(__file__).parent / "resources"
test_data = resources / "testdata"


@mark.parametrize(
    "pickle_path",
    map(lambda file: param(file, id=file.name), (test_data / "good").glob("*.pickles.ndjson")),  # type: ignore[no-any-return]
)
def test_simple_load_pickle(pickle_path):
    with pickle_path.open(mode="r") as pickle_file:
        for pickle_line in pickle_file:
            pickle_data = json.loads(pickle_line)["pickle"]
            pickle = Pickle().load(data=pickle_data, unknown="RAISE")
            dumped_pickle_data = Pickle().dump(pickle)

            assert pickle_data == dumped_pickle_data
