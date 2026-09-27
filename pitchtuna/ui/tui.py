"""Curses-based real-time terminal UI.

A thin wrapper around the curses screen. All musical content still comes from
:mod:`pitchtuna.ui.table`; this class only places the text and polls keys.
Non-ASCII glyphs are stripped for the curses view to keep legacy terminals
safe; the graphical dial and one-shot views keep the full emoji set.
"""

from __future__ import annotations

import curses
from typing import List

from .table import render_block


class CursesUI:
    def __enter__(self) -> "CursesUI":
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
        return self

    def __exit__(self, *exc) -> None:
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    @staticmethod
    def _ascii(line: str) -> str:
        return line.encode("ascii", "ignore").decode("ascii")

    def draw(self, ev, tuning, a4: float) -> None:
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        block = render_block(ev, tuning, a4)
        lines: List[str] = block.split("\n")
        footer = "Keys:  [q] quit   [c] next instrument   [C] previous"
        lines.append("")
        lines.append(footer)
        for y, line in enumerate(lines):
            if y >= height - 1:
                break
            text = self._ascii(line)[: max(0, width - 1)]
            try:
                self.stdscr.addstr(y, 0, text)
            except curses.error:
                pass
        self.stdscr.refresh()

    def poll_key(self) -> int:
        return self.stdscr.getch()
