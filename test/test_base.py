import pytest


def raise_or_assert(callback, raises, expected):
    """
    Assert that an exception is raised of type 'raises' and the expected value is 'expected'
    Or if 'raises' is set to False, assert that the output from the callback is 'expected'
    """
    if raises:
        with pytest.raises(raises) as excinfo:
            callback()
    else:
        assert callback() == expected
