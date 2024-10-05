from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from pytest import mark
from pytest_httpserver import HTTPServer

from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.webloc import write as webloc_write

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Testdir

MINIMAL_FEATURE = dedent(
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
)

MINIMAL_CONFTEST = dedent(
    # language=python
    f"""\
    from pytest_bdd import given

    @given("I have {{cuckes_count}} cukes in my belly")
    def results(cuckes_count):
        assert cuckes_count == '42'
    """
)


def test_feature_load_by_http(testdir: "Testdir", httpserver: HTTPServer):
    httpserver.expect_request("/feature").respond_with_data(
        MINIMAL_FEATURE,
        content_type=Mimetype.gherkin_plain.value,
    )
    testdir.makepyfile(
        # language=python
        test_http=f"""\
            from pytest_bdd import given, scenarios, FeaturePathType
            from pytest_bdd.mimetypes import Mimetype

            @given("I have {{cuckes_count}} cukes in my belly")
            def results(cuckes_count):
                assert cuckes_count == '42'

            test_cuckes = scenarios(
                f"http://localhost:{httpserver.port}/feature",
                features_mimetype=Mimetype.gherkin_plain,
                features_path_type=FeaturePathType.URL
            )
        """
    )
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)


def test_feature_load_by_http_from_url_file(testdir, httpserver: HTTPServer):
    httpserver.expect_request("/feature").respond_with_data(
        MINIMAL_FEATURE,
        content_type=Mimetype.gherkin_plain.value,
    )
    testdir.makefile(
        # language=ini
        test_http=f"""\
                [InternetShortcut]
                URL=http://localhost:{httpserver.port}/feature
            """,
        ext=".url",
    )

    testdir.makeconftest(MINIMAL_CONFTEST)
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)


def test_feature_load_by_http_from_desktop_file(testdir, httpserver: HTTPServer):
    httpserver.expect_request("/feature").respond_with_data(
        MINIMAL_FEATURE,
        content_type=Mimetype.gherkin_plain.value,
    )
    testdir.makefile(
        # language=ini
        test_http=f"""\
            [Desktop Entry]
            Type=Link
            URL=http://localhost:{httpserver.port}/feature
        """,
        ext=".desktop",
    )
    testdir.makeconftest(MINIMAL_CONFTEST)
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)


def test_feature_load_by_http_from_webloc_file(testdir: "Testdir", httpserver: HTTPServer):
    httpserver.expect_request("/feature").respond_with_data(
        MINIMAL_FEATURE,
        content_type=Mimetype.gherkin_plain.value,
    )
    webloc_write(Path(testdir.tmpdir) / "test_http.webloc", f"http://localhost:{httpserver.port}/feature")
    testdir.makeconftest(
        # language=python
        f"""\
        from pytest_bdd import given

        @given("I have {{cuckes_count}} cukes in my belly")
        def results(cuckes_count):
            assert cuckes_count == '42'

        """
    )
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)


@mark.skipif(not STRUCT_BDD_INSTALLED, reason="StructBDD is not installed")
def test_struct_bdd_feature_load_by_http(testdir, httpserver: HTTPServer):
    httpserver.expect_request("/feature").respond_with_data(
        dedent(
            # language=yaml
            """
            Name: minimal
            Description: |
              Cucumber doesn't execute this markdown, but @cucumber/react renders it

              * This is
              * a bullet
              * list
            Steps:
                - Step:
                    Name: Passing cukes
                    Steps:
                        - Given: I have 42 cukes in my belly
            """
        ),
        content_type=Mimetype.struct_bdd_yaml.value,
    )
    testdir.makepyfile(
        # language=python
        test_http=f"""\
            from pytest_bdd import given, scenarios, FeaturePathType

            @given("I have {{cuckes_count}} cukes in my belly")
            def results(cuckes_count):
                assert cuckes_count == '42'

            test_cuckes = scenarios(
                f"http://localhost:{httpserver.port}/feature",
                features_path_type=FeaturePathType.URL
            )
        """
    )
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)


def test_feature_load_by_http_with_base_url(testdir, httpserver: HTTPServer):
    httpserver.expect_request("/feature").respond_with_data(
        MINIMAL_FEATURE,
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
                f"/feature",
                features_mimetype=Mimetype.gherkin_plain,
                features_base_url="http://localhost:{httpserver.port}",
            )
        """
    )
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)


def test_feature_load_by_http_with_base_url_from_ini(testdir, httpserver: HTTPServer):
    httpserver.expect_request("/feature").respond_with_data(
        MINIMAL_FEATURE,
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
            from pytest_bdd import given, scenarios, FeaturePathType

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
