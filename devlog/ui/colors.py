"""Color definitions and initialization for the TUI."""

import curses

# Color pair constants
C_GREEN = 1
C_GREY = 2
C_WHITE = 3
C_DIM = 4
C_CURSOR_BG = 5
C_CYAN = 6
C_HINT = 7
C_CURSOR_GREEN = 8
C_YELLOW = 9
C_RED = 10
C_HEAT_1 = 11
C_HEAT_2 = 12
C_HEAT_3 = 13
C_HEAT_4 = 14
C_MAGENTA = 15
C_WS_ACTIVE = 16
C_WS_DIM = 17
C_SEARCH_HL = 18


def init_colors():
    """Initialize all color pairs for the TUI."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(C_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(C_GREY, 245, -1)
    curses.init_pair(C_WHITE, curses.COLOR_WHITE, -1)
    curses.init_pair(C_DIM, 241, -1)
    curses.init_pair(C_CURSOR_BG, curses.COLOR_WHITE, 237)
    curses.init_pair(C_CYAN, curses.COLOR_CYAN, -1)
    curses.init_pair(C_HINT, 245, -1)
    curses.init_pair(C_CURSOR_GREEN, curses.COLOR_GREEN, 237)
    curses.init_pair(C_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_RED, curses.COLOR_RED, -1)
    curses.init_pair(C_HEAT_1, 22, -1)
    curses.init_pair(C_HEAT_2, 28, -1)
    curses.init_pair(C_HEAT_3, 34, -1)
    curses.init_pair(C_HEAT_4, 46, -1)
    curses.init_pair(C_MAGENTA, curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_WS_ACTIVE, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(C_WS_DIM, 245, -1)
    curses.init_pair(C_SEARCH_HL, curses.COLOR_BLACK, curses.COLOR_YELLOW)


__all__ = [
    'C_GREEN', 'C_GREY', 'C_WHITE', 'C_DIM', 'C_CURSOR_BG',
    'C_CYAN', 'C_HINT', 'C_CURSOR_GREEN', 'C_YELLOW', 'C_RED',
    'C_HEAT_1', 'C_HEAT_2', 'C_HEAT_3', 'C_HEAT_4',
    'C_MAGENTA', 'C_WS_ACTIVE', 'C_WS_DIM', 'C_SEARCH_HL',
    'init_colors'
]
