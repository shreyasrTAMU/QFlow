
# coding: utf-8

# # Constructing an approximate transition matrix

# In[1]:


import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import pickle


# In[9]:


data = pd.read_csv('dataModified.csv')


# In[10]:


features = data.values[:,0:4]
targets = data.values[:,8:13]

numActions = 2

numStallStates = 5
# Digitize QoE
numQoEbins = 9
bins = np.linspace(1, 5, numQoEbins)
for i in range(targets.shape[0]):
  features[i][1] = np.digitize(features[i][1], bins)
  targets[i][1] = np.digitize(targets[i][1], bins)
# Digitize buffer
numBufferbins = 21
bins = np.linspace(0, 20, numBufferbins)
for i in range(targets.shape[0]):
  if(features[i][0] > 20):
    features[i][0] = 20
  features[i][0] = np.digitize(features[i][0], bins)
  if(targets[i][0] > 20):
    targets[i][0] = 20
  targets[i][0] = np.digitize(targets[i][0], bins)

num_labels = (numQoEbins+1)*(numBufferbins+1)*(numStallStates+1)
nextState = [0 for itr in range(targets.shape[0])]
currState = [0 for itr in range(targets.shape[0])]
action = [0 for itr in range(targets.shape[0])]

# Convert measured Throughput to Action
for itr in range(features.shape[0]):
  if(int(targets[itr][3]) == 30):
    action[itr] = 0
  elif(int(targets[itr][3]) == 10):
    action[itr] = 1

# Convert state to quantized index
for itr in range(targets.shape[0]):
  index = int(features[itr][0]*numStallStates*numQoEbins + features[itr][1]*numStallStates + features[itr][2])
  currState[itr] = index
  index = int(targets[itr][0]*numStallStates*numQoEbins + targets[itr][1]*numStallStates + targets[itr][2])
  nextState[itr] = index

# Run ID to identify six clients as a group
runID = [0 for i in range(targets.shape[0])]
for itr in range(targets.shape[0]):
  runID[itr] = int(targets[itr][4])
  
# Separate data for the two actions
highQ_states = []
lowQ_states = []
  
states = []
for itr in range(features.shape[0]):
  if(action[itr] == 0):
    states.append(currState[itr])
    states.append(nextState[itr])
    lowQ_states.append(states)
    states=[]
  elif(action[itr] == 1):
    states.append(currState[itr])
    states.append(nextState[itr])
    highQ_states.append(states)
    states=[]

# Transition probability matrices for the two actions
highQ_trans = [[0.0 for i in range(num_labels)] for j in range(num_labels)]
lowQ_trans = [[0.0 for i in range(num_labels)] for j in range(num_labels)]

for i in range(len(highQ_states)):
  highQ_trans[highQ_states[i][0]][highQ_states[i][1]] += 1.0
              
for i in range(len(lowQ_states)):
  lowQ_trans[lowQ_states[i][0]][lowQ_states[i][1]] += 1.0
             
for i in range(num_labels):
  if(sum(highQ_trans[i]) != 0):
    highQ_trans[i] = [x/sum(highQ_trans[i]) for x in highQ_trans[i]]
  elif(sum(highQ_trans[i]) == 0):
    idx = np.random.choice(len(highQ_states),1)[0]
    highQ_trans[i][highQ_states[idx][1]] = 1.0
    #highQ_trans[i] = [1.0/num_labels for x in highQ_trans[i]]
  if(sum(lowQ_trans[i]) != 0):
    lowQ_trans[i] = [x/sum(lowQ_trans[i]) for x in lowQ_trans[i]]
  elif(sum(lowQ_trans[i]) == 0):
    idx = np.random.choice(len(lowQ_states),1)[0]
    lowQ_trans[i][lowQ_states[idx][1]] = 1.0
    #lowQ_trans[i] = [1.0/num_labels for x in lowQ_trans[i]]
       
# Reward matrices for the two actions
highQ_rew = [[0.0 for i in range(num_labels)] for j in range(num_labels)]
lowQ_rew = [[0.0 for i in range(num_labels)] for j in range(num_labels)]

for i in range(num_labels):
  for j in range(num_labels):
    if(highQ_trans[i][j] > 0):
      highQ_rew[i][j] = (j/numStallStates)%numQoEbins
    if(lowQ_trans[i][j] > 0):
      lowQ_rew[i][j] = (j/numStallStates)%numQoEbins
    
ind_P_6 = []
ind_P_6.append(lowQ_trans)
ind_P_6.append(highQ_trans)
file = open('ind_P_6clients', 'wb')
pickle.dump(ind_P_6, file)
file.close()


# In[4]:


num_clients = 6

# list of combined states of num_clients
list_bigCurState = []
list_bigNextState = []
list_bigAction = []
tmpCL = []
tmpNL = []
tmpA = []
tmpCnt = 0

tmpID = runID[0]
for itr in range(targets.shape[0]):
  if(tmpID == runID[itr]):
    tmpCnt+=1
    tmpCL.append(currState[itr])
    tmpNL.append(nextState[itr])
    tmpA.append(action[itr])
  elif(tmpID != runID[itr]):
    if(tmpCnt == 6):
      list_bigCurState.append(tmpCL)
      list_bigNextState.append(tmpNL)
      list_bigAction.append(tmpA)

    tmpID=runID[itr]
    tmpCnt=0
    tmpCL=[]
    tmpNL=[]
    tmpA=[]
    
    tmpCnt+=1
    tmpCL.append(currState[itr])
    tmpNL.append(nextState[itr])
    tmpA.append(action[itr])

newbiglist=[]
newbiglist.append(list_bigCurState[0])
for state in list_bigCurState:
    if state not in newbiglist:
        newbiglist.append(state)   
N=len(newbiglist)    
print(N)


# In[5]:


n_queues=2
n_clients=6
action_cardinality = n_queues**n_clients

actions = [
        [(i//(n_queues**c))%n_queues for c in range(n_clients)]
        for i in range(action_cardinality) 
        if sum([(i//(n_queues**c))%n_queues for c in range(n_clients)]) == 2
    ]

P = [[[0 for i in range(N)] for j in range(N)] for k in range(len(actions))]
R = [[[0 for i in range(N)] for j in range(N)] for k in range(len(actions))]

def findDistance(state, nextState):
  sum=0.0
  for i in range(len(state)):
    sum += (state[i]-nextState[i])**2
  return math.sqrt(sum)

def findNearestState(nextState):
  minDist=10000000.0
  nearestState = []
  for state in newbiglist:
    dis = findDistance(state, nextState)
    if dis < minDist:
      minDist=dis
      nearestState = state
      
  return newbiglist.index(nearestState)

def generateNextState(state,action):
  nextStates=np.zeros(n_clients)
  for i in range(n_clients):
    if(action[i] == 0):
      p = lowQ_trans[state[i]]
    else:
      p = highQ_trans[state[i]]
      
    nextStates[i] = np.random.choice(num_labels, 1, p)[0] 
  return nextStates

def calcReward(nextState):
  reward = 0.0
  for itr in nextState:
    reward += (itr/numStallStates)%numQoEbins
  return reward/n_clients

M=100

for action in actions:
  print(actions.index(action))  
  for state in newbiglist:
    for itr in range(M):
      nextState = generateNextState(state,action)
      idx = findNearestState(nextState)        
      P[actions.index(action)][newbiglist.index(state)][idx] += 1
      R[actions.index(action)][newbiglist.index(state)][idx] += calcReward(nextState)        
    P[actions.index(action)][newbiglist.index(state)] = [elem/M for elem in P[actions.index(action)][newbiglist.index(state)]]
    R[actions.index(action)][newbiglist.index(state)] = [elem/M for elem in R[actions.index(action)][newbiglist.index(state)]]


# In[6]:


import mdptoolbox as mdpT

Num_iter=10000
discount=0.975
epsilon=0.0001

Ptrans = np.array(P)
Rtrans = np.array(R)

pi = mdpT.mdp.PolicyIteration(Ptrans, Rtrans, discount, None, Num_iter)
pi.run()

print (pi.policy)

vi = mdpT.mdp.ValueIteration(Ptrans, Rtrans, discount, epsilon, Num_iter)
vi.run()

print (vi.policy)


# In[7]:


import matplotlib.pyplot as plt

plt.hist(vi.policy, bins='auto')  # arguments are passed to np.histogram
plt.title("Histogram with 'auto' bins")
plt.show()


# In[8]:


file = open('policy', 'wb')
pickle.dump(vi.policy, file)
file.close()
file=open('BigList','wb')
pickle.dump(newbiglist,file)
file.close()

