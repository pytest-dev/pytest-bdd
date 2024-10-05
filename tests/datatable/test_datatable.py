import textwrap
from typing import List

from src.pytest_bdd.gherkin_parser import DataTable
from src.pytest_bdd.utils import collect_dumped_objects

DATA_TABLE_FEATURE = """\
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

                Then the user should have the following permissions:
                  | permission     | allowed |
                  | view dashboard | true    |
                  | edit content   | true    |
                  | delete content | false   |
            """


DATA_TABLE_STEPS = """\
        from pytest_bdd import given, when, then
        from pytest_bdd.utils import dump_obj


        @given("the following user details:")
        def _(data_table):
            given_data_table = data_table
            dump_obj(given_data_table)


        @when("the user is assigned the following roles:")
        def _(data_table):
            when_data_table = data_table
            dump_obj(when_data_table)


        @then("the user should have the following permissions:")
        def _(data_table):
            then_data_table = data_table
            dump_obj(then_data_table)

    """


DATA_TABLE_TEST_FILE = """\
        from pytest_bdd import scenario

        @scenario("data_table.feature", "Creating a new user with roles and permissions")
        def test_data_table():
            pass
        """


def test_steps_with_data_tables(pytester):
    pytester.makefile(".feature", data_table=textwrap.dedent(DATA_TABLE_FEATURE))
    pytester.makeconftest(textwrap.dedent(DATA_TABLE_STEPS))
    pytester.makepyfile(textwrap.dedent(DATA_TABLE_TEST_FILE))

    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)

    def get_row_values(data_table: DataTable) -> List[List[str]]:
        return [[cell.value for cell in row.cells] for row in data_table.rows]

    data_tables: List[DataTable] = collect_dumped_objects(result)
    assert get_row_values(data_tables[0]) == [
        ["name", "email", "age"],
        ["John", "john@example.com", "30"],
        ["Alice", "alice@example.com", "25"],
    ]
    assert get_row_values(data_tables[1]) == [
        ["role", "description"],
        ["Admin", "Full access to the system"],
        ["Contributor", "Can add content"],
    ]
    assert get_row_values(data_tables[2]) == [
        ["permission", "allowed"],
        ["view dashboard", "true"],
        ["edit content", "true"],
        ["delete content", "false"],
    ]


def test_steps_with_data_tables_as_dict(pytester):
    pytester.makefile(".feature", data_table=textwrap.dedent(DATA_TABLE_FEATURE))
    pytester.makeconftest(textwrap.dedent(DATA_TABLE_STEPS))
    pytester.makepyfile(textwrap.dedent(DATA_TABLE_TEST_FILE))

    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)

    data_tables: List[DataTable] = collect_dumped_objects(result)
    assert data_tables[0].to_dict() == {
        "age": ["30", "25"],
        "email": ["john@example.com", "alice@example.com"],
        "name": ["John", "Alice"],
    }
    assert data_tables[1].to_dict() == {
        "description": ["Full access to the system", "Can add content"],
        "role": ["Admin", "Contributor"],
    }
    assert data_tables[2].to_dict() == {
        "allowed": ["true", "true", "false"],
        "permission": ["view dashboard", "edit content", "delete content"],
    }


def test_steps_with_data_tables_transposed(pytester):
    pytester.makefile(".feature", data_table=textwrap.dedent(DATA_TABLE_FEATURE))
    pytester.makeconftest(textwrap.dedent(DATA_TABLE_STEPS))
    pytester.makepyfile(textwrap.dedent(DATA_TABLE_TEST_FILE))

    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)

    def get_row_values(data_table: DataTable) -> List[List[str]]:
        return [[cell.value for cell in row.cells] for row in data_table.rows]

    data_tables: List[DataTable] = collect_dumped_objects(result)
    assert get_row_values(data_tables[0].transpose()) == [
        ["name", "John", "Alice"],
        ["email", "john@example.com", "alice@example.com"],
        ["age", "30", "25"],
    ]

    assert get_row_values(data_tables[1].transpose()) == [
        ["role", "Admin", "Contributor"],
        ["description", "Full access to the system", "Can add content"],
    ]

    assert get_row_values(data_tables[2].transpose()) == [
        ["permission", "view dashboard", "edit content", "delete content"],
        ["allowed", "true", "true", "false"],
    ]


def test_steps_with_missing_data_tables(pytester):
    pytester.makefile(
        ".feature",
        missing_data_table=textwrap.dedent(
            """\
            Feature: Missing data table

              Scenario: Data table is missing for a step
                Given this step has a data table:
                  | name  | email             | age |
                  | John  | john@example.com  | 30  |
                  | Alice | alice@example.com | 25  |

                When this step has no data table but tries to use the data_table fixture
                Then an error is thrown
            """
        ),
    )
    pytester.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then
        from pytest_bdd.utils import dump_obj


        @given("this step has a data table:")
        def _(data_table):
            given_data_table = data_table
            dump_obj(given_data_table)


        @when("this step has no data table but tries to use the data_table fixture")
        def _(data_table):
            when_data_table = data_table
            dump_obj(when_data_table)


        @then("an error is thrown")
        def _(data_table):
            pass

    """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("missing_data_table.feature", "Data table is missing for a step")
        def test_data_table():
            pass
        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*fixture 'data_table' not found*"])


def test_steps_with_data_tables_too_short_for_to_dict(pytester):
    pytester.makefile(
        ".feature",
        too_short_data_table=textwrap.dedent(
            """\
            Feature: Short data table

              Scenario: Data table too short for transforming to dict
                Given this step has a data table:
                  | name  | email             | age |

            """
        ),
    )
    pytester.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then


        @given("this step has a data table:")
        def _(data_table):
            data_table.to_dict()

    """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("too_short_data_table.feature", "Data table too short for transforming to dict")
        def test_data_table():
            pass
        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*ValueError: DataTable needs at least two rows: one for headers and one for values*"])
