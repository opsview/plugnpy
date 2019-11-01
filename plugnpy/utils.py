"""
Helpful utility functions.
"""

import hashlib


def hash_string(string):
    """Generate a SHA-256 Hash."""
    return hashlib.sha256(string).hexdigest().encode('ascii')
