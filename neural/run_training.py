import math
import tensorflow as tf
import numpy as np
import time
import random
import os
import pickle
import datetime
from lib.network import Network
from lib.game import Game
from lib.memory import Memory
from lib.trainer import Trainer

HIDDEN_LAYER_SIZE = 100
NO_HIDDEN_LAYERS = 3
GAME_LENGTH = 120000
GAME_STEP_TIME = 20
GAMES_PER_TRAINING_SESSION = 1
NUMBER_OF_TRAINING_SESSIONS = 10
MEMORY_SIZE = 60000
MAX_EPSILON = 0.999
MIN_EPSILON = 0.001
EPSILON_DECAY = 0.0001
GAMMA = 0.999
STARTING_VERSION = 0
DIRECTORY = './trained_networks/' + datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

HYPERPARAMETER_DICT = {
    'HIDDEN_LAYER_SIZE': HIDDEN_LAYER_SIZE,
    'NO_HIDDEN_LAYERS': NO_HIDDEN_LAYERS,
    'GAME_LENGTH': GAME_LENGTH,
    'GAME_STEP_TIME': GAME_STEP_TIME,
    'GAMES_PER_TRAINING_SESSION': GAMES_PER_TRAINING_SESSION,
    'NUMBER_OF_TRAINING_SESSIONS': NUMBER_OF_TRAINING_SESSIONS,
    'MEMORY_SIZE': MEMORY_SIZE,
    'MAX_EPSILON': MAX_EPSILON,
    'MIN_EPSILON': MIN_EPSILON,
    'EPSILON_DECAY': EPSILON_DECAY,
    'GAMMA ': GAMMA,
    'STARTING_VERSION': STARTING_VERSION,
    'DIRECTORY': DIRECTORY
}


def main():
    champion_graph = tf.Graph()
    competitor_graph = tf.Graph()
    champion_session = tf.Session(graph=champion_graph)
    competitor_session = tf.Session(graph=competitor_graph)

    memory_bank = Memory(MEMORY_SIZE)
    pong_game = Game(GAME_LENGTH, GAME_STEP_TIME)

    with champion_graph.as_default():
        champion = Network(3, 10, hidden_layer_size=HIDDEN_LAYER_SIZE, no_hidden_layers=NO_HIDDEN_LAYERS)
        champion_session.run(champion.variable_initializer)
    with competitor_graph.as_default():
        competitor = Network(3, 10, hidden_layer_size=HIDDEN_LAYER_SIZE, no_hidden_layers=NO_HIDDEN_LAYERS)
        competitor_session.run(competitor.variable_initializer)

    trainer = Trainer(pong_game, champion_session, competitor_session, champion_graph, competitor_graph, memory_bank, champion, competitor, MAX_EPSILON, MIN_EPSILON, EPSILON_DECAY, GAMMA)

    champion.save_network(champion_session, DIRECTORY + '/version_' + str(STARTING_VERSION) + '/')

    for version in range(STARTING_VERSION, STARTING_VERSION + NUMBER_OF_TRAINING_SESSIONS):

        start_time = time.time()
        for _ in range(GAMES_PER_TRAINING_SESSION):
            trainer.run_game()

        print("Time taken for training session: %s", time.time() - start_time)
        champion.save_network(champion_session, DIRECTORY + '/version_' + str(version + 1) + '/')

        test_score = trainer.test_game()

        if test_score < 0:
            print('Competitor wins, score was ' + str(test_score))
            with competitor_graph.as_default():
                competitor.save_network(competitor_session, './competitor_save/temp')
            with champion_graph.as_default():
                    champion.load_network(champion_session, './competitor_save/temp')
        else:
            print('Champion continues, score was ' + str(test_score))

        new_competitor_version = random.randint(0, version)
        print('New competitor version: ' + str(new_competitor_version))

        with competitor_graph.as_default():
            competitor.load_network(competitor_session, DIRECTORY + '/version_' + str(new_competitor_version) + '/')

        trainer = Trainer(pong_game, champion_session, competitor_session, champion_graph, competitor_graph, memory_bank, champion, competitor, MAX_EPSILON, MIN_EPSILON, EPSILON_DECAY, GAMMA)


if __name__ == '__main__':
    print('Creating directory')
    os.mkdir(DIRECTORY)
    print('Pickling hyperparameter dictionary')
    with open(DIRECTORY + '/hyperparameters.pickle', 'wb') as storage:
        pickle.dump(HYPERPARAMETER_DICT, storage, protocol=pickle.HIGHEST_PROTOCOL)
    print('Starting training session')
    main()
    print('Training session complete')