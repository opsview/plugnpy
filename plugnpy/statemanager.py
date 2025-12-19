"""
State Manager Client class.
Copyright (C) 2003-2025 ITRS Group Limited. All rights reserved
"""

import os
import json
import time

from socket import error as SocketError
from typing import Optional

from geventhttpclient import HTTPClient

from .exception import StateManagerStoreError

ESCAPE_CHARACTER = '\\'
DELIMITER = '#'


class StateManagerUtils:
    """Utility functions for State Manager"""

    client = None
    host = os.environ.get('OPSVIEW_STATE_MANAGER_HOST')
    port = os.environ.get('OPSVIEW_STATE_MANAGER_PORT')
    namespace = os.environ.get('OPSVIEW_STATE_MANAGER_NAMESPACE')

    @staticmethod
    def _initialise_client():
        """ Initialise the client """
        if not StateManagerUtils.client:
            StateManagerUtils.client = StateManagerClient(
                StateManagerUtils.host,
                StateManagerUtils.port,
                StateManagerUtils.namespace,
            )

    @staticmethod
    def store_data(key: str, data: str, ttl: int, timestamp: Optional[float] = None):
        """ Store or update the data in the persistent storage indexed by key.

        :param key: The key to store the data under.
        :param data: The data to store.
        :param ttl: The number of seconds for which the data is valid.
        :param timestamp: The time of the data.

        Raises a StateManagerStoreError if the data was not saved to the persistent store.
        Raises TypeError if either data or key is not a string object
        """
        if not isinstance(data, str):
            raise TypeError(f"Data must be a str type, not {type(data)}")

        StateManagerUtils._initialise_client()
        StateManagerUtils.client.store_data(key, data, ttl, timestamp)

    @staticmethod
    def fetch_data(key: str):
        """ Fetch the data from the persistent storage, indexed by key.

        :param key: The key under which the data is stored.
        :returns: The data, or None if not found.

        Raises a StateManagerStoreError if an error occccurred when attempting to fetch the data.
        """
        StateManagerUtils._initialise_client()
        return StateManagerUtils.client.fetch_data(key)


class StateManagerClient:
    """A simple client to contact the State Manager and set or get persistent data"""

    # pylint: disable=duplicate-code
    HTTP_STATUS_OK_MIN = 200
    HTTP_STATUS_OK_MAX = 299

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
            self, host, port, namespace,
            concurrency=1, connection_timeout=30, network_timeout=30
    ):
        """Constructor for State Manager Client

        :param host: Host IP or name of the state manager.
        :param port: Port of the state manager.
        :param namespace: Namespace for the plugin.
        :param concurrency: Number of concurrent http connections allowed (default is 1).
        :param connection_timeout: Number of seconds before HTTP connection times out.
        :param network_timeout: Number of seconds before the data read times out.
        """
        self._namespace = namespace
        self._headers = {'Referer': host, 'Content-Type': 'application/json'}
        self._http_client = HTTPClient(
            host,
            port,
            concurrency=concurrency,
            connection_timeout=connection_timeout,
            network_timeout=network_timeout,
        )

    def store_data(self, key: str, data: str, ttl: int, timestamp: Optional[float] = None):
        """ Store or update the data in the persistent storage indexed by key.

        :param key: The key to store the data under.
        :param data: The data to store.
        :param ttl: The number of seconds for which the data is valid.

        Raises a StateManagerStoreError if the data was not saved to the persistent storage.
        Raises TypeError if either data or key is not a string object
        """
        if not isinstance(data, str):
            raise TypeError(f"Data must be a str type, not {type(data)}")

        params = {
            'namespace': self._namespace,
            'key': key,
            'data': data,
            'ttl': ttl,
            'timestamp': timestamp or time.time(),
        }
        try:
            response = self._send_persistent(self._http_client.post, 'store_data', params)
        except StateManagerStoreError:
            raise
        except Exception as ex:
            raise StateManagerStoreError(str(ex)) from ex

        if (response.status_code < self.HTTP_STATUS_OK_MIN) or (response.status_code > self.HTTP_STATUS_OK_MAX):
            raw_body = response.read()
            raise StateManagerStoreError(f"{response.status_code}: {response.status_message} - {raw_body}")
    # pylint: enable=duplicate-code

    def fetch_data(self, key: str) -> Optional[str]:
        """ Fetch the data from the persistent storage, indexed by key.

        :param key: The key under which the data is stored.
        :returns: The data, or None if not found.

        Raises a StateManagerStoreError if an error occurred when attempting to fetch the data.
        """
        params = {
            'namespace': self._namespace,
            'key': key,
        }
        try:
            response = self._send_persistent(self._http_client.post, 'fetch_data', params)
        except StateManagerStoreError:
            raise
        except Exception as ex:
            raise StateManagerStoreError(str(ex)) from ex

        if response.status_code == 404:
            # data not found
            return None

        raw_body = response.read()
        if (response.status_code < self.HTTP_STATUS_OK_MIN) or (response.status_code > self.HTTP_STATUS_OK_MAX):
            raise StateManagerStoreError(f"{response.status_code}: {response.status_message} - {raw_body}")

        try:
            return json.loads(raw_body.decode('utf-8'))['data']
        except Exception as ex:
            raise StateManagerStoreError(f"Unable to process response ({ex}) - {raw_body}") from ex

    def close(self):
        """Close a client connection"""
        if self._http_client:
            self._http_client.close()
            self._http_client = None

    def _send_persistent(self, method, path, data):
        """ Send a request to the State Manager (persistent store) """
        body = json.dumps(data)
        try:
            response = method(path, body=body, headers=self._headers)
        except SocketError as ex:
            raise StateManagerStoreError(f"Failed to connect to state manager: {ex}") from None
        return response
