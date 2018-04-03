"""Test scenario reporting."""
import textwrap

import execnet.gateway_base


class equals_any(object):

    """Helper object comparison to which is always 'equal'."""

    def __init__(self, type=None):
        self.type = type

    def __eq__(self, other):
        return isinstance(other, self.type) if self.type else True

    def __cmp__(self, other):
        return 0 if (isinstance(other, self.type) if self.type else False) else -1


string = type(u'')


def test_step_trace(testdir):
    """Test step trace."""
    feature = testdir.makefile('.feature', test=textwrap.dedent("""
    @feature-tag
    Feature: One passing scenario, one failing scenario

        @scenario-passing-tag
        Scenario: Passing
            Given a passing step
            And some other passing step

        @scenario-failing-tag
        Scenario: Failing
            Given a passing step
            And a failing step

        Scenario Outline: Outlined
            Given there are <start> cucumbers
            When I eat <eat> cucumbers
            Then I should have <left> cucumbers

            Examples:
            | start | eat | left |
            |  12   |  5  |  7   |
            |  5    |  4  |  1   |
    """))
    relpath = feature.relto(testdir.tmpdir.dirname)
    testdir.makepyfile(textwrap.dedent("""
        import pytest
        from pytest_bdd import given, when, then, scenarios

        @given('a passing step')
        def a_passing_step():
            return 'pass'

        @given('some other passing step')
        def some_other_passing_step():
            return 'pass'

        @given('a failing step')
        def a_failing_step():
            raise Exception('Error')

        @given('there are <start> cucumbers')
        def start_cucumbers(start):
            assert isinstance(start, int)
            return dict(start=start)


        @when('I eat <eat> cucumbers')
        def eat_cucumbers(start_cucumbers, eat):
            assert isinstance(eat, float)
            start_cucumbers['eat'] = eat


        @then('I should have <left> cucumbers')
        def should_have_left_cucumbers(start_cucumbers, start, eat, left):
            assert isinstance(left, str)
            assert start - eat == int(left)
            assert start_cucumbers['start'] == start
            assert start_cucumbers['eat'] == eat

        scenarios('test.feature', example_converters=dict(start=int, eat=float, left=str))
    """))
    result = testdir.inline_run('-vvl')
    assert result.ret
    report = result.matchreport('test_passing', when='call').scenario
    expected = {'feature': {'description': u'',
                            'filename': feature.strpath,
                            'line_number': 2,
                            'name': u'One passing scenario, one failing scenario',
                            'rel_filename': relpath,
                            'tags': [u'feature-tag']},
                'line_number': 5,
                'name': u'Passing',
                'steps': [{'duration': equals_any(float),
                           'failed': False,
                           'keyword': 'Given',
                           'line_number': 6,
                           'name': u'a passing step',
                           'type': 'given'},
                          {'duration': equals_any(float),
                           'failed': False,
                           'keyword': 'And',
                           'line_number': 7,
                           'name': u'some other passing step',
                           'type': 'given'}],
                'tags': [u'scenario-passing-tag'],
                'examples': [],
                'example_kwargs': {}}

    assert report == expected

    report = result.matchreport('test_failing', when='call').scenario
    expected = {'feature': {'description': u'',
                            'filename': feature.strpath,
                            'line_number': 2,
                            'name': u'One passing scenario, one failing scenario',
                            'rel_filename': relpath,
                            'tags': [u'feature-tag']},
                'line_number': 10,
                'name': u'Failing',
                'steps': [{'duration': equals_any(float),
                           'failed': False,
                           'keyword': 'Given',
                           'line_number': 11,
                           'name': u'a passing step',
                           'type': 'given'},
                          {'duration': equals_any(float),
                           'failed': True,
                           'keyword': 'And',
                           'line_number': 12,
                           'name': u'a failing step',
                           'type': 'given'}],
                'tags': [u'scenario-failing-tag'],
                'examples': [],
                'example_kwargs': {}}
    assert report == expected

    report = result.matchreport('test_outlined[12-5.0-7]', when='call').scenario
    expected = {'feature': {'description': u'',
                            'filename': feature.strpath,
                            'line_number': 2,
                            'name': u'One passing scenario, one failing scenario',
                            'rel_filename': relpath,
                            'tags': [u'feature-tag']},
                'line_number': 14,
                'name': u'Outlined',
                'steps': [{'duration': equals_any(float),
                           'failed': False,
                           'keyword': 'Given',
                           'line_number': 15,
                           'name': u'there are <start> cucumbers',
                           'type': 'given'},
                          {'duration': equals_any(float),
                           'failed': False,
                           'keyword': 'When',
                           'line_number': 16,
                           'name': u'I eat <eat> cucumbers',
                           'type': 'when'},
                          {'duration': equals_any(float),
                           'failed': False,
                           'keyword': 'Then',
                           'line_number': 17,
                           'name': u'I should have <left> cucumbers',
                           'type': 'then'}],
                'tags': [],
                'examples': [{'line_number': 19,
                              'name': None,
                              'row_index': 0,
                              'rows': [['start', 'eat', 'left'],
                                       [[12, 5.0, '7'], [5, 4.0, '1']]]}],
                'example_kwargs': {'eat': '5.0', 'left': '7', 'start': '12'},
                }
    assert report == expected

    report = result.matchreport('test_outlined[5-4.0-1]', when='call').scenario
    expected = {'feature': {'description': u'',
                            'filename': feature.strpath,
                            'line_number': 2,
                            'name': u'One passing scenario, one failing scenario',
                            'rel_filename': relpath,
                            'tags': [u'feature-tag']},
                'line_number': 14,
                'name': u'Outlined',
                'steps': [{'duration': equals_any(float),
                           'failed': False,
                           'keyword': 'Given',
                           'line_number': 15,
                           'name': u'there are <start> cucumbers',
                           'type': 'given'},
                          {'duration': equals_any(float),
                           'failed': False,
                           'keyword': 'When',
                           'line_number': 16,
                           'name': u'I eat <eat> cucumbers',
                           'type': 'when'},
                          {'duration': equals_any(float),
                           'failed': False,
                           'keyword': 'Then',
                           'line_number': 17,
                           'name': u'I should have <left> cucumbers',
                           'type': 'then'}],
                'tags': [],
                'examples': [{'line_number': 19,
                              'name': None,
                              'row_index': 1,
                              'rows': [['start', 'eat', 'left'],
                                       [[12, 5.0, '7'], [5, 4.0, '1']]]}],
                'example_kwargs': {'eat': '4.0', 'left': '1', 'start': '5'},
                }
    assert report == expected


def test_complex_types(testdir):
    """Test serialization of the complex types."""
    testdir.makefile('.feature', test=textwrap.dedent("""
    Feature: Report serialization containing parameters of complex types

        Scenario: Complex
            Given there is a coordinate <point>

            Examples:
            |  point  |
            |  10,20  |
    """))
    testdir.makepyfile(textwrap.dedent("""
        import pytest
        from pytest_bdd import given, when, then, scenario

        class Point(object):

            def __init__(self, x, y):
                self.x = x
                self.y = y

            @classmethod
            def parse(cls, value):
                return cls(*(int(x) for x in value.split(',')))

        class Alien(object):
            pass

        @given('there is a coordinate <point>')
        def point(point):
            assert isinstance(point, Point)
            return point


        @pytest.mark.parametrize('alien', [Alien()])
        @scenario('test.feature', 'Complex', example_converters=dict(point=Point.parse))
        def test_complex(alien):
            pass

    """))
    result = testdir.inline_run('-vvl')
    report = result.matchreport('test_complex[point0-alien0]', when='call')
    assert execnet.gateway_base.dumps(report.item)
    assert execnet.gateway_base.dumps(report.scenario)
