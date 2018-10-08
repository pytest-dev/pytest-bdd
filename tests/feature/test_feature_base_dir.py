"""Test feature base dir."""
import pytest


@pytest.mark.parametrize(
    'base_dir', [
        '.',
        '/does/not/exist/',
    ]
)
def test_feature_path_not_found(testdir, base_dir):
    """Test feature base dir."""
    prepare_testdir(testdir, base_dir)

    result = testdir.runpytest('-k', 'test_not_found')
    result.assert_outcomes(passed=1)


def test_feature_path_ok(testdir):
    base_dir = 'features'
    prepare_testdir(testdir, base_dir)

    result = testdir.runpytest('-k', 'test_ok')
    result.assert_outcomes(passed=1)


def prepare_testdir(testdir, base_dir):
    testdir.makeini("""
            [pytest]
            bdd_feature_base_dir={}
        """.format(base_dir))

    feature_file = testdir.mkdir('features').join('steps.feature')
    feature_file.write("""
    Scenario: When scenario found
        Given found
    """)

    testdir.makepyfile("""
    import pytest
    from pytest_bdd import scenario
    import os.path

    @pytest.fixture(params=[
        'When scenario found',
    ])
    def scenario_name(request):
        return request.param

    def test_not_found(scenario_name):
        base_dir = '{}'
        print("BS: %s" % base_dir)
        with pytest.raises(IOError) as exc:
            scenario('steps.feature', scenario_name)
        assert os.path.abspath(os.path.join(base_dir, 'steps.feature')) in str(exc.value)

    def test_ok(scenario_name):
        # Shouldn't raise any exception
        scenario('steps.feature', scenario_name)
    """.format(base_dir))
