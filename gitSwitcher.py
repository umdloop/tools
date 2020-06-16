#!/usr/bin/env python

import functools
import curses
from curses import panel
import glob
import os

# credit to @kalhartt, see SO post 14200721
class Menu(object):
    def __init__(self, items, stdscreen):
        self.window = stdscreen.subwin(0, 0)
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.position = 0
        self.items = items
        self.items.append(("exit", "exit"))

    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items) - 1

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.window.refresh()
            curses.doupdate()
            for index, item in enumerate(self.items):
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                msg = "%d. %s" % (index, item[0])
                self.window.addstr(1 + index, 1, msg, mode)

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                if self.position == len(self.items) - 1:
                    break
                else:
                    self.items[self.position][1](self.items[self.position][0])

            elif key == curses.KEY_UP or key == ord('k'):
                self.navigate(-1)

            elif key == curses.KEY_DOWN or key == ord('j'):
                self.navigate(1)
            elif key >= ord('0') and key <= ord('9'):
                self.position = key-ord('0')  
                if self.position < 0:
                    self.position = 0
                elif self.position >= len(self.items):
                    self.position = len(self.items) - 1

                if self.position == len(self.items) - 1:
                    break
                else:
                    self.items[self.position][1](self.items[self.position][0])

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()

def proc(stdscreen, name):
    os.unlink(".git")
    os.symlink(name, ".git")
    stdscreen.clear()
    stdscreen.addstr(0, 0, ".git linked to %s" % (name))
    stdscreen.refresh()

class MyApp(object):
    def __init__(self, stdscreen):
        self.screen = stdscreen
        curses.curs_set(0)
        file_count = 0
        files = glob.glob(".git*")

        for name in files:
            if not os.path.isdir(name) or name.endswith(".git") or name.endswith(".gitignore"):
                files.remove(name)
        
        main_menu_items = [(name, functools.partial(proc, stdscreen)) for name in files]

#        main_menu_items = [
#            ("beep", curses.beep),
#            ("flash", curses.flash),
#        ]
        main_menu = Menu(main_menu_items, self.screen)
        main_menu.display()


if __name__ == "__main__":
    curses.wrapper(MyApp)
