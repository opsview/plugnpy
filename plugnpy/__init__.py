"""plugnpy - A Simple Python Library for creating Opsview Opspack plugins"""

__version__ = '1.0.0'
__release__ = '1'
__program_name__ = 'plugnpy'

from .check import Check
from .exception import ParamError, ResultError, AssumedOK, InvalidMetricThreshold, InvalidMetricName
from .parser import Parser
from .metric import Metric
