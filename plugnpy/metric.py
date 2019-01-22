"""
Metric Class.
"""
from .exceptions import InvalidMetricThreshold
import re

# Prefixes for units
FACTOR_BASE_NUMBER = {
    'decimal': 1000,
    'bytes': 1024
}
DISPLAY_UNIT_FACTORS = {
    '': {'decimal': 1.0, 'bytes': 1.0},
    'B': {'decimal': 1.0, 'bytes': 1.0},
    'p': {'decimal': FACTOR_BASE_NUMBER['decimal']**4, 'bytes': FACTOR_BASE_NUMBER['bytes']**4},  # pico
    'n': {'decimal': FACTOR_BASE_NUMBER['decimal']**3, 'bytes': FACTOR_BASE_NUMBER['bytes']**3},  # nano
    'u': {'decimal': FACTOR_BASE_NUMBER['decimal']**2, 'bytes': FACTOR_BASE_NUMBER['bytes']**2},  # micro
    'm': {'decimal': FACTOR_BASE_NUMBER['decimal'], 'bytes': FACTOR_BASE_NUMBER['bytes']},  # mili
    'K': {'decimal': 1.0 / FACTOR_BASE_NUMBER['decimal'], 'bytes': 1.0 / FACTOR_BASE_NUMBER['bytes']},  # kilo
    'M': {'decimal': 1.0 / FACTOR_BASE_NUMBER['decimal']**2, 'bytes': 1.0 / FACTOR_BASE_NUMBER['bytes']**2},  # mega
    'G': {'decimal': 1.0 / FACTOR_BASE_NUMBER['decimal']**3, 'bytes': 1.0 / FACTOR_BASE_NUMBER['bytes']**3},  # giga
    'T': {'decimal': 1.0 / FACTOR_BASE_NUMBER['decimal']**4, 'bytes': 1.0 / FACTOR_BASE_NUMBER['bytes']**4},  # tera
}


class Metric(object):
    """Object to represent Metrics added to a Check object.

    Keyword Arguments:
        - name -- Name of the Metric
        - value -- Value of the Metric (note: do not include unit of measure)
        - unit -- Unit of Measure of the Metric
        - warning_threshold -- Warning threshold for the Metric (default: '')
        - critical_threshold -- Critical threshold for the Metric (default: '')
        - display_unit_factor_type -- Whether to convert Bytes in to Decimal or Binary formats  (default: 'bytes')
        - display_format -- Formatting string to print the Metric (default: "{name} is {value} {unit}")
        - convert_metric -- Whether to convert the metric in to a friendly form (default: True)
        - display_name -- Name to be used in friendly output (default: value of name)
        - display_in_perf -- Whether to print the metric in performance variable (default: True)
        """

    P_INF = float('inf')
    N_INF = float('-inf')

    def __init__(
            self, name, value, unit,
            warning_threshold='',
            critical_threshold='',
            display_unit_factor_type='bytes',
            display_format="{name} is {value} {unit}",
            convert_metric=True,
            display_name=None,
            display_in_summary=True,
            display_in_perf=True,
    ):
        self.name = name
        self.display_in_summary = display_in_summary
        self.display_in_perf = display_in_perf
        if not display_name:
            display_name = self.name
        self.display_name = display_name
        self.value = value
        self.unit = unit

        self.display_unit_factor_type = display_unit_factor_type
        self.display_format = display_format
        self.message = None
        self.convert_metric = convert_metric

        # if convert_metric:
        #     if warning_threshold:
        #         warning_threshold = self.convert_threshold(warning_threshold)
        #     if critical_threshold:
        #         critical_threshold = self.convert_threshold(critical_threshold)
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

        if self.critical_threshold and self.check(value, *self.parse_threshold(self.critical_threshold)):
            self.state = 2
        elif self.warning_threshold and self.check(value, *self.parse_threshold(self.warning_threshold)):
            self.state = 1
        else:
            self.state = 0

    def convert_automatic_value(self, value):
        """Converts values with the right prefix for display"""
        for key in ('T', 'G', 'M', 'K'):
            if 1 / DISPLAY_UNIT_FACTORS[key][self.display_unit_factor_type] <= float(value):
                return float(value) * DISPLAY_UNIT_FACTORS[key][self.display_unit_factor_type], '{0}{1}'.format(key, self.unit)
        return value, self.unit

    def convert_threshold(self, value):
        split_list = re.split(r"([a-z])", str(value), 1, flags=re.I)
        value = int(split_list[0])
        if len(split_list) > 1:
            try:
                unit = "".join(split_list[1:])[0]
                return str(int(value / DISPLAY_UNIT_FACTORS[unit][self.display_unit_factor_type]))
            except Exception as e:
                raise InvalidMetricThreshold(e)
        else:
            return str(value)

    def __str__(self):
        if self.message:
            return self.message
        name = self.display_name
        value = self.value
        unit = self.unit

        if self.convert_metric:
            if self.unit == 'B':
                value, unit = self.convert_automatic_value(self.value)
                if unit != 'B':
                    value = "{0:.2f}".format(value)
        return self.display_format.format(**{'name': name, 'value': value, 'unit': unit})

    def parse_threshold_limit(self, value, is_start):
        """Parses a numeric string with a unit prefix e.g. 10 > 10.0, 10m > 0.001, 10M > 1000000.0, ~ > -inf/inf."""
        if value == '~':  # Infinite values
            if is_start:
                return self.N_INF
            else:
                return self.P_INF
        if value[-1].isdigit():  # No unit prefix
            return float(value)
        elif value[-1] == 'a':  # Bytes unit prefix
            return float(value[:-1])
        else:  # Decimal unit prefix
            return self.convert_threshold(value)

    def parse_threshold(self, threshold):
        """
        Parse threshold and return the range and whether we alert if value is out of range or in the range.
        See: https://nagios-plugins.org/doc/guidelines.html#THRESHOLDFORMAT
        """
        try:
            check_outside_range = True
            if threshold.startswith('@'):
                check_outside_range = False
                threshold = threshold[1:]
            if ':' not in threshold:
                start = 0.0
                end = self.parse_threshold_limit(threshold, False)
            elif threshold.endswith(':'):
                start = self.parse_threshold_limit(threshold[:-1], True)
                end = self.P_INF
            else:
                unparsed_start, unparsed_end = threshold.split(':')
                start = self.parse_threshold_limit(unparsed_start, True)
                end = self.parse_threshold_limit(unparsed_end, False)
            return start, end, check_outside_range
        except Exception as e:
            raise InvalidMetricThreshold(str(e))

    @staticmethod
    def check(value, start, end, check_outside_range):
        """Check whether the value is inside/outside the range."""
        value, start, end = float(value), float(start), float(end)
        outside_range = value < start or value > end
        if check_outside_range:
            return outside_range
        else:
            return not outside_range
