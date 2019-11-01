import os
import functools
import pytest
from socket import error as SocketError
from plugnpy import CacheManagerUtils, CacheManagerClient, ResultError
from .test_base import raise_or_assert


@pytest.mark.parametrize('no_cachemanager, cachemanager_host, raises, expected', [
    (True, 'host', None, False),
    (True, '', None, False),
    (False, 'host', None, True),
    (False, '', ResultError, None),
])
def test_is_required(no_cachemanager, cachemanager_host, raises, expected):
    raise_or_assert(
        functools.partial(CacheManagerUtils._is_required, no_cachemanager, cachemanager_host),
        raises,
        expected
    )


@pytest.mark.parametrize(
    'no_cachemanager, cachemanager_host, get_data_retval, get_data_side_effect, raises, expected',
    [
        (True, 'host', {'data': None, 'lock': None}, None, None, '4'),
        (True, '', {'data': None, 'lock': None}, None, None, '4'),
        (False, '', {'data': None, 'lock': None}, None, ResultError, None),
        (False, 'host', {'data': None, 'lock': None}, None, ResultError, None),
        (False, 'host', {'data': '"data"', 'lock': None}, None, None, 'data'),
        (False, 'host', {'data': '"data"', 'lock': None}, SocketError, ResultError, 'data'),
        (False, 'host', {'data': None, 'lock': True}, None, None, '4'),
    ]
)
def test_get_via_cachemanager(mocker, no_cachemanager, cachemanager_host, get_data_retval, get_data_side_effect, raises,
                              expected):
    host = os.environ['OPSVIEW_CACHE_MANAGER_HOST'] = cachemanager_host
    port = os.environ['OPSVIEW_CACHE_MANAGER_PORT'] = 'some_port'
    namespace = os.environ['OPSVIEW_CACHE_MANAGER_NAMESPACE'] = 'some_namespace'

    func = lambda x: str(x**2)

    CacheManagerClient.get_data = mocker.Mock(return_value=get_data_retval, side_effect=get_data_side_effect)
    CacheManagerClient.set_data = mocker.Mock()

    raise_or_assert(
        functools.partial(CacheManagerUtils.get_via_cachemanager, no_cachemanager, 'key', func, 2),
        raises,
        expected
    )
