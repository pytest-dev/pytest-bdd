from pathlib import Path

from src.pytest_bdd.gherkin_parser import get_gherkin_document


def test_parser():
    test_dir = Path(__file__).parent
    feature_file = test_dir / "test.feature"
    feature_file_path = str(feature_file.resolve())

    get_gherkin_document(feature_file_path)
