"""
Helpful utility functions.
"""

import hashlib
from six import iteritems

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = 86400


def hash_string(string):
    """Generate a SHA-256 Hash."""
    return hashlib.sha256(string.encode('ascii')).hexdigest()


def convert_seconds(count_seconds):
    """Convert a number in seconds into a human readable format"""
    days = count_seconds // SECONDS_IN_DAY
    hours = count_seconds % SECONDS_IN_DAY // SECONDS_IN_HOUR
    minutes = count_seconds % SECONDS_IN_HOUR // SECONDS_IN_MINUTE
    seconds = count_seconds % SECONDS_IN_MINUTE
    summary = []
    if days:
        summary.append("{0:.0f}d".format(days))
    if hours:
        summary.append("{0:.0f}h".format(hours))
    if minutes:
        summary.append("{0:.0f}m".format(minutes))
    if summary:
        output = ' '.join(summary)
    else:
        output = "{0:.0f}s".format(seconds)
    return output


def import_modules(modules_to_import):
    """Dynamically import modules"""
    imported_modules = {}
    for module, fromlist in iteritems(modules_to_import):
        imported_modules[module] = dynamic_import(module, fromlist)
    return imported_modules


def dynamic_import(module, fromlist=None):
    """Import the given module from the given class name"""
    return __import__(module, fromlist=fromlist)
