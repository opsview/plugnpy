"""
Exceptions to be called by service check plugins when the appropriate situations arrive.
None of these have special behaviour.
"""


class ParamError(Exception):
    """To be thrown when user input causes the issue"""
    pass


class ResultError(Exception):
    """To be thrown when the API/Metric Check returns either no result (when this isn't expected)
    or returns a result that is essentially unusable.
"""
    pass


class AssumedOK(Exception):
    """To be thrown when the status of the check cannot be identified.
    This is usually used when the check requires the result of a previous run and this is the first run."""
    pass


class InvalidMetricThreshold(Exception):
    """To be thrown when you pass a metric threshold with wrong syntax"""
    pass
