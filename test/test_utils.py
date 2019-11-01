import pytest

from plugnpy import hash_string


def test_hash_string():
    # generated with https://emn178.github.io/online-tools/sha256.html
    expected = '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
    actual = hash_string('password')
    assert actual == expected
