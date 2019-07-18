"""
Check class, contains Check Object that controls the check execution.
"""

from __future__ import print_function
from .metric import Metric
from .exception import InvalidMetricName


class Check(object):
    """Object for defining and running Opsview Service Checks.

    Keyword Arguments:
        - state_type -- The string printed before the Service Check status (default: METRIC)
        - sep -- The string separating each metric's output (default: ', ')
    """
    STATUS = {0: 'OK', 1: 'WARNING', 2: 'CRITICAL', 3: 'UNKNOWN'}

    def __init__(self, state_type="METRIC", sep=', '):
        self.state_type = state_type
        self.sep = sep
        self.metrics = []

    def add_metric_obj(self, metric_obj):
        """Add a metric to the check's performance data from an existing Metric object"""
        self.add_metric(metric_obj.name,
                        metric_obj.value,
                        metric_obj.unit,
                        metric_obj.warning_threshold,
                        metric_obj.critical_threshold,
                        metric_obj.display_format,
                        metric_obj.display_in_perf,
                        metric_obj.display_in_summary,
                        metric_obj.display_name,
                        metric_obj.convert_metric,
                        metric_obj.si_bytes_conversion,
                        metric_obj.summary_precision,
                        metric_obj.perf_data_precision)

    def add_metric(self, name, value, unit='', warning_threshold='', critical_threshold='',
                   display_format='{name} is {value}{unit}', display_in_perf=True,
                   display_in_summary=True, display_name=None, convert_metric=None, si_bytes_conversion=False,
                   summary_precision=2, perf_data_precision=2):
        """Add a metric to the check's performance data.

        Keyword Arguments:
        - name -- Name of the Metric
        - value -- Value of the Metric (note: do not include unit of measure)
        - unit -- Unit of Measure of the Metric
        - warning_threshold -- Warning threshold for the Metric (default: '') - see Monitoring Plugins Development Guidelines
        - critical_threshold -- Critical threshold for the Metric (default: '') - see Monitoring Plugins Development Guidelines
        - display_format -- Formatting string to print the Metric (default: "{name} is {value} {unit}")
        - display_name -- Name to be used in friendly output (default: value of name)
        - display_in_summary -- Whether to print the metric in the summary (default: True)
        - display_in_perf -- Whether to print the metric in performance data (default: True)
        - convert_metric -- Whether to convert the metric value to a more human friendly unit (default: False)
        - si_bytes_conversion -- Whether to convert values using the SI standard, uses IEC by default (default: False)
        - precision -- The number of decimal places to round the metric value to (default 2)
        """

        if "'" in name:
            raise InvalidMetricName("Metric names cannot contain \"'\".")
        if "=" in name:
            raise InvalidMetricName("Metric names cannot contain \"=\".")

        metric = Metric(name, value, unit, warning_threshold or '', critical_threshold or '',
                        display_format=display_format, display_in_perf=display_in_perf,
                        display_in_summary=display_in_summary, display_name=display_name,
                        convert_metric=convert_metric, si_bytes_conversion=si_bytes_conversion,
                        summary_precision=summary_precision, perf_data_precision=perf_data_precision)
        self.metrics.append(metric)

    def add_message(self, message):
        """Add a message"""
        self.metrics[-1].message = message

    def exit(self, code, message):
        """Exits with specified message and specified exit status.
        Note: existing messages and metrics are discarded.
        """
        print("{0} {1} - {2}".format(self.state_type, Check.STATUS[code], message))
        exit(code)

    def exit_ok(self, message):
        """Exits with specified message and OK exit status.
        Note: existing messages and metrics are discarded.
        """
        self.exit(0, message)

    def exit_warning(self, message):
        """Exits with specified message and WARNING exit status.
        Note: existing messages and metrics are discarded.
        """
        self.exit(1, message)

    def exit_critical(self, message):
        """Exits with specified message and CRITICAL exit status.
        Note: existing messages and metrics are discarded.
        """
        self.exit(2, message)

    def exit_unknown(self, message):
        """Exits with specified message and UNKNOWN exit status.
        Note: existing messages and metrics are discarded.
        """
        self.exit(3, message)

    def final(self):
        """Calculates the final check output and exit status, prints and exits with the appropriate code."""
        human_results = [str(metric) for metric in self.metrics if metric.display_in_summary]
        perf_results = [metric.perf_data for metric in self.metrics if metric.display_in_perf]

        summary = "{0}{1}{2}".format(self.sep.join(human_results),
                                     ' | ' if perf_results else '',
                                     ' '.join(perf_results))

        exit_code = max([metric.state for metric in self.metrics])

        print("{0} {1} - {2}".format(self.state_type, Check.STATUS[exit_code], summary))
        exit(exit_code)
