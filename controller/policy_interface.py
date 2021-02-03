
# pip install "mysqlclient==1.3.12"
import MySQLdb
import numpy as np
from time import time
import traceback

hostIP = "127.0.0.1"     # Database server IP
username = "root"
passwd = "cesgtamu"
db = "flow_bazaar"                  # Database name


def execute_db(sql_script):
    '''
    read a query's result from the flowbazaar database
    '''
    results = None
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)
        cur = con.cursor()
        cur.execute(sql_script)
        results = cur.fetchall()
        return results
    except:
        traceback.print_exc()


run_cols = [    #Columns in results table 
    'runID', 
    'processID',
    'threadID',
    'ports', 
    'play_state', 
    'bitrate', 
    'Stalls', 
    'stallDur', 
    'prev_QoE',
    'prev_play_state',
    'prev_buffer_state', 
    'buffer_state',
    'queueID',
    'QoE',
    'timestamp' 
]

def client_id(ip, thread):
    '''
    get ids of the clients
    '''
    return execute_db(
        "SELECT * from flow_bazaar.client_table WHERE IPAddress='{}' AND threadID='{}' ORDER BY timestamp DESC LIMIT 1".format(
            ip, thread
        )
    )[0]


def latest_run():   #get the highest-value runID in the flowbazaar database
    try:
        return int(execute_db(
            "SELECT CAST(runID as SIGNED) from flow_bazaar.results_table ORDER BY `timestamp` DESC")[0][0])
    except:
        return 0



def fetch_latest_state(ip=None, thread=None):   #get the latest state of a client
    return execute_db(
        "SELECT {} FROM flow_bazaar.results_table WHERE IPAddress = '{}' and threadID = '{}' ORDER BY timestamp DESC LIMIT 1;".format(
            ', '.join(run_cols), ip, thread
        )
    )[0]


def fetch_run(run):   #read a run from the flowbazaar database

    try:
        result = execute_db(
            "SELECT * FROM flow_bazaar.results_table WHERE runID = '{}';".format(run, ))

        #print('RESULT: ',result)
        if len(result) > 0:
            return result
        return None
    except:
        traceback.print_exc()

queues = (30, 10)
def write_assignment(var_processID, var_threadID, var_ports, var_play_state, var_prev_buffer_state, var_buffer_state, var_QoE, var_highQ, var_queue, var_Stalls):   #Assign flows to queues

    timenow = int(time())
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)
        cur = con.cursor()
        cur.execute("INSERT INTO `policy_table` (`processID`, `threadID`,`ports`, `play_state`, `prev_buffer_state`, `buffer_state`, `QoE`,`No_of_HighQs`,`queueID`, `Stalls`, `timestamp`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(var_processID, var_threadID, var_ports, var_play_state, var_prev_buffer_state, var_buffer_state, var_QoE, var_highQ, var_queue, var_Stalls,timenow) )
        con.commit()
        results = cur.fetchall()
        return results
    except:
        traceback.print_exc()

