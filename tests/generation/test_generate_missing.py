"""Code generation and assertion tests."""
import itertools
import os.path
import textwrap

from pytest_bdd.scenario import get_python_name_generator


def test_python_name_generator():
    """Test python name generator function."""
    itertools.islice(get_python_name_generator('Some name'), 2) == ['some_name', 'some_name_2']


def test_generate_missing(testdir):
    """Test generate missing command."""
    dirname = "test_generate_missing"
    tests = testdir.mkpydir(dirname)
    with open(os.path.join(os.path.dirname(__file__), "generation.feature")) as fd:
        tests.join('generation.feature').write(fd.read())

    tests.join("test_foo.py").write(textwrap.dedent("""
        import functools

        from pytest_bdd import scenario, given

        scenario = functools.partial(scenario, "generation.feature")

        @given("I have a bar")
        def i_have_a_bar():
            return "bar"

        @scenario("Scenario tests which are already bound to the tests stay as is")
        def test_foo():
            pass

        @scenario("Code is generated for scenario steps which are not yet defined(implemented)")
        def test_missing_steps():
            pass
    """))

    result = testdir.runpytest(dirname, "--generate-missing", "--feature", tests.join('generation.feature').strpath)

    result.stdout.fnmatch_lines([
        'Scenario "Code is generated for scenarios which are not bound to any tests" is not bound to any test *']
    )

    result.stdout.fnmatch_lines(
        [
            'Step Given "I have a custom bar" is not defined in the scenario '
            '"Code is generated for scenario steps which are not yet defined(implemented)" *',
        ]
    )

    result.stdout.fnmatch_lines(
        ['Step Given "I have a foobar" is not defined in the background of the feature "Missing code generation" *']
    )

    result.stdout.fnmatch_lines(["Please place the code above to the test file(s):"])
