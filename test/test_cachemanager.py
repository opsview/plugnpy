"""
Unit tests for PlugNPy cachemanager.py
Copyright (C) 2003-2025 ITRS Group Ltd. All rights reserved
"""

import functools
import json
import pytest

from socket import error as SocketError
from plugnpy.cachemanager import CacheManagerUtils, CacheManagerClient
from plugnpy.exception import ResultError
from .test_base import raise_or_assert


HOST = 'a.host'
PORT = 1234
NAMESPACE = 'some-namespace'
KEY = 'key'
TTL = 99
DATA = 'foodata' * 100
MAX_WAIT = 42
VALUE = '{"value": 2112}'
PATH = '/cachemanager/path'
BODY = json.dumps({'other': 'foo', 'data': DATA})


@pytest.fixture
def cmutils(mocker):
    mocker.patch.object(CacheManagerUtils, 'host', HOST)
    mocker.patch.object(CacheManagerUtils, 'port', PORT)
    mocker.patch.object(CacheManagerUtils, 'namespace', NAMESPACE)
    utils = CacheManagerUtils()
    yield utils


@pytest.fixture
def cmclient(mocker):
    mock_http_client = mocker.patch('plugnpy.cachemanager.HTTPClient')
    client = CacheManagerClient(HOST, PORT, NAMESPACE)
    yield client


@pytest.mark.parametrize('no_cachemanager, cachemanager_host, raises, expected', [
    pytest.param(True, HOST, None, False, id="no_cachemanager"),
    pytest.param(True, '', None, False, id="no_cachemanager_no_cmhost"),
    pytest.param(False, HOST, None, True, id="use_cachemanager"),
    pytest.param(False, '', ResultError, None, id="use_cachemanager_no_cmhost"),
])
def test_cache_manager_utils_is_required(no_cachemanager, cachemanager_host, raises, expected):
    raise_or_assert(
        functools.partial(CacheManagerUtils._is_required, no_cachemanager, cachemanager_host),
        raises,
        expected
    )


@pytest.mark.parametrize(
    'no_cachemanager, cachemanager_host, get_data_retval, get_data_side_effect, raises, expected',
    [
        pytest.param(True, HOST, {'data': None, 'lock': None}, None, None, '4', id="no_cachemanager"),
        pytest.param(True, '', {'data': None, 'lock': None}, None, None, '4', id="no_cachemanager_no_host"),
        pytest.param(False, '', {'data': None, 'lock': None}, None, ResultError, None, id="no_host"),
        pytest.param(False, HOST, {'data': None, 'lock': None}, None, ResultError, None, id="no_data_no_lock"),
        pytest.param(False, HOST, {'data': '"data"', 'lock': None}, None, None, 'data', id="data_success"),
        pytest.param(False, HOST, {'data': '"data"', 'lock': None}, SocketError, ResultError, 'data', id="socket_error"),
        pytest.param(False, HOST, {'data': None, 'lock': True}, None, None, '4', id="func_success"),
    ]
)
def test_cache_manager_utils_get_via_cachemanager(
        no_cachemanager, cachemanager_host, get_data_retval, get_data_side_effect, raises, expected,
        mocker, cmutils,
):
    def func(x): return str(x**2)

    cmutils._initialise_client()
    mocker.patch.object(cmutils.client, 'get_data', return_value=get_data_retval, side_effect=get_data_side_effect)
    mocker.patch.object(cmutils.client, 'set_data')

    raise_or_assert(
        functools.partial(cmutils.get_via_cachemanager, no_cachemanager, KEY, 900, func, 2),
        raises,
        expected
    )


def test_cache_manager_utils_get_via_cachemanager_exception(mocker, cmutils):

    def func(error):
        raise Exception(error)

    cmutils._initialise_client()
    mocker.patch.object(cmutils.client, 'get_data', return_value={'data': None, 'lock': True})
    mocker.patch.object(cmutils.client, 'set_data')

    raise_or_assert(
        functools.partial(cmutils.get_via_cachemanager, False, KEY, 900, func, "Something went wrong"),
        False,
        {'error': 'Something went wrong'}
    )


def test_cache_manager_utils_set_data(mocker, cmutils):
    expected = DATA
    mocker.patch.object(cmutils.client, 'set_data', return_value=expected)
    actual = cmutils.set_data(KEY, {'some': DATA}, 900)
    assert actual == expected


# generated with https://emn178.github.io/online-tools/sha256.html
@pytest.mark.parametrize(
    'arg1, arg2, arg3, expected',
    [
        pytest.param('foo', 'bar', 'baz', 'c851d6b72c3403e8b8e2f6cbacaa2408fd5cc3b4d6ba4c3d9af7ef8d9c1dca29', id="baz"),
        pytest.param('foo', 'bar', 'b#az', '69a23c03596c3910e13fcbcb1e8dec0bf0187f78b9bdef8b89ced3b358cfe9d7', id="b#az"),
        pytest.param('foo', 'bar', r'b\#az', 'ae4d9cb53b330c479b9ebe734afd1b84aec2f96e75acf66c59863d773c9cfc81', id="bytes"),
    ]
)
def test_cache_manager_utils_generate_key(arg1, arg2, arg3, expected, cmutils):
    actual = cmutils.generate_key(arg1, arg2, arg3)
    assert actual == expected



def test_cache_manager_client_init(mocker):
    mock_http_client = mocker.patch('plugnpy.cachemanager.HTTPClient')
    client = CacheManagerClient(HOST, PORT, NAMESPACE)
    assert client._namespace == NAMESPACE
    assert client._headers == {
        'Referer': HOST,
        'Content-Type': 'application/json',
    }
    mock_http_client.assert_called()
    assert mock_http_client.call_args == mocker.call(
        HOST, PORT, concurrency=1, connection_timeout=30, network_timeout=30)


def test_cache_manager_client_get_data(mocker, cmclient):
    mocker.patch.object(cmclient, '_post', return_value=DATA)
    assert cmclient.get_data(KEY, MAX_WAIT) == DATA
    assert cmclient._post.call_args == mocker.call(
        'get_data',
        {
            'namespace': NAMESPACE,
            'key': KEY,
            'max_wait_time': MAX_WAIT,
        },
    )


def test_cache_manager_client_set_data(mocker, cmclient):
    mocker.patch.object(cmclient, '_post', return_value=VALUE)
    assert cmclient.set_data(KEY, DATA, TTL) == VALUE
    assert cmclient._post.call_args == mocker.call(
        'set_data',
        {
            'namespace': NAMESPACE,
            'key': KEY,
            'data': DATA,
            'ttl': TTL,
        },
    )


def test_cache_manager_client_status(mocker, cmclient):
    mocker.patch.object(cmclient, '_send', return_value=VALUE)
    assert cmclient.status() == VALUE
    assert cmclient._send.call_args == mocker.call(cmclient._http_client.get, 'status')


@pytest.mark.parametrize('isopen', [True, False])
def test_cache_manager_client_close(isopen, mocker, cmclient):
    mock_client = cmclient._http_client
    if not isopen:
        cmclient._http_client = None
    cmclient.close()
    assert mock_client.close.called == isopen


def test_cache_manager_client_post(mocker, cmclient):
    mocker.patch.object(cmclient, '_send', return_value=VALUE)
    assert cmclient._post(PATH, DATA) == VALUE
    assert cmclient._send.call_args == mocker.call(cmclient._http_client.post, PATH, DATA)


@pytest.mark.parametrize('data, raw, expected', [
    pytest.param(None, None, None, id="nothing"),
    pytest.param(DATA, None, None, id="data"),
    pytest.param(DATA, json.dumps(VALUE), VALUE, id="response_data"),
])
def test_cache_manager_client_send(data, raw, expected, cmclient, mocker):
    mock_resp = mocker.Mock(status_code=200)
    mock_resp.read.return_value = raw
    mock_method = mocker.Mock(return_value=mock_resp)
    assert cmclient._send(mock_method, PATH, data) == expected


@pytest.mark.parametrize('status, msg, raw, exception', [
    pytest.param(200, 'OK', None, None, id="ok"),
    pytest.param(404, 'Not Found', None, True, id="error"),
    pytest.param(500, 'Server Error', 'raw error', True, id="error_with_body"),
])
def test_cache_manager_client_check_for_error(status, msg, raw, exception, mocker, cmclient):
    mock_resp = mocker.Mock(status_code=status, status_message=msg)
    mock_resp.read.return_value = raw
    if not exception:
        cmclient._check_for_error(mock_resp)
    else:
        with pytest.raises(ResultError) as ex:
            cmclient._check_for_error(mock_resp)
        assert f'{status}: {msg} - {raw}' in str(ex)
