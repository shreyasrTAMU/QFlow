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
    'IPAddress',
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
        sleep(max(0, PERIOD - toc + tic))

    tic = time()


    #define getlatestrun in policy_interface 
    #example = list(fetch_run(10))   #List of latest information about each client
    #print(PI.fetch_run(PI.latest_run()))
    example = list(PI.fetch_run(PI.latest_run())) #Selects all fields from results_table that has runid
    print('Setting policy for run: ',PI.latest_run())
    print('length of example:',len(example))
    allnotequal = [0,0,0,0,0,0]
    for i,client in enumerate(example):
        #print(len(example[i]))
        #print(example[i])

        print(client[PI.run_cols.index('threadID')])
        print(client[PI.run_cols.index('processID')])
        print(client[PI.run_cols.index('prev_buffer_state')])
        sqlcommand = "select * from results_table where threadID = '{}' and prev_buffer_state != buffer_state and processID = '{}' order by runID+0 desc;".format(client[PI.run_cols.index('threadID')],client[PI.run_cols.index('processID')])
        #print(sqlcommand)
        numberofnotequal = len(PI.execute_db(sqlcommand)) 
        print(numberofnotequal)
        j = clients_index[client[PI.run_cols.index('threadID')]]    #Getting index corresponding to threadID in dictionary of threadID:index
        if (numberofnotequal > allnotequal[j]):
            states[j][0] = client[PI.run_cols.index('buffer_state')]
            states[j][1] = client[PI.run_cols.index('Stalls')]
            states[j][2] = client[PI.run_cols.index('QoE')]
            allnotequal[j] = numberofnotequal

        
        # print(example[i][12])
        print()
        # print(example[i][1])
    #print(example)
    print(states)
    print('=============================================')
    # for i, client in enumerate(example):

    #     if client[PI.run_cols.index('IPAddress')] == '192.168.1.130':
    #         queueID = 10
    #     else:
    #         queueID = 30

    #     PI.write_assignment(
    #         client[PI.run_cols.index('IPAddress')], 
    #         client[PI.run_cols.index('processID')], 
    #         client[PI.run_cols.index('threadID')], 
    #         client[PI.run_cols.index('ports')],
    #         #client[PI.run_cols.index('queueID')]
    #         queueID
    #     )        
    toc = time()




