import time
from random import randrange as rand
import pygame, sys
import numpy as np
import copy

# The configuration
config = {
    'cell_size': 30,
    'cols': 10,
    'rows': 20,
    'delay': 750,
    'maxfps': 30
}

removed_row = 0
blank_space = 300

colors = [
    (0, 0, 0),
    (255, 0, 0),
    (0, 150, 0),
    (0, 0, 255),
    (255, 120, 0),
    (255, 255, 0),
    (180, 0, 255),
    (0, 220, 220)
]

# Define the shapes of the single parts
tetris_shapes = [
    [[1, 1, 1],
     [0, 1, 0]],

    [[0, 2, 2],
     [2, 2, 0]],

    [[3, 3, 0],
     [0, 3, 3]],

    [[4, 0, 0],
     [4, 4, 4]],

    [[0, 0, 5],
     [5, 5, 5]],

    [[6, 6, 6, 6]],

    [[7, 7],
     [7, 7]]
]


def rotate_clockwise(shape):
    return [[shape[y][x]
             for y in range(len(shape))]
            for x in range(len(shape[0]) - 1, -1, -1)]


def check_collision(board, shape, offset):
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            try:
                if cell and board[cy + off_y][cx + off_x]:
                    return True
            except IndexError:
                return True
    return False


def remove_row(board, row):
    del board[row]
    global removed_row
    removed_row += 1
    return [[0 for i in range(config['cols'])]] + board


def remove_row2(board, row):
    del board[row]
    return [[0 for i in range(config['cols'])]] + board


def join_matrix(mat1, mat2, mat2_off):
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cy + off_y - 1][cx + off_x] += val
    return mat1


def new_board():
    board = [[0 for x in range(config['cols'])]
             for y in range(config['rows'])]
    board += [[1 for x in range(config['cols'])]]
    return board


##################################################################################


class TetrisApp(object):
    def __init__(self):
        self.game_score = 0
        pygame.init()
        pygame.key.set_repeat(250, 25)
        self.width = config['cell_size'] * config['cols'] + blank_space
        self.height = config['cell_size'] * config['rows']

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.event.set_blocked(pygame.MOUSEMOTION)  # We do not need
        # mouse movement
        # events, so we
        # block them.
        self.init_game()

    def new_stone(self):
        self.stone = tetris_shapes[rand(len(tetris_shapes))]
        self.stone_x = int(config['cols'] / 2 - len(self.stone[0]) / 2)
        self.stone_y = 0

        if check_collision(self.board,
                           self.stone,
                           (self.stone_x, self.stone_y)):
            self.gameover = True

    def init_game(self):
        self.board = new_board()
        self.new_stone()

    def init_game2(self):
        self.board2 = new_board()
        self.new_stone2()

    def center_msg(self, msg):
        for i, line in enumerate(msg.splitlines()):
            msg_image = pygame.font.Font(
                pygame.font.get_default_font(), 12).render(
                line, False, (255, 255, 255), (0, 0, 0))

            msgim_center_x, msgim_center_y = msg_image.get_size()
            msgim_center_x //= 2
            msgim_center_y //= 2

            self.screen.blit(msg_image, (
                self.width // 2 - msgim_center_x,
                self.height // 2 - msgim_center_y + i * 22))

    def draw_matrix(self, matrix, offset):
        off_x, off_y = offset
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val:
                    pygame.draw.rect(
                        self.screen,
                        colors[val],
                        pygame.Rect(
                            (off_x + x) *
                            config['cell_size'],
                            (off_y + y) *
                            config['cell_size'],
                            config['cell_size'],
                            config['cell_size']), 0)

    def move(self, delta_x, board):
        if not self.gameover and not self.paused:
            new_x = self.stone_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > config['cols'] - len(self.stone[0]):
                new_x = config['cols'] - len(self.stone[0])
            if not check_collision(board,
                                   self.stone,
                                   (new_x, self.stone_y)):
                self.stone_x = new_x

    def quit(self):
        self.center_msg("Exiting...")
        pygame.display.update()
        sys.exit()

    def drop(self, board):
        self.board = board
        if not self.gameover and not self.paused:
            self.stone_y += 1
            if check_collision(board,
                               self.stone,
                               (self.stone_x, self.stone_y)):
                self.board = join_matrix(
                    board,
                    self.stone,
                    (self.stone_x, self.stone_y))
                self.new_stone()
                while True:
                    for i, row in enumerate(self.board[:-1]):
                        if 0 not in row:
                            self.board = remove_row(
                                self.board, i)
                            break
                    else:
                        break

    def drop_down(self, board):
        started_moving = False
        start_y = 0
        while start_y != self.stone_y or not started_moving:
            pygame.time.set_timer(pygame.USEREVENT + 1, 1)
            started_moving = True
            self.drop(board)
        pygame.time.set_timer(pygame.USEREVENT + 1, config['delay'])

    def rotate_stone(self, board):
        if not self.gameover and not self.paused:
            new_stone = rotate_clockwise(self.stone)
            if not check_collision(board,
                                   new_stone,
                                   (self.stone_x, self.stone_y)):
                self.stone = new_stone

    def toggle_pause(self):
        self.paused = not self.paused

    def start_game(self):
        if self.gameover:
            self.init_game()
            self.gameover = False

    def draw_lines(self):
        font = pygame.font.SysFont('calibri', 30, True, True)
        self.game_score = removed_row * 100
        score_message = "Score: " + str(removed_row*100)
        screen_message = font.render(score_message, True, (255, 255, 255))
        text_width, text_height = font.size(score_message)
        self.screen.blit(screen_message,
                         [config['cell_size'] * config['cols'] + (blank_space - text_width) / 2, self.height / 2])
        pygame.draw.line(self.screen, (255, 255, 255), (config['cell_size'] * config['cols'], 0),
                         (config['cell_size'] * config['cols'], config['cell_size'] * config['rows']), 1)
        for i in range(config['cols']):
            pygame.draw.line(self.screen, (100, 100, 100), (config['cell_size'] * i, 0),
                             (config['cell_size'] * i, config['cell_size'] * config['rows']), 1)
        for j in range(config['rows']):
            pygame.draw.line(self.screen, (100, 100, 100), (0, config['cell_size'] * j),
                             (config['cell_size'] * config['cols'], config['cell_size'] * j), 1)

    #####################################

    def run(self):
        key_actions = {
            'ESCAPE': self.quit,
            'LEFT': lambda: self.move(-1, self.board),
            'RIGHT': lambda: self.move(+1, self.board),
            'DOWN': lambda: self.drop(self.board),
            'UP': lambda: self.rotate_stone(self.board),
            'p': self.toggle_pause,
            's': self.start_game,
            'SPACE': lambda: self.drop_down(self.board)
        }

        self.gameover = False
        self.paused = False

        pygame.time.set_timer(pygame.USEREVENT + 1, config['delay'])
        cpu = pygame.time.Clock()
        while True:
            self.screen.fill((0, 0, 0))
            self.draw_lines()
            if self.gameover:
                self.center_msg("""Game Over! Press A to continue""")
                global removed_row
                removed_row = 0
            else:
                if self.paused:
                    self.center_msg("Paused")
                else:
                    self.draw_matrix(self.board, (0, 0))
                    self.draw_matrix(self.stone,
                                     (self.stone_x,
                                      self.stone_y))

            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    self.drop(self.board)
                elif event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    for key in key_actions:
                        if event.key == eval("pygame.K_"
                                             + key):
                            key_actions[key]()

            cpu.tick(config['maxfps'])


if __name__ == '__main__':
    App = TetrisApp()
    App.run()
