#!/usr/bin/env python3

#
# Author: Sean O'Beirne
# Date: 03/08/2024
# File: app.py
# Usage: python3 textwall.py [s/m/l]
#

#
# Boilerplate for curses application
#


import curses
from curses import wrapper
from curses.textpad import rectangle, Textbox

import subprocess, os, sys, threading
import random
from random import randint

import time


HEADER = [
"         ____________________         ",
"     ___/_/_/            \_\_\___     ",
" ___/_/_/_/_/  welcome!  \_\_\_\_\___ ",
"/_/_/_/_/_/_/____________\_\_\_\_\_\_\\"
]

HOME = os.path.expanduser("~")
CWD = os.getcwd()

# For regular printing, after curses ends (debugging)
stderr_buffer = "RUNNING LOG; POST EXECUTION ERRORS:\n"
stdout_buffer = "RUNNING LOG; POST EXECUTION OUTPUT:\n"
# Enable / Disable debugging output
DEBUG = True


stdscr = curses.initscr()


# Define colors
curses.start_color()
if curses.can_change_color():
    black_rgb = (0, 0, 0)
    white_rgb = (1000, 1000, 1000)
    red_rgb = (1000, 450, 450)
    green_rgb = (450, 1000, 450)
    green2_rgb = (350, 800, 350)
    green3_rgb = (250, 600, 250)
    green4_rgb = (150, 400, 150)

    curses.init_color(curses.COLOR_BLACK, *black_rgb)
    curses.init_color(curses.COLOR_WHITE, *white_rgb)
    curses.init_color(curses.COLOR_RED, *red_rgb)
    curses.init_color(curses.COLOR_GREEN, *green_rgb)
    curses.init_color(curses.COLOR_GREEN + 1, *green2_rgb)
    curses.init_color(curses.COLOR_GREEN + 2, *green3_rgb)
    curses.init_color(curses.COLOR_GREEN + 3, *green4_rgb)
curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(4, curses.COLOR_GREEN + 1, curses.COLOR_BLACK)
curses.init_pair(5, curses.COLOR_GREEN + 2, curses.COLOR_BLACK)
curses.init_pair(6, curses.COLOR_GREEN + 3, curses.COLOR_BLACK)
RED_AND_BLACK = curses.color_pair(1)
WHITE_AND_BLACK = curses.color_pair(2)
GREEN_AND_BLACK = curses.color_pair(3)
GREEN2_AND_BLACK = curses.color_pair(4)
GREEN3_AND_BLACK = curses.color_pair(5)
GREEN4_AND_BLACK = curses.color_pair(6)

x_pad = 1
matrix_elements = []
curses_lock = threading.Lock()
mode = "command"



class MatrixElement:
    def __init__(self, stdscr, y, x, trail_length=8):
        self.stdscr = stdscr
        self.y = y
        self.x = x
        self.trail_length = trail_length
        self.trail = []

    def drop(self):
        self.y += 1

    def draw(self):
        # TODO: make this smart
        height, width = self.stdscr.getmaxyx()

        green = curses.color_pair(3)
        for line in range(self.trail_length):
            draw_y = self.y - line
            if 0 <= draw_y < height:
                # Check if the new location is empty
                if self.stdscr.inch(draw_y, self.x) == ord(' '):
                    self.stdscr.addch(draw_y, self.x, self.get_char(), green)
                    if line > 1:
                        green = curses.color_pair(4)
                    if line > 3:
                        green = curses.color_pair(5)
                    if line > 5:
                        green = curses.color_pair(6)

    def __str__(self):
        return f"Matrix Element\n{self.y =}\n{self.x =}\n{self.trail_length =}\n{self.trail =}\n{stdscr.getmaxyx = }\n"

    def get_char(self):
        return randint(48, 90)



####################
# HELPER FUNCTIONS #
####################

# Exit gracefully, print from error buffer if debugging
def clean_up(status):
    stdscr.clear()
    curses.endwin()
    if DEBUG:
        print(stderr_buffer)
        print()
        print(stdout_buffer)
    exit(status)

# Add addition to current stdout buffer
def add_to_stdout(addition):
    global stdout_buffer
    stdout_buffer += str(addition)
    stdout_buffer += '\n'

# Add addition to current stderr buffer
def add_to_stderr(addition):
    global stderr_buffer
    stderr_buffer += str(addition)
    stderr_buffer += '\n'


# Get the x for a centered string
def get_x(width, string):
    return max(0, (width - len(string)) // 2)


# Draws beautiful boiletplate screen with info and menu
def draw_frame():

    # Screen setup
    curses.curs_set(0)
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    # stdscr.refresh()
    
    # draw_background()

    # Draw custom header and workspace border
    stdscr.attron(RED_AND_BLACK)
    i = 0
    for heading in HEADER:
        start_x = get_x(width, heading)
        start_y = i
        stdscr.addstr(start_y, start_x, heading)
        i += 1
    rectangle(stdscr, 4, x_pad, height - 1, width - 1 - x_pad)

    stdscr.attroff(RED_AND_BLACK)


    stdscr.attron(WHITE_AND_BLACK)
    stdscr.attron(curses.A_BOLD)

    # Populate header information
    # stdscr.addstr(6, 5, f"cwd:  {CWD}")
    stdscr.addstr(6, 5, f"x_pad:  {x_pad}")
    stdscr.addstr(6, width - 14, "q to quit")
    stdscr.addstr(7, 5, f"home: {HOME}")

    # Populate menu
    """
    opt1 = "1 - create file shortcut in home"
    opt2 = "2 - delete a shortcut in home"
    opt3 = "3 - run home shortcuts report"
    stdscr.addstr(10,get_x(width, opt1), opt1)
    stdscr.addstr(11,get_x(width, opt2), opt2)
    stdscr.addstr(12,get_x(width, opt3), opt3)
    """

    stdscr.attroff(curses.A_BOLD)
    stdscr.attroff(WHITE_AND_BLACK)

    # Draw screen
    stdscr.refresh()


def tick():
    while(True):
        with curses_lock:
            draw_frame()
        for ele in matrix_elements:
            ele.drop()
        
        with curses_lock:
            draw_elements()
            loto = randint(0,1)
            if loto == 0:
                spawn_element()
            time.sleep(0.05)
            stdscr.refresh()


def draw_elements():
    height, width = stdscr.getmaxyx()
    for matrix_element in matrix_elements:
        try:
            matrix_element.draw()
        except Exception as e:
            add_to_stderr(str(e))
            add_to_stderr(f"matrix element: {matrix_element}")
            matrix_elements.remove(matrix_element)
    stdscr.refresh()


def spawn_element():
    height, width = stdscr.getmaxyx()
    combined_range = list(range(1, x_pad)) + list(range(width - x_pad, width - 1))
    random_number = random.choice(combined_range)
    matrix_element = MatrixElement(stdscr, 0, random_number)
    matrix_elements.append(matrix_element)


def get_input(stdscr, prompt):
    height, width = stdscr.getmaxyx()

    # Draw prompt
    prompt_x = get_x(width, prompt)
    x_i = prompt_x + 2
    stdscr.addstr(15, prompt_x, prompt)

    # Get file name from user
    stdscr.move(16, x_i)
    curses.echo()
    curses.curs_set(1)
    filename = stdscr.getstr(16, x_i, width - x_i - 2).decode('utf-8')
    curses.curs_set(0)
    curses.noecho()

    return filename

def create_textbox():
    height, width = stdscr.getmaxyx()

    # Calculate textbox position and size
    textbox_height = 3
    textbox_width = width - 2 - x_pad
    textbox_y = 5
    textbox_x = x_pad

    # Create a window for the textbox
    textbox_win = curses.newwin(textbox_height, textbox_width, textbox_y, textbox_x)

"""
    # Draw a border around the textbox
    textbox_win.border()

    # Enable text input
    curses.curs_set(1)
    textbox_win.addstr(1, 1, "Enter text: ")

    # Get user input
    textbox_content = textbox_win.getstr(1, 12, textbox_width - 12).decode("utf-8")

    # Disable text input
    curses.curs_set(0)

    return textbox_content
"""
"""
def create_textbox():
    height, width = stdscr.getmaxyx()
    curses.curs_set(1)
    win = curses.newwin(height - 4 - 2, width - (2 * x_pad) - 2, 5, x_pad + 1)
    box = Textbox(win)
    stdscr.refresh()
    box.edit()
    curses.curs_set(0)
"""

class MatrixThread(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            # Call the tick() method here
            tick()
            time.sleep(0.1)  # Sleep for 0.5 seconds


def main(stdscr):
    global x_pad
    args = sys.argv[1:]
    height, width = stdscr.getmaxyx()

    if args[0] == 's':
        x_pad = width // 4
    elif args[0] == 'm':
        x_pad = width // 8
    else:
        x_pad = 1

    stdscr.erase()


    draw_frame()

    try:
        background_thread = threading.Thread(target=tick)
        background_thread.daemon = True  # Daemonize the thread to automatically terminate it when the main thread exits
        background_thread.start()
    except Exception as e:
        add_to_stderr(e)

    # matrix_thread = MatrixThread()
    # matrix_thread_instance = threading.Thread(target=matrix_thread, args=(stdscr,))
    # matrix_thread_instance.start()
    # matrix_thread.start()
    global mode

    while True:

        sel = stdscr.getch()

        if mode == "command":
            if sel in(113, 81): # quit, q/Q
                clean_up(0)
            elif sel in (43, 61): # grow box, +/=
                x_pad -= 1
            elif sel == 45: # shrink box, -
                x_pad += 1
            elif sel == 32: # pass space
                pass
            elif sel in (73, 105): # insert mode, i/I
                mode = "insert"
                create_textbox()
        elif mode == "insert":
            if sel in(113, 81): # quit
                clean_up(0)
            elif sel in (43, 61):
                x_pad -= 1
            elif sel == 45:
                x_pad += 1
            elif sel == 32:
                pass
            elif sel in (73, 105):
                mode = "insert"
                create_textbox()
                textbox_content = create_textbox()
                # create_textbox(stdscr, height // 2, width // 2, 20)


        stdscr.erase()
        stdscr.refresh()


    stdscr.getch()
    clean_up(0)


wrapper(main)
