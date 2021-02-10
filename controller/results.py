from __future__ import division
from calcDQS import interruptDQS
from calcDQS import playbackDQS
import traceback
import time
import statistics
import numpy
import MySQLdb
import time
import datetime



hostIP = "127.0.0.1"     # Database server IP
username = "root"
passwd = "cesgtamu"
db = "flow_bazaar"                  # Database name
time_inbetween_runs = 10

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

def insert_into_db(runID, processID,threadID, ports, buffer_state, play_state, bitrate, currentStall, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE):
    timestamp = int(time.time())
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("INSERT INTO flow_bazaar.results_table(runID, processID,threadID, ports, buffer_state, play_state, bitrate, Stalls, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE, timestamp) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (runID, processID,threadID, ports, buffer_state, play_state, bitrate, currentStall, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE, timestamp))
        con.commit()
        con.close()

    except:
        traceback.print_exc()


def get_event_ts(threadID,processID, video_no, stall,event,order):    #order will always be ASC
    try:
        
        results = execute_db("SELECT timestamp FROM flow_bazaar.client_table WHERE threadID = '{}' AND processID = {} AND video_no = '{}' AND stallNo = '{}' AND dqs_state = '{}' ORDER BY timestamp {} LIMIT 1;".format(threadID,processID, video_no, stall,event,order))
        

        if not results:
            return -1

        results = results[0][0]
        return int(results)

    except:
        traceback.print_exc()


def get_prev_state(threadID):
    try:
        results = execute_db("SELECT QoE, buffer_state, play_state FROM flow_bazaar.results_table WHERE threadID = '{}' ORDER BY timestamp DESC LIMIT 1;".format(threadID, ))

        if not results:
            results = -1
        else:
            results = results[0]
        return results

    except:
        traceback.print_exc()


def get_youtube_stalls_10sec_ago(threadID, time_10sec_back):
    try:
        results = execute_db("SELECT stallNo FROM flow_bazaar.client_table WHERE threadID = '{}' AND timestamp <= '{}' ORDER BY timestamp DESC LIMIT 1;".format(threadID, time_10sec_back))

        if not results:
            print "     No new youtube prev stall state"
            results = 0
        else:
            results = results[0][0]
        return results

    except:
        traceback.print_exc()


def get_youtube_specific(threadID):
    try:
        results = execute_db("SELECT video_no, ports, load_and_play_state, video_player_state, bitrate, stallNo, timestamp FROM flow_bazaar.client_table WHERE threadID = '{}' ORDER BY timestamp DESC LIMIT 1;".format(threadID))

        if not results:
            print "No new youtube state"
            results = 0
        return results

    except:
        traceback.print_exc()


def get_process_id(threadID):
    _timestamp = int(time.time())
    lb_timestamp = _timestamp - time_inbetween_runs

    try:

        results = execute_db("SELECT processID FROM flow_bazaar.client_table WHERE threadID = '{}' AND timestamp >= '{}' ORDER BY timestamp DESC;".format(threadID, lb_timestamp))

        if(not results):
            print "no process id."
            results = 0
        else:
            results = results[0][0]
        return results
    except:
        traceback.print_exc()


def get_client_threadIDs():
    _timestamp = int(time.time())
    lb_timestamp = _timestamp - 20

    try:
        results = execute_db("SELECT threadID FROM flow_bazaar.client_table WHERE timestamp >= '{}' ORDER BY timestamp DESC;".format(lb_timestamp))

        if(not results):
            print "No new users/data"
            results = 0

        return results

    except:
        traceback.print_exc()

def get_latest_run():
    try:
        results = execute_db("Select runID from flow_bazaar.results_table order by timestamp DESC limit 1;")
        
        if(not results):
            results = 0
        else:
            results = results[0][0]
        return results

    except:
        traceback.print_exc()

def geteventStartEnd(stall):

    if stall > 1:
        eventStart = 'multiple rebuffering'
        eventEnd = 'multiple rebuffering playing'
        #print '       >1 present stalls'
    else:
        eventStart = 'first rebuffering'
        eventEnd = 'first rebuffering playing'
        #print '      There is 1 present stall'
    return eventStart,eventEnd

def QoEfromstalls(threadID, processID, video_no, stall, eventStart, eventEnd, QoE_stallDur, time_10sec_back):
    QoE, stallDur = QoE_stallDur[0], QoE_stallDur[1]

    tsStallStart, tsStallEnd = get_event_ts(threadID,processID, video_no, stall,eventStart,'ASC'), get_event_ts(threadID, processID, video_no, stall, eventEnd, 'ASC') #Gets timestamps of when eventStart and eventEnd occurred
    print '     time10secback: ',time_10sec_back
    print '     eventstart: ',eventStart, '    ',tsStallStart
    print '     eventend: ',eventEnd,'     ',tsStallEnd
    if tsStallEnd == -1 and tsStallStart > time_10sec_back:   #Buffering has started in the past 10 sec and is still going on
        print '     Buffering has started in the past 10 sec and is still going on'
        tsStallEnd = time_10sec_back + 10 #int(get_event_end_ts(IP_Address,processID,stall,eventStart))
        print '     ==>tsstallend: ',tsStallEnd
    if tsStallEnd > time_10sec_back:    #If buffering ended in the last 10 sec
        print '     Buffering ended in last 10sec'
        if tsStallStart < time_10sec_back:    #If buffering began before last 10 sec too
            tsStallStart = time_10sec_back
    #print tsStallStart, tsStallEnd, time_10sec_back
        stallDur = tsStallEnd - tsStallStart + 1

        if stallDur > 10:
            stallDur = 10

        print '     ',threadID, ': QoE -> ',QoE, ',stall -> ',stall, ',Stall duration -> ', stallDur
        QoE = interruptDQS(QoE, stall, stallDur)[-1]

    else:   #event ended more than 10sec back
        print "     Playback without stalls!"
        print '     ',threadID, ': QoE -> ',QoE, ',stall -> ',stall, ',Stall duration -> ', stallDur
        QoE = playbackDQS(QoE, stall, 10-stallDur)[-1]

    
    QoE_stallDur = [QoE, stallDur]
    return QoE_stallDur


runID = -1
while True:

    print 'Waiting for run'
    runID = int(get_latest_run()) + 1  #Returns 0 if no data in results table
    print 'runID: ',runID
    threadIDs = get_client_threadIDs() #Get threadIDs >20sec back from client table
    
    if( threadIDs != 0): #data exists in client table
        Unique_threadIDs = list(set(threadIDs))
        print Unique_threadIDs
        for threadID in Unique_threadIDs:
            threadID = threadID[0]  #threadID is of a tuple of form ('xxdf',)
            processID = get_process_id(threadID) # processid corresponding to threadidfrom client table
            print threadID
            try:

                queueID = 0

                #Getting data from client table    ##############################
                ################################

                fields = get_youtube_specific(threadID)  #Gets latest fields from client table - video_no, ports,load_and_play_state, video_player_state, bitrate, stallNo, timestamp
                fields = fields[0]
                #print '     fields', fields
                video_no, ports, load_and_play_state, play_state, bitrate, stall, currentTime = [fields[i] for i in range(len(fields))]

                stall = int(stall)
                currentTime = int(currentTime)
                #print '     Latest time current time: ',currentTime
                time_10sec_back = currentTime - time_inbetween_runs  

                stalls_10sec_ago = int(get_youtube_stalls_10sec_ago(threadID,time_10sec_back))  #Gets  stall number from client table with latest timestamp less than time_10sec_back
                print '     video number: ',video_no
                print '     stalls_10sec_ago ', stalls_10sec_ago


                #Getting previous data from results table   ########################
                #########################################

                prev_result_state = get_prev_state(threadID)   #Getting latest QoE, buffer_state, play_state from results table
                if prev_result_state == -1:
                    print '     New video'
                    prev_buffer_state, prev_play_state, prev_QoE = 0, 'initial playing', 5

                else:
                    prev_buffer_state, prev_play_state, prev_QoE = prev_result_state[1], prev_result_state[2], prev_result_state[0]

                if prev_buffer_state < 0:
                    prev_buffer_state = 0
                #print '     prev_buffer_state: ',prev_buffer_state
                #print '     prev_play_state: ',prev_play_state
                print "     Prev QoE -> ", prev_QoE

                if stalls_10sec_ago > stall:  #If we start a new video for some reason number of stalls 10 sec back > present number of stalls
                    stalls_10sec_ago = stall

                print '     stalls ',stall
                QoE = prev_QoE

                # Processing client and previous results data #####################################
                #####################################

                stallDur = 0

                if stall >= 1:
                    eventStart, eventEnd = geteventStartEnd(stall)  #first/multiple buffering/playing

                QoE_stallDur = [QoE, stallDur]
                if stall == 0:
                    QoE = playbackDQS(prev_QoE, 1, 10)[-1]
                    print "     Current QoE (DQS) -> ", QoE

                elif stall == stalls_10sec_ago:   #No new stalls
                    print '     No new stalls'
                    QoE_stallDur = QoEfromstalls(threadID, processID, video_no, stall, eventStart, eventEnd, QoE_stallDur, time_10sec_back)
                    QoE, stallDur = QoE_stallDur[0], QoE_stallDur[1]
                    print "     Current QoE (DQS) -> ", QoE
            
                elif stall > stalls_10sec_ago:    #Stall(s) has occurred in the past 10 sec

                    print "     New stalls"
                    for itr in range(int(stalls_10sec_ago), int(stall)):

                        QoE_stallDur = QoEfromstalls(threadID, processID, video_no, itr+1, eventStart, eventEnd, QoE_stallDur, time_10sec_back)

                        if stallDur + QoE_stallDur[1] > 10: #stallDur is previous stallDur 
                            QoE_stallDur[1] = 10

                        QoE, stallDur = QoE_stallDur[0], QoE_stallDur[1]
                        # tsStallStart, tsStallEnd = get_event_ts(threadID,processID, itr+1,eventStart, 'ASC'), get_event_ts(threadID,processID, itr+1,eventEnd, 'DESC')

                        print "     Current QoE (DQS) -> ", QoE

                test = load_and_play_state.split(', ')
                #print 'test: ',test
                if len(test) > 1:
                    now_progress = float(test[0].split('[')[1])
                    now_load = float(test[1].split(']')[0])
                    buffer_state = now_load - now_progress
                    if buffer_state < 0:
                        buffer_state = 0
                    #print "Current buffer state -> ",buffer_state

                currentStall = stall


                print '     ',runID, processID,threadID, buffer_state, play_state, currentStall, stallDur, prev_QoE, prev_buffer_state, prev_play_state, QoE


                insert_into_db(runID, processID,threadID, ports, buffer_state, play_state, bitrate, currentStall, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE)
            except:
                traceback.print_exc()
                pass

            print '-----------------------------------------------------'

    time.sleep(time_inbetween_runs)
    print '========================================================================================'