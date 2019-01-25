import functools

import pytest

from plugnpy.exception import InvalidMetricThreshold
from plugnpy.metric import Metric


def raise_or_assert(callback, raises, expected):
    if raises:
        with pytest.raises(raises):
            callback()
    else:
        assert callback() == expected


@pytest.mark.parametrize('display_unit_factor_type,display_format,raises,expected,convert_metric', [
    ('bytes', '{name} is {value} {unit}', False, 'Memory is 1024 bytes', False),
    ('bytes', '{value}{unit}', False, '1024bytes', False),
    ('bytes', '{bad} {wrong}', KeyError, None, False),
    ('decimal', '{name} is {value} {unit}', False, 'Memory is 1024 bytes', False),
    ('bytes', '{name} is {value} {unit}', False, 'Memory is 1024 bytes', True),
],
    ids=[
        'display_unit_factor',
        'no_display_unit_factor',
        'wrong_display_format',
        'automatic_value_decimal',
        'automatic_value_bytes',
])
def test_str(display_unit_factor_type, display_format, raises, expected, convert_metric):
    raise_or_assert(
        functools.partial(str, Metric(
            'Memory', 1024, 'bytes',
            display_unit_factor_type=display_unit_factor_type,
            display_format=display_format,
            convert_metric=convert_metric
        )),
        raises,
        expected
    )


@pytest.mark.parametrize('value,start,end,check_outside_range,expected', [
    (1, 1, 100, True, False),
    (0, 1, 100, True, True),
    (1, 1, 100, False, True),
    (0, 1, 100, False, False),
], ids=[
    'outside_ok',
    'outside_ko',
    'inside_ok',
    'inside_ko',
])
def test_check(value, start, end, check_outside_range, expected):
    assert Metric.check(value, start, end, check_outside_range) == expected


@pytest.mark.parametrize('value,is_start,raises,expected', [
    ('~', False, False, Metric.P_INF),
    ('~', True, False, Metric.N_INF),
    ('10', True, False, 10.0),
    ('10K', True, False, "10240"),
    ('10S', True, InvalidMetricThreshold, None),
], ids=[
    'infinite',
    'negative_infinite',
    'no_prefix',
    'prefix',
    'wrong_prefix',
])
def test_parse_threshold_limit(value, is_start, raises, expected):
    raise_or_assert(
        functools.partial(Metric('Something', 10, '%').parse_threshold_limit, value, is_start), raises, expected
    )


@pytest.mark.parametrize('threshold,raises,expected', [
    ('@1:3', False, (1.0, 3.0, False)),
    ('10', False, (0.0, 10.0, True)),
    ('3:', False, (3.0, Metric.P_INF, True)),
    ('~:5', False, (Metric.N_INF, 5.0, True)),
    ('bad', InvalidMetricThreshold, None),
], ids=[
    'inside_range',
    'zero_start',
    'infinite_end',
    'normal_range',
    'wrong_threshold'
])
def test_parse_threshold(threshold, raises, expected):
    raise_or_assert(functools.partial(Metric('Something', 10, '%').parse_threshold, threshold), raises, expected)


@pytest.mark.parametrize('warning_threshold,critical_threshold,expected', [
    ('50:120', '30:150', 0),
    ('110:150', '90:170', 1),
    ('130:150', '110:170', 2),
], ids=[
    'ok',
    'warning',
    'critical',
])
def test_state(warning_threshold, critical_threshold, expected):
    assert Metric('Memory', 100, 'bytes', warning_threshold, critical_threshold).state == expected
