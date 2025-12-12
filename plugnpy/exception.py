"""
Exceptions to be called by service check plugins when the appropriate situations arrive.
None of these have special behaviour.
Copyright (C) 2003-2025 ITRS Group Limited. All rights reserved
"""


class ParamErrorWithHelp(Exception):
    """To be thrown when user input causes the issue but the help text also needs to be printed"""


class ParamError(Exception):
    """To be thrown when user input causes the issue"""


class ResultError(Exception):
    """To be thrown when the API/Metric Check returns either no result (when this isn't expected)
    or returns a result that is essentially unusable."""


class AssumedOK(Exception):
    """To be thrown when the status of the check cannot be identified.
    This is usually used when the check requires the result of a previous run and this is the first run."""


class InvalidMetricThreshold(Exception):
    """To be thrown when you pass a metric threshold with wrong syntax"""


class InvalidMetricName(Exception):
    """To be thrown when you pass an invalid metric name."""


class StateManagerStoreError(Exception):
    """ Used to report a State Manager error """
