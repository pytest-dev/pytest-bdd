from __future__ import annotations

from pathlib import Path

from src.pytest_bdd.gherkin_parser import (
    Background,
    Cell,
    Child,
    Comment,
    DataTable,
    DocString,
    ExamplesTable,
    Feature,
    GherkinDocument,
    Location,
    Row,
    Rule,
    Scenario,
    Step,
    Tag,
    get_gherkin_document,
)


def test_parser():
    test_dir = Path(__file__).parent
    feature_file = test_dir / "test.feature"
    feature_file_path = str(feature_file.resolve())

    # Call the function to parse the Gherkin document
    gherkin_doc = get_gherkin_document(feature_file_path)

    # Define the expected structure
    expected_document = GherkinDocument(
        feature=Feature(
            keyword="Feature",
            location=Location(column=1, line=2),
            tags=[],
            name="User login",
            description="  As a registered user\n  I want to be able to log in\n  So that I can access my account",
            language="en",
            children=[
                Child(
                    background=Background(
                        id="1",
                        keyword="Background",
                        location=Location(column=3, line=8),
                        name="",
                        description="",
                        steps=[
                            Step(
                                id="0",
                                keyword="Given",
                                keyword_type="Context",
                                location=Location(column=5, line=10),
                                text="the login page is open",
                                datatable=None,
                                docstring=None,
                            )
                        ],
                    ),
                    rule=None,
                    scenario=None,
                ),
                Child(
                    background=None,
                    rule=None,
                    scenario=Scenario(
                        id="6",
                        keyword="Scenario",
                        location=Location(column=3, line=13),
                        name="Successful login with valid credentials",
                        description="",
                        steps=[
                            Step(
                                id="2",
                                keyword="Given",
                                keyword_type="Context",
                                location=Location(column=5, line=14),
                                text="the user enters a valid username",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="3",
                                keyword="And",
                                keyword_type="Conjunction",
                                location=Location(column=5, line=15),
                                text="the user enters a valid password",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="4",
                                keyword="When",
                                keyword_type="Action",
                                location=Location(column=5, line=16),
                                text="the user clicks the login button",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="5",
                                keyword="Then",
                                keyword_type="Outcome",
                                location=Location(column=5, line=17),
                                text="the user should see the dashboard",
                                datatable=None,
                                docstring=None,
                            ),
                        ],
                        tags=[],
                        examples=[],
                    ),
                ),
                Child(
                    background=None,
                    rule=None,
                    scenario=Scenario(
                        id="15",
                        keyword="Scenario Outline",
                        location=Location(column=3, line=19),
                        name="Unsuccessful login with invalid credentials",
                        description="",
                        steps=[
                            Step(
                                id="7",
                                keyword="Given",
                                keyword_type="Context",
                                location=Location(column=5, line=20),
                                text='the user enters "<username>" as username',
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="8",
                                keyword="And",
                                keyword_type="Conjunction",
                                location=Location(column=5, line=21),
                                text='the user enters "<password>" as password',
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="9",
                                keyword="When",
                                keyword_type="Action",
                                location=Location(column=5, line=22),
                                text="the user clicks the login button",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="10",
                                keyword="Then",
                                keyword_type="Outcome",
                                location=Location(column=5, line=23),
                                text='the user should see an error message "<error_message>"',
                                datatable=None,
                                docstring=None,
                            ),
                        ],
                        tags=[],
                        examples=[
                            ExamplesTable(
                                location=Location(column=5, line=26),
                                name="",
                                tags=[],
                                table_header=Row(
                                    id="11",
                                    location=Location(column=7, line=27),
                                    cells=[
                                        Cell(
                                            location=Location(column=9, line=27),
                                            value="username",
                                        ),
                                        Cell(
                                            location=Location(column=23, line=27),
                                            value="password",
                                        ),
                                        Cell(
                                            location=Location(column=35, line=27),
                                            value="error_message",
                                        ),
                                    ],
                                ),
                                table_body=[
                                    Row(
                                        id="12",
                                        location=Location(column=7, line=28),
                                        cells=[
                                            Cell(
                                                location=Location(column=9, line=28),
                                                value="invalidUser",
                                            ),
                                            Cell(
                                                location=Location(column=23, line=28),
                                                value="wrongPass",
                                            ),
                                            Cell(
                                                location=Location(column=35, line=28),
                                                value="Invalid username or password",
                                            ),
                                        ],
                                    ),
                                    Row(
                                        id="13",
                                        location=Location(column=7, line=29),
                                        cells=[
                                            Cell(
                                                location=Location(column=9, line=29),
                                                value="user123",
                                            ),
                                            Cell(
                                                location=Location(column=23, line=29),
                                                value="incorrect",
                                            ),
                                            Cell(
                                                location=Location(column=35, line=29),
                                                value="Invalid username or password",
                                            ),
                                        ],
                                    ),
                                ],
                            )
                        ],
                    ),
                ),
                Child(
                    background=None,
                    rule=None,
                    scenario=Scenario(
                        id="20",
                        keyword="Scenario",
                        location=Location(column=3, line=31),
                        name="Login with empty username",
                        description="",
                        steps=[
                            Step(
                                id="16",
                                keyword="Given",
                                keyword_type="Context",
                                location=Location(column=5, line=32),
                                text="the user enters an empty username",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="17",
                                keyword="And",
                                keyword_type="Conjunction",
                                location=Location(column=5, line=33),
                                text="the user enters a valid password",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="18",
                                keyword="When",
                                keyword_type="Action",
                                location=Location(column=5, line=34),
                                text="the user clicks the login button",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="19",
                                keyword="Then",
                                keyword_type="Outcome",
                                location=Location(column=5, line=35),
                                text='the user should see an error message "Username cannot be empty"',
                                datatable=None,
                                docstring=None,
                            ),
                        ],
                        tags=[],
                        examples=[],
                    ),
                ),
                Child(
                    background=None,
                    rule=None,
                    scenario=Scenario(
                        id="25",
                        keyword="Scenario",
                        location=Location(column=3, line=37),
                        name="Login with empty password",
                        description="",
                        steps=[
                            Step(
                                id="21",
                                keyword="Given",
                                keyword_type="Context",
                                location=Location(column=5, line=38),
                                text="the user enters a valid username",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="22",
                                keyword="And",
                                keyword_type="Conjunction",
                                location=Location(column=5, line=39),
                                text="the user enters an empty password",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="23",
                                keyword="When",
                                keyword_type="Action",
                                location=Location(column=5, line=40),
                                text="the user clicks the login button",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="24",
                                keyword="Then",
                                keyword_type="Outcome",
                                location=Location(column=5, line=41),
                                text='the user should see an error message "Password cannot be empty"',
                                datatable=None,
                                docstring=None,
                            ),
                        ],
                        tags=[],
                        examples=[],
                    ),
                ),
                Child(
                    background=None,
                    rule=None,
                    scenario=Scenario(
                        id="30",
                        keyword="Scenario",
                        location=Location(column=3, line=43),
                        name="Login with SQL injection attempt",
                        description="",
                        steps=[
                            Step(
                                id="26",
                                keyword="Given",
                                keyword_type="Context",
                                location=Location(column=5, line=44),
                                text="the user enters \"admin' OR '1'='1\" as username",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="27",
                                keyword="And",
                                keyword_type="Conjunction",
                                location=Location(column=5, line=45),
                                text='the user enters "password" as password',
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="28",
                                keyword="When",
                                keyword_type="Action",
                                location=Location(column=5, line=46),
                                text="the user clicks the login button",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="29",
                                keyword="Then",
                                keyword_type="Outcome",
                                location=Location(column=5, line=47),
                                text='the user should see an error message "Invalid username or password"',
                                datatable=None,
                                docstring=None,
                            ),
                        ],
                        tags=[],
                        examples=[],
                    ),
                ),
                Child(
                    background=None,
                    rule=None,
                    scenario=Scenario(
                        id="35",
                        keyword="Scenario",
                        location=Location(column=3, line=50),
                        name="Login button disabled for empty fields",
                        description="",
                        steps=[
                            Step(
                                id="31",
                                keyword="Given",
                                keyword_type="Context",
                                location=Location(column=5, line=51),
                                text="the user has not entered any username or password",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="32",
                                keyword="Then",
                                keyword_type="Outcome",
                                location=Location(column=5, line=52),
                                text="the login button should be disabled",
                                datatable=None,
                                docstring=None,
                            ),
                        ],
                        tags=[
                            Tag(id="33", location=Location(column=3, line=49), name="@login"),
                            Tag(
                                id="34",
                                location=Location(column=10, line=49),
                                name="@critical",
                            ),
                        ],
                        examples=[],
                    ),
                ),
                Child(
                    background=None,
                    rule=None,
                    scenario=Scenario(
                        id="39",
                        keyword="Scenario",
                        location=Location(column=3, line=56),
                        name="Login page loads correctly",
                        description="",
                        steps=[
                            Step(
                                id="36",
                                keyword="Given",
                                keyword_type="Context",
                                location=Location(column=5, line=57),
                                text="the login page is loaded",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="37",
                                keyword="Then",
                                keyword_type="Outcome",
                                location=Location(column=5, line=58),
                                text="the login form should be visible",
                                datatable=None,
                                docstring=None,
                            ),
                        ],
                        tags=[Tag(id="38", location=Location(column=3, line=55), name="@smoke")],
                        examples=[],
                    ),
                ),
                Child(
                    background=None,
                    rule=None,
                    scenario=Scenario(
                        id="53",
                        keyword="Scenario",
                        location=Location(column=3, line=61),
                        name="Login with multiple sets of credentials",
                        description="",
                        steps=[
                            Step(
                                id="44",
                                keyword="Given",
                                keyword_type="Context",
                                location=Location(column=5, line=62),
                                text="the following users are registered:",
                                datatable=DataTable(
                                    location=Location(column=7, line=63),
                                    rows=[
                                        Row(
                                            id="40",
                                            location=Location(column=7, line=63),
                                            cells=[
                                                Cell(location=Location(column=9, line=63), value="username"),
                                                Cell(location=Location(column=20, line=63), value="password"),
                                            ],
                                        ),
                                        Row(
                                            id="41",
                                            location=Location(column=7, line=64),
                                            cells=[
                                                Cell(location=Location(column=9, line=64), value="user1"),
                                                Cell(location=Location(column=20, line=64), value="pass1"),
                                            ],
                                        ),
                                        Row(
                                            id="42",
                                            location=Location(column=7, line=65),
                                            cells=[
                                                Cell(location=Location(column=9, line=65), value="user2"),
                                                Cell(location=Location(column=20, line=65), value="pass2"),
                                            ],
                                        ),
                                        Row(
                                            id="43",
                                            location=Location(column=7, line=66),
                                            cells=[
                                                Cell(location=Location(column=9, line=66), value="user3"),
                                                Cell(location=Location(column=20, line=66), value="pass3"),
                                            ],
                                        ),
                                    ],
                                ),
                                docstring=None,
                            ),
                            Step(
                                id="48",
                                keyword="When",
                                keyword_type="Action",
                                location=Location(column=5, line=67),
                                text="the user tries to log in with the following credentials:",
                                datatable=DataTable(
                                    location=Location(column=7, line=68),
                                    rows=[
                                        Row(
                                            id="45",
                                            location=Location(column=7, line=68),
                                            cells=[
                                                Cell(location=Location(column=9, line=68), value="username"),
                                                Cell(location=Location(column=20, line=68), value="password"),
                                            ],
                                        ),
                                        Row(
                                            id="46",
                                            location=Location(column=7, line=69),
                                            cells=[
                                                Cell(location=Location(column=9, line=69), value="user1"),
                                                Cell(location=Location(column=20, line=69), value="pass1"),
                                            ],
                                        ),
                                        Row(
                                            id="47",
                                            location=Location(column=7, line=70),
                                            cells=[
                                                Cell(location=Location(column=9, line=70), value="user2"),
                                                Cell(location=Location(column=20, line=70), value="wrongPass"),
                                            ],
                                        ),
                                    ],
                                ),
                                docstring=None,
                            ),
                            Step(
                                id="52",
                                keyword="Then",
                                keyword_type="Outcome",
                                location=Location(column=5, line=71),
                                text="the login attempts should result in:",
                                datatable=DataTable(
                                    location=Location(column=7, line=72),
                                    rows=[
                                        Row(
                                            id="49",
                                            location=Location(column=7, line=72),
                                            cells=[
                                                Cell(location=Location(column=9, line=72), value="username"),
                                                Cell(location=Location(column=20, line=72), value="result"),
                                            ],
                                        ),
                                        Row(
                                            id="50",
                                            location=Location(column=7, line=73),
                                            cells=[
                                                Cell(location=Location(column=9, line=73), value="user1"),
                                                Cell(location=Location(column=20, line=73), value="success"),
                                            ],
                                        ),
                                        Row(
                                            id="51",
                                            location=Location(column=7, line=74),
                                            cells=[
                                                Cell(location=Location(column=9, line=74), value="user2"),
                                                Cell(location=Location(column=20, line=74), value="failure"),
                                            ],
                                        ),
                                    ],
                                ),
                                docstring=None,
                            ),
                        ],
                        tags=[],
                        examples=[],
                    ),
                ),
                Child(
                    background=None,
                    rule=None,
                    scenario=Scenario(
                        id="57",
                        keyword="Scenario",
                        location=Location(column=3, line=77),
                        name="Check login error message with detailed explanation",
                        description="",
                        steps=[
                            Step(
                                id="54",
                                keyword="Given",
                                keyword_type="Context",
                                location=Location(column=5, line=78),
                                text="the user enters invalid credentials",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="55",
                                keyword="When",
                                keyword_type="Action",
                                location=Location(column=5, line=79),
                                text="the user clicks the login button",
                                datatable=None,
                                docstring=None,
                            ),
                            Step(
                                id="56",
                                keyword="Then",
                                keyword_type="Outcome",
                                location=Location(column=5, line=80),
                                text="the user should see the following error message:",
                                datatable=None,
                                docstring=DocString(
                                    content="Your login attempt was unsuccessful.\nPlease check your username and password and try again.\nIf the problem persists, contact support.",
                                    delimiter='"""',
                                    location=Location(column=7, line=81),
                                ),
                            ),
                        ],
                        tags=[],
                        examples=[],
                    ),
                ),
                Child(
                    background=None,
                    rule=Rule(
                        id="64",
                        keyword="Rule",
                        location=Location(column=3, line=88),
                        name="a sale cannot happen if there is no stock",
                        description="",
                        tags=[
                            Tag(
                                id="63",
                                location=Location(column=3, line=87),
                                name="@some-tag",
                            )
                        ],
                        children=[
                            Child(
                                background=None,
                                rule=None,
                                scenario=Scenario(
                                    id="62",
                                    keyword="Example",
                                    location=Location(column=3, line=90),
                                    name="No chocolates left",
                                    description="",
                                    steps=[
                                        Step(
                                            id="58",
                                            keyword="Given",
                                            keyword_type="Context",
                                            location=Location(column=5, line=91),
                                            text="the customer has 100 cents",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                        Step(
                                            id="59",
                                            keyword="And",
                                            keyword_type="Conjunction",
                                            location=Location(column=5, line=92),
                                            text="there are no chocolate bars in stock",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                        Step(
                                            id="60",
                                            keyword="When",
                                            keyword_type="Action",
                                            location=Location(column=5, line=93),
                                            text="the customer tries to buy a 1 cent chocolate bar",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                        Step(
                                            id="61",
                                            keyword="Then",
                                            keyword_type="Outcome",
                                            location=Location(column=5, line=94),
                                            text="the sale should not happen",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                    ],
                                    tags=[],
                                    examples=[],
                                ),
                            )
                        ],
                    ),
                    scenario=None,
                ),
                Child(
                    background=None,
                    rule=Rule(
                        id="75",
                        keyword="Rule",
                        location=Location(column=3, line=96),
                        name="A sale cannot happen if the customer does not have enough money",
                        description="",
                        tags=[],
                        children=[
                            Child(
                                background=None,
                                rule=None,
                                scenario=Scenario(
                                    id="69",
                                    keyword="Example",
                                    location=Location(column=5, line=98),
                                    name="Not enough money",
                                    description="",
                                    steps=[
                                        Step(
                                            id="65",
                                            keyword="Given",
                                            keyword_type="Context",
                                            location=Location(column=7, line=99),
                                            text="the customer has 100 cents",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                        Step(
                                            id="66",
                                            keyword="And",
                                            keyword_type="Conjunction",
                                            location=Location(column=7, line=100),
                                            text="there are chocolate bars in stock",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                        Step(
                                            id="67",
                                            keyword="When",
                                            keyword_type="Action",
                                            location=Location(column=7, line=101),
                                            text="the customer tries to buy a 125 cent chocolate bar",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                        Step(
                                            id="68",
                                            keyword="Then",
                                            keyword_type="Outcome",
                                            location=Location(column=7, line=102),
                                            text="the sale should not happen",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                    ],
                                    tags=[],
                                    examples=[],
                                ),
                            ),
                            Child(
                                background=None,
                                rule=None,
                                scenario=Scenario(
                                    id="74",
                                    keyword="Example",
                                    location=Location(column=5, line=105),
                                    name="Enough money",
                                    description="",
                                    steps=[
                                        Step(
                                            id="70",
                                            keyword="Given",
                                            keyword_type="Context",
                                            location=Location(column=7, line=106),
                                            text="the customer has 100 cents",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                        Step(
                                            id="71",
                                            keyword="And",
                                            keyword_type="Conjunction",
                                            location=Location(column=7, line=107),
                                            text="there are chocolate bars in stock",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                        Step(
                                            id="72",
                                            keyword="When",
                                            keyword_type="Action",
                                            location=Location(column=7, line=108),
                                            text="the customer tries to buy a 75 cent chocolate bar",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                        Step(
                                            id="73",
                                            keyword="Then",
                                            keyword_type="Outcome",
                                            location=Location(column=7, line=109),
                                            text="the sale should happen",
                                            datatable=None,
                                            docstring=None,
                                        ),
                                    ],
                                    tags=[],
                                    examples=[],
                                ),
                            ),
                        ],
                    ),
                    scenario=None,
                ),
            ],
        ),
        comments=[
            Comment(location=Location(column=1, line=1), text="# This is a comment"),
            Comment(
                location=Location(column=1, line=9),
                text="    # Background steps run before each scenario",
            ),
            Comment(location=Location(column=1, line=12), text="    # Scenario within the rule"),
            Comment(
                location=Location(column=1, line=25),
                text="      # Examples table provides data for the scenario outline",
            ),
            Comment(
                location=Location(column=1, line=54),
                text="  # Tags can be used to categorize scenarios",
            ),
            Comment(
                location=Location(column=1, line=60),
                text="  # Using Data Tables for more complex data",
            ),
            Comment(
                location=Location(column=1, line=76),
                text="  # Using Doc Strings for multi-line text",
            ),
            Comment(location=Location(column=1, line=89), text="  # Unhappy path"),
            Comment(location=Location(column=1, line=97), text="    # Unhappy path"),
            Comment(location=Location(column=1, line=104), text="    # Happy path"),
        ],
    )

    assert gherkin_doc == expected_document
