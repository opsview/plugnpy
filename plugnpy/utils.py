"""
Helpful utility functions.
"""

import hashlib
from six import iteritems


def hash_string(string):
    """Generate a SHA-256 Hash."""
    return hashlib.sha256(string.encode('ascii')).hexdigest()


def import_modules(modules_to_import):
    """Dynamically import modules"""
    imported_modules = {}
    for module, fromlist in iteritems(modules_to_import):
        imported_modules[module] = dynamic_import(module, fromlist)
    return imported_modules


def dynamic_import(module, fromlist=None):
    """Import the given module from the given class name"""
    return __import__(module, fromlist=fromlist)
