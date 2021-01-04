#policy_interface

# pip install "mysqlclient==1.3.12"
import MySQLdb
import numpy as np
from time import time

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
    except MySQLdb.Error as e:
        print("Error {}: {}".format(e.args[0],e.args[1]))


run_cols = [    #Columns in results table
    'IPAddress', 
    'threadID', 
    'processID', 
    # 'runID', 
    'timestamp', 
    'ports', 
    'buffer_state', 
    'play_state', 
    'bitrate', 
    'Stalls', 
    'stallDur', 
    'queueID',
    'prev_QoE', 
    'QoE', 
    'prev_buffer_state' 
    # 'prev_QoE', 
    # 'prev_play_state'
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


def first_run():    #get the minum-value runID in the flowbazaar database
    return int(execute_db(
        "SELECT MIN(runID) from flow_bazaar.results_table"
    )[0][0])


def fetch_latest_state(ip=None, thread=None):   #get the latest state of a client
    return execute_db(
        "SELECT {} FROM flow_bazaar.results_table WHERE IPAddress = '{}' and threadID = '{}' ORDER BY timestamp DESC LIMIT 1;".format(
            ', '.join(run_cols), ip, thread
        )
    )[0]


def fetch_run(run, ip=None, thread=None):   #read a run from the flowbazaar database

    if ip is None:
        return execute_db(
            "SELECT {} FROM flow_bazaar.results_table WHERE runID = {} ORDER BY IPAddress ASC, threadID ASC;".format(
                ', '.join(run_cols), run
            )
        )

    result = execute_db(
        "SELECT {} FROM flow_bazaar.results_table WHERE runID = {} and IPAddress = '{}' and threadID = '{}';".format(
            ', '.join(run_cols), run, ip, thread
        )
    )
    if len(result) > 0:
        return result[0]
    return None

queues = (30, 10)
def write_assignment(var_ip, var_processID, var_threadID, var_ports, var_queue):   #Assign flows to queues

    timenow = int(time())
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)
        cur = con.cursor()
        cur.execute("INSERT INTO `policy_table` (`IPAddress`, `processID`, `threadID`,`ports`, `queueID`, `timestamp`) VALUES (%s, %s,%s,%s,%s,%s)",(var_ip, var_processID, var_threadID, var_ports, var_queue, timenow) )
        con.commit()
        results = cur.fetchall()
        return results
    except MySQLdb.Error as e:
        print("Error {}: {}".format(e.args[0],e.args[1]))
    # return execute_db(
    #     "INSERT INTO `policy_table` (`IPAddress`, `processID`, `threadID`,`ports`, `queueID`, `timestamp`) VALUES (%s, %s,%s,%s,%s,%s)",(var_ip, var_processID, var_threadID, var_ports, var_queue, timenow) )
    


# get latest run value
# print(latest_run())

# get client id
# print(client_id('192.168.1.132', 'Thread-1'))
# print(fetch_latest_state('192.168.1.132', 'Thread-1'))



# get unique labels
# print(execute_db(
#     "SELECT DISTINCT play_state FROM flow_bazaar.results_table;"
#     ))
