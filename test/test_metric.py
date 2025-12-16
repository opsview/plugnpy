"""
Unit tests for PlugNPy metric.py
Copyright (C) 2003-2025 ITRS Group Ltd. All rights reserved
"""

import functools
import pytest

from plugnpy.exception import InvalidMetricThreshold
from plugnpy.metric import Metric
from .test_base import raise_or_assert


@pytest.mark.parametrize('value, si_bytes_conversion, display_format, raises, expected, convert_metric', [
    pytest.param(1024, False, '{name} is {value} {unit}', False, 'Memory is 1024.00 B', False, id="convert_false"),
    pytest.param(1024, False, '{value}{unit}', False, '1024.00B', False, id="display_format"),
    pytest.param(1024, False, '{bad} {wrong}', KeyError, None, False, id="wrong_display_format"),
    pytest.param(1024, False, '{name} is {value} {unit}', False, 'Memory is 1.00 KB', True, id="convert_si_units"),
    pytest.param(1000, True, '{name} is {value} {unit}', False, 'Memory is 1.00 KB', True, id="convert_non_si_units"),
    pytest.param('GREEN', False, '{name} is {value}', False, 'Memory is GREEN', False, id="str_value"),
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
    pytest.param(1, 1, 100, True, False, id="outside_ok"),
    pytest.param(0, 1, 100, True, True, id="outside_ko"),
    pytest.param(1, 1, 100, False, True, id="inside_ok"),
    pytest.param(0, 1, 100, False, False, id="inside_ko"),
])
def test_check_range(value, start, end, check_outside_range, expected):
    assert Metric._check_range(value, start, end, check_outside_range) == expected


@pytest.mark.parametrize('value, unit, si_bytes_conversion, raises, expected', [
    # bytes conversion IEC (International Electrotechnical Commission) units
    (1, 'B', False, False, (1.0, 'B')),
    (1024, 'B', False, False, (1.0, 'KB')),

    # bytes conversion SI (International System) units
    (1, 'B', True, False, (1.0, 'B')),
    (1e-3, 'B', True, False, (0.001, 'B')),
    (1e3, 'B', True, False, (1.0, 'KB')),
    (1e6, 'B', True, False, (1.0, 'MB')),
    (1e9, 'B', True, False, (1.0, 'GB')),
    (1e12, 'B', True, False, (1.0, 'TB')),
    (1e15, 'B', True, False, (1.0, 'PB')),
    (1e18, 'B', True, False, (1.0, 'EB')),

    # conversion SI units
    (1, 'W', True, False, (1.0, 'W')),
    (1e-3, 'Hz', True, False, (1.0, 'mHz')),
    (1e-6, 'W', True, False, (1.0, 'uW')),
    (1e-9, 'Hz', True, False, (1.0, 'nHz')),
    (1e-12, 's', True, False, (1.0, 'ps')),
    (1e3, 'Hz', True, False, (1.0, 'KHz')),
    (1e6, 'W', True, False, (1.0, 'MW')),
    (1e9, 'Hz', True, False, (1.0, 'GHz')),
    (86400 + 3600 + 60, 's', True, False, ("1d 1h 1m", '')),
    (45, 's', True, False, ("45s", '')),

    # no conversion
    (1, '', True, False, (1.0, '')),
    (1e3, '', True, False, (1000, '')),
    (1e-3, '', True, False, (0.001, '')),

    # invalid value
    ('a', '', True, Exception, None),
])
def test_convert_value(value, unit, si_bytes_conversion, raises, expected):
    raise_or_assert(
        functools.partial(Metric.convert_value, value, unit, si_bytes_conversion), raises, expected
    )


@pytest.mark.parametrize('value, si_bytes_conversion, raises, expected', [
    ('1', True, False, 1.0),
    ('1B', True, False, 1.0),
    ('1KB', True, False, 1000.0),
    ('1000m', True, False, 1.0),
    ('1', False, False, 1.0),
    ('1B', False, False, 1.0),
    ('1KB', False, False, 1024.0),
    ('', False, InvalidMetricThreshold, ''),
    ('KB', False, InvalidMetricThreshold, ''),
    ('-1KB', True, False, -1000.0),
])
def test_convert_threshold(value, si_bytes_conversion, raises, expected):
    raise_or_assert(
        functools.partial(Metric._convert_threshold, value, si_bytes_conversion), raises, expected
    )


@pytest.mark.parametrize('value, is_start, raises, expected', [
    pytest.param('~', False, False, Metric.P_INF, id="infinite"),
    pytest.param('~', True, False, Metric.N_INF, id="negative_infinite"),
    pytest.param('-10K', True, False, -10000.0, id="negative_prefix"),
    pytest.param('10', True, False, 10.0, id="no_prefix"),
    pytest.param('10K', True, False, 10000.0, id="prefix"),
    pytest.param('10S', True, InvalidMetricThreshold, None, id="wrong_prefix"),
])
def test_parse_threshold_limit(value, is_start, raises, expected):
    raise_or_assert(
        functools.partial(Metric._parse_threshold_limit, value, is_start, Metric.SI_UNIT_FACTOR), raises, expected
    )


@pytest.mark.parametrize('threshold, raises, expected', [
    pytest.param('@1:3', False, (1.0, 3.0, False), id="inside_range"),
    pytest.param('10', False, (0.0, 10.0, True), id="zero_start"),
    pytest.param('3:', False, (3.0, Metric.P_INF, True), id="infinite_end"),
    pytest.param('~:5', False, (Metric.N_INF, 5.0, True), id="normal_range"),
    pytest.param('bad', InvalidMetricThreshold, None, id="wrong_threshold"),
    pytest.param('1MB:2MB', False, (1000000.0, 2000000.0, True), id="identical_conversion_factors"),
    pytest.param('1KB:2MB', False, (1000.0, 2000000.0, True), id="different_conversion_factors"),
    pytest.param('-2:-1', False, (-2.0, -1.0, True), id="negative"),
    pytest.param('-2KB:-1KB', False, (-2000.0, -1000.0, True), id="negative_conversion_factors"),
])
def test_parse_threshold(threshold, raises, expected):
    raise_or_assert(functools.partial(Metric._parse_threshold, threshold, Metric.SI_UNIT_FACTOR), raises, expected)


@pytest.mark.parametrize('warning_threshold, critical_threshold, expected', [
    pytest.param('50:120', '30:150', 0, id="ok"),
    pytest.param('110:150', '90:170', 1, id="warning"),
    pytest.param('130:150', '110:170', 2, id="critical"),
])
def test_state(warning_threshold, critical_threshold, expected):
    assert Metric('Memory', 100, 'bytes', warning_threshold, critical_threshold).state == expected


def test_precision():
    metric = Metric('metric_name', 10.12345, '', summary_precision=3, perf_data_precision=2)
    assert '10.123' in str(metric)
    assert '10.12' in str(metric.perf_data)
    assert '10.12345' not in str(metric)
    assert '10.123' not in str(metric.perf_data)


@pytest.mark.parametrize('value, error_msg', [
    pytest.param(
        None, "Invalid value for performance data precision 'None': int() argument must be",
        id="no_value"),
    pytest.param(
        'abc',
        "Invalid value for performance data precision 'abc': invalid literal for int() with base 10: 'abc'",
        id="bad_int"),
])
def test_invalid_perf_data_precision(value, error_msg):
    with pytest.raises(Exception) as ex:
        Metric('metric_name', 10.12345, 'B', perf_data_precision=value)
    assert error_msg in str(ex.value)


@pytest.mark.parametrize('value, error_msg', [
    pytest.param(
        None,
        "Invalid value for summary precision 'None': int() argument must be a string",
        id="no_value"),
    pytest.param(
        'abc',
        "Invalid value for summary precision 'abc': invalid literal for int() with base 10: 'abc'",
        id="bad_int"),
])
def test_invalid_summary_precision(value, error_msg):
    with pytest.raises(Exception) as ex:
        Metric('metric_name', 10.12345, 'B', summary_precision=value)
    assert error_msg in str(ex.value)


def test_perf_data_type_conversion():
    metric = Metric('metric_name', '1', 'B')
    assert 'metric_name=1.00B' in str(metric.perf_data)
