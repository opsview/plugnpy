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
    CacheManagerUtils.host = cachemanager_host
    CacheManagerUtils.port = 'some_port'
    CacheManagerUtils.namespace = 'some_namespace'

    func = lambda x: str(x**2)

    CacheManagerClient.get_data = mocker.Mock(return_value=get_data_retval, side_effect=get_data_side_effect)
    CacheManagerClient.set_data = mocker.Mock()

    raise_or_assert(
        functools.partial(CacheManagerUtils.get_via_cachemanager, no_cachemanager, 'key', 900, func, 2),
        raises,
        expected
    )

def test_get_via_cachemanager_exception(mocker):
    CacheManagerUtils.host = 'host'
    CacheManagerUtils.port = 'some_port'
    CacheManagerUtils.namespace = 'some_namespace'

    def func(error):
        raise Exception(error)

    CacheManagerClient.get_data = mocker.Mock(return_value={'data': None, 'lock': True})
    CacheManagerClient.set_data = mocker.Mock()

    raise_or_assert(
        functools.partial(CacheManagerUtils.get_via_cachemanager, False, 'key', 900, func, "Something went wrong"),
        False,
        {'error': 'Something went wrong'}
    )

def test_set_data(mocker):
    CacheManagerUtils.host = 'host'
    CacheManagerUtils.port = 'some_port'
    CacheManagerUtils.namespace = 'some_namespace'
    CacheManagerUtils.client = None
    expected = 'data'
    CacheManagerClient.set_data = mocker.Mock(return_value=expected)

    assert CacheManagerUtils.client == None
    actual = CacheManagerUtils.set_data('key', {'some': 'data'}, 900)
    assert actual == expected

    # after call client will be initialised
    assert CacheManagerUtils.client != None
    actual = CacheManagerUtils.set_data('key', {'some': 'data'}, 900)
    assert actual == expected


# generated with https://emn178.github.io/online-tools/sha256.html
@pytest.mark.parametrize(
    'arg1, arg2, arg3, expected',
    [
        ('foo', 'bar', 'baz', 'c851d6b72c3403e8b8e2f6cbacaa2408fd5cc3b4d6ba4c3d9af7ef8d9c1dca29'),
        ('foo', 'bar', 'b#az', '69a23c03596c3910e13fcbcb1e8dec0bf0187f78b9bdef8b89ced3b358cfe9d7'),
        ('foo', 'bar', r'b\#az', 'ae4d9cb53b330c479b9ebe734afd1b84aec2f96e75acf66c59863d773c9cfc81'),
    ]
)
def test_generate_key(arg1, arg2, arg3, expected):
    actual = CacheManagerUtils.generate_key(arg1, arg2, arg3)
    assert actual == expected
