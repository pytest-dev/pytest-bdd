import os


def get_test_filepath(filepath):
    curr_file_dirpath = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(curr_file_dirpath, filepath)


def prepare_feature_and_py_files(testdir, feature_file, py_file):
    feature_filepath = get_test_filepath(feature_file)
    with open(feature_filepath) as feature_file:
        feature_content = feature_file.read()
    testdir.makefile('.feature', unicode=feature_content)

    py_filepath = get_test_filepath(py_file)
    with open(py_filepath) as py_file:
        py_content = py_file.read()
    testdir.makepyfile(test_gherkin=py_content)
