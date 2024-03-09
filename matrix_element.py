from random import randint

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
        self.stdscr.addch(self.y, self.x, self.get_char())
        self.stdscr.addch(self.y - 1, self.x, self.get_char())
        self.stdscr.addch(self.y - 2, self.x, self.get_char())
        self.stdscr.addch(self.y - 3, self.x, self.get_char())

    def get_char(self):
        return randint(48, 90)

