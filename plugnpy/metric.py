"""
Metric Class.
"""
import re
from .exception import InvalidMetricThreshold


# Prefixes for units
DISPLAY_UNIT_FACTORS = {
    'B': lambda factor: 1.0,
    'p': lambda factor: factor ** 4,  # pico
    'n': lambda factor: factor ** 3,  # nano
    'u': lambda factor: factor ** 2,  # micro
    'm': lambda factor: factor,  # mili
    'K': lambda factor: 1.0 / factor,  # kilo
    'M': lambda factor: 1.0 / factor ** 2,  # mega
    'G': lambda factor: 1.0 / factor ** 3,  # giga
    'T': lambda factor: 1.0 / factor ** 4,  # tera
}


class Metric(object):
    """Object to represent Metrics added to a Check object.

    Keyword Arguments:
        - name -- Name of the Metric
        - value -- Value of the Metric (note: do not include unit of measure)
        - unit -- Unit of Measure of the Metric
        - warning_threshold -- Warning threshold for the Metric (default: '')
        - critical_threshold -- Critical threshold for the Metric (default: '')
        - display_format -- Formatting string to print the Metric (default: "{name} is {value} {unit}")
        - convert_metric -- Whether to convert the metric in to a friendly form (default: True)
        - display_name -- Name to be used in friendly output (default: value of name)
        - display_in_perf -- Whether to print the metric in performance variable (default: True)
        """

    P_INF = float('inf')
    N_INF = float('-inf')

    BYTES_UNIT = 'B'

    def __init__(
            self, name, value, unit,
            warning_threshold='',
            critical_threshold='',
            display_format="{name} is {value}{unit}",
            display_name=None,
            display_in_summary=True,
            display_in_perf=True,
            convert_metric=False,
            si_bytes_conversion=False
    ):
        self.name = name
        self.display_in_summary = display_in_summary
        self.display_in_perf = display_in_perf
        if not display_name:
            display_name = self.name
        self.display_name = display_name
        self.value = value
        self.unit = unit

        self.display_format = display_format
        self.message = None
        self.convert_metric = convert_metric

        bytes_conversion_factor = 1000 if si_bytes_conversion else 1024
        self.conversion_factor = bytes_conversion_factor if self.unit == self.BYTES_UNIT else 1000

        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

        if self.critical_threshold and self.check(value, *self.parse_threshold(self.critical_threshold)):
            self.state = 2
        elif self.warning_threshold and self.check(value, *self.parse_threshold(self.warning_threshold)):
            self.state = 1
        else:
            self.state = 0


    def convert_automatic_value(self, value):
        """Converts values with the right prefix for display."""

        if self.unit != self.BYTES_UNIT and value < 1:
            keys = ('m', 'u', 'n', 'p')
        else:
            keys = ('T', 'G', 'M', 'K')

        for key in keys:
            multiplication_factor = DISPLAY_UNIT_FACTORS[key](self.conversion_factor)
            if 1.0 / multiplication_factor <= value:
                return value * multiplication_factor, '{0}{1}'.format(key, self.unit)
        return value, self.unit

    def convert_threshold(self, value):
        """Convert threshold value."""
        split_list = re.split(r"([a-z])", str(value), 1, flags=re.I)
        value = float(split_list[0])
        if len(split_list) > 1:
            try:
                unit = "".join(split_list[1:])[0]
                value = value / DISPLAY_UNIT_FACTORS[unit](self.conversion_factor)
            except Exception as exp:
                raise InvalidMetricThreshold(exp)
        return "{0:.2f}".format(value)

    def __str__(self):
        if self.message:
            return self.message
        name = self.display_name
        unit = self.unit
        value = self.value

        if self.convert_metric:
            value, unit = self.convert_automatic_value(self.value)

        value = "{0:.2f}".format(value)

        return self.display_format.format(**{'name': name, 'value': value, 'unit': unit})

    def parse_threshold_limit(self, value, is_start):
        """Parses a numeric string with a unit prefix e.g. 10 > 10.0, 10m > 0.001, 10M > 1000000.0, ~ > -inf/inf."""
        if value == '~':  # Infinite values
            if is_start:
                return self.N_INF
            return self.P_INF
        if value[-1].isdigit():  # No unit suffix
            return float(value)
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
        except Exception as exp:
            raise InvalidMetricThreshold("Invalid metric threshold: {0}.".format(exp))

    @staticmethod
    def check(value, start, end, check_outside_range):
        """Check whether the value is inside/outside the range."""
        value, start, end = float(value), float(start), float(end)
        outside_range = value < start or value > end
        if check_outside_range:
            return outside_range
        return not outside_range
