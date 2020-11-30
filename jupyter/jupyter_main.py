import os
import sys
from pacman.game import Game
from qlearning.q_learning import QLearn
from utils.file_utils import load_pickle

# Append path to use modules outside pycharm environment, e.g. terminal
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))


# map 0 => easy - 10 | medium - 50 | hard - 100 | extreme - 500
# map 1 => easy -  | medium -  | hard -  | extreme -
# map 4 =>
def play_q_learning_model(level='level-4', model_path='./q_table_map4.pkl'):
    q_model = QLearn()
    # q_model.train(level, 10)
    q_model.q_table = load_pickle(model_path)

    def ai_func(current_game_state):
        return q_model.pick_optimal_action(current_game_state, printing=False)

    game = Game(level, init_screen=True, ai_function=ai_func)
    game.run()


play_q_learning_model()
