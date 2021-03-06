import sys
from copy import deepcopy

import pygame

import graphics.draw_board as b
from pacman import gamelogic
from pacman.gamelogic import ActionEvent, check_if_pacman_ate_food, check_ghost_collisions
from pacman.gamestate import GameState
from pacman.initializer import initialize_gamestate_from_file
from pacman.keymapper import map_key_to_move

import time

MOVE_GHOST_EVENT = pygame.USEREVENT+1
PACMAN_TICK = pygame.USEREVENT+2

class Game:
    def __init__(self, level, init_screen=False, ai_function=None):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.initial_game_state = initialize_gamestate_from_file(level)
        self.game_state = self.initial_game_state
        self.done = False
        self.ai_function = ai_function
        pygame.time.set_timer(MOVE_GHOST_EVENT, 400)
        pygame.time.set_timer(PACMAN_TICK, 400)
        if init_screen:
            self.init_screen()

    def init_screen(self):
        self.screen = pygame.display.set_mode((760, 840))

    def run(self):
        while not self.done:
            self.execute_game_loop()

    def move_ghosts(self):
        for ghost in self.game_state.ghosts:
            ghost.tick()

    def animate(self):
        """
            Draws game graphics
        """
        # Wipe screen from previous cycle
        self.screen.fill((1, 1, 1))

        # Draw current gamestate to the screen
        b.draw_board(self.game_state, self.screen)
        b.draw_lives(self.game_state, self.screen)
        b.draw_score(self.game_state, self.screen)

        pygame.display.flip()

    def handle_input_action(self, event):
        move = map_key_to_move(event)
        self.game_state.pacman.set_move(move)

    def reset_if_ghost_collision(self):
        if check_ghost_collisions(self.game_state):
            self.game_state = deepcopy(self.initial_game_state)

    def execute_game_loop(self, animate=True):
        # Handle keyboard events for manual playing
        for event in pygame.event.get():
            self.game_state.last_game_event = ActionEvent.NONE

            if event.type == PACMAN_TICK:
                if self.ai_function:
                    action = self.ai_function(self.game_state)
                    self.game_state.pacman.set_move(action.name)
                is_move_valid = self.game_state.pacman.tick(self.game_state)
                if not is_move_valid:
                    self.game_state.last_game_event = ActionEvent.WALL

                self.reset_if_ghost_collision()
            if event.type == pygame.QUIT:
                self.done = True
            if event.type == MOVE_GHOST_EVENT:
                self.move_ghosts()
                self.reset_if_ghost_collision()

        # self.handle_input_action(event)

        if animate:
            self.animate()

        if self.game_state.has_won():
            print("Congratulations you won!")
            pygame.quit()
            sys.exit()
        elif self.game_state.has_lost():
            print("Sorry. You lost.")
            pygame.quit()
            sys.exit()

        # Limit FPS to 60 (still unnecessarily high)
        self.clock.tick(60)

