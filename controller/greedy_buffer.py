import gym
import time
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from virtual_env import VideoStreamEnv
from stable_baselines import DQN
import pickle 
import random 

top_limit = 2
n_queues = 2

n_clients = 6
action_cardinality = n_queues**n_clients

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
action = actions[random.randint(0,14)]
_states = 0
buffer_state = []
how_many = 2 # change this to increase number of clients allowed in the high q 
#to do: values between [0,5]

for i in range (1): #episodes
    obs = env.reset()
    for t in range(270):  # timesteps for each episode (TTL)
        obs, rewards, dones, info = env.step(action) #110000
        action = [0,0,0,0,0,0]
        buffer_state = np.array([obs[0][c][0] for c in range(n_clients)])
        buffer_state = [float(i) for i in buffer_state]
        buffer_state = np.array(buffer_state)
        print("buffer_state: ",buffer_state)
        least_buffered = (buffer_state.argsort()[:how_many])
        #print(least_buffered)
        for m in range (n_clients):
            if (m == least_buffered[0] or m == least_buffered[1]):
                action[m] = 1
            else:
                action[m] = 0 
        reward_list.append(rewards)
        file = open('rewards_greedy_buffer.txt', 'a')
        file.write(str(rewards))
        file.write(',')
        file.close()
        print('reward={0}  t ={1}, action = {2}'.format(rewards,t, action))
        print('---------------------------------------------------------------')
save_trace(reward_list, 'reward_list_greedy_buffer_tr_2')
print("avg_qoe: {}".format(sum(reward_list)/len(reward_list)))
plt.title('Rewards')
plt.xlabel('Time')
plt.ylabel('Reward')
plt.plot(reward_list, label='episodic_avg')
plt.legend()
plt.savefig('greedy_results.png')
plt.show()
