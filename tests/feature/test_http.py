from textwrap import dedent

from pytest_httpserver import HTTPServer

from pytest_bdd.mimetypes import Mimetype


def test_feature_load_by_http(testdir, httpserver: HTTPServer):
    httpserver.expect_request("/feature").respond_with_data(
        dedent(
            # language=gherkin
            """
            Feature: minimal

              Cucumber doesn't execute this markdown, but @cucumber/react renders it

              * This is
              * a bullet
              * list

              Scenario: Passing cukes
                Given I have 42 cukes in my belly
            """
        ),
        content_type=Mimetype.gherkin_plain.value,
    )
    testdir.makepyfile(
        # language=python
        test_http=f"""\
            from pytest_bdd import given, scenarios
            from pytest_bdd.mimetypes import Mimetype

            @given("I have {{cuckes_count}} cukes in my belly")
            def results(cuckes_count):
                assert cuckes_count == '42'

            test_cuckes = scenarios(
                f"http://localhost:{httpserver.port}/feature",
                features_mimetype=Mimetype.gherkin_plain
            )
        """
    )
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)


def test_feature_load_by_http_with_base_url(testdir, httpserver: HTTPServer):
    httpserver.expect_request("/feature").respond_with_data(
        dedent(
            # language=gherkin
            """
            Feature: minimal

              Cucumber doesn't execute this markdown, but @cucumber/react renders it

              * This is
              * a bullet
              * list

              Scenario: Passing cukes
                Given I have 42 cukes in my belly
            """
        ),
        content_type=Mimetype.gherkin_plain.value,
    )
    testdir.makepyfile(
        # language=python
        test_http=f"""\
            from pytest_bdd import given, scenarios
            from pytest_bdd.mimetypes import Mimetype
            from pytest_bdd.scenario import FeaturePathType

            @given("I have {{cuckes_count}} cukes in my belly")
            def results(cuckes_count):
                assert cuckes_count == '42'

            test_cuckes = scenarios(
                f"/feature",
                features_mimetype=Mimetype.gherkin_plain,
                features_base_url="http://localhost:{httpserver.port}",
                features_path_type=FeaturePathType.URL
            )
        """
    )
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)


def test_feature_load_by_http_with_base_url_from_ini(testdir, httpserver: HTTPServer):
    httpserver.expect_request("/feature").respond_with_data(
        dedent(
            # language=gherkin
            """
            Feature: minimal

              Cucumber doesn't execute this markdown, but @cucumber/react renders it

              * This is
              * a bullet
              * list

              Scenario: Passing cukes
                Given I have 42 cukes in my belly
            """
        ),
        content_type=Mimetype.gherkin_plain.value,
    )

    testdir.makeini(
        f"""\
        [pytest]
        console_output_style=classic
        bdd_features_base_url=http://localhost:{httpserver.port}
        """
    )

    testdir.makepyfile(
        # language=python
        test_http=f"""\
            from pytest_bdd import given, scenarios
            from pytest_bdd.scenario import FeaturePathType

            @given("I have {{cuckes_count}} cukes in my belly")
            def results(cuckes_count):
                assert cuckes_count == '42'

            test_cuckes = scenarios(
                f"/feature",
                features_path_type=FeaturePathType.URL
            )
        """
    )
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)
