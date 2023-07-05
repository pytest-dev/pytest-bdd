def test_hook_execution_on_feature_tag(testdir):
    testdir.makefile(
        ".ini",
        # language=ini
        pytest="""\
                [pytest]
                markers =
                    tag
                """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        same_name="""\
            @tag
            Feature: Feature with tag
                Scenario: Scenario with tag
                    When Do something
            """,
    )
    testdir.makeconftest(
        # language=python
        f"""\
        from pytest import fixture
        from pytest_bdd import when
        from pytest_bdd.hook import before,after,around
        from pytest_bdd.compatibility.pytest import FixtureRequest
        from pytest_bdd.utils import inject_fixture


        @fixture(scope='session')
        def session_fixture():
            return 'session_fixture'

        @before('tag')
        def inject_custom_fixture(request: FixtureRequest, session_fixture):
            inject_fixture(request, 'tag_fixture', True)
            assert session_fixture == 'session_fixture'

        @before('tag')
        def inject_another_custom_fixture(request: FixtureRequest):
            inject_fixture(request, 'another_tag_fixture', True)

        @after('tag')
        def check_step_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @around('tag')
        def check_around_test_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert not hasattr(request.config, 'test_attr')
            yield
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @when("Do something")
        def do_something(
            tag_fixture,
            another_tag_fixture,
            request,
        ):
            assert tag_fixture
            assert another_tag_fixture
            inject_fixture(request, 'step_fixture', 'step_fixture')
            request.config.test_attr = 'test_attr'
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
