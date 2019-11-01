"""plugnpy - A Simple Python Library for creating Opsview Opspack plugins"""

__version__ = '2.0.2'
__program_name__ = 'plugnpy'

from .check import Check
from .exception import ParamError, ResultError, AssumedOK, InvalidMetricThreshold, InvalidMetricName
from .parser import Parser
from .metric import Metric
from .cachemanager import CacheManagerClient, CacheManagerUtils
from .utils import hash_string

__all__ = ['Check', 'ParamError', 'ResultError', 'AssumedOK', 'InvalidMetricThreshold', 'InvalidMetricName', 'Parser',
           'Metric', 'CacheManagerClient', 'CacheManagerUtils', 'hash_string']
