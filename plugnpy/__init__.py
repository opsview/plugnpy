"""plugnpy - A Simple Python Library for creating Opsview Opspack plugins"""

__version__ = '2.0.4'
__program_name__ = 'plugnpy'

from .check import Check
from .exception import ParamError, ParamErrorWithHelp, ResultError, AssumedOK, InvalidMetricThreshold, InvalidMetricName
from .parser import Parser
from .metric import Metric
from .cachemanager import CacheManagerClient, CacheManagerUtils
from .utils import hash_string

__all__ = [
    'Check', 'ParamError', 'ParamErrorWithHelp', 'ResultError', 'AssumedOK', 'InvalidMetricThreshold',
    'InvalidMetricName', 'Parser', 'Metric', 'CacheManagerClient', 'CacheManagerUtils', 'hash_string'
]
