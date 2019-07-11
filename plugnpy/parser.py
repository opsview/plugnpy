"""
Argument Parser class for use in service checks.
Based on argparse.ArgumentParser but overwrites exiting calls to exit Unknowns.
"""
import argparse
from gettext import gettext
import sys


class _HelpAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help=None):
        super(_HelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        parser.exit(3)


argparse._HelpAction = _HelpAction


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
    """

    def __init__(self, *args, **kwargs):
        self._copyright = None
        if 'copystr' in kwargs:
            self._copyright = kwargs['copystr']
            del kwargs['copystr']
        super(Parser, self).__init__(*args, **kwargs)

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
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()

    def error(self, message):
        """Overrides ArgumentParser.error() to replace exit code with 3 (Unknown) and print to stdout.
        Opsview Monitor cannot (or chooses not to) display stderr output in Service Check Summarys, so we'll
        output to stdout instead."""
        self.print_usage(sys.stdout)
        self.exit(3, gettext('%s: error: %s\n') % (self.prog, message))

    def exit(self, status=0, message=None):
        """Overrides ArgumentParser.exit() to print to stdout.
        Opsview Monitor cannot (or chooses not to) display stderr output in Service Check Summarys, so we'll
        output to stdout instead."""
        if message:
            self._print_message(message, sys.stdout)
        sys.exit(status)

    def set_copyright(self, copystr):
        """Set copyright string."""
        self._copyright = copystr
