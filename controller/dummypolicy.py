import policy_interface as PI
from time import sleep, time


PERIOD = 10
clients_index = {'192.168.1.129/1':0,'192.168.1.129/2':1, '192.168.1.130/1':2, '192.168.1.130/2':3, '192.168.1.132/1': 4, '192.168.1.132/2':5}
states = [[0,0,0] for _ in range(6)]

# state feature labels
FEATURE_LABELS = [PI.run_cols.index(label) for label in [ 
 
    'buffer_state', 
    # 'play_state', 
    'bitrate', 
    'Stalls', 
    'stallDur', 
    # 'queueIP',
    'prev_QoE', 
    'QoE'
]]

# client ID labels
ID_LABELS = [PI.run_cols.index(label) for label in [
    'processID',
    'threadID',
    'ports'
]]


steps = 0
# render the requested number of decisions

while True:
    steps += 1
    print 'steps: ',steps
    # wait decision period all but first time
    if steps > 1:
        sleep(PERIOD)

    print('Setting policy for run: ',PI.latest_run())
    example = PI.fetch_run(PI.latest_run())
    #print example
    example = list(example) #Selects all fields from results_table that has runid
    print('length of example:',len(example))

    #print(example)
    print(states)
    print('=============================================')
    for i, client in enumerate(example):

        if '192.168.1.132' in client[PI.run_cols.index('threadID')]:
            queueID = 10            #Low queue 9mbit
        else:
            queueID = 30

        PI.write_assignment(
            client[PI.run_cols.index('processID')], 
            client[PI.run_cols.index('threadID')], 
            client[PI.run_cols.index('ports')],
            client[PI.run_cols.index('play_state')],        
            client[PI.run_cols.index('prev_buffer_state')],
            client[PI.run_cols.index('buffer_state')],
            client[PI.run_cols.index('QoE')],
            1,      #No_of_HighQs 
            queueID,        
            client[PI.run_cols.index('Stalls')]

        )        




