from functools import reduce
import collections
import os
from enum import Enum
from functools import reduce
import collections
import copy
import pygame
import time
import pygame
import random



OPPOSITE_MOVES = dict(UP="DOWN", LEFT="RIGHT", DOWN="UP", RIGHT="LEFT")
DIRECTION_FROM_MOVE = dict(UP=(0,-1), LEFT=(-1,0), DOWN=(0,1), RIGHT=(1,0), NONE=(0,0))


def calculate_euclidean_distance_to_target(current, target):
    return (current[0] - target[0]) ** 2 + (current[1] - target[1]) ** 2


def get_next_position_by_move(current_position):
    return dict(UP=(current_position[0] + DIRECTION_FROM_MOVE["UP"][0], current_position[1] + DIRECTION_FROM_MOVE["UP"][1]),
                              LEFT=(current_position[0] + DIRECTION_FROM_MOVE["LEFT"][0], current_position[1] + DIRECTION_FROM_MOVE["LEFT"][1]),
                              DOWN=(current_position[0] + DIRECTION_FROM_MOVE["DOWN"][0], current_position[1] + DIRECTION_FROM_MOVE["DOWN"][1]),
                              RIGHT=(current_position[0] + DIRECTION_FROM_MOVE["RIGHT"][0], current_position[1] + DIRECTION_FROM_MOVE["RIGHT"][1]))

# NB: use lower case file names to ensure it will work on all OS

_image_library = {}


def get_image(path, force_reload=False):
    global _image_library
    image = _image_library.get(path)
    if image == None or force_reload:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(canonicalized_path)
        _image_library[path] = image
    return image


class Action(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    @staticmethod
    def get_all_actions():
        return [action for action in Action]

class GameState:
    def __init__(self):
        self.pacman = None
        self.walls = []
        self.ghosts = []
        self.dots = []
        self.dimensions = []
        # As walls are static, we do not need to look them up every time we need to know
        self.wall_positions = []
        self.last_game_event = None
        self.num_dots_left = 0

    def __str__(self):
        board = self.get_text_representation_of_gamestate()
        collapsed = [''.join(row) for row in board]

        return '\n'.join(collapsed)

    def __hash__(self):
        obj_hash = hash(tuple([9*x for x in self.pacman.position]))

        for w in self.walls:
            obj_hash += hash(w.position)

        for g in self.ghosts:
            obj_hash += hash(g.position)

        for d in self.dots:
            if not d.is_eaten:
                obj_hash += hash(d.position)

        return obj_hash

    def __eq__(self, other):
        if isinstance(other, GameState):
            if self.pacman.position != other.pacman.position:
                return False
            if collections.Counter([w.position for w in self.walls]) != collections.Counter([w.position for w in other.walls]):
                return False
            if collections.Counter([w.position for w in self.ghosts]) != collections.Counter([w.position for w in other.ghosts]):
                return False
            if collections.Counter([w.position for w in self.dots]) != collections.Counter([w.position for w in other.dots]):
                return False
            if self.num_dots_left != other.num_dots_left:
                return False
        return True

    def get_active_dots(self):
        return [dot for dot in self.dots if not dot.is_eaten]

    def get_number_of_dots_eaten(self):
        # TODO: Test
        return reduce((lambda acc, dot: acc + 1 if dot.is_eaten else acc), self.dots, 0)

    def get_wall_positions(self):
        return self.wall_positions

    def get_corners(self):
        w, h = self.dimensions
        return [(0,0), (w, 0), (0, h), (h, w)]

    def has_won(self):
        if len(self.get_active_dots()) > 0:
            return False
        if len(self.get_active_fruits()) > 0:
            return False
        if self.pacman.lives > 0:
            return True
        return False

    def has_lost(self):
        return self.pacman.lives <= 0

    def calculate_score(self):
        score = 0
        for dot in self.dots:
            score += dot.score if dot.is_eaten else 0
        return score - self.pacman.number_of_ticks

    # The order matters. It determines the drawing order
    def retrieve_all_active_items(self):
        items = []
        items.extend(self.walls)
        items.extend(self.get_active_dots())
        items.extend(self.ghosts)
        items.append(self.pacman)
        return items

    def insert_object_symbol_into_textual_gamestate(self, item, board):
        board[item.position[1]][item.position[0]] = item.symbol

    def get_text_representation_of_gamestate(self):
        board = [[' ' for i in range(self.dimensions[1])] for j in range(self.dimensions[0])]
        active_items = self.retrieve_all_active_items()
        for item in active_items:
            self.insert_object_symbol_into_textual_gamestate(item, board)
        return board

class ActionEvent(Enum):
    DOT = 1
    CAPTURED_BY_GHOST = 2
    OUT_OF_LIVES = 4
    WALL = 7
    NONE = 8
    WON = 9
    LOST = 10


def add_move_to_position(old_position, move):
    return old_position[0] + move[0], old_position[1] + move[1]


def is_eaten_by_ghost(gamestate, position):
    for ghost in gamestate.ghosts:
        if ghost.position == position:
            reset(gamestate)
            break


def reset(gamestate):
    for ghost in gamestate.ghosts:
        ghost.respawn()
    gamestate.pacman.lose_life(1)
    gamestate.pacman.respawn()


def check_ghost_collisions(gamestate):
    for ghost in gamestate.ghosts:
        if ghost.position == gamestate.pacman.position:
            gamestate.last_game_event = ActionEvent.CAPTURED_BY_GHOST
            reset(gamestate)

    return None


def check_if_pacman_ate_food(
        current_game_state,
        next_game_state
):
    """
        Determine if Pac-Man has eaten food
    Args:
        current_game_state (GameState):
        next_game_state (GameState):

    Returns:

    """
    if has_eaten_dot(current_game_state, next_game_state):
        return ActionEvent.DOT
    else:
        return None


def has_eaten_dot(current_game_state, next_game_state):
    """
        Determine if Pac-Man has eaten dot
    Args:
        current_game_state (GameState):
        next_game_state (GameState):

    Returns:
        Boolean
    """
    dots_diff = current_game_state.num_dots_left - next_game_state.num_dots_left
    if dots_diff == 1:
        return True
    elif dots_diff != 1 and dots_diff != 0:
        raise Exception("Error: dots_diff should be 0 or 1. Dots diff:", dots_diff)
    else:
        return False


def get_next_game_state_from_action(current_game_state, action):
    """

    Args:
        current_game_state (GameState):
        action:
        game:

    Returns:

    """
    next_game_state = copy.deepcopy(current_game_state)
    next_game_state.pacman.set_move(action)

    is_move_valid = next_game_state.pacman.tick(next_game_state)
    if not is_move_valid:
        next_game_state.last_game_event = ActionEvent.WALL
    else:
        next_game_state.last_game_event = ActionEvent.NONE

    eaten_food = check_if_pacman_ate_food(current_game_state, next_game_state)
    if eaten_food is not None:
        next_game_state.last_game_event = eaten_food

    check_ghost_collisions(next_game_state)

    for ghost in next_game_state.ghosts:
        ghost.tick()

    check_ghost_collisions(next_game_state)

    if next_game_state.has_won():
        next_game_state.last_game_event = ActionEvent.WON

    if next_game_state.has_lost():
        next_game_state.last_game_event = ActionEvent.LOST

    return next_game_state, next_game_state.last_game_event


def get_next_gamestate_DEBUG(gamestate):
    print("----------")
    print(gamestate)
    print('|')
    print('|')
    print('|')
    print('\\/')
    for move in ["UP", "LEFT", "DOWN", "RIGHT"]:
        print(get_next_game_state_from_action(gamestate, move))


# Returns how the gamestate would look if current move is executed
def get_next_gamestate_by_move(gamestate):
    return {move: get_next_game_state_from_action(gamestate, move) for move in ["UP", "LEFT", "DOWN", "RIGHT"]}


def is_wall(gamestate, position):
    for wall in gamestate.walls:
        if wall.position == position:
            return True
    return False


class Existence:
    def __init__(self, location, gamestate, icon, symbol, score=0):
        self.position = location
        self.previous_position = location
        self.icon = icon
        self.gamestate = gamestate
        self.symbol = symbol
        self.score = score

    def get_position(self):
        return self.position

    def get_icon(self):
        return self.icon

    def get_symbol(self):
        return self.symbol

    def move(self, direction):
        self.previous_position = self.position
        if self.is_move_valid(direction):
            self.position = self.position[0] + direction[0], self.position[1] + direction[1]
            return True
        else:
            return False

    def is_move_valid(self, direction):
        old_position = self.position
        attempted_new_position = add_move_to_position(old_position, direction)
        return not is_wall(self.gamestate, attempted_new_position)


class Dot(Existence):
    def __init__(self, position, gamestate):
        self.is_eaten = False
        super().__init__(position, gamestate, icon='pacdot.png', symbol='.', score=10)

    def eat(self):
        self.is_eaten = True


# Ghost logic mostly follows this: http://gameinternals.com/post/2072558330/understanding-pac-man-ghost-behavior

CHASE = 'CHASE'
SCATTER = 'SCATTER'
FRIGHTENED_DURATION = 5


class Ghost(Existence):
    def __init__(self, position, gamestate):
        super().__init__(position, gamestate, icon='ghost.png', symbol='G', score=100)

        self.respawn_position = position
        self.target_position = (3, 3)
        self.mode = CHASE
        self.previous_move = None
        self.time_at_respawn = time.time()
        self.time_at_last_tick = time.time()

    def ghost_event_routine(self):
        if time.time() - self.time_at_respawn > 84:
            return CHASE
        if time.time() - self.time_at_respawn > 79:
            return SCATTER
        if time.time() - self.time_at_respawn > 59:
            return CHASE
        if time.time() - self.time_at_respawn > 54:
            return SCATTER
        if time.time() - self.time_at_respawn > 34:
            return CHASE
        if time.time() - self.time_at_respawn > 27:
            return SCATTER
        if time.time() - self.time_at_respawn > 7:
            return CHASE
        return SCATTER

    def respawn(self):
        self.time_at_respawn = time.time()
        self.position = self.respawn_position

    def get_available_moves(self):
        all_possible_moves = get_next_position_by_move(self.position)

        non_blocked_moves = {}
        for direction, new_position in all_possible_moves.items():
            # Remove directions that hit a wall
            if new_position in self.gamestate.get_wall_positions():
                continue
            # Remove previous direction
            if OPPOSITE_MOVES[direction] == self.previous_move:
                continue
            non_blocked_moves[direction] = new_position

        # This means that we are stuck in a corner
        if len(non_blocked_moves.values()) == 0:
            opposite_direction = OPPOSITE_MOVES[self.previous_move]
            non_blocked_moves[opposite_direction] = all_possible_moves[opposite_direction]

        return non_blocked_moves

    def get_direction(self):
        possible_moves = self.get_available_moves()
        distance_per_move = {}
        for direction, new_position in possible_moves.items():
            distance_per_move[direction] = calculate_euclidean_distance_to_target(self.target_position, new_position)

        min_distance = min(distance_per_move.values())
        best_moves = [move for move in distance_per_move if distance_per_move[move] == min_distance]
        return self.get_prioritized_moves(best_moves)

    def get_prioritized_moves(self, possible_moves):
        for move in possible_moves:
            if move == "UP":
                return move
            if move == "LEFT":
                return move
            if move == "DOWN":
                return move
            if move == "RIGHT":
                return move

    def chase_pacman(self):
        direction = self.get_direction()
        self.execute_move(direction)

    def scatter(self):
        direction = self.get_direction()
        self.execute_move(direction)

    def execute_move(self, next_move):
        self.previous_move = next_move
        direction = DIRECTION_FROM_MOVE[next_move]
        # direction = random.choice(list(moves.DIRECTION_FROM_MOVE.values()))
        super().move(direction)

    def set_mode(self, mode):
        if mode == self.mode:
            return
        if mode == SCATTER:
            corners = self.gamestate.get_corners()
            random.shuffle(corners)
            self.target_position = corners[0]
            self.mode = mode
        if mode == CHASE:
            self.target_position = self.gamestate.pacman.position

    def tick(self):
        self.time_at_last_tick = time.time()
        self.set_mode(self.ghost_event_routine())
        if self.mode == CHASE:
            self.chase_pacman()
        elif self.mode == SCATTER:
            self.scatter()


class Pacman(Existence):
    def __init__(self, position, gamestate):
        super().__init__(position, gamestate, icon='pacman.png', symbol='P')
        self.lives = 3
        self.max_lives = 3
        self.respawn_position = position
        self.current_move = "NONE"
        self.time_at_last_tick = time.time()
        self.number_of_ticks = 0

    def lose_life(self, lives_lost):
        self.lives -= lives_lost

    def respawn(self):
        self.position = self.respawn_position
        self.current_move = "NONE"

    def set_move(self, move):
        if move == "NONE":
            return
        self.current_move = move

    def handle_action(self, game_state):
        """

        Args:
            game_state (GameState):

        Returns:

        """
        active_items = []
        active_items.extend(self.gamestate.get_active_dots())

        for item in active_items:
            if item.position == self.position:
                item.eat()
                if type(item) == Dot:
                    game_state.num_dots_left -= 1

    def tick(self, game_state):
        direction = DIRECTION_FROM_MOVE[self.current_move]
        is_move_valid = super().move(direction)  # If not valid -> wall crash
        self.handle_action(game_state)
        self.time_at_last_tick = time.time()
        self.number_of_ticks += 1

        return is_move_valid


class Wall(Existence):
    def __init__(self, position, gamestate):
        super().__init__(position, gamestate, icon='wall.png', symbol='%')


def map_key_to_move(event):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP:
            return "UP"
        if event.key == pygame.K_RIGHT:
            return "RIGHT"
        if event.key == pygame.K_DOWN:
            return "DOWN"
        if event.key == pygame.K_LEFT:
            return "LEFT"
    return "NONE"


def translate_input_symbol_to_object(position, gamestate, symbol):
    if symbol == "P":
        gamestate.pacman = Pacman(position, gamestate)
    if symbol == "%":
        gamestate.walls.append(Wall(position, gamestate))
        gamestate.wall_positions.append(position)
    if symbol == "G":
        gamestate.ghosts.append(Ghost(position, gamestate))
    if symbol == ".":
        gamestate.dots.append(Dot(position, gamestate))
        gamestate.num_dots_left += 1


def initialize_gamestate_from_file(file):
    gamestate = read_level(file)
    return gamestate


def read_level(level):
    y_pointer = 0
    x_pointer = 0
    gamestate = GameState()
    with open("./boards/" + level + '.txt', "r") as f:
        f = f.read().splitlines()
        gamestate.dimensions = [len(f), len(f[0])]
        for y in f:
            for item in y:
                current_position = x_pointer, y_pointer
                translate_input_symbol_to_object(current_position, gamestate, item)
                x_pointer += 1
            y_pointer += 1
            x_pointer = 0
    return gamestate


