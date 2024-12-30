"""Test feature base dir."""

from __future__ import annotations

import os

import pytest

NOT_EXISTING_FEATURE_PATHS = [".", "/does/not/exist/"]


@pytest.mark.parametrize("base_dir", NOT_EXISTING_FEATURE_PATHS)
def test_feature_path_not_found(pytester, base_dir):
    """Test feature base dir."""
    prepare_testdir(pytester, base_dir)

    result = pytester.runpytest("-k", "test_not_found_by_ini")
    result.assert_outcomes(passed=2)


def test_feature_path_ok(pytester):
    base_dir = "features"
    prepare_testdir(pytester, base_dir)

    result = pytester.runpytest("-k", "test_ok_by_ini")
    result.assert_outcomes(passed=2)


def test_feature_path_ok_running_outside_rootdir(pytester):
    base_dir = "features"
    prepare_testdir(pytester, base_dir)

    old_dir = os.getcwd()
    os.chdir("/")
    try:
        result = pytester.runpytest(pytester.path, "-k", "test_ok_by_ini")
        result.assert_outcomes(passed=2)
    finally:
        os.chdir(old_dir)


def test_feature_path_by_param_not_found(pytester):
    """As param takes precedence even if ini config is correct it should fail
    if passed param is incorrect"""
    base_dir = "features"
    prepare_testdir(pytester, base_dir)

    result = pytester.runpytest("-k", "test_not_found_by_param")
    result.assert_outcomes(passed=4)


@pytest.mark.parametrize("base_dir", NOT_EXISTING_FEATURE_PATHS)
def test_feature_path_by_param_ok(pytester, base_dir):
    """If ini config is incorrect but param path is fine it should be able
    to find features"""
    prepare_testdir(pytester, base_dir)

    result = pytester.runpytest("-k", "test_ok_by_param")
    result.assert_outcomes(passed=2)


def prepare_testdir(pytester, ini_base_dir):
    pytester.makeini(
        f"""
            [pytest]
            bdd_features_base_dir={ini_base_dir}
        """
    )

    feature_file = pytester.mkdir("features").joinpath("steps.feature")
    feature_file.write_text(
        """
        Feature: Feature path
            Scenario: When scenario found
                Given found
    """
    )

    pytester.makepyfile(
        f"""
    import os.path

    import pytest

    from pytest_bdd import scenario, scenarios

    FEATURE = 'steps.feature'


    @pytest.fixture(params=[
        'When scenario found',
    ])
    def scenario_name(request):
        return request.param


    @pytest.mark.parametrize(
        'multiple', [True, False]
    )
    def test_not_found_by_ini(scenario_name, multiple):
        with pytest.raises(IOError) as exc:
            if multiple:
                scenarios(FEATURE)
            else:
                scenario(FEATURE, scenario_name)
        assert os.path.abspath(os.path.join('{ini_base_dir}', FEATURE)) in str(exc.value)


    @pytest.mark.parametrize(
        'multiple', [True, False]
    )
    def test_ok_by_ini(scenario_name, multiple):
        # Shouldn't raise any exception
        if multiple:
            scenarios(FEATURE)
        else:
            scenario(FEATURE, scenario_name)


    @pytest.mark.parametrize(
        'multiple', [True, False]
    )
    @pytest.mark.parametrize(
        'param_base_dir', [
            '.',
            '/does/not/exist/',
        ]
    )
    def test_not_found_by_param(scenario_name, param_base_dir, multiple):
        with pytest.raises(IOError) as exc:
            if multiple:
                scenarios(FEATURE, features_base_dir=param_base_dir)
            else:
                scenario(FEATURE, scenario_name, features_base_dir=param_base_dir)
        assert os.path.abspath(os.path.join(param_base_dir, FEATURE)) in str(exc.value)


    @pytest.mark.parametrize(
        'multiple', [True, False]
    )
    def test_ok_by_param(scenario_name, multiple):
        # Shouldn't raise any exception no matter of bdd_features_base_dir in ini
        if multiple:
            scenarios(FEATURE, features_base_dir='features')
        else:
            scenario(FEATURE, scenario_name, features_base_dir='features')

    """
    )
