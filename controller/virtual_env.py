# make a better interface with virtual system, use 'open_ai-gym' style
import numpy as np
import matplotlib.pyplot as plt
import gym
from gym import spaces 
#-------------------------------------------------------------------#
import policy_interface as PI
#from fillmodel_table import fill_to_table
hostIP = "127.0.0.1"     # Database server IP
username = "root"
passwd = "cesgtamu"
db = "flow_bazaar"
import calcDQS


from time import sleep, time

######################################################################
# Temporary: Constants

# time step between decisions in seconds
TIME_STEP = 10

top_limit = 2
n_queues = 2
n_clients = 6
action_cardinality = n_queues**n_clients
actions = [
    [(i//(n_queues**c))%n_queues for c in range(n_clients)]
    for i in range(action_cardinality) 
    if sum([(i//(n_queues**c))%n_queues for c in range(n_clients)]) == top_limit
]


class VideoStreamEnv(gym.Env):
    

    def __init__(self):
        '''
        set up video stream environment
        ----------------------------------------------------------------
        Parameters
        queues:      list of Queue objects
        clients:     list of Client objects
        time_step:   time to pass in each step in seconds
        fair_reward: whether queues should use fair sum-of-log (True) or straight sum (False)
        ----------------------------------------------------------------
        Returns
        self:        for chaining
        '''

        
        self.action_space =  spaces.Discrete(15)  #no_clients c 2
       
        observations_max =    np.array([np.finfo(np.float32).max, np.finfo(np.float32).max, 5,
                                        np.finfo(np.float32).max, np.finfo(np.float32).max, 5,
                                        np.finfo(np.float32).max, np.finfo(np.float32).max, 5,
                                        np.finfo(np.float32).max, np.finfo(np.float32).max, 5,
                                        np.finfo(np.float32).max, np.finfo(np.float32).max, 5,
                                        np.finfo(np.float32).max, np.finfo(np.float32).max, 5,]).reshape(1,6,3)
        observations_min = np.array([0,0,0,
                                    0,0,0,
                                    0,0,0,
                                    0,0,0,
                                    0,0,0,
                                    0,0,0]).reshape(1,6,3)

        self.observation_space = spaces.Box(observations_min, observations_max, shape=(1,6,3))
        self.step_counter = 0
    
    def write_to_policy(self,client,action,queueID):
            PI.write_assignment(
            client[PI.run_cols.index('processID')], 
            client[PI.run_cols.index('threadID')], 
            client[PI.run_cols.index('ports')],
            client[PI.run_cols.index('play_state')],
            client[PI.run_cols.index('prev_buffer_state')],
            client[PI.run_cols.index('buffer_state')],
            client[PI.run_cols.index('QoE')],
            #action.count(1), #for dqn
            np.count_nonzero(action == 1), # for non-rl
            queueID,
            client[PI.run_cols.index('Stalls')]
        )


    def step(self, action):
        '''
        Execute a time step with the given action
        ----------------------------------------------------------------
        Parameters
        action:           assignment of clients to queues.
                          len() should be same as clients
                          entries should be integer index of queue
        ----------------------------------------------------------------
        Returns
        ob, reward, episode_over, info : tuple
            ob:           array of state information
            reward:       QoE, to be increased
            episode_over: always false
            info:         none, doesn't matter
        '''
        self.step_counter = self.step_counter+1
        done = False
        if(self.step_counter > 1):
        	sleep(TIME_STEP)
        #action = actions[action] #for dqn 

        states = [[0,0,0] for _ in range(n_clients)]
        reward = 0

        latestrun = PI.latest_run()

        print('Latest run: ',latestrun)
        print('Action to take: ',action)

        allinfo = PI.fetch_run(latestrun)
        if allinfo: 
            
            allinfo = list(allinfo)

            print('Reading ',len(allinfo), ' clients')
            allinfolength = len(allinfo)
            if allinfolength == 0:
                allinfolength = 1

            for i, client in enumerate(allinfo):
                state1client = [
                    client[PI.run_cols.index('buffer_state')],
                    client[PI.run_cols.index('Stalls')],
                    client[PI.run_cols.index('QoE')],
                ]
                states[i] = state1client

                reward = reward + float(client[PI.run_cols.index('QoE')])

                if action[i] == 1:
                    queueID = 10	#High priority queue
                else:
                    queueID = 30

                print(client[PI.run_cols.index('threadID')],'  QoE:', client[PI.run_cols.index('QoE')],' sent to ',queueID)
                self.write_to_policy(client,action,queueID)

            self.state = states
            #fill_to_table()
            return np.array(states).reshape(-1,6,3), ((reward/allinfolength)), done, {}   

        else:
            print('No run to fetch data from')
    def reset(self):
        states = [[0,0,5] for _ in range(n_clients)]
        # for c in self.clients:
        #     c.reset()
        # self.state = [c.state for c in self.clients]
        # return np.array(self.state).reshape(-1,6,3)
        return np.array(states).reshape(-1,6,3)

    def render(self, mode='human', close=False):
        raise NotImplementedError