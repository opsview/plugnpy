import pytest

from plugnpy import hash_string, dynamic_import, import_modules


def test_hash_string():
    # generated with https://emn178.github.io/online-tools/sha256.html
    expected = '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
    actual = hash_string('password')
    assert actual == expected

def test_dynamic_import_module():
    json = dynamic_import('json')
    expected = '{"a": 10}'
    actual = json.dumps({'a': 10})
    assert actual == expected

def test_dynamic_import_fromlist():
    json = dynamic_import('json', ['dumps', 'loads'])
    expected = {'a': 10}
    actual = json.loads('{"a": 10}')
    assert actual == expected

def test_import_modules():
    modules_to_import = {
        'json': None,  # import json
        'datetime': ['datetime']  # from datetime import datetime, strptime
    }
    imported_modules = import_modules(modules_to_import)

    json = imported_modules['json']
    expected = {'a': 10}
    actual = json.loads('{"a": 10}')
    assert actual == expected

    datetime = imported_modules['datetime']
    expected = datetime.datetime(2020, 3, 17)
    actual = datetime.datetime.strptime('17 March 2020', '%d %B %Y')
    assert actual == expected
