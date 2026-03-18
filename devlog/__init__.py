"""A minimal, beautiful terminal todo app."""

__version__ = "2.0.0"

from .tui import main as run_tui
from .cli import execute_cli_command, create_parser
from .core.config import load_config

__all__ = ['run', 'run_tui', 'load_config']


def run():
    """Main entry point - handles both CLI and TUI modes."""
    import sys
    import os
    import curses

    parser = create_parser()
    args = parser.parse_args()

    # If no command, launch TUI
    if not args.command:
        os.environ.setdefault("ESCDELAY", "25")
        try:
            curses.wrapper(run_tui)
        except KeyboardInterrupt:
            pass
        return

    # Execute CLI command
    execute_cli_command(args)
