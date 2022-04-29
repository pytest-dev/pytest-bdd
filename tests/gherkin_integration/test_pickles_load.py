import json
from pathlib import Path

from pytest import mark, param

from pytest_bdd.model.scenario import Scenario, ScenarioSchema

resources = Path(__file__).parent / "resources"
test_data = resources / "testdata"


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
            pickle = ScenarioSchema().load(data=pickle_data, unknown="RAISE")
            assert isinstance(pickle, Scenario)

            dumped_pickle_data = ScenarioSchema().dump(pickle)

            assert pickle_data == dumped_pickle_data
