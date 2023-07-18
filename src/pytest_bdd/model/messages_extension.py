from enum import Enum


class ExpressionType(Enum):
    pytest_bdd_heuristic_expression = "PYTEST_BDD_HEURISTIC_EXPRESSION"
    pytest_bdd_string_expression = "PYTEST_BDD_STRING_EXPRESSION"
    pytest_bdd_regular_expression = "PYTEST_BDD_REGULAR_EXPRESSION"
    pytest_bdd_parse_expression = "PYTEST_BDD_PARSE_EXPRESSION"
    pytest_bdd_cfparse_expression = "PYTEST_BDD_CFPARSE_EXPRESSION"
    pytest_bdd_other_expression = "PYTEST_BDD_OTHER_EXPRESSION"
