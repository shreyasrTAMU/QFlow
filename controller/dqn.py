import gym
import time
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from virtual_env import VideoStreamEnv
from stable_baselines import DQN
import pickle 

# from stable_baselines.common.policies import MlpPolicy
# from stable_baselines.common import make_vec_env
# from stable_baselines import A2C
def save_trace(what_to_save, file_path):
    with open(file_path, 'wb') as file: 
        pickle.dump(what_to_save, file)

#env_id = 'LunarLander-v2'
# video_folder = '/home/ndn1/Manav/RL'
# video_length = 100000
# tuned so round_robin barely fails
top_limit = 2
n_queues = 2

n_clients = 6


action_cardinality = n_queues**n_clients
# actions have pre-existing knowledge built in to if statement
actions = [
    [(i//(n_queues**c))%n_queues for c in range(n_clients)]
    for i in range(action_cardinality) 
    if sum([(i//(n_queues**c))%n_queues for c in range(n_clients)]) == top_limit
]

env = VideoStreamEnv()
env = DummyVecEnv([lambda: env])
reward_list = []
model = DQN.load("Qflow32_128_32",env)
_states = 0
episodelength = 360
no_epi = 1
for i in range (no_epi): 
    obs = env.reset()
    avg_qoe = 0

    for i in range(episodelength):
        action, _states = model.predict(obs)
        obs, rewards, dones, info = env.step(action)
        avg_qoe = avg_qoe+rewards
        reward_list.append(rewards)
        #to do: discounting 
        print("The AVG QoE: ",rewards)
        if dones: 
            #reward_list.append(avg_qoe/episodelength)
            break
save_trace(reward_list, 'reward_list_dqn_1')
print("avg_qoe: {}".format(sum(reward_list)/len(reward_list)))
plt.title('Rewards')
plt.xlabel('Time')
plt.ylabel('Reward')
plt.plot(reward_list, label='Episodic Average')
plt.legend()
plt.savefig('dqn_results.png')
plt.show()
