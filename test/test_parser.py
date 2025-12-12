"""
Unit tests for plugnpy.parser
Copyright (C) 2003-2025 ITRS Group Limited. All rights reserved
"""

import os
import sys

import pytest
from plugnpy.parser import Parser, ExecutionStyle
from argparse import Namespace


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

@pytest.mark.parametrize(
    'mock_uses_stdin, mock_readlines, mock_argv, mock_opsview_scriptrunner, mock_is_file, '
    'expected_args, expected_epilog, expected_out, expected_exit_code',
    [
        pytest.param(
            False,
            None,
            ['script_name'],
            '',
            True,
            None,
            """NOTE: This plugin only accepts options via STDIN for security.
See https://docs.itrsgroup.com/docs/opsview/current/secure-arguments/ for more information.""",
            "",
            0,
            id='no_stdin_no_cmdline_args'
        ),
        pytest.param(
            False,
            None,
            ['script_name', '-h'],
            '',
            True,
            None,
            """NOTE: This plugin only accepts options via STDIN for security.
See https://docs.itrsgroup.com/docs/opsview/current/secure-arguments/ for more information.""",
            '',
            0,
            id='no_stdin_h_cmdline'
        ),
        pytest.param(
            False,
            None,
            ['script_name', '--help'],
            '',
            True,
            None,
            """NOTE: This plugin only accepts options via STDIN for security.
See https://docs.itrsgroup.com/docs/opsview/current/secure-arguments/ for more information.""",
            '',
            0,
            id='no_stdin_help_cmdline'
        ),
        pytest.param(
            False,
            None,
            ['script_name', '--cmdline-option', 'cmdline-value'],
            '',
            True,
            None,
            None,
            """This plugin only accepts options via STDIN for security.
Please rerun as follows (IMPORTANT: Using this utility will briefly expose arguments on this system so cannot be considered fully secure):

    script_name <<< $(/opt/opsview/monitoringscripts/commands/ov_cmd_split --cmdline-option cmdline-value)

Example: `my_script --foo bar` becomes `my_script <<< $(/opt/opsview/monitoringscripts/commands/ov_cmd_split --foo bar)`
See https://docs.itrsgroup.com/docs/opsview/current/secure-arguments/ for more information.
""",
            3,
            id='no_stdin_and_cmdline_args'
        ),
        pytest.param(
            False,
            None,
            ['script_name', '--cmdline-option', 'cmdline-value'],
            '',
            False,
            None,
            None,
            """This plugin only accepts options via STDIN for security.
See https://docs.itrsgroup.com/docs/opsview/current/secure-arguments/ for more information.
""",
            3,
            id='no_stdin_and_cmdline_args_no_ov_cmd_split'
        ),
        pytest.param(
            False,
            None,
            ['script_name', '--cmdline-option', 'cmdline-value'],
            'OPSVIEW_SCRIPTRUNNER',
            True,
            None,
            None,
            """This plugin only accepts options via STDIN for security.
You have provided command line arguments.
Please reconfigure this plugin to use the correct execution style.
""",
            3,
            id='no_stdin_and_cmdline_args_scriptrunner'
        ),
        pytest.param(
            True,
            ['{"cmd": ["--stdin-option", "stdin-value"]}'],
            ['script_name', '--cmdline-option', 'cmdline-value'],
            '',
            True,
            None,
            None,
            """This plugin only accepts options via STDIN for security.
You have provided a mix of command line and STDIN arguments.
Please rerun without any arguments after `script_name`
See https://docs.itrsgroup.com/docs/opsview/current/secure-arguments/ for more information.
""",
            3,
            id='stdin_and_cmdline_args'
        ),
        pytest.param(
            True,
            ['{"cmd": ["--stdin-option", "stdin-value"]}'],
            ['script_name', '--cmdline-option', 'cmdline-value'],
            'OPSVIEW_SCRIPTRUNNER',
            True,
            None,
            None,
            """This plugin only accepts options via STDIN for security.
You have provided a mix of command line and STDIN arguments.
Please reconfigure this plugin to use the correct execution style.
""",
            3,
            id='stdin_and_cmdline_args_scriptrunner'
        ),
        pytest.param(
            True,
            ['{"cmd": ["--stdin-option", "stdin-value"]}'],
            ['script_name'],
            '',
            True,
            ['--stdin-option', 'stdin-value'],
            None,
            "",
            0,
            id='stdin_only'
        ),
        pytest.param(
            True,
            '',
            ['script_name'],
            '',
            True,
            None,
            """NOTE: This plugin only accepts options via STDIN for security.
See https://docs.itrsgroup.com/docs/opsview/current/secure-arguments/ for more information.""",
            "",
            0,
            id='stdin_empty'
        ),
        pytest.param(
            AttributeError,
            None,
            ['script_name', '--cmdline-option', 'cmdline-value'],
            'OPSVIEW_SCRIPTRUNNER',
            True,
            None,
            None,
            """This plugin only accepts options via STDIN for security.
You have provided command line arguments.
Please reconfigure this plugin to use the correct execution style.
""",
            3,
            id='stdin_AttributeError_and_cmdline_args_scriptrunner'
        ),
    ]
)
def test_get_stdin_args(
        capsys, mocker, monkeypatch,
        mock_uses_stdin, mock_readlines, mock_argv, mock_opsview_scriptrunner,
        mock_is_file, expected_args, expected_epilog, expected_out, expected_exit_code,
):
    monkeypatch.setenv('OPSVIEW_SCRIPTRUNNER', mock_opsview_scriptrunner)
    mocker.patch.object(sys, 'argv', mock_argv)
    if isinstance(mock_uses_stdin, bool):
        mock_fstat = mocker.Mock()
        mock_fstat.st_mode = 4480 if mock_uses_stdin else 8592
    else:
        mock_fstat = mock_uses_stdin

    mocker.patch('plugnpy.parser.sys.stdin.fileno', return_value=0)
    mocker.patch('plugnpy.parser.os.fstat', side_effect=[mock_fstat])
    mocker.patch('plugnpy.parser.sys.stdin.readlines', return_value=mock_readlines)
    mocker.patch('plugnpy.parser.os.path.isfile', return_value=mock_is_file)

    parser = Parser(execution_style=ExecutionStyle.STDIN_ARGS)
    parser.add_argument('--test', help='test')
    args = None
    if expected_exit_code:
        with pytest.raises(SystemExit) as ex:
            args = parser.get_stdin_args()
        assert ex.value.code == expected_exit_code
    else:
        args = parser.get_stdin_args()

    assert parser.epilog == expected_epilog
    assert args == expected_args

    captured = capsys.readouterr()
    assert captured.out == expected_out
    assert captured.err == ""


@pytest.mark.parametrize('known_args, stdin_args, expected', [
    pytest.param(None, None, (Namespace(), []), id="no_args"),
    pytest.param(['--test', 'test'], None, (Namespace(), ['--test', 'test']), id="known_args"),
    pytest.param(None, ['--test', 'test'], (Namespace(), ['--test', 'test']), id="stdin_args"),
])

def test_parse_known_args(mocker, monkeypatch, known_args, stdin_args, expected):
    mock_fstat = mocker.Mock()
    mock_fstat.st_mode = 8592
    monkeypatch.setenv('OPSVIEW_SCRIPTRUNNER', '')
    mocker.patch.object(sys, 'argv', ['script_name'])
    mocker.patch('plugnpy.parser.sys.stdin.fileno', return_value=0)
    mocker.patch('plugnpy.parser.os.fstat', return_value=mock_fstat)
    mocker.patch('plugnpy.parser.sys.stdin.readlines', return_value=[])
    parser = Parser(execution_style=ExecutionStyle.STDIN_ARGS)
    parser._stdin_args = stdin_args
    args = parser.parse_known_args(args=known_args)
    assert args == expected
