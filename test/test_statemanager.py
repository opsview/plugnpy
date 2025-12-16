"""
Unit tests for PlugNPy statemanager.py
Copyright (C) 2003-2025 ITRS Group Ltd. All rights reserved
"""

import functools
import json
import pytest

from socket import error as SocketError
from plugnpy.statemanager import StateManagerUtils, StateManagerClient
from plugnpy.exception import StateManagerStoreError


HOST = 'a.host'
PORT = 1234
NAMESPACE = 'some-namespace'
KEY = 'key'
TTL = 99
NOW = 123456789
DATA = 'foodata' * 100
PATH = '/statemanager/path'
BODY = json.dumps({'other': 'foo', 'data': DATA}).encode('utf-8')


@pytest.fixture
def smutils(mocker):
    mocker.patch.object(StateManagerUtils, 'host', HOST)
    mocker.patch.object(StateManagerUtils, 'port', PORT)
    mocker.patch.object(StateManagerUtils, 'namespace', NAMESPACE)
    utils = StateManagerUtils()
    yield utils


@pytest.fixture
def smclient(mocker):
    mock_http_client = mocker.patch('plugnpy.statemanager.HTTPClient')
    client = StateManagerClient(HOST, PORT, NAMESPACE)
    yield client


@pytest.mark.parametrize('data, valid', [
    pytest.param(DATA, True, id="str"),
    pytest.param(b'bytes', False, id="bytes"),
    pytest.param(123, False, id="int"),
    pytest.param(123.909, False, id="float"),
])
def test_utils_store_data(data, valid, mocker, smutils):
    smutils._initialise_client()
    mocker.patch.object(smutils.client, 'store_data')
    if valid:
        smutils.store_data(KEY, data, TTL)
        smutils.client.store_data.assert_called()
        assert smutils.client.store_data.call_args == mocker.call(KEY, DATA, TTL, None)
    else:
        with pytest.raises(TypeError):
            smutils.store_data(KEY, data, TTL)


def test_utils_fetch_data(mocker, smutils):
    smutils._initialise_client()
    mocker.patch.object(smutils.client, 'fetch_data', return_value=DATA)
    assert smutils.fetch_data(KEY) == DATA
    smutils.client.fetch_data.assert_called()
    assert smutils.client.fetch_data.call_args == mocker.call(KEY)


def test_state_manager_client_init(mocker):
    mock_http_client = mocker.patch('plugnpy.statemanager.HTTPClient')
    client = StateManagerClient(HOST, PORT, NAMESPACE)
    assert client._namespace == NAMESPACE
    assert client._headers == {
        'Referer': HOST,
        'Content-Type': 'application/json',
    }
    mock_http_client.assert_called()
    assert mock_http_client.call_args == mocker.call(
        HOST, PORT, concurrency=1, connection_timeout=30, network_timeout=30)


@pytest.mark.parametrize('data, timestamp, send, status, exception, expected', [
    pytest.param(DATA, None, None, (200, 'OK', 'ok'), None, None, id="success"),
    pytest.param(DATA, NOW - 42, None, (200, 'OK', 'ok'), None, None, id="success_with_timestamp"),
    pytest.param(99, None, None, None, TypeError, 'Data must be a str', id="data_is_int"),
    pytest.param(DATA.encode('utf-8'), None, None, None, TypeError, 'Data must be a str', id="data_is_bytes"),
    pytest.param(DATA, None, StateManagerStoreError('foo'), None, StateManagerStoreError, 'foo', id="store_error"),
    pytest.param(DATA, None, Exception('bar'), None, StateManagerStoreError, 'bar', id="other_error"),
    pytest.param(
        DATA, None, None, (500, 'Server Error', 'fail'),
        StateManagerStoreError, '500: Server Error - fail',
        id="server_error"),
])
def test_state_manager_client_store_data(data, timestamp, send, status, exception, expected, mocker, smclient):
    mocker.patch('plugnpy.statemanager.time.time', return_value=NOW)
    if status:
        mock_resp = mocker.Mock(status_code=status[0], status_message=status[1])
        mock_resp.read.return_value = status[2]
    else:
        mock_resp = None
    mock_send = mocker.patch.object(smclient, '_send_persistent', return_value=mock_resp, side_effect=send)
    if not exception:
        smclient.store_data(KEY, data, TTL, timestamp)
        assert mock_send.call_args == mocker.call(
            smclient._http_client.post,
            'store_data', 
            {
                'namespace': NAMESPACE,
                'key': KEY,
                'data': DATA,
                'ttl': TTL,
                'timestamp': timestamp or NOW,
            },
        )
    else:
        with pytest.raises(exception) as ex:
            smclient.store_data(KEY, data, TTL, timestamp)
        assert expected in str(ex)


@pytest.mark.parametrize('send, status, exception, expected', [
    pytest.param(None, (200, 'OK', BODY), None, DATA, id="success"),
    pytest.param(None, (404, 'Not Found', None), None, None, id="not_found"),
    pytest.param(StateManagerStoreError('foo'), None, StateManagerStoreError, 'foo', id="store_error"),
    pytest.param(Exception('bar'), None, StateManagerStoreError, 'bar', id="other_error"),
    pytest.param(
        None, (500, 'Server Error', 'fail'),
        StateManagerStoreError, '500: Server Error - fail',
        id="server_error"),
    pytest.param(None, (200, 'OK', 'fubar'), StateManagerStoreError, 'Unable to process response', id="bad_data"),
])
def test_state_manager_client_fetch_data(send, status, exception, expected, mocker, smclient):
    if status:
        mock_resp = mocker.Mock(status_code=status[0], status_message=status[1])
        mock_resp.read.return_value = status[2]
    else:
        mock_resp = None
    mock_send = mocker.patch.object(smclient, '_send_persistent', return_value=mock_resp, side_effect=send)
    if not exception:
        assert smclient.fetch_data(KEY) == expected
        assert mock_send.call_args == mocker.call(
            smclient._http_client.post,
            'fetch_data', 
            {
                'namespace': NAMESPACE,
                'key': KEY,
            },
        )
    else:
        with pytest.raises(exception) as ex:
            smclient.fetch_data(KEY)
        assert expected in str(ex)


@pytest.mark.parametrize('isopen', [True, False])
def test_state_manager_client_close(isopen, mocker, smclient):
    mock_client = smclient._http_client
    if not isopen:
        smclient._http_client = None
    smclient.close()
    assert smclient._http_client is None
    assert mock_client.close.called == isopen


@pytest.mark.parametrize('error', [True, False])
def test_state_manager_client_send_persistent(error, mocker, smclient):
    mock_method = mocker.Mock()
    if error:
        mock_method.side_effect = SocketError
    if not error:
        smclient._send_persistent(mock_method, PATH, DATA)
    else:
        with pytest.raises(StateManagerStoreError) as ex:
            smclient._send_persistent(mock_method, PATH, DATA)
        assert 'Failed to connect to state manager' in str(ex)
    assert mock_method.call_args == mocker.call(PATH, body=json.dumps(DATA), headers=smclient._headers)
