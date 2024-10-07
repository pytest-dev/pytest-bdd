import textwrap
from typing import List

from src.pytest_bdd.utils import collect_dumped_objects


def test_steps_with_datatables(pytester):
    pytester.makefile(
        ".feature",
        datatable=textwrap.dedent(
            """\
            Feature: Manage user accounts

              Scenario: Creating a new user with roles and permissions
                Given the following user details:
                  | name  | email             | age |
                  | John  | john@example.com  | 30  |
                  | Alice | alice@example.com | 25  |

                When the user is assigned the following roles:
                  | role        | description               |
                  | Admin       | Full access to the system |
                  | Contributor | Can add content           |

                And this step has no datatable

                Then the user should have the following permissions:
                  | permission     | allowed |
                  | view dashboard | true    |
                  | edit content   | true    |
                  | delete content | false   |
            """
        ),
    )
    pytester.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then
        from pytest_bdd.utils import dump_obj


        @given("the following user details:")
        def _(datatable):
            given_datatable = datatable
            dump_obj(given_datatable)


        @when("the user is assigned the following roles:")
        def _(datatable):
            when_datatable = datatable
            dump_obj(when_datatable)


        @when("this step has no datatable")
        def _():
            pass


        @then("the user should have the following permissions:")
        def _(datatable):
            then_datatable = datatable
            dump_obj(then_datatable)

    """
        )
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("datatable.feature", "Creating a new user with roles and permissions")
        def test_datatable():
            pass
        """
        )
    )

    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)

    datatables: List[DataTable] = collect_dumped_objects(result)
    assert datatables[0] == [
        ["name", "email", "age"],
        ["John", "john@example.com", "30"],
        ["Alice", "alice@example.com", "25"],
    ]
    assert datatables[1] == [
        ["role", "description"],
        ["Admin", "Full access to the system"],
        ["Contributor", "Can add content"],
    ]
    assert datatables[2] == [
        ["permission", "allowed"],
        ["view dashboard", "true"],
        ["edit content", "true"],
        ["delete content", "false"],
    ]


def test_steps_with_missing_datatables(pytester):
    pytester.makefile(
        ".feature",
        missing_datatable=textwrap.dedent(
            """\
            Feature: Missing data table

              Scenario: Data table is missing for a step
                Given this step has a data table:
                  | name  | email             | age |
                  | John  | john@example.com  | 30  |
                  | Alice | alice@example.com | 25  |

                When this step has no data table but tries to use the datatable fixture
                Then an error is thrown
            """
        ),
    )
    pytester.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then


        @given("this step has a data table:")
        def _(datatable):
            print(datatable)


        @when("this step has no data table but tries to use the datatable fixture")
        def _(datatable):
            print(datatable)


        @then("an error is thrown")
        def _(datatable):
            pass

    """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("missing_datatable.feature", "Data table is missing for a step")
        def test_datatable():
            pass
        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*fixture 'datatable' not found*"])
