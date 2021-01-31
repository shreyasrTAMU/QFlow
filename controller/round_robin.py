import gym
import time
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from virtual.virtual_env import VideoStreamEnv
from stable_baselines import DQN
import pickle

def save_trace(what_to_save, file_path):
    with open(file_path, 'wb') as file: 
        pickle.dump(what_to_save, file)

top_limit = 2
n_queues = 2
# queues = [
#     Queue(4*1.1e+3*1024, fairness=1e+2), 
#     Queue(2*6e+3*1024, fairness=1e+3)    
# ]
n_clients = 6
# clients = [
#     Client(bitrate_dist=(2.9e+6, 1e+6), length_dist=(10*60, 10*5), initial_buffer=10)
#     for _ in range(n_clients)
# ]

action_cardinality = n_queues**n_clients
# actions have pre-existing knowledge built in to if statement
actions = [
    [(i//(n_queues**c))%n_queues for c in range(n_clients)]
    for i in range(action_cardinality) 
    if sum([(i//(n_queues**c))%n_queues for c in range(n_clients)]) == top_limit
]

env = VideoStreamEnv()

# env = DummyVecEnv([lambda: env])
reward_list = []

action = 0
_states = 0
a = 0
for i in range (1): #episodes
    obs = env.reset()
    avg_qoe = 0
    for t in range(180):  # timesteps for each episode (TTL)
        obs, rewards, dones, info = env.step(actions[a])
        a = a + 1 
        if(a == 15):
            a = 0
        avg_qoe = avg_qoe+(rewards)
        reward_list.append(rewards)
        print("avg_qoe:",rewards)
        print("a: ", a)
        file = open('rewards.txt', 'a')
        file.write(str(rewards))
        file.write(',')
        file.close()
        if dones: 
            # reward_list.append(avg_qoe)
            break

save_trace(reward_list, 'reward_list_rr_trial_1.p')
print("avg_qoe: {}".format(sum(reward_list)/len(reward_list)))
plt.title('Rewards')
plt.xlabel('Time')
plt.ylabel('Reward')
plt.plot(reward_list, label='episodic_avg')
plt.legend()
plt.savefig('eval_results.png')
plt.show()
