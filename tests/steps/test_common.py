import textwrap
from typing import Any, Callable
from unittest import mock

import pytest

from pytest_bdd import given, parsers, then, when
from pytest_bdd.utils import collect_dumped_objects


@pytest.mark.parametrize("step_fn, step_type", [(given, "given"), (when, "when"), (then, "then")])
@pytest.mark.parametrize(
    "params",
    [
        pytest.param({"name": "foo"}, id="simple"),
        pytest.param(
            {
                "name": parsers.re(r"foo (?P<n>\d+)"),
                "converters": {"n": int},
                "target_fixture": "foo_n",
                "stacklevel": 3,
            },
            id="advanced",
        ),
    ],
)
def test_given_when_then_delegate_to_step(step_fn: Callable[..., Any], step_type: str, params: dict[str, Any]):
    """Test that @given, @when, @then just delegate the work to @step(...).
    This way we don't have to repeat integration tests for each step decorator.
    """
    default_params = {
        "converters": None,
        "target_fixture": None,
        "stacklevel": 1,
    }
    with mock.patch("pytest_bdd.steps.step", autospec=True) as step_mock:
        step_fn(**params)

    all_params = {**default_params, **params}
    step_mock.assert_called_once_with(**all_params, type_=step_type)


def test_step_function_multiple_target_fixtures(testdir):
    testdir.makefile(
        ".feature",
        target_fixture=textwrap.dedent(
            """\
            Feature: Multiple target fixtures for step function
                Scenario: A step can be decorated multiple times with different target fixtures
                    Given there is a foo with value "test foo"
                    And there is a bar with value "test bar"
                    Then foo should be "test foo"
                    And bar should be "test bar"
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenarios, parsers
        from pytest_bdd.utils import dump_obj

        scenarios("target_fixture.feature")

        @given(parsers.parse('there is a foo with value "{value}"'), target_fixture="foo")
        @given(parsers.parse('there is a bar with value "{value}"'), target_fixture="bar")
        def _(value):
            return value

        @then(parsers.parse('foo should be "{expected_value}"'))
        def _(foo, expected_value):
            dump_obj(foo)
            assert foo == expected_value

        @then(parsers.parse('bar should be "{expected_value}"'))
        def _(bar, expected_value):
            dump_obj(bar)
            assert bar == expected_value
        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)

    [foo, bar] = collect_dumped_objects(result)
    assert foo == "test foo"
    assert bar == "test bar"


def test_step_functions_same_parser(testdir):
    testdir.makefile(
        ".feature",
        target_fixture=textwrap.dedent(
            """\
            Feature: A feature
                Scenario: A scenario
                    Given there is a foo with value "(?P<value>\\w+)"
                    And there is a foo with value "testfoo"
                    When pass
                    Then pass
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenarios, parsers
        from pytest_bdd.utils import dump_obj

        scenarios("target_fixture.feature")

        STEP = 'there is a foo with value "(?P<value>\\w+)"'

        @given(STEP)
        def _():
            dump_obj(('str',))

        @given(parsers.re(STEP))
        def _(value):
            dump_obj(('re', value))

        @when("pass")
        @then("pass")
        def _():
            pass
        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)

    [first_given, second_given] = collect_dumped_objects(result)
    assert first_given == ("str",)
    assert second_given == ("re", "testfoo")


def test_user_implements_a_step_generator(testdir):
    """Test advanced use cases, like the implementation of custom step generators."""
    testdir.makefile(
        ".feature",
        user_step_generator=textwrap.dedent(
            """\
            Feature: A feature
                Scenario: A scenario
                    Given I have 10 EUR
                    And the wallet is verified
                    And I have a wallet
                    When I pay 1 EUR
                    Then I should have 9 EUR in my wallet
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
            import re
            from dataclasses import dataclass, fields

            import pytest
            from pytest_bdd import given, when, then, scenarios, parsers
            from pytest_bdd.utils import dump_obj


            @dataclass
            class Wallet:
                verified: bool

                amount_eur: int
                amount_usd: int
                amount_gbp: int
                amount_jpy: int

                def pay(self, amount: int, currency: str) -> None:
                    if not self.verified:
                        raise ValueError("Wallet account is not verified")
                    currency = currency.lower()
                    field = f"amount_{currency}"
                    setattr(self, field, getattr(self, field) - amount)


            @pytest.fixture
            def wallet__verified():
                return False


            @pytest.fixture
            def wallet__amount_eur():
                return 0


            @pytest.fixture
            def wallet__amount_usd():
                return 0


            @pytest.fixture
            def wallet__amount_gbp():
                return 0


            @pytest.fixture
            def wallet__amount_jpy():
                return 0


            @pytest.fixture()
            def wallet(
                wallet__verified,
                wallet__amount_eur,
                wallet__amount_usd,
                wallet__amount_gbp,
                wallet__amount_jpy,
            ):
                return Wallet(
                    verified=wallet__verified,
                    amount_eur=wallet__amount_eur,
                    amount_usd=wallet__amount_usd,
                    amount_gbp=wallet__amount_gbp,
                    amount_jpy=wallet__amount_jpy,
                )


            def wallet_steps_generator(model_name="wallet"):
                @given("I have a wallet", target_fixture=model_name, stacklevel=2)
                def _(wallet):
                    return wallet

                @given(
                    parsers.re(r"the wallet is (?P<negation>not)?verified"),
                    target_fixture=f"{model_name}__verified",
                    stacklevel=2,
                )
                def _(negation: str):
                    if negation:
                        return False
                    return True

                # Generate steps for currency fields:
                for field in fields(Wallet):
                    match = re.fullmatch(r"amount_(?P<currency>[a-z]{3})", field.name)
                    if not match:
                        continue
                    currency = match["currency"]

                    @given(
                        parsers.parse(f"I have {{value:d}} {currency.upper()}"),
                        target_fixture=f"{model_name}__amount_{currency}",
                        stacklevel=2,
                    )
                    def _(value: int, _currency=currency) -> int:
                        dump_obj(f"given {value} {_currency.upper()}")
                        return value

                    @when(
                        parsers.parse(f"I pay {{value:d}} {currency.upper()}"),
                        stacklevel=2,
                    )
                    def _(wallet: Wallet, value: int, _currency=currency) -> None:
                        dump_obj(f"pay {value} {_currency.upper()}")
                        wallet.pay(value, _currency)

                    @then(
                        parsers.parse(f"I should have {{value:d}} {currency.upper()} in my wallet"),
                        stacklevel=2,
                    )
                    def _(wallet: Wallet, value: int, _currency=currency) -> None:
                        dump_obj(f"assert {value} {_currency.upper()}")
                        assert getattr(wallet, f"amount_{_currency}") == value

            wallet_steps_generator()

            scenarios("user_step_generator.feature")
        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)

    [given, pay, assert_] = collect_dumped_objects(result)
    assert given == "given 10 EUR"
    assert pay == "pay 1 EUR"
    assert assert_ == "assert 9 EUR"


def test_step_catches_all(testdir):
    """Test that the @step(...) decorator works for all kind of steps."""
    testdir.makefile(
        ".feature",
        step_catches_all=textwrap.dedent(
            """\
            Feature: A feature
                Scenario: A scenario
                    Given foo
                    And foo parametrized 1
                    When foo
                    And foo parametrized 2
                    Then foo
                    And foo parametrized 3
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import step, scenarios, parsers
        from pytest_bdd.utils import dump_obj

        scenarios("step_catches_all.feature")

        @step("foo")
        def _():
            dump_obj("foo")

        @step(parsers.parse("foo parametrized {n:d}"))
        def _(n):
            dump_obj(("foo parametrized", n))
        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)

    objects = collect_dumped_objects(result)
    assert objects == ["foo", ("foo parametrized", 1), "foo", ("foo parametrized", 2), "foo", ("foo parametrized", 3)]
