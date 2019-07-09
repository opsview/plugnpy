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


@pytest.mark.parametrize('value,display_unit_factor_type,display_format,raises,expected,convert_metric', [
    (1024, 'bytes', '{name} is {value} {unit}', False, 'Memory is 1024 B', False),
    (1024, 'bytes', '{value}{unit}', False, '1024B', False),
    (1024, 'bytes', '{bad} {wrong}', KeyError, None, False),
    (1024, 'decimal', '{name} is {value} {unit}', False, 'Memory is 1024 B', False),
    (1, 'bytes', '{name} is {value} {unit}', False, 'Memory is 1 B', True),
],
    ids=[
        'display_unit_factor',
        'no_display_unit_factor',
        'wrong_display_format',
        'automatic_value_decimal',
        'automatic_value_bytes',
])
def test_str(value, display_unit_factor_type, display_format, raises, expected, convert_metric):
    raise_or_assert(
        functools.partial(str, Metric(
            'Memory', value, 'B',
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


@pytest.mark.parametrize('value, factor_type, raises, expected', [
    (1, 'decimal', False, (1.0, 'B')),
    (1 * 1000, 'decimal', False, (1.0, 'KB')),
])
def test_convert_automatic_value(value, factor_type, raises, expected):
    metric = Metric('metric', 10, 'B', display_unit_factor_type=factor_type)
    actual = metric.convert_automatic_value(value)
    assert actual == expected


@pytest.mark.parametrize('value, factor_type, expected', [
    ('1', 'decimal', '1'),
    ('1B', 'decimal', '1'),
    ('1KB', 'decimal', '1000'),
])
def test_convert_threshold(value, factor_type, expected):
    metric = Metric('metric', 10, 'B', display_unit_factor_type=factor_type)
    assert metric.convert_threshold(value) == expected


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
