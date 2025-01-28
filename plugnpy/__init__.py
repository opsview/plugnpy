"""plugnpy - A Simple Python Library for creating Opsview Opspack plugins"""

__version__ = '2.0.19'
__program_name__ = 'plugnpy'

from .check import Check
from .exception import ParamError, ParamErrorWithHelp, ResultError, AssumedOK, InvalidMetricThreshold, InvalidMetricName
from .metric import Metric
from .parser import Parser, ExecutionStyle

__all__ = [
    'Check',
    'ParamError', 'ParamErrorWithHelp', 'ResultError', 'AssumedOK', 'InvalidMetricThreshold', 'InvalidMetricName',
    'Metric',
    'Parser',
    'ExecutionStyle',
]
