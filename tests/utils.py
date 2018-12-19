import os


def get_test_filepath(filepath):
    curr_file_dirpath = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(curr_file_dirpath, filepath)


def get_filename_without_ext(path):
    filename = os.path.basename(path)
    return os.path.splitext(filename)[0]


def prepare_feature_and_py_files(testdir, feature_file, py_file):
    feature_filepath = get_test_filepath(feature_file)
    with open(feature_filepath) as feature_file:
        feature_content = feature_file.read()
    feature_filename = get_filename_without_ext(feature_file.name)
    kwargs = {feature_filename: feature_content}
    testdir.makefile('.feature', **kwargs)

    py_filepath = get_test_filepath(py_file)
    with open(py_filepath) as py_file:
        py_content = py_file.read()
    py_filename = get_filename_without_ext(py_file.name)
    kwargs = {py_filename: py_content}
    testdir.makepyfile(**kwargs)
