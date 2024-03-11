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
    white_rgb = (1000, 1000, 1000)  # Adjust as needed for your terminal
    red_rgb = (1000, 450, 450)
    green_rgb = (450, 1000, 450)
    green2_rgb = (350, 800, 350)  # Custom green color 2
    green3_rgb = (250, 600, 250)  # Custom green color 3
    green4_rgb = (150, 400, 150)  # Custom green color 4

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

class MatrixElement:
    def __init__(self, stdscr, y, x, trail_length=5):
        self.stdscr = stdscr
        self.y = y
        self.x = x
        self.trail_length = trail_length
        self.trail = []


    def drop(self):
        self.y += 1

    def draw(self):
        self.stdscr.addch(self.y, self.x, self.get_char(), curses.color_pair(3))
        if self.y > 0:
            self.stdscr.addch(self.y - 1, self.x, self.get_char(), curses.color_pair(4))
        if self.y > 1:
            self.stdscr.addch(self.y - 2, self.x, self.get_char(), curses.color_pair(5))
        if self.y > 2:
            self.stdscr.addch(self.y - 3, self.x, self.get_char(), curses.color_pair(6))

    def get_char(self):
        return randint(48, 90)

####################
# HELPER FUNCTIONS #
####################

# Exit gracefully, print from error buffer if debugging
def clean_up(status):
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
def draw_frame(stdscr):

    # Screen setup
    curses.curs_set(0)
    height, width = stdscr.getmaxyx()
    stdscr.clear()
    stdscr.refresh()
    
    # draw_background(stdscr)

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
        draw_frame(stdscr)
        for ele in matrix_elements:
            ele.drop()
        
        draw_elements(stdscr)
        loto = randint(0,1)
        if loto == 0:
            spawn_element(stdscr)
        time.sleep(0.05)
        stdscr.refresh()


def draw_elements(stdscr):
    height, width = stdscr.getmaxyx()
    for matrix_element in matrix_elements:
        if 0 < matrix_element.y < height and 0 < matrix_element.x < width:
            try:
                stdscr.attron(GREEN_AND_BLACK)
                matrix_element.draw()
                stdscr.attroff(GREEN_AND_BLACK)
            except Exception as e:
                add_to_stderr(str(e))
    stdscr.refresh()


def spawn_element(stdscr):
    height, width = stdscr.getmaxyx()
    combined_range = list(range(0, x_pad)) + list(range(width - x_pad, width))
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
    curses.curs_set(1)
    win = curses.newwin(height - 4 - 2, width - (2 * x_pad) - 2, 5, x_pad + 1)
    box = Textbox(win)
    stdscr.refresh()
    box.edit()
    curses.curs_set(0)


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

    stdscr.clear()


    draw_frame(stdscr)

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

    while True:

        sel = stdscr.getch()

        if sel in(113, 81): # quit
            clean_up(0)
        elif sel in (43, 61):
            x_pad -= 1
        elif sel == 45:
            x_pad += 1
        elif sel == 32:
            pass
        elif sel in (73, 105):
            create_textbox()



        stdscr.refresh()


    stdscr.getch()
    clean_up(0)


wrapper(main)
