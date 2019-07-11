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


@pytest.mark.parametrize('value, si_bytes_conversion, display_format, raises, expected, convert_metric', [
    (1024, False, '{name} is {value} {unit}', False, 'Memory is 1024.00 B', False),
    (1024, False, '{value}{unit}', False, '1024.00B', False),
    (1024, False, '{bad} {wrong}', KeyError, None, False),
    (1024, False, '{name} is {value} {unit}', False, 'Memory is 1.00 KB', True),
    (1000, True, '{name} is {value} {unit}', False, 'Memory is 1.00 KB', True),
],
    ids=[
        'convert_false',
        'display_format',
        'wrong_display_format',
        'convert_si_units',
        'convert_non_si_units',
])
def test_str(value, si_bytes_conversion, display_format, raises, expected, convert_metric):
    raise_or_assert(
        functools.partial(str, Metric(
            'Memory', value, 'B',
            display_format=display_format,
            convert_metric=convert_metric,
            si_bytes_conversion=si_bytes_conversion
        )),
        raises,
        expected
    )


@pytest.mark.parametrize('value, start, end, check_outside_range, expected', [
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


@pytest.mark.parametrize('value, unit, conversion_factor, expected', [
    # bytes conversion IEC (International Electrotechnical Commission) units
    (1, 'B', 1024, (1.0, 'B')),
    (1024, 'B', 1024, (1.0, 'KB')),

    # bytes conversion SI (International System) units
    (1, 'B', 1000, (1.0, 'B')),
    (1e3, 'B', 1000, (1.0, 'KB')),
    (1e6, 'B', 1000, (1.0, 'MB')),
    (1e9, 'B', 1000, (1.0, 'GB')),
    (1e12, 'B', 1000, (1.0, 'TB')),
    (1e15, 'B', 1000, (1.0, 'PB')),
    (1e18, 'B', 1000, (1.0, 'EB')),

    # conversion SI units
    (1, '', 1000, (1.0, '')),
    (1e-3, '', 1000, (1.0, 'm')),
    (1e-6, '', 1000, (1.0, 'u')),
    (1e-9, '', 1000, (1.0, 'n')),
    (1e-12, '', 1000, (1.0, 'p')),
    (1e3, '', 1000, (1.0, 'K')),
    (1e6, '', 1000, (1.0, 'M')),
    (1e9, '', 1000, (1.0, 'G')),
    (1e12, '', 1000, (1.0, 'T')),
])
def test_convert_automatic_value(value, unit, conversion_factor, expected):
    actual = Metric.convert_automatic_value(value, unit, conversion_factor)
    assert actual == expected


@pytest.mark.parametrize('value, si_bytes_conversion, raises, expected', [
    ('1', True, False, '1.00'),
    ('1B', True, False, '1.00'),
    ('1KB', True, False, '1000.00'),
    ('1000m', True, False, '1.00'),
    ('1', False, False, '1.00'),
    ('1B', False, False, '1.00'),
    ('1KB', False, False, '1024.00'),
    ('', False, InvalidMetricThreshold, ''),
    ('KB', False, InvalidMetricThreshold, ''),
])
def test_convert_threshold(value, si_bytes_conversion, raises, expected):
    raise_or_assert(
        functools.partial(Metric('metric', 10, 'B', si_bytes_conversion=si_bytes_conversion).convert_threshold,
                          value), raises, expected
    )


@pytest.mark.parametrize('value, is_start, raises, expected', [
    ('~', False, False, Metric.P_INF),
    ('~', True, False, Metric.N_INF),
    ('10', True, False, 10.0),
    ('10K', True, False, "10000.00"),
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


@pytest.mark.parametrize('threshold, raises, expected', [
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


@pytest.mark.parametrize('warning_threshold, critical_threshold, expected', [
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
