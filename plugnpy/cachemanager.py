"""
Cache Manager Client class.
"""

import os
import json
from socket import error as SocketError
from geventhttpclient import HTTPClient
from .exception import ResultError
from .utils import hash_string

ESCAPE_CHARACTER = '\\'
DELIMITER = '#'


class CacheManagerUtils:  # pylint: disable=too-few-public-methods
    """Utility functions for cache manager"""

    client = None
    host = os.environ.get('OPSVIEW_CACHE_MANAGER_HOST')
    port = os.environ.get('OPSVIEW_CACHE_MANAGER_PORT')
    namespace = os.environ.get('OPSVIEW_CACHE_MANAGER_NAMESPACE')

    @staticmethod
    def generate_key(*args):
        """Generate a key for use in cache manager

        Escapes escape characters in the arguments and then produces a hash of all the arguments passed in.

        :param args: The arguments to be used to create the key.
        """
        values = []
        for arg in args:
            if ESCAPE_CHARACTER in arg:
                arg = arg.replace(ESCAPE_CHARACTER, ESCAPE_CHARACTER * 2)
            if DELIMITER in arg:
                arg = arg.replace(DELIMITER, ESCAPE_CHARACTER + DELIMITER)
            values.append(arg)
        return hash_string(DELIMITER.join(values))

    @staticmethod
    def set_data(key, data, ttl=900):
        """Set data in the cache manager

        :param key: The key to store the data under.
        :param data: The data to store.
        :param ttl: The number of seconds data is valid for.
        """
        if not CacheManagerUtils.client:
            CacheManagerUtils.client = CacheManagerClient(
                CacheManagerUtils.host,
                CacheManagerUtils.port,
                CacheManagerUtils.namespace
            )
        data = json.dumps(data)
        key = hash_string(key)
        return CacheManagerUtils.client.set_data(key, data, ttl)

    @staticmethod
    def get_via_cachemanager(no_cachemanager, key, ttl, func, *args, **kwargs):
        """Gets data via the cache manager

        If the cache manager is not required, calls the function directly and returns the data.
        If the cache manager is required, tries to get the data from the cachemanager.
        If the data does not exist, calls the function and stores the returned data in the cache manager.

        :param no_cachemanager: True if cache manager is not required, False otherwise.
        :param key: The key to store the data under.
        :param ttl: The number of seconds data is valid for.
        :param func: The function to retrieve the data, if the data is not in the cache manager.
        :param args: The arguments to pass to the user's data retrieval function.
        :param kwargs: The keyword arguments to pass to the user's data retrieval function.
        """
        if not CacheManagerUtils._is_required(no_cachemanager, CacheManagerUtils.host):
            data = func(*args, **kwargs)
            return data

        if not CacheManagerUtils.client:
            CacheManagerUtils.client = CacheManagerClient(
                CacheManagerUtils.host,
                CacheManagerUtils.port,
                CacheManagerUtils.namespace
            )

        key = hash_string(key)
        try:
            response = CacheManagerUtils.client.get_data(key)
        except SocketError as ex:
            raise ResultError("Failed to connect to cache manager: {0}".format(ex)) from None
        data, lock = response['data'], response['lock']
        if lock:
            # Any exceptions in the function call will be stored in the cache manager under the 'error' key
            try:
                data = func(*args, **kwargs)
            except Exception as ex:  # pylint: disable=broad-except
                data = {'error': str(ex)}
            data = json.dumps(data)
            CacheManagerUtils.client.set_data(key, data, ttl)
        if not data:
            raise ResultError("Failed to retrieve data from cache manager")
        data = json.loads(data)
        return data

    @staticmethod
    def _is_required(no_cachemanager, cachemanager_host=None):
        """Check if cache manager is required for this execution"""
        if cachemanager_host:
            return not no_cachemanager
        if not no_cachemanager:
            raise ResultError("Cache manager host is required")
        return False


class CacheManagerClient:  # pragma: no cover
    """A simple client to contact the cachemanager and set or get cached data"""

    HTTP_STATUS_OK_MIN = 200
    HTTP_STATUS_OK_MAX = 299

    def __init__(self, host, port, namespace, concurrency=1,  # pylint: disable=too-many-arguments
                 connection_timeout=30, network_timeout=30):
        """Constructor for Cache Manager Client

        :param host: Host IP or name of the cache manager.
        :param port: Port of the cache manager.
        :param namespace: Namespace for the plugin.
        :param concurrency: Number of concurrent http connections allowed (default is 1).
        :param connection_timeout: Number of seconds before HTTP connection times out.
        :param network_timeout: Number of seconds before the data read times out.
        """
        self._namespace = namespace
        self._headers = {'Referer': host, 'Content-Type': 'application/json'}
        self._client = HTTPClient(
            host,
            port,
            concurrency=concurrency,
            connection_timeout=connection_timeout,
            network_timeout=network_timeout,
        )

    def get_data(self, key, max_wait_time=30):
        """Gets data from the cache. Optionally, may get a lock if there is no data present.

        :param key: The key of the data element to fetch, within the namespace.
        :param max_wait_time: Max time to wait for a lock (seconds).
        :returns: A tuple of (data, lock_key). The 'lock_key' may be None.
        """
        params = {
            'namespace': self._namespace,
            'key': key,
            'max_wait_time': max_wait_time,
        }
        return self._post('get_data', params)

    def set_data(self, key, data, ttl=900):
        """Sets data into the cache.

        :param key: The key of the data element to store, within the namespace.
        :param data: The data to store.
        :param ttl: The time that the data is valid for (seconds).
        """
        params = {
            'namespace': self._namespace,
            'key': key,
            'data': data,
            'ttl': ttl,
        }
        return self._post('set_data', params)

    def status(self):
        """Fetches the current status of the cache."""
        return self._send(self._client.get, 'status')

    def close(self):
        """Close a client connection"""
        if self._client:
            self._client.close()

    def _post(self, path, data):
        return self._send(self._client.post, path, data)

    def _send(self, method, path, data=None):
        if data:
            body = json.dumps(data)
            response = method(path, body=body, headers=self._headers)
        else:
            response = method(path, headers=self._headers)
        self._check_for_error(response)
        raw_response = response.read()
        return json.loads(raw_response) if raw_response else None

    def _check_for_error(self, response):
        if (response.status_code < self.HTTP_STATUS_OK_MIN) or (response.status_code > self.HTTP_STATUS_OK_MAX):
            raw_body = response.read()
            raise ResultError("{0}: {1} - {2}".format(response.status_code, response.status_message, raw_body))
