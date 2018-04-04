import re


import pytest

from pytest_bdd import scenario, given, when, then


@scenario('gherkin_terminal_reporter.feature',
          'Should default output be the same as regular terminal reporter')
def test_Should_default_output_be_the_same_as_regular_terminal_reporter():
    pass


@scenario('gherkin_terminal_reporter.feature',
          'Should verbose mode enable displaying feature and scenario names rather than test names in a single line')
def test_Should_verbose_mode_enable_displaying_feature_and_scenario_names_rather_than_test_names_in_a_single_line():
    pass


@scenario('gherkin_terminal_reporter.feature',
          'Should verbose mode preserve displaying of regular tests as usual')
def test_Should_verbose_mode_preserve_displaying_of_regular_tests_as_usual():
    pass


@scenario('gherkin_terminal_reporter.feature',
          'Should double verbose mode enable displaying of full gherkin scenario description')
def test_Should_double_verbose_mode_enable_displaying_of_full_gherkin_scenario_description():
    pass


@scenario('gherkin_terminal_reporter.feature',
          'Should error message be displayed when no scenario is found')
def test_Should_error_message_be_displayed_when_no_scenario_is_found(verbosity_mode):
    pass


@scenario('gherkin_terminal_reporter.feature',
          'Should error message be displayed when no step is found')
def test_Should_error_message_be_displayed_when_no_step_is_found(verbosity_mode):
    pass


@scenario('gherkin_terminal_reporter.feature',
          'Should error message be displayed when error occurs during test execution')
def test_Should_error_message_be_displayed_when_error_occurs_during_test_execution(verbosity_mode):
    pass


@scenario('gherkin_terminal_reporter.feature',
          'Should local variables be displayed when --showlocals option is used')
def test_Should_local_variables_be_displayed_when___showlocals_option_is_used():
    pass


@scenario('gherkin_terminal_reporter.feature',
          'Should step parameters be replaced by their values')
def test_Should_step_parameters_be_replaced_by_their_values():
    pass


@pytest.fixture(params=[0, 1, 2],
                ids=['compact mode', 'line per test', 'verbose'])
def verbosity_mode(request):
    return request.param, '-' + 'v' * request.param if request.param else ''


@pytest.fixture
def test_execution():
    return {}


@given("there is non-gherkin scenario implemented")
def non_gherkin_test(testdir):
    testdir.makepyfile(test_regular="""
        def test_1():
            pass
    """)


@given("there is gherkin scenario implemented")
def gherkin_scenario(testdir):
    testdir.makefile('.feature', test="""
    Feature: Gherkin terminal output feature
    Scenario: Scenario example 1
        Given there is a bar
        When the bar is accessed
        Then world explodes
    """)
    testdir.makepyfile(test_gherkin="""
        import pytest
        from pytest_bdd import given, when, scenario, then

        @given('there is a bar')
        def a_bar():
            return 'bar'

        @when('the bar is accessed')
        def the_bar_is_accessed():
            pass

        @then('world explodes')
        def world_explodes():
            pass

        @scenario('test.feature', 'Scenario example 1')
        def test_scenario_1():
            pass
    """)


@given("there is gherkin scenario outline implemented")
def gherkin_scenario_outline(testdir):
    example = {
        'start': 12,
        'eat': 5,
        'left': 7,
    }
    testdir.makefile('.feature', test="""
    Feature: Gherkin terminal output feature
    Scenario Outline: Scenario example 2
        Given there are <start> cucumbers
        When I eat <eat> cucumbers
        Then I should have <left> cucumbers

        Examples:
        | start | eat | left |
        |{start}|{eat}|{left}|
    """.format(**example))
    testdir.makepyfile(test_gherkin="""
        import pytest
        from pytest_bdd import given, when, scenario, then

        @given('there are <start> cucumbers')
        def start_cucumbers(start):
            return start

        @when('I eat <eat> cucumbers')
        def eat_cucumbers(start_cucumbers, eat):
            pass

        @then('I should have <left> cucumbers')
        def should_have_left_cucumbers(start_cucumbers, start, eat, left):
            pass

        @scenario('test.feature', 'Scenario example 2')
        def test_scenario_2():
            pass
    """)
    return example


@when("tests are run")
def tests_are_run(testdir, test_execution):
    test_execution['regular'] = testdir.runpytest()
    test_execution['gherkin'] = testdir.runpytest('--gherkin-terminal-reporter')


@then("output must be formatted the same way as regular one")
def output_must_be_the_same_as_regular_reporter(test_execution):
    reg = test_execution['regular']
    ghe = test_execution['gherkin']
    assert reg.ret == 0
    assert ghe.ret == 0
    #  last line can be different because of test execution time is printed
    reg_lines = reg.stdout.lines if reg.stdout.lines[-1] else reg.stdout.lines[:-2]
    reg_lines[-1] = re.sub(r' \d+\.\d+ ', ' X ', reg_lines[-1])
    ghe_lines = ghe.stdout.lines if ghe.stdout.lines[-1] else ghe.stdout.lines[:-2]
    ghe_lines[-1] = re.sub(r' \d+\.\d+ ', ' X ', ghe_lines[-1])
    for l1, l2 in zip(reg_lines, ghe_lines):
        assert l1 == l2


@when("tests are run with verbose mode")
def tests_are_run_with_verbose_mode(testdir, test_execution):
    test_execution['regular'] = testdir.runpytest('-v')
    test_execution['gherkin'] = testdir.runpytest('--gherkin-terminal-reporter', '-v')


@when("tests are run with very verbose mode")
def tests_are_run_with_very_verbose_mode(testdir, test_execution):
    test_execution['regular'] = testdir.runpytest('-vv')
    test_execution['gherkin'] = testdir.runpytest('--gherkin-terminal-reporter', '-vv')


@when("tests are run with step expanded mode")
def tests_are_run_with_step_expanded_mode(testdir, test_execution):
    test_execution['regular'] = testdir.runpytest('-vv')
    test_execution['gherkin'] = testdir.runpytest(
        '--gherkin-terminal-reporter',
        '--gherkin-terminal-reporter-expanded',
        '-vv',
    )


@then("output should contain single line feature description")
def output_should_contain_single_line_feature_description(test_execution):
    ghe = test_execution['gherkin']
    assert ghe.ret == 0
    ghe.stdout.fnmatch_lines('Feature: Gherkin terminal output feature')


@then("output should contain single line scenario description")
def output_should_contain_single_line_scenario_description(test_execution):
    ghe = test_execution['gherkin']
    assert ghe.ret == 0
    ghe.stdout.fnmatch_lines('*Scenario: Scenario example 1 PASSED')


@then("output must contain full gherkin scenario description")
def output_should_contain_full_gherkin_scenario_description(test_execution):
    ghe = test_execution['gherkin']
    assert ghe.ret == 0
    ghe.stdout.fnmatch_lines('*Scenario: Scenario example 1')
    ghe.stdout.fnmatch_lines('*Given there is a bar')
    ghe.stdout.fnmatch_lines('*When the bar is accessed')
    ghe.stdout.fnmatch_lines('*Then world explodes')
    ghe.stdout.fnmatch_lines('*PASSED')


@given('there is gherkin scenario without implementation')
def gherkin_scenario_without_implementation(testdir):
    testdir.makefile('.feature', test="""
    Feature: Gherkin terminal output feature
    Scenario: Scenario example 1
        Given there is a bar
        When the bar is accessed
        Then world explodes
    """)
    testdir.makepyfile(test_gherkin="""
        import pytest
        from pytest_bdd import scenarios

        scenarios('.')

    """)


@when('tests are run with any verbosity mode')
def tests_are_run_with_any_verbosity_mode(
        test_execution, verbosity_mode, testdir,
        gherkin_scenario_without_implementation):
    #  test_execution['gherkin'] = testdir.runpytest(
    #      '--gherkin-terminal-reporter', '-vv')
    if verbosity_mode[1]:
        test_execution['gherkin'] = testdir.runpytest(
            '--gherkin-terminal-reporter', verbosity_mode[1])
    else:
        test_execution['gherkin'] = testdir.runpytest(
            '--gherkin-terminal-reporter')


@then('output contains error about missing scenario implementation')
def output_contains_error_about_missing_scenario_implementation(test_execution):
    ghe = test_execution['gherkin']
    assert ghe.ret
    ghe.stdout.fnmatch_lines('''*StepDefinitionNotFoundError: Step definition is not found: Given "there is a bar". '''
                             '''Line 3 in scenario "Scenario example 1"*''')


@given('there is gherkin scenario partially implemented')
def partially_implemented_gherkin_scenario(testdir):
    testdir.makefile('.feature', test="""
    Feature: Gherkin terminal output feature
    Scenario: Scenario example 1
        Given there is a bar
        When the bar is accessed
        Then world explodes
    """)
    testdir.makepyfile(test_gherkin="""
        import pytest
        from pytest_bdd import given, when, scenario, then

        @given('there is a bar')
        def a_bar():
            return 'bar'

        @when('the bar is accessed')
        def the_bar_is_accessed():
            pass

        @scenario('test.feature', 'Scenario example 1')
        def test_scenario_1():
            pass
    """)


@then('output contains error about missing step implementation')
def output_contains_error_about_missing_step_implementation(test_execution):
    ghe = test_execution['gherkin']
    assert ghe.ret
    ghe.stdout.fnmatch_lines('''*StepDefinitionNotFoundError: Step definition is not found: Given "there is a bar". '''
                             '''Line 3 in scenario "Scenario example 1"*''')


@given('there is gherkin scenario with broken implementation')
def there_is_gherkin_scenario_with_broken_implementation(testdir):
    testdir.makefile('.feature', test="""
    Feature: Gherkin terminal output feature
    Scenario: Scenario example 1
        Given there is a bar
        When the bar is accessed
        Then world explodes
    """)
    testdir.makepyfile(test_gherkin="""
        import pytest
        from pytest_bdd import given, when, scenario, then

        @given('there is a bar')
        def a_bar(request):
            return 'bar'

        @when('the bar is accessed')
        def the_bar_is_accessed(request):
            local_var = 'value2'
            raise Exception("ERROR")

        @scenario('test.feature', 'Scenario example 1')
        def test_scenario_1():
            pass
    """)


@when('tests are run with --showlocals')
def tests_are_run_with___showlocals(test_execution, testdir):
    test_execution['gherkin'] = testdir.runpytest('--gherkin-terminal-reporter', '--showlocals')


@then('error traceback contains local variable descriptions')
def error_traceback_contains_local_variable_descriptions(test_execution):
    ghe = test_execution['gherkin']
    assert ghe.ret
    ghe.stdout.fnmatch_lines('''request*=*<FixtureRequest for *''')
    ghe.stdout.fnmatch_lines('''local_var*=*''')


@then("output must contain parameters values")
def output_output_must_contain_parameters_values(test_execution, gherkin_scenario_outline):
    ghe = test_execution['gherkin']
    assert ghe.ret == 0
    ghe.stdout.fnmatch_lines('*Scenario: Scenario example 2')
    ghe.stdout.fnmatch_lines('*Given there are {start} cucumbers'.format(**gherkin_scenario_outline))
    ghe.stdout.fnmatch_lines('*When I eat {eat} cucumbers'.format(**gherkin_scenario_outline))
    ghe.stdout.fnmatch_lines('*Then I should have {left} cucumbers'.format(**gherkin_scenario_outline))
    ghe.stdout.fnmatch_lines('*PASSED')
