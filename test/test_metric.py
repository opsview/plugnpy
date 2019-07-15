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
], ids=[
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
    assert Metric._check(value, start, end, check_outside_range) == expected


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
def test_convert_value(value, unit, conversion_factor, expected):
    actual = Metric.convert_value(value, unit, conversion_factor)
    assert actual == expected


@pytest.mark.parametrize('value, conversion_factor, raises, expected', [
    ('1', 1000, False, '1.00'),
    ('1B', 1000, False, '1.00'),
    ('1KB', 1000, False, '1000.00'),
    ('1000m', 1000, False, '1.00'),
    ('1', 1024, False, '1.00'),
    ('1B', 1024, False, '1.00'),
    ('1KB', 1024, False, '1024.00'),
    ('', 1024, InvalidMetricThreshold, ''),
    ('KB', 1024, InvalidMetricThreshold, ''),
])
def test_convert_threshold(value, conversion_factor, raises, expected):
    raise_or_assert(
        functools.partial(Metric._convert_threshold, value, conversion_factor), raises, expected
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
        functools.partial(Metric._parse_threshold_limit, value, is_start, Metric.SI_UNIT_FACTOR), raises, expected
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
    raise_or_assert(functools.partial(Metric._parse_threshold, threshold, Metric.SI_UNIT_FACTOR), raises, expected)


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

def test_precision():
    metric = Metric('metric_name', 10.12345, 'B', precision=3)
    assert '10.123' in str(metric)
    assert '10.12345' not in str(metric)

    with pytest.raises(Exception) as ex:
        Metric('metric_name', 10.12345, 'B', precision='a')
        assert "Invalid value for precision" in ex.value
