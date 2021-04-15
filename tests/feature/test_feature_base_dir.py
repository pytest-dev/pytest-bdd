"""Test feature base dir."""
import pytest

NOT_EXISTING_FEATURE_PATHS = [".", "/does/not/exist/"]


@pytest.mark.parametrize("base_dir", NOT_EXISTING_FEATURE_PATHS)
def test_feature_path_not_found(testdir, base_dir):
    """Test feature base dir."""
    prepare_testdir(testdir, base_dir)

    result = testdir.runpytest("-k", "test_not_found_by_ini")
    result.assert_outcomes(passed=2)


def test_feature_path_ok(testdir):
    base_dir = "features"
    prepare_testdir(testdir, base_dir)

    result = testdir.runpytest("-k", "test_ok_by_ini")
    result.assert_outcomes(passed=2)


def test_feature_path_by_param_not_found(testdir):
    """As param takes precendence even if ini config is correct it should fail
    if passed param is incorrect"""
    base_dir = "features"
    prepare_testdir(testdir, base_dir)

    result = testdir.runpytest("-k", "test_not_found_by_param")
    result.assert_outcomes(passed=4)


@pytest.mark.parametrize("base_dir", NOT_EXISTING_FEATURE_PATHS)
def test_feature_path_by_param_ok(testdir, base_dir):
    """If ini config is incorrect but param path is fine it should be able
    to find features"""
    prepare_testdir(testdir, base_dir)

    result = testdir.runpytest("-k", "test_ok_by_param")
    result.assert_outcomes(passed=2)


def prepare_testdir(testdir, ini_base_dir):
    testdir.makeini(
        """
            [pytest]
            bdd_features_base_dir={}
        """.format(
            ini_base_dir
        )
    )

    feature_file = testdir.mkdir("features").join("steps.feature")
    feature_file.write(
        """
        Feature: Feature path
            Scenario: When scenario found
                Given found
    """
    )

    testdir.makepyfile(
        """
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
        assert os.path.abspath(os.path.join('{}', FEATURE)) in str(exc.value)


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

    """.format(
            ini_base_dir
        )
    )
