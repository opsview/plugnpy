"""
Argument Parser class for use in service checks.
Based on argparse.ArgumentParser but overwrites exiting calls to exit Unknowns.
"""

import argparse
import json
import os
import select
import sys
import stat
from gettext import gettext
from enum import Enum


class ExecutionStyle(Enum):
    """The execution style of the plugin determines whether arguments are passed via command line or STDIN."""

    COMMAND_LINE_ARGS = 1
    STDIN_ARGS = 2


class _HelpAction(argparse.Action):  # pylint: disable=too-few-public-methods
    def __init__(
        self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=None
    ):  # pylint: disable=redefined-builtin
        super().__init__(option_strings=option_strings, dest=dest, default=default, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        parser.exit(3)


argparse._HelpAction = _HelpAction  # pylint: disable=protected-access


class Parser(argparse.ArgumentParser):
    """Object for parsing command line strings into Python objects.
    Modified to exit with Opsview specific exits.

    Keyword Arguments:
        - prog -- The name of the program (default: sys.argv[0])
        - usage -- A usage message (default: auto-generated from arguments)
        - description -- A description of what the program does
        - epilog -- Text following the argument descriptions
        - parents -- Parsers whose arguments should be copied into this one
        - formatter_class -- HelpFormatter class for printing help messages
        - prefix_chars -- Characters that prefix optional arguments
        - fromfile_prefix_chars -- Characters that prefix files containing additional arguments
        - argument_default -- The default value for all arguments
        - conflict_handler -- String indicating how to handle conflicts
        - add_help -- Add a -h/-help option
        - allow_abbrev -- Allow long options to be abbreviated unambiguously
        - copystr -- A copyright string to be printed in the help message
        - execution_style -- Determines whether arguments are passed via command line or STDIN
    """

    _OV_CMD_SPLIT_PATH = '/opt/opsview/monitoringscripts/commands/ov_cmd_split'

    def __init__(self, *args, **kwargs):
        self._copyright = None
        self._stdin_args = None
        if 'copystr' in kwargs:
            self._copyright = kwargs['copystr']
            del kwargs['copystr']
        if 'execution_style' in kwargs:
            self._execution_style = kwargs['execution_style']
            del kwargs['execution_style']
        else:
            self._execution_style = ExecutionStyle.COMMAND_LINE_ARGS
        super().__init__(*args, **kwargs)

    def format_help(self):
        formatter = self._get_formatter()

        if self._copyright:
            formatter.add_text(self._copyright)

        # usage
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        # description
        formatter.add_text(self.description)

        # positionals, optionals and user-defined groups
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)  # pylint: disable=protected-access
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()

    def error(self, message):
        """Overrides ArgumentParser.error() to replace exit code with 3 (Unknown) and print to stdout.
        Opsview Monitor cannot (or chooses not to) display stderr output in Service Check summaries, so we'll
        output to stdout instead."""
        self.print_usage(sys.stdout)
        self.exit(3, gettext('%s: error: %s\n') % (self.prog, message))

    def exit(self, status=0, message=None):
        """Overrides ArgumentParser.exit() to print to stdout.
        Opsview Monitor cannot (or chooses not to) display stderr output in Service Check summaries, so we'll
        output to stdout instead."""
        if message:
            self._print_message(message, sys.stdout)
        sys.exit(status)

    def set_copyright(self, copystr):
        """Set copyright string."""
        self._copyright = copystr

    def _print_warning(self, is_opsview_executing, no_stdin):
        if no_stdin:
            if is_opsview_executing:
                self.exit(
                    3,
                    "This plugin only accepts options via STDIN for security."
                    "\nYou have provided command line arguments."
                    "\nPlease reconfigure this plugin to use the correct execution style.\n",
                )
            else:
                has_ov_cmd_split = os.path.isfile(Parser._OV_CMD_SPLIT_PATH)
                example = (
                    (
                        "\nPlease rerun as follows (IMPORTANT: Using this utility will briefly expose arguments on "
                        "this system so cannot be considered fully secure):"
                        f"\n\n    {sys.argv[0]} <<< $({Parser._OV_CMD_SPLIT_PATH} {' '.join(sys.argv[1:])})"
                        "\n\nExample: `my_script --foo bar` becomes `my_script <<< "
                        f"$({Parser._OV_CMD_SPLIT_PATH} --foo bar)`"
                    )
                    if has_ov_cmd_split
                    else ""
                )

                self.exit(
                    3,
                    "This plugin only accepts options via STDIN for security."
                    f"{example}"
                    "\nSee https://docs.itrsgroup.com/docs/opsview/current/secure-arguments/ for "
                    "more information.\n",
                )
        else:
            if is_opsview_executing:
                self.exit(
                    3,
                    "This plugin only accepts options via STDIN for security."
                    "\nYou have provided a mix of command line and STDIN arguments."
                    "\nPlease reconfigure this plugin to use the correct execution style.\n",
                )
            else:
                self.exit(
                    3,
                    "This plugin only accepts options via STDIN for security."
                    "\nYou have provided a mix of command line and STDIN arguments."
                    f"\nPlease rerun without any arguments after `{sys.argv[0]}`"
                    "\nSee https://docs.itrsgroup.com/docs/opsview/current/secure-arguments/ "
                    "for more information.\n",
                )

    def get_stdin_args(self):
        """Get arguments from stdin."""
        cmd = None
        is_opsview_executing = bool(os.environ.get('OPSVIEW_SCRIPTRUNNER'))
        has_cmdline_args = len(sys.argv) > 1
        has_empty_cmdline_args = not any(sys.argv[1:])

        # Check if we should be using STDIN
        # If STDIN is available, we only care if we have a PIPE or FILE redirection
        try:
            fd = sys.stdin.fileno()
            stat_data = os.fstat(fd)
            uses_stdin = stat.S_ISREG(stat_data.st_mode) or stat.S_ISFIFO(stat_data.st_mode)
        except (OSError, AttributeError, TypeError):
            uses_stdin = False

        if uses_stdin:
            if has_cmdline_args:
                # we have mixed stdin and commandline
                self._print_warning(is_opsview_executing, (not uses_stdin))
            data = sys.stdin.readlines()
            try:
                arg_string = data[0].strip()
                cmd = json.loads(arg_string)['cmd']
            except IndexError:
                uses_stdin = False
        if not uses_stdin:
            if (not has_cmdline_args) or has_empty_cmdline_args or ('-h' in sys.argv[1:]) or ('--help' in sys.argv[1:]):
                self.epilog = (
                    "NOTE: This plugin only accepts options via STDIN for security."
                    "\nSee https://docs.itrsgroup.com/docs/opsview/current/secure-arguments/"
                    " for more information."
                )
            else:
                # we have non-help command line args
                self._print_warning(is_opsview_executing, (not uses_stdin))
        return cmd

    def parse_known_args(self, args=None, namespace=None):
        """Parse command line arguments and return a Namespace object.
        If no arguments are provided and the execution style is STDIN_ARGS, parse arguments from stdin.
        """
        if args is None and self._execution_style == ExecutionStyle.STDIN_ARGS:
            if self._stdin_args is None:
                self._stdin_args = self.get_stdin_args()
            args = self._stdin_args
        return super().parse_known_args(args, namespace)
