import os
import sys

import pytest

from plugnpy.parser import Parser


def test_copyright(capsys):
    parser = Parser(copystr='copyright string')
    parser.print_help(sys.stdout)
    assert 'copyright string' in capsys.readouterr().out

    parser.set_copyright('new copyright string')
    parser.print_help(sys.stdout)
    assert 'new copyright string' in capsys.readouterr().out


def test_customizations(capsys):
    with pytest.raises(SystemExit) as e:
        Parser().error('something')
    assert e.value.code == 3
    assert capsys.readouterr().out.endswith('something{0}'.format(os.linesep))


def test_help_exit(capsys):
    parser = Parser()
    with pytest.raises(SystemExit) as ex:
        parser.parse_args(args=['-h'])
    assert ex.value.code == 3

    with pytest.raises(SystemExit) as ex:
        parser._help_exit_unknown()
    assert ex.value.code == 3
