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

STATUS_LINE_Y = 5

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


OPEN_PROMPT = "Enter file name: "
OPEN_SUCCESS = "Successfully opened file"
WRITE_PROMPT = "Enter file name to save to: "
WRITE_SUCCESS = "Successfully wrote file"
input_prompt = ""
input_buffer = []
input_command = ""

filename = ""

x_pad = 1
matrix_elements = []
mode = "command"
text_buffer = []



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
        og_y, og_x = self.stdscr.getyx()
        

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
        stdscr.move(og_y, og_x)

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
    time.sleep(0.15)
    curses.endwin()
    # os.system("clear")
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
    height, width = stdscr.getmaxyx()
    curses.curs_set(0)
    curses.noecho()
    
    draw_text()
    # draw_background()

    # Draw custom header and workspace border
    stdscr.attron(RED_AND_BLACK)
    i = 0
    for heading in HEADER:
        start_x = get_x(width, heading)
        start_y = i
        stdscr.addstr(start_y, start_x, heading)
        i += 1
    rectangle(stdscr, 4, x_pad, height - 1 - STATUS_LINE_Y, width - 1 - x_pad)
    rectangle(stdscr, height - STATUS_LINE_Y, x_pad, height - 1, width - 1 - x_pad)

    stdscr.attroff(RED_AND_BLACK)


    stdscr.attron(WHITE_AND_BLACK)
    stdscr.attron(curses.A_BOLD)

    # Populate header information
    if filename != "":
        if filename[0] == '/':
            stdscr.addstr(height - STATUS_LINE_Y + 1, x_pad + 1, f"file: {filename}")
        else:
            stdscr.addstr(height - STATUS_LINE_Y + 1, x_pad + 1, f"file: {CWD}/{filename}")
    # stdscr.addstr(6, 5, f"x_pad:  {x_pad}")
    stdscr.addstr(height - STATUS_LINE_Y + 1, width - x_pad - 10, "q to quit")
    stdscr.addstr(height - STATUS_LINE_Y + 3, width - x_pad - len(mode) - 1, mode)
    # stdscr.addstr(7, 5, f"home: {HOME}")
    # add_to_stdout(f"{input_buffer =}")
    # stdscr.addstr(height - STATUS_LINE_Y + 2, x_pad + 1, "ENTER SHIT")
    if input_prompt != "":
        stdscr.addstr(height - STATUS_LINE_Y + 2, x_pad + 1, input_prompt)
        stdscr.addstr(height - STATUS_LINE_Y + 3, x_pad + 1, ''.join(input_buffer))

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
    stdscr.noutrefresh()

def clear_background_area():
    try:
        height, width = stdscr.getmaxyx()
        space_char = ' '.encode('utf-8')
        for y in range(curses.LINES):
            for x in range(curses.COLS):
                if x < x_pad or x >= width - x_pad:
                    stdscr.addstr(y, x, space_char)
    except Exception as e:
        add_to_stderr(f"{e =}")
        stdscr.noutrefresh()

def tick():
    while(True):
        clear_background_area()
        for ele in matrix_elements:
            ele.drop()
        draw_elements()
        loto = randint(0,1)
        if loto == 0:
            spawn_element()
        time.sleep(0.05)
        stdscr.noutrefresh()
        curses.doupdate()


def draw_text():
    height, width = stdscr.getmaxyx()
    x = x_pad + 1
    y = 5
    for c in text_buffer:
        if x >= width - x_pad - 1 or c == '\n':
            y += 1
            x = x_pad
        try:
            stdscr.addch(y, x, c, GREEN_AND_BLACK)
        except Exception as e:
            add_to_stderr(e)
        x += 1


def draw_elements():
    height, width = stdscr.getmaxyx()
    for matrix_element in matrix_elements:
        try:
            matrix_element.draw()
        except Exception as e:
            add_to_stderr(str(e))
            add_to_stderr(f"matrix element: {matrix_element}")
            matrix_elements.remove(matrix_element)
    stdscr.noutrefresh()


def spawn_element():
    height, width = stdscr.getmaxyx()
    combined_range = list(range(1, x_pad)) + list(range(width - x_pad, width - 1))
    random_number = random.choice(combined_range)
    matrix_element = MatrixElement(stdscr, 0, random_number)
    matrix_elements.append(matrix_element)


def write_file():
    global input_prompt
    try:
        with open(filename, 'w') as file:
            for line in text_buffer:
                file.write(line)
        add_to_stdout(f"Text buffer successfully written to '{filename}'.")
        input_prompt = WRITE_SUCCESS
    except Exception as e:
        print(f"Error writing to file '{filename}': {e}")


def open_file():
    global text_buffer
    global input_prompt
    text_buffer.clear()
    try:
        with open (filename, 'r') as file:
            for line in file:
                for char in line:
                    text_buffer.append(char)
        input_prompt = OPEN_SUCCESS
    except FileNotFoundError:
        add_to_stderr(f"{filename =}  File not found")


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
    global input_buffer
    global input_prompt
    global input_command
    global filename
    args = sys.argv[1:]
    height, width = stdscr.getmaxyx()

    if len(args) != 1:
        add_to_stderr("usage: textwall.py size(s/m/l)")
        clean_up(1)

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

    global mode

    # curses.curs_set(0)

    x, y = x_pad + 1, 5

    while True:

        draw_frame()
        
        stdscr.move(y, x)

        sel = stdscr.getkey()

        if mode == "command":
            add_to_stdout("COMMAND BLOCKING CURSOR")
            curses.curs_set(0)
            curses.noecho()
            if sel in('q', 'Q'): # quit, q/Q
                clean_up(0)
            elif sel in ('+', '='): # grow box, +/=
                x_pad -= 1
            elif sel == '-': # shrink box, -
                x_pad += 1
            elif sel == ' ': # pass space
                pass
            elif sel in ('o', 'O'): # write mode, w/W
                mode = "input"
                input_command = "open"
                input_prompt = OPEN_PROMPT
                # add_to_stdout(input_buffer)
            elif sel in ('w', 'W'): # open mode, o/O
                mode = "input"
                input_command = "write"
                input_prompt = WRITE_PROMPT
                # add_to_stdout(input_buffer)
            elif sel in ('i', 'I'): # insert mode, i/I
                mode = "insert"
        elif mode == "insert": # able to type in main buffer
            curses.echo()
            curses.curs_set(1)
            
            if sel in ('KEY_ESCAPE', '^[', '\x1b'):
                mode = "command"
                curses.curs_set(0)
                curses.noecho()
            elif sel == 'KEY_BACKSPACE':
                if len(text_buffer):
                    text_buffer.pop()
                x = max(x, 0)
            elif sel in ('KEY_ENTER', '\n'):
                # add_to_stdout("ENTER HIT")
                text_buffer.append(sel)
                y += 1
                x = x_pad + 1
                curses.curs_set(0)
                curses.noecho()
            else:
                text_buffer.append(sel)
                x += 1
            stdscr.noutrefresh()
        elif mode == "input": # command follow up input
            curses.echo()
            curses.curs_set(1)
            
            # stdscr.move(height - STATUS_LINE_Y + 2, x_pad + 1)
            # stdscr.addstr(height - STATUS_LINE_Y + 1, x_pad + 1, f"file:  {CWD}/FILE.TXT")
            # stdscr.addstr(height - STATUS_LINE_Y + 2, x_pad + 1, "Enter file name: ")
            # filename = stdscr.getstr(height - STATUS_LINE_Y + 2, x_pad + len("Enter file name: "), width - x_pad - len()).decode('utf-8')
            if sel in ('KEY_ESCAPE', '^[', '\x1b'):
                input_buffer.clear()
                curses.curs_set(0)
                curses.noecho()
                mode = "command"
            elif sel == 'KEY_BACKSPACE':
                if len(input_buffer):
                    input_buffer.pop()
                    stdscr.noutrefresh()
            elif sel == '\n':
                filename = ''.join(input_buffer)
                # add_to_stdout(filename)
                if input_command == "open":
                    add_to_stdout(f"HELLO {filename}")
                    curses.curs_set(0)
                    curses.noecho()
                    open_file()
                if input_command == "write":
                    add_to_stdout(f"GOODBYE {filename}")
                    curses.curs_set(0)
                    curses.noecho()
                    write_file()
                input_buffer.clear()
                mode = "command"
            else:
                input_buffer.append(sel)
                stdscr.noutrefresh()

            # add_to_stdout(f"FILE: {filename}")
            stdscr.noutrefresh()
            

        # add_to_stdout(input_buffer)
        curses.doupdate()
        # stdscr.erase()
        # stdscr.refresh()



    stdscr.getch()
    clean_up(0)


wrapper(main)
