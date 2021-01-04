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
import threading
import random
import pandas as pd

hostIP = "127.0.0.1"     # Database server IP
username = "root"
passwd = "cesgtamu"
db = "flow_bazaar"                  # Database name
time_inbetween_runs = 10

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


def get_event_ts(threadID,bufID,event):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT timestamp FROM flow_bazaar.client_table WHERE threadID = %s AND stallNo = %s AND dqs_state = %s ORDER BY timestamp ASC LIMIT 1;", (threadID,bufID,event))
        results = cur.fetchone()
        con.close()
        if(bool(results) is not False):
            return results[0]
        elif(bool(results) is False):
            results = -1
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_prev_state(threadID):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT QoE, buffer_state, play_state FROM flow_bazaar.results_table WHERE threadID = %s ORDER BY timestamp DESC LIMIT 1;", (threadID))
        results = cur.fetchone()
        con.close()
        if(bool(results) is not False):
            return results
        elif(bool(results) is False):
            results = -1
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_youtube_stalls_10sec_ago(threadID, time_10sec_back):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT stallNo FROM flow_bazaar.client_table WHERE threadID = %s AND timestamp <= %s ORDER BY timestamp DESC LIMIT 1;", (threadID, time_10sec_back))
        results = cur.fetchall()
        con.close()
        if(bool(results) is not False):
            return results
        elif(bool(results) is False):
            print "     No new youtube prev stall state"
            results = 0
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_youtube_specific(threadID):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT load_and_play_state, video_player_state, bitrate, stallNo FROM flow_bazaar.client_table WHERE threadID = %s ORDER BY timestamp DESC LIMIT 1;", (threadID))
        results = cur.fetchall()
        con.close()
        if(bool(results) is not False):
            return results
        elif(bool(results) is False):
            print "No new youtube state"
            results = 0
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_prev_ts_client(threadID):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)
        cur = con.cursor()
        cur.execute("SELECT timestamp FROM flow_bazaar.client_table WHERE threadID = %s ORDER BY timestamp DESC LIMIT 1;", (threadID))
        results = cur.fetchone()

        con.close()

        if(bool(results) is not False):
            return results[0]
        elif(bool(results) is False):
            results = 0
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_ports(threadID):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT ports FROM flow_bazaar.client_table WHERE threadID = %s ORDER BY timestamp DESC LIMIT 1;", (threadID))
        results = cur.fetchall()
        if con:
            con.close()
            if(bool(results) is not False):
                return results
            elif(bool(results) is False):
                print "No new youtube state"
                results = 0
                return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])



def get_queue(IP_Address,processID):    #Check output when policy table is empty
    _timestamp = int(time.time())
    lb_timestamp = _timestamp - time_inbetween_runs

    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT queueID FROM flow_bazaar.policy_table WHERE IPAddress = %s AND processID = %s ORDER BY timestamp DESC LIMIT 1;", (IP_Address, processID))
        results = cur.fetchall()    #print
        con.close()
        if(bool(results) is not False):
            return results
        elif(bool(results) is False):
            print "No new queue."
            results = 0 #NULL 
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_process_id(threadID):
    _timestamp = int(time.time())
    lb_timestamp = _timestamp - time_inbetween_runs

    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT processID FROM flow_bazaar.client_table WHERE threadID = %s AND timestamp >= %s ORDER BY timestamp DESC;", (threadID, lb_timestamp))
        results = cur.fetchall()
        con.close()
        if(bool(results) is not False):
            return results
        elif(bool(results) is False):
            print "no process id."
            results = [0]
            return results
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_user_threadID():
    _timestamp = int(time.time())
    lb_timestamp = _timestamp - 20

    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT threadID FROM flow_bazaar.client_table WHERE timestamp >= (%s) ORDER BY timestamp DESC;", (lb_timestamp, )  )
        results = cur.fetchall()
        con.close()
        if(bool(results) is not False):
            return results
        elif(bool(results) is False):
            print "No new users/data"
            results = 0
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])

def get_latest_run():
    try:
        con = MySQLdb.connect(host= hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("Select runID from flow_bazaar.results_table order by timestamp DESC limit 1;")
        results = cur.fetchone()
        #print 'results of get_latest_run sql ',results
        if(bool(results) is not False):
            return results[0]
        elif(bool(results) is False):
            results = 0
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])



currentStall = -1
runID = -1


while True:

    print 'Waiting for run'
    time.sleep(time_inbetween_runs)
    runID = int(get_latest_run())   #Returns 0 if no data in results table
    runID = runID+1
    print 'runID: ',runID
    threadIDs = get_user_threadID() #Get threadIDs >20sec back from client table

    if( threadIDs != 0): #data exists in client table
        Unique_threadID = list(set(threadIDs))

        for threadID in Unique_threadID:
            threadID = threadID[0]  #threadID is a tuple of the form ('x.x.y.y', )
            process = get_process_id(threadID) # from table1

            QoE = 0

            try:

                proceQFlowssID = process[0]

                #queueID = get_queue(IP_Address, processID)[0][0]    #Try without dereferencing - 
                #queueID = get_queue(IP_Address, processID)
                #print '     queueID: ',queueID


                buffer_state = 0    #loaded minus progressed

                stallDur = 0

                #Getting data from client table    ##############################
                ports = get_ports(threadID)[0] #Gets ports from client table

                currentTime = int(get_prev_ts_client(threadID))
                time_10sec_back = currentTime - time_inbetween_runs  
                #print '     currentTime - time_inbetween_runs ', time_10sec_back
                fields = get_youtube_specific(threadID)[0]  #Gets other fields from client table - load_and_play_state, video_player_state, bitrate, stallNo
                print '     fields', fields
                load_and_play_state = fields[0]
                play_state = fields[1]
                bitrate = fields[2]
                stall = int(fields[3])

                if get_youtube_stalls_10sec_ago(threadID,time_10sec_back) == 0:   #Gets stall number from client table with timestamp less than time_10sec_back
                    stalls_10sec_ago = 0
                else:
                    stalls_10sec_ago = int(get_youtube_stalls_10sec_ago(threadID,time_10sec_back)[0][0])
                print '     stalls_10sec_ago ', stalls_10sec_ago


                #Getting data from results table   ########################

                prev_result_state = get_prev_state(threadID)   #Getting QoE, buffer_state, play_state from results table
                print '     prev_result_state', prev_result_state

                if prev_result_state != -1:
                    prev_buffer_state = prev_result_state[1]
                    prev_play_state = prev_result_state[2]
                    QoE = prev_result_state[0]
                    #print '           if prev_result_state != -1'
                else:
                    prev_buffer_state = 0
                    prev_play_state = 'initial playing'
                    QoE = 5
                    #print '           if prev_result_state == -1'
                
                print '     prev_buffer_state: ',prev_buffer_state
                print '     prev_play_state: ',prev_play_state
"""                 if QoE == -1: #Initial condition for QoE
                    QoE = 5 """
                prev_QoE = QoE
                print "     Prev QoE -> ", prev_QoE

                if stalls_10sec_ago > stall:  #If for some reason number of stalls 10 sec back > present number of stalls
                    stalls_10sec_ago = stall

                print '     stalls ',stall
                if stall == 1:
                    eventStart = 'first rebuffering'
                    eventEnd = 'first rebuffering playing'
                    print '      There is 1 present stall'
                elif stall > 1:
                    eventStart = 'multiple rebuffering'
                    eventEnd = 'multiple rebuffering playing'
                    print '       >1 present stalls'

                if stall == 0:
                    QoE = playbackDQS(QoE, 1, 10)[-1]

                elif stall == stalls_10sec_ago:   #No new stalls
                    tsStallStart = int(get_event_ts(threadID,stall,eventStart)) #Gets timestamp of when eventStart occurred
                    tsStallEnd = int(get_event_ts(threadID,stall,eventEnd))

                    if tsStallEnd == -1 and tsStallStart > time_10sec_back:   #Buffering has started in the past 10 sec and is still going on
                        tsStallEnd = currentTime #int(get_event_end_ts(IP_Address,processID,stall,eventStart))

                    if tsStallEnd > time_10sec_back:    #If buffering ended in the last 10 sec
                        if tsStallStart < time_10sec_back:    #If buffering began before last 10 sec too
                            tsStallStart = time_10sec_back
                    #print tsStallStart, tsStallEnd, time_10sec_back
                        stallDur = tsStallEnd - tsStallStart + 1


                        if stallDur > 10:
                            stallDur = 10

                    print threadID, ": Stall duration -> ", stallDur
                    QoE = interruptDQS(QoE, stall, stallDur)[-1]
                    else:
                        print "Playback without stalls!"

            
                elif stall > stalls_10sec_ago:    #Stall(s) has occurred in the past 10 sec

                    print "   New stalls (stall > stalls_10sec_ago)"
                    for itr in range(int(stalls_10sec_ago), int(stall)):
                        tsStallStart = int(get_event_ts(threadID,itr+1,eventStart))
                        tsStallEnd = int(get_event_ts(threadID,itr+1,eventEnd))

                        if tsStallEnd == -1 and tsStallStart >= time_10sec_back:    #If stall started in the past 10 sec and stall hasnt ended
                            tsStallEnd = currentTime
                        if tsStallEnd >= time_10sec_back:   #If stall ended in the past 10 sec
                            if tsStallStart < time_10sec_back:    #If stall started more than 10sec ago too
                                tsStallStart = time_10sec_back
  
                            stallDur += (tsStallEnd - tsStallStart + 1)
                            if stallDur > 10:
                                stallDur = 10
                            print IP_Address, threadID, ": Stall duration -> ", stallDur
                            QoE = interruptDQS(QoE, stall, stallDur)[-1]
                        else:
                            #print "Playback without stalls!"
                            QoE = playbackDQS(QoE, stall, 10-stallDur)[-1]


                if prev_buffer_state < 0:
                    prev_buffer_state = 0

                print "     Prev buffer state and prev_play_state -> ", prev_buffer_state, prev_play_state
                print "     Current QoE (DQS) -> ", QoE


                test = load_and_play_state.split(', ')
                #print '     test[1]', test[1].split(']')
                if len(test) > 1:
                    now_progress = float(test[0].split('[')[1])
                    now_load = float(test[1].split(']')[0])
                    buffer_state = now_load - now_progress
                    if buffer_state < 0:
                    buffer_state = 0
                    #print "Current buffer state -> ",buffer_state

                currentStall = stall


                print runID, processID,threadID, ports, buffer_state, play_state, bitrate, currentStall, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE


                insert_into_db(runID, processID,threadID, ports, buffer_state, play_state, bitrate, currentStall, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE)
            except:
                traceback.print_exc()
                pass

            print '-----------------------------------------------------'

    print '========================================================================================'