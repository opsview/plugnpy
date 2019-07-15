"""
Metric Class.
"""
from .exception import InvalidMetricThreshold


class Metric(object):
    """Object to represent Metrics added to a Check object.

    Keyword Arguments:
        - name -- Name of the Metric
        - value -- Value of the Metric (note: do not include unit of measure)
        - unit -- Unit of Measure of the Metric
        - warning_threshold -- Warning threshold for the Metric (default: '')
        - critical_threshold -- Critical threshold for the Metric (default: '')
        - display_format -- Formatting string to print the Metric (default: "{name} is {value} {unit}")
        - display_name -- Name to be used in friendly output (default: value of name)
        - display_in_summary -- Whether to print the metric in the summary (default: True)
        - display_in_perf -- Whether to print the metric in performance data (default: True)
        - convert_metric -- Whether to convert the metric value to a more human friendly unit (default: False)
        - si_bytes_conversion -- Whether to convert values using the SI standard, uses IEC by default (default: False)
        - precision -- The number of decimal places to round the metric value to (default 2)
        """

    P_INF = float('inf')
    N_INF = float('-inf')

    STATUS_OK = 0
    STATUS_WARNING = 1
    STATUS_CRITICAL = 2
    STATUS_UNKNOWN = 3

    SI_UNIT_FACTOR = 1000
    IEC_UNIT_FACTOR = 1024

    UNIT_BYTES = 'B'
    UNIT_PICO = 'p'
    UNIT_NANO = 'n'
    UNIT_MICRO = 'u'
    UNIT_MILLI = 'm'
    UNIT_KILO = 'K'
    UNIT_MEGA = 'M'
    UNIT_GIGA = 'G'
    UNIT_TERA = 'T'
    UNIT_PETA = 'P'
    UNIT_EXA = 'E'

    UNIT_PREFIXES_P = (UNIT_EXA, UNIT_PETA, UNIT_TERA, UNIT_GIGA, UNIT_MEGA, UNIT_KILO)
    UNIT_PREFIXES_N = (UNIT_MILLI, UNIT_MICRO, UNIT_NANO, UNIT_PICO)

    # Prefixes for units
    DISPLAY_UNIT_FACTORS = {
        UNIT_BYTES: lambda factor: 1.0,
        UNIT_PICO: lambda factor: factor ** 4,
        UNIT_NANO: lambda factor: factor ** 3,
        UNIT_MICRO: lambda factor: factor ** 2,
        UNIT_MILLI: lambda factor: factor,
        UNIT_KILO: lambda factor: 1.0 / factor,
        UNIT_MEGA: lambda factor: 1.0 / factor ** 2,
        UNIT_GIGA: lambda factor: 1.0 / factor ** 3,
        UNIT_TERA: lambda factor: 1.0 / factor ** 4,
        UNIT_PETA: lambda factor: 1.0 / factor ** 5,
        UNIT_EXA: lambda factor: 1.0 / factor ** 6,
    }

    def __init__(
            self, name, value, unit,
            warning_threshold='',
            critical_threshold='',
            display_format="{name} is {value}{unit}",
            display_name=None,
            display_in_summary=True,
            display_in_perf=True,
            convert_metric=False,
            si_bytes_conversion=False,
            precision=2
    ):
        self.name = name
        self.value = value
        self.unit = unit
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.display_in_summary = display_in_summary
        self.display_in_perf = display_in_perf
        self.display_format = display_format
        self.message = None
        self.convert_metric = convert_metric
        self.si_bytes_conversion = si_bytes_conversion
        self.state = Metric.evaluate(value, warning_threshold, critical_threshold, si_bytes_conversion)

        if not display_name:
            display_name = self.name
        self.display_name = display_name

        try:
            self.precision = int(precision)
        except (ValueError, TypeError) as ex:
            raise Exception("Invalid value for precision '{0}': {1}".format(precision, ex))

    def __str__(self):
        if self.message:
            return self.message
        unit = self.unit
        value = self.value

        if self.convert_metric:
            value, unit = Metric.convert_value(self.value, self.unit, self.si_bytes_conversion)

        # try to convert value to precision specified if it's a number
        try:
            value = float(value)
            value = "{0:.{1}f}".format(value, self.precision)
        except (ValueError, TypeError):
            pass

        return self.display_format.format(**{'name': self.display_name, 'value': value, 'unit': unit})

    @staticmethod
    def evaluate(value, warning_threshold, critical_threshold, si_bytes_conversion=False):
        """return the status code of a service check given the value, warning and critical thresholds"""
        status = Metric.STATUS_OK
        if warning_threshold:
            if Metric._check_range(value, *Metric._parse_threshold(warning_threshold, si_bytes_conversion)):
                status = Metric.STATUS_WARNING
        if critical_threshold:
            if Metric._check_range(value, *Metric._parse_threshold(critical_threshold, si_bytes_conversion)):
                status = Metric.STATUS_CRITICAL
        return status

    @staticmethod
    def convert_value(value, unit, si_bytes_conversion=False):
        """Converts values with the right prefix for display."""
        try:
            value = float(value)
        except (ValueError, TypeError) as ex:
            raise Exception("Invalid value for value '{0}': {1}".format(value, ex))

        conversion_factor = Metric._get_conversion_factor(unit, si_bytes_conversion)
        keys = Metric.UNIT_PREFIXES_N if unit != Metric.UNIT_BYTES and value < 1 else Metric.UNIT_PREFIXES_P

        for key in keys:
            multiplication_factor = Metric.DISPLAY_UNIT_FACTORS[key](conversion_factor)
            if 1.0 / multiplication_factor <= value:
                return value * multiplication_factor, '{0}{1}'.format(key, unit)
        return value, unit

    @staticmethod
    def _get_conversion_factor(unit, si_bytes_conversion):
        if unit == Metric.UNIT_BYTES and not si_bytes_conversion:
            return Metric.IEC_UNIT_FACTOR
        return Metric.SI_UNIT_FACTOR

    @staticmethod
    def _convert_threshold(value, si_bytes_conversion):
        """Convert threshold value."""
        value = str(value)
        unit = value.lstrip('.1234567890')
        if unit:
            value = value[:-len(unit)]

        try:
            value = float(value)
        except (ValueError, TypeError) as exp:
            raise InvalidMetricThreshold("Invalid metric threshold: {0}.".format(exp))

        if unit:
            try:
                unit_prefix = unit[0]
                conversion_factor = Metric._get_conversion_factor(unit[-1], si_bytes_conversion)
                value = value / Metric.DISPLAY_UNIT_FACTORS[unit_prefix](conversion_factor)
            except KeyError as exp:
                raise InvalidMetricThreshold("Invalid metric threshold: {0}.".format(exp))
        return value

    @staticmethod
    def _parse_threshold_limit(value, is_start, si_bytes_conversion):
        """Parses a numeric string with a unit prefix e.g. 10 -> 10.0, 10m -> 0.001, 10M -> 1000000.0, ~ -> -inf/inf."""
        if value == '~':  # Infinite values
            if is_start:
                return Metric.N_INF
            return Metric.P_INF
        if value[-1].isdigit():  # No unit suffix
            return float(value)
        return Metric._convert_threshold(value, si_bytes_conversion)

    @staticmethod
    def _parse_threshold(threshold, si_bytes_conversion):
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
                end = Metric._parse_threshold_limit(threshold, False, si_bytes_conversion)
            elif threshold.endswith(':'):
                start = Metric._parse_threshold_limit(threshold[:-1], True, si_bytes_conversion)
                end = Metric.P_INF
            else:
                unparsed_start, unparsed_end = threshold.split(':')
                start = Metric._parse_threshold_limit(unparsed_start, True, si_bytes_conversion)
                end = Metric._parse_threshold_limit(unparsed_end, False, si_bytes_conversion)
            return start, end, check_outside_range
        except Exception as exp:
            raise InvalidMetricThreshold("Invalid metric threshold: {0}.".format(exp))

    @staticmethod
    def _check_range(value, start, end, check_outside_range):
        """Check whether the value is inside/outside the range."""
        value, start, end = float(value), float(start), float(end)
        outside_range = value < start or value > end
        if check_outside_range:
            return outside_range
        return not outside_range
