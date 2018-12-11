'''
Created Date: Saturday December 1st 2018
Last Modified: Saturday December 1st 2018 9:52:19 pm
Author: ankurrc
'''
import numpy as np
import traceback as tb

from keras.models import Sequential, Model
from keras.layers import Dense, Activation, Flatten, Input, Concatenate
from keras.optimizers import Adam
from keras.callbacks import TensorBoard

from rl.random import OrnsteinUhlenbeckProcess
from rl.callbacks import ModelIntervalCheckpoint, FileLogger

from carla_rl import carla_config
from carla_rl.carla_environment_wrapper import CarlaEnvironmentWrapper as CarlaEnv
from carla_settings import get_carla_settings

from processor import MultiInputProcessor
from models import Models
from memory import PrioritizedExperience
from agent import DDPG_PERAgent

ENV_NAME = "Carla"
np.random.seed(123)

config_file = "mysettings.ini"  # file should be placed in CARLA_ROOT folder
weights_filename = 'ddpg_' + ENV_NAME + '_{step}_weights.h5f'
checkpoint_weights_filename = 'ddpg_' + ENV_NAME + '_weights_{step}.h5f'
log_filename = 'ddpg_{}_log.json'.format(ENV_NAME)

nb_actions = 2
window_size = 4
odometry_shape = (10,)

# memory params
alpha0 = 0.6
beta0 = 0.6

nb_steps = 10**6

env = CarlaEnv(is_render_enabled=False, automatic_render=False, num_speedup_steps=10, run_offscreen=False,
               cameras=["SceneFinal"], save_screens=False, carla_settings=get_carla_settings(), carla_server_settings=config_file, early_termination_enabled=True)

models = Models(image_shape=(carla_config.render_width, carla_config.render_height, 3),
                odometry_shape=odometry_shape, window_length=window_size, nb_actions=nb_actions)

actor = models.build_actor()
critic = models.build_critic()

train_history = None

try:
    processor = MultiInputProcessor(window_length=window_size, nb_inputs=2)
    memory = PrioritizedExperience(
        memory_size=2**16, alpha=alpha0, beta=beta0, window_length=window_size)

    random_process = OrnsteinUhlenbeckProcess(
        size=nb_actions, theta=.15, mu=0., sigma=.2, n_steps_annealing=nb_steps)

    callbacks = []
    # callbacks = [ModelIntervalCheckpoint(
    #     checkpoint_weights_filename, interval=2500)]
    # callbacks += [FileLogger(log_filename, interval=100)]
    # callbacks += [TensorBoard()]

    agent = DDPG_PERAgent(nb_actions=nb_actions, actor=actor, critic=critic, critic_action_input=models.action_input,
                          memory=memory, nb_steps_warmup_critic=1024, nb_steps_warmup_actor=1024,
                          random_process=random_process, gamma=.99, target_model_update=1e-3, batch_size=16, processor=processor)

    agent.compile([Adam(lr=1e-4), Adam(lr=1e-3)], metrics=['mae'])

    train_history = agent.fit(env, nb_steps=nb_steps, visualize=False,
                              verbose=1, action_repetition=1, callbacks=callbacks)

    agent.save_weights('ddpg_' + ENV_NAME + '_weights.h5f', overwrite=True)

    # Finally, evaluate our algorithm for 5 episodes.
    # agent.test(env, nb_episodes=5, visualize=False, nb_max_episode_steps=200)
except Exception as e:
    tb.print_exc()
    env.close_client_and_server()

finally:
    print(train_history)
