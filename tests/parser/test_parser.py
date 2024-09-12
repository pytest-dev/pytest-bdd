from pathlib import Path

from src.pytest_bdd.gherkin_parser import get_gherkin_document


def test_parser():
    # Get the directory of the current file
    test_dir = Path(__file__).parent

    # Resolve the path to the feature file relative to the test directory
    feature_file = test_dir / "test.feature"

    # Convert to string if necessary, but Path objects are often used directly
    feature_file_path = str(feature_file.resolve())

    get_gherkin_document(feature_file_path)
