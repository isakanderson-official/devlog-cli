"""Inline text editor widget for the TUI."""

import curses

from .colors import C_CYAN
from .drawing import saddstr


def text_input(scr, y, x, prompt, prefill=""):
    """
    Inline text editor for entering/editing task text.

    Returns the edited text or None if cancelled (Esc).
    """
    h, w = scr.getmaxyx()
    max_w = w - x - 2
    curses.curs_set(1)
    buf = list(prefill)
    pos = len(buf)
    scroll = 0

    while True:
        scr.move(y, x)
        scr.clrtoeol()
        saddstr(scr, y, x, prompt, curses.color_pair(C_CYAN) | curses.A_BOLD)
        vis_w = max_w - len(prompt)
        if vis_w < 4:
            vis_w = 4
        if pos - scroll >= vis_w:
            scroll = pos - vis_w + 1
        if pos < scroll:
            scroll = pos
        visible = "".join(buf[scroll : scroll + vis_w])
        saddstr(scr, y, x + len(prompt), visible)
        try:
            scr.move(y, x + len(prompt) + pos - scroll)
        except curses.error:
            pass
        scr.refresh()

        try:
            ch = scr.get_wch()
        except curses.error:
            continue

        if ch == "\n" or ch == curses.KEY_ENTER or (isinstance(ch, int) and ch in (10, 13)):
            break
        elif ch == "\x1b" or (isinstance(ch, int) and ch == 27):
            curses.curs_set(0)
            return None
        elif ch in (curses.KEY_BACKSPACE, "\x7f", "\b") or (isinstance(ch, int) and ch == 127):
            if pos > 0:
                buf.pop(pos - 1)
                pos -= 1
        elif ch == curses.KEY_DC:
            if pos < len(buf):
                buf.pop(pos)
        elif ch == curses.KEY_LEFT:
            pos = max(0, pos - 1)
        elif ch == curses.KEY_RIGHT:
            pos = min(len(buf), pos + 1)
        elif isinstance(ch, str) and len(ch) == 1 and ch.isprintable():
            buf.insert(pos, ch)
            pos += 1

    curses.curs_set(0)
    result = "".join(buf).strip()
    return result if result else None


__all__ = ["text_input"]
