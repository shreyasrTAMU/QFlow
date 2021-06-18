import gym
import time
import numpy as np
import math
import matplotlib.pyplot as plt
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from virtual_env import VideoStreamEnv
from stable_baselines import DQN
import pickle 
import random

# from stable_baselines.common.policies import MlpPolicy
# from stable_baselines.common import make_vec_env
# from stable_baselines import A2C
def save_trace(what_to_save, file_path):
    with open(file_path, 'wb') as file: 
        pickle.dump(what_to_save, file)

with open('/home/ndn2/qflow/QFlow/controller/RL_code/BigList', 'rb') as f1:
    biglist = pickle.load(f1)

with open('/home/ndn2/qflow/QFlow/controller/RL_code/policy', 'rb') as f2:
    ind_policy = pickle.load(f2)


def findDistance(state, nextState):
    sum=0.0
    for i in range(len(state)):
        sum += (state[i]-nextState[i])**2
    return math.sqrt(sum)

def findNearestState(nextState):
    minDist=10000000.0
    nearestState = []
    for state in biglist:
        dis = findDistance(state, nextState)
        if dis < minDist:
            minDist=dis
            nearestState = state
      
    return biglist.index(nearestState)

def getindexaction(obs, biglist, ind_policy):
    obs = obs[0]
    
    buffer_state = np.array([obs[0][c][0] for c in range(n_clients)])
    print('buffer state: ',buffer_state)
    numBufferbins = 21
    bins = np.linspace(0, 20, numBufferbins)
    for i in range(len(buffer_state)):
        # if(buffer_state[i] > 20):
        #     buffer_state[i] = 20
        # buffer_state[i] = np.digitize(buffer_state[i], bins)
        # if(buffer_state[i] > 20):
        #     buffer_state[i] = 20
        # buffer_state[i] = np.digitize(buffer_state[i], bins)
        buffer_state[i] = np.digitize(buffer_state[i], bins)

    stall_state = np.array([obs[0][c][2] for c in range(n_clients)])
    print('stall state: ',stall_state)

    QoEs = np.array([obs[0][c][1] for c in range(n_clients)])
    print('qoe: ',QoEs)
    numQoEbins = 9
    QoEbins = np.linspace(1, 5, numQoEbins)
    for i in range(len(QoEs)):
        QoEs[i] = np.digitize(QoEs[i], QoEbins)

    # print('digitized buffer state: ',buffer_state)
    # print('digitized stall state: ',stall_state)
    # print('digitized qoe: ',QoEs)
    s = [int(buffer_state[i]*5*numQoEbins + QoEs[i]*5 + stall_state[i]) for i in range(6)]
    print(s)
    return ind_policy[findNearestState(s)]


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

action = random.randint(0,14)
episodelength = 540    #180 episodes counts for half an hour
no_epi = 1
for i in range (no_epi): 
    obs = env.reset()
    avg_qoe = 0

    for i in range(episodelength):
        obs, rewards, dones, info = env.step([action])
        action = getindexaction(obs, biglist, ind_policy)
        avg_qoe = avg_qoe+rewards
        reward_list.append(rewards)
        #to do: discounting 
        print("The AVG QoE: ",rewards)
        print('==============================================================')
        if dones: 
            #reward_list.append(avg_qoe/episodelength)
            break
save_trace(reward_list, 'reward_list_index_1')
print("avg_qoe: {}".format(sum(reward_list)/len(reward_list)))
plt.title('Rewards')
plt.xlabel('Time')
plt.ylabel('Reward')
plt.plot(reward_list, label='Episodic Average')
plt.legend()
plt.savefig('results_index.png')
plt.show()