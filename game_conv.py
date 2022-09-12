import numpy as np
from scipy.ndimage import convolve

from lifeparser import autoguess_life_file


class GameOfLife:
    board = None
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]], dtype=np.uint8)

    def __init__(self, width, height):
        np.random.seed(42)

        self.board = np.zeros(
            width * height).reshape((width, height))

    def insert(self, x, y):
        self.board[x][y] = True

    def step(self):
        convolved_board = convolve(self.board, self.kernel, mode="wrap")
        self.board = (
            ((self.board == 0) & (convolved_board == 3)) |
            ((self.board == 1) & (convolved_board > 1) & (convolved_board < 4))
        ).astype(np.uint8)

    def get_cell(self, x, y):
        return self.board[x, y]

    def get_alive_cells(self):
        return list(zip(*np.nonzero(self.board)))

    @staticmethod
    def from_lif(filename):
        cells, _ = autoguess_life_file(filename)

        min_width = min(*[x for x, y in cells])
        min_height = min(*[y for x, y in cells])

        max_width = max(*[x for x, y in cells])
        max_height = max(*[y for x, y in cells])

        width = max_width - min_width
        height = max_height - min_height
        x_offset = int(width/4)
        y_offset = int(height/4)

        game = GameOfLife(width + 1 + x_offset * 2,
                          height + 1 + y_offset * 2)
        for x, y in cells:
            game.board[x - min_width + x_offset, y - min_height + y_offset] = 1

        return game

    @staticmethod
    def from_random(width, height):
        game = GameOfLife(width, height)

        game.board = np.random.random(
            width * height).reshape((width, height)).round()
        return game


if __name__ == "__main__":
    import sys

    print(GameOfLife.from_lif(sys.argv[1]))
