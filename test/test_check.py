import os

import pytest

from plugnpy.check import Check
from plugnpy.metric import Metric


def test_add_metric():
    check = Check()
    check.add_metric('Memory', 4500000, 'bytes', '4M:', '6M:')
    check.add_metric('CPU', 7, '%', '20:', '50:')
    assert len(check.metrics) == 2
    for metric in check.metrics:
        assert isinstance(metric, Metric)


@pytest.mark.parametrize('status,expected', [
    ('ok', 0),
    ('warning', 1),
    ('critical', 2),
    ('unknown', 3),
], ids=[
    'ok',
    'warning',
    'critical',
    'unknown',
])
def test_exit(capsys, status, expected):
    with pytest.raises(SystemExit) as e:
        Check().__getattribute__('exit_{0}'.format(status))('something')
    assert e.value.code == expected
    assert capsys.readouterr().out == 'METRIC {0}: something{1}'.format(status.upper(), os.linesep)


def test_final(capsys):
    check = Check()
    check.add_metric('Memory', 4500000, 'B', '4M:', '6M:', convert_metric=True)
    check.add_metric('CPU', 7, '%', '20:', '50:')
    with pytest.raises(SystemExit) as e:
        check.final()
    assert e.value.code == 2
    assert capsys.readouterr().out == (
        'METRIC CRITICAL - Memory is 4.29MB, CPU is 7% | Memory=4500000B;4M:;6M: CPU=7%;20:;50:{0}'.format(
            os.linesep
        )
    )
