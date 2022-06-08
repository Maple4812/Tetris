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
    'maxfps': 60
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

    [[0, 7, 7],
     [0, 7, 7]]
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


def get_array(board):
    if len(board) == config['rows'] + 1:
        del board[board.index(board[config['rows']])]
    grid = np.array(board)
    for j in range(config['rows']):
        for i in range(config['cols']):
            if grid[j][i] != 0:
                grid[j][i] = 1

    return grid


def get_full_array(board):
    grid = np.array(board)
    for j in range(config['rows']):
        for i in range(config['cols']):
            if grid[j][i] != 0:
                grid[j][i] = 1

    return grid


def get_height_sum(board):
    height_sum = 0
    grid = get_array(board)
    for i in range(config['rows']):
        for j in range(config['cols']):
            if grid[i][j] == 1:
                height_sum += 1

    return height_sum


def get_difference(board):
    board = get_array(board).T
    grid = board.tolist()
    col_list = [0 for _ in range(config['cols'])]
    for i in range(config['cols']):
        if 1 in grid[i]:
            col_list[i] = grid[i].count(1)
    difference = max(col_list) - min(col_list)

    return difference


def get_bumpiness(board):
    board = get_array(board).T
    grid = board.tolist()
    bump_list = [0 for _ in range(config['cols'])]
    for i in range(config['cols']):
        if 1 in grid[i]:
            bump_list[i] = config['rows'] - grid[i].index(1)
    bumpiness = np.std(bump_list)

    return bumpiness


''''''


def get_peaks(board):
    board = get_array(board).T
    grid = board.tolist()
    bump_list = [0 for _ in range(config['cols'])]
    for i in range(config['cols']):
        if 1 in grid[i]:
            bump_list[i] = config['rows'] - grid[i].index(1)

    return bump_list


def get_max_wells(peaks):
    wells = [0 for _ in range(config['cols'])]
    for i in range(len(peaks)):
        if i == 0:
            w = peaks[1] - peaks[0]
            w = w if w > 0 else 0
            wells[i] = w
        elif i == len(peaks) - 1:
            w = peaks[-2] - peaks[-1]
            w = w if w > 0 else 0
            wells[i] = w
        else:
            w1 = peaks[i - 1] - peaks[i]
            w2 = peaks[i + 1] - peaks[i]
            w1 = w1 if w1 > 0 else 0
            w2 = w2 if w2 > 0 else 0
            w = w1 if w1 >= w2 else w2
            wells[i] = w
        max_well = np.std(wells)
    return max_well


''' https://ichi.pro/ko/yujeonhag-algolijeum-eulo-teteuliseu-gb-segye-gilog-eul-gyeongsin-118795294920347 '''


def get_holes(board):
    holes = 0
    board = get_array(board).T
    grid = board.tolist()
    for i in range(config['cols']):
        if 1 in grid[i]:
            holes += grid[i].count(0) - grid[i].index(1)

    return holes


def get_removed():
    return removed_row


def get_sides(board):
    grid = get_array(board)
    side = 0
    side_list = []
    for i in range(config['rows']):
        side_list.append([0, i])
        side_list.append([config['cols'] - 1, i])
    for j in range(config['cols']):
        side_list.append([j, config['rows'] - 1])
    for i, j in side_list:
        if grid[j][i] == 1:
            side += 1

    return side


def get_fitness(board, w_list):
    bumpiness = get_bumpiness(board)
    holes = get_holes(board)
    removed = get_removed()
    height_sum = get_height_sum(board)
    difference = get_difference(board)
    max_well = get_max_wells(get_peaks(board))
    sides = get_sides(board)

    score = bumpiness * w_list[0] + \
            holes * w_list[1] + \
            removed * w_list[2] + \
            height_sum * w_list[3] + \
            difference * w_list[4] + \
            max_well * w_list[5] + \
            sides * w_list[6]

    return round(score, 3)


##################################################################################


def get_current_block_text(shape):
    if shape == tetris_shapes[0]:
        return 'T'
    if shape == tetris_shapes[1]:
        return 'S'
    if shape == tetris_shapes[2]:
        return 'Z'
    if shape == tetris_shapes[3]:
        return 'J'
    if shape == tetris_shapes[4]:
        return 'L'
    if shape == tetris_shapes[5]:
        return 'I'
    if shape == tetris_shapes[6]:
        return 'O'


def check_needed_turn(block):
    # Check how many turns we need to check for a block
    if block == 'I' or block == 'S' or block == 'Z':
        return 2
    elif block == 'O':
        return 1
    else:
        return 4


def check_needed_dirs(block):
    # Return left, right moves needed
    if block == 'I':
        return 3, 6
    elif block == 'O':
        return 4, 7
    else:
        return 3, 5


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
        self.stone = tetris_shapes[rand(len(tetris_shapes))]  # 블럭 랜덤 부분
        self.stone_x = int(config['cols'] / 2 - len(self.stone[0]) / 2)
        self.stone_y = 0

        if check_collision(self.board,
                           self.stone,
                           (self.stone_x, self.stone_y)):
            self.gameover = True

    def new_stone2(self):
        self.stone2 = tetris_shapes[rand(len(tetris_shapes))]
        self.stone2_x = int(config['cols'] / 2 - len(self.stone2[0]) / 2)
        self.stone2_y = 0

        if check_collision(self.board2,
                           self.stone2,
                           (self.stone2_x, self.stone2_y)):
            self.gameover2 = True

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

    def move2(self, delta_x, board):
        if not self.gameover2 and not self.paused:
            new_x = self.stone2_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > config['cols'] - len(self.stone2[0]):
                new_x = config['cols'] - len(self.stone2[0])
            if not check_collision(board,
                                   self.stone2,
                                   (new_x, self.stone2_y)):
                self.stone2_x = new_x

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

    def drop2(self, board):
        if not self.paused:
            self.stone2_y += 1
            if check_collision(board,
                               self.stone2,
                               (self.stone2_x, self.stone2_y)):
                self.board2 = join_matrix(
                    board,
                    self.stone2,
                    (self.stone2_x, self.stone2_y))
                self.new_stone2()
                while True:
                    for i, row in enumerate(self.board2[:-1]):
                        if 0 not in row:
                            self.board2 = remove_row2(
                                self.board2, i)
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

    def drop_down2(self, board):
        started_moving = False
        start_y = 0
        while start_y != self.stone2_y or not started_moving:
            pygame.time.set_timer(pygame.USEREVENT + 1, 1)
            started_moving = True
            self.drop2(board)
        pygame.time.set_timer(pygame.USEREVENT + 1, config['delay'])

    def rotate_stone(self, board):
        if not self.gameover and not self.paused:
            new_stone = rotate_clockwise(self.stone)
            if not check_collision(board,
                                   new_stone,
                                   (self.stone_x, self.stone_y)):
                self.stone = new_stone

    def rotate_stone2(self, board):
        if not self.gameover2 and not self.paused:
            new_stone = rotate_clockwise(self.stone2)
            if not check_collision(board,
                                   new_stone,
                                   (self.stone2_x, self.stone2_y)):
                self.stone2 = new_stone

    def toggle_pause(self):
        self.paused = not self.paused

    def start_game(self):
        if self.gameover:
            self.init_game()
            self.gameover = False

    def draw_lines(self):
        font = pygame.font.SysFont('calibri', 30, True, True)
        self.game_score = removed_row * 100
        score_message = "Lines: " + str(removed_row)
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

    def go_sideway(self, way, dirs, board):
        if way == 'Left':
            self.move(-dirs, board)
        if way == 'Right':
            self.move(+dirs, board)

    def go_sideway2(self, way, dirs, board):
        if way == 'Left':
            self.move2(-dirs, board)
        if way == 'Right':
            self.move2(+dirs, board)

    def go_down(self, board):
        self.drop_down(board)

    def go_down2(self, board):
        self.drop_down2(board)

    def rotate(self, board):
        self.rotate_stone(board)

    def rotate2(self, board):
        self.rotate_stone2(board)

    #############################################

    def eval_network(self, w_list):
        self.init_game()
        self.init_game2()

        scores = []
        run_per_child = 99999
        max_score = 99999
        run = 0

        pygame.time.set_timer(pygame.USEREVENT + 1, config['delay'])

        while run < run_per_child:
            self.gameover = False
            self.gameover2 = False
            self.paused = False
            action_list = []
            self.game_score = 0
            self.screen.fill((0, 0, 0))
            self.draw_lines()

            self.draw_matrix(self.board, (0, 0))
            self.draw_matrix(self.stone,
                             (self.stone_x,
                              self.stone_y))

            pygame.display.update()

            self.board2 = copy.deepcopy(self.board)
            self.stone2 = copy.deepcopy(self.stone)
            current_board = copy.deepcopy(self.board)
            current_block = copy.deepcopy(self.stone)

            cur_block = get_current_block_text(self.stone2)
            needed_turn = check_needed_turn(cur_block)
            needed_left, needed_right = check_needed_dirs(cur_block)

            # left
            for turn in range(needed_turn):
                for dirs in range(1, needed_left + 1):
                    self.drop2(self.board2)
                    for _ in range(turn):
                        self.rotate_stone2(self.board2)
                    self.go_sideway2('Left', dirs, self.board2)
                    self.drop_down2(self.board2)
                    action = {'Turn': turn, 'Left': dirs, 'Right': 0, 'Fitness': get_fitness(self.board2, w_list)}
                    action_list.append(action)
                    self.board2 = copy.deepcopy(current_board)
                    self.stone2 = current_block
                    time.sleep(0.001)

            # right
            for turn in range(needed_turn):
                for dirs in range(1, needed_right + 1):
                    self.drop2(self.board2)
                    for _ in range(turn):
                        self.rotate_stone2(self.board2)
                    self.go_sideway2('Right', dirs, self.board2)
                    self.drop_down2(self.board2)
                    action = {'Turn': turn, 'Left': 0, 'Right': dirs, 'Fitness': get_fitness(self.board2, w_list)}
                    action_list.append(action)
                    self.board2 = copy.deepcopy(current_board)
                    self.stone2 = current_block
                    time.sleep(0.001)

            # middle
            for turn in range(needed_turn):
                for _ in range(turn):
                    self.rotate_stone2(self.board2)
                self.drop2(self.board2)
                self.drop_down2(self.board2)
                action = {'Turn': turn, 'Left': 0, 'Right': 0, 'Fitness': get_fitness(self.board2, w_list)}
                action_list.append(action)
                self.board2 = copy.deepcopy(current_board)
                self.stone2 = current_block
                time.sleep(0.001)

            # 일단 'O'의 경우에 왼쪽으로 한 칸씩 밀린다...ㅠㅠㅠ

            def get_key(l):
                return l['Fitness']

            action_list.sort(key=get_key)
            action_list.reverse()
            best_action = action_list[0]

            # Do best action
            for _ in range(best_action['Turn']):
                self.rotate(self.board)
            self.go_sideway('Left', best_action['Left'], self.board)
            self.go_sideway('Right', best_action['Right'], self.board)
            self.drop(self.board)
            self.drop_down(self.board)

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    pass
                elif event.type == pygame.QUIT:
                    self.quit()

            if self.gameover or self.game_score > max_score:
                scores.append(self.game_score)
                global removed_row
                removed_row = 0
                if run == run_per_child - 1:
                    child_fitness = np.average(scores)

                    return child_fitness
                else:
                    self.start_game()
                run += 1

    def run_ai(self, w_list):
        self.init_game()
        self.init_game2()

        scores = []
        run_per_child = 1
        run = 0

        pygame.time.set_timer(pygame.USEREVENT + 1, config['delay'])

        while run < run_per_child:
            self.gameover = False
            self.gameover2 = False
            self.paused = False
            action_list = []
            self.game_score = 0
            self.screen.fill((0, 0, 0))
            self.draw_lines()

            self.draw_matrix(self.board, (0, 0))
            self.draw_matrix(self.stone,
                             (self.stone_x,
                              self.stone_y))

            pygame.display.update()

            self.board2 = copy.deepcopy(self.board)
            self.stone2 = copy.deepcopy(self.stone)
            current_board = copy.deepcopy(self.board)
            current_block = copy.deepcopy(self.stone)

            cur_block = get_current_block_text(self.stone2)
            needed_turn = check_needed_turn(cur_block)
            needed_left, needed_right = check_needed_dirs(cur_block)

            # left
            for turn in range(needed_turn):
                for dirs in range(1, needed_left + 1):
                    self.drop2(self.board2)
                    for _ in range(turn):
                        self.rotate_stone2(self.board2)
                    self.go_sideway2('Left', dirs, self.board2)
                    self.drop_down2(self.board2)
                    action = {'Turn': turn, 'Left': dirs, 'Right': 0, 'Fitness': get_fitness(self.board2, w_list)}
                    action_list.append(action)
                    self.board2 = copy.deepcopy(current_board)
                    self.stone2 = current_block
                    time.sleep(0.3)

            # right
            for turn in range(needed_turn):
                for dirs in range(1, needed_right + 1):
                    self.drop2(self.board2)
                    for _ in range(turn):
                        self.rotate_stone2(self.board2)
                    self.go_sideway2('Right', dirs, self.board2)
                    self.drop_down2(self.board2)
                    action = {'Turn': turn, 'Left': 0, 'Right': dirs, 'Fitness': get_fitness(self.board2, w_list)}
                    action_list.append(action)
                    self.board2 = copy.deepcopy(current_board)
                    self.stone2 = current_block
                    time.sleep(0.3)

            # middle
            for turn in range(needed_turn):
                for _ in range(turn):
                    self.rotate_stone2(self.board2)
                self.drop2(self.board2)
                self.drop_down2(self.board2)
                action = {'Turn': turn, 'Left': 0, 'Right': 0, 'Fitness': get_fitness(self.board2, w_list)}
                action_list.append(action)
                self.board2 = copy.deepcopy(current_board)
                self.stone2 = current_block
                time.sleep(0.3)

            # 일단 'O'의 경우에 왼쪽으로 한 칸씩 밀린다...ㅠㅠㅠ

            def get_key(l):
                return l['Fitness']

            action_list.sort(key=get_key)
            action_list.reverse()
            best_action = action_list[0]

            # Do best action
            for _ in range(best_action['Turn']):
                self.rotate(self.board)
            self.go_sideway('Left', best_action['Left'], self.board)
            self.go_sideway('Right', best_action['Right'], self.board)
            self.drop(self.board)
            self.drop_down(self.board)

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    pass
                elif event.type == pygame.QUIT:
                    self.quit()

            if self.gameover:
                scores.append(self.game_score)
                global removed_row
                removed_row = 0
                if run == run_per_child - 1:
                    child_fitness = np.average(scores)

                    return child_fitness
                else:
                    self.start_game()
                run += 1

    #####################################


if __name__ == '__main__':
    App = TetrisApp()
    App.eval_network([-0.6, -0.95, 0.92, -0.04, -0.07, -0.8, 0.18])

    # score =
    #         bumpiness
    #         \* w_list[0] + \
    #         holes * w_list[1] + \
    #         removed * w_list[2] + \
    #         height_sum * w_list[3] + \
    #         difference * w_list[4] + \
    #         max_well * w_list[5] + \
    #         sides * w_list[6]

# TODO Visualization 과정에 있어서 하나의 세대의 모든 유전자를 한번에 eval_network 실행
# TODO 일반적으로 인공지능을 실행시킬 때에는 eval_network 말고 다른 코드 사용하여 메모리 사용 최소화
# TODO 병렬연산
