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

#CHANGE get_user_IP() get_process_id timestamp
hostIP = "127.0.0.1"     # Database server IP
username = "root"
passwd = "cesgtamu"
db = "flow_bazaar"                  # Database name
time_inbetween_runs = 10

def insert_into_db(runID, IP_Address, processID,thread_id, ports, buffer_state, play_state, bitrate, currentStall, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE):
    timestamp = int(time.time())
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("INSERT INTO flow_bazaar.results_table(runID, IPAddress, processID,threadID, ports, buffer_state, play_state, bitrate, Stalls, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE, timestamp) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (runID, IP_Address, processID,thread_id, ports, buffer_state, play_state, bitrate, currentStall, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE, timestamp))
        con.commit()
        con.close()

    except:
        traceback.print_exc()


def get_event_ts(_IP_Address,processID,bufID,event):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT timestamp FROM flow_bazaar.client_table WHERE IPAddress = %s AND processID = %s AND stallNo = %s AND dqs_state = %s ORDER BY timestamp ASC LIMIT 1;", (_IP_Address, processID,bufID,event))
        results = cur.fetchone()
        con.close()
        if(bool(results) is not False):
            return results[0]
        elif(bool(results) is False):
            results = -1
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_prev_state(_IP_Address,processID):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT QoE, buffer_state, play_state FROM flow_bazaar.results_table WHERE IPAddress = %s AND processID = %s ORDER BY timestamp DESC LIMIT 1;", (_IP_Address, processID))
        results = cur.fetchone()
        con.close()
        if(bool(results) is not False):
            return results
        elif(bool(results) is False):
            results = -1
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_youtube_stalls_10sec_ago(IP_Address, processID, prev_time):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT stallNo FROM flow_bazaar.client_table WHERE IPAddress = %s AND processID = %s AND timestamp <= %s ORDER BY timestamp DESC LIMIT 1;", (IP_Address, processID,prev_time))
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


def get_youtube_specific(IP_Address, processID):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT load_and_play_state, video_player_state, bitrate, stallNo FROM flow_bazaar.client_table WHERE IPAddress = %s AND processID = %s ORDER BY timestamp DESC LIMIT 1;", (IP_Address, processID))
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


def get_prev_ts_client(_IP_Address,processID):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)
        cur = con.cursor()
        cur.execute("SELECT timestamp FROM flow_bazaar.client_table WHERE IPAddress = %s AND processID = %s ORDER BY timestamp DESC LIMIT 1;", (_IP_Address, processID))
        results = cur.fetchone()

        con.close()

        if(bool(results) is not False):
            return results[0]
        elif(bool(results) is False):
            results = 0
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_user_specific(IP_Address, processID):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT threadID, ports FROM flow_bazaar.client_table WHERE IPAddress = %s AND processID = %s ORDER BY timestamp DESC LIMIT 1;", (IP_Address, processID))
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

def get_occupants(queueID):
    try:
        con = MySQLdb.connect(host="localhost", user="root", passwd="web002", db="flow_bazaar")

        cur = con.cursor()
        cur.execute("SELECT num_occupants FROM flow_bazaar.Occupants_table WHERE queueID = %s ORDER BY timestamp DESC LIMIT 1;", (queueID))

        results = cur.fetchall()
        con.close()
        if(bool(results) is not False):
            return results
        elif(bool(results) is False):
            print "No occupant info"
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


def get_prev_parameters(_IP_Address,processID):
    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT timestamp FROM flow_bazaar.results_table WHERE IPAddress = %s AND processID = %s ORDER BY timestamp DESC LIMIT 1;", (_IP_Address, processID))
        results = cur.fetchone()
        con.close()
        if(bool(results) is not False):
            return results[0]
        elif(bool(results) is False):
            results = 0
            return results

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])


def get_process_id(IP_Address):
    _timestamp = int(time.time())
    lb_timestamp = _timestamp - time_inbetween_runs

    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT processID FROM flow_bazaar.client_table WHERE IPaddress = %s AND timestamp >= %s ORDER BY timestamp DESC;", (IP_Address, lb_timestamp))
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


def get_user_IP():
    _timestamp = int(time.time())
    lb_timestamp = _timestamp - 20

    try:
        con = MySQLdb.connect(host=hostIP, user=username, passwd=passwd, db=db)

        cur = con.cursor()
        cur.execute("SELECT IPAddress FROM flow_bazaar.client_table WHERE timestamp >= (%s) ORDER BY timestamp DESC;", (lb_timestamp, )  )
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
    runID = int(get_latest_run())
    runID = runID+1
    print 'runID: ',runID
    IP_Addresses = get_user_IP() # from client table
    #print IP_Addresses
    if( IP_Addresses != 0): #No data exists in client table yet
        Unique_IP_Address = list(set(IP_Addresses))
        #print Unique_IP_Address
        for ip_address in Unique_IP_Address:
            IP_Address = ip_address[0]  #ip_address is a tuple of the form ('x.x.y.y', )
            process = get_process_id(IP_Address) # from table1
            Unique_process = list(set(process))
            print IP_Address, Unique_process
            QoE = 0

            for process in Unique_process:
                print 'Process ',process
                try:

                    processID = process[0]
                    #print IP_Address, processID

                    
                    #queueID = get_queue(IP_Address, processID)[0][0]    #Try without dereferencing - 
                    queueID = get_queue(IP_Address, processID)
                    #print '     queueID: ',queueID


                    buffer_state = 0    #loaded - progressed
                    hasStalled = 0
                    stallDur = 0

                    #Getting data from client table    ##############################
                    threadID_and_ports = get_user_specific(IP_Address,processID)[0] #Gets threadIP and ports from client table
                    print '     threadID_and_ports ',threadID_and_ports
                    thread_id = threadID_and_ports[0]
                    ports = threadID_and_ports[1]
                    currentTime = int(get_prev_ts_client(IP_Address,processID))
                    time_10sec_back = currentTime - time_inbetween_runs  #Gets timestamp from client table - 10
                    #print '     currentTime - time_inbetween_runs ', time_10sec_back
                    fields = get_youtube_specific(IP_Address,processID)[0]  #Gets other fields from client table - load_and_play_state, video_player_state, bitrate, stallNo
                    print '     fields', fields
                    load_and_play_state = fields[0]
                    play_state = fields[1]
                    bitrate = fields[2]
                    stall = int(fields[3])

                    if get_youtube_stalls_10sec_ago(IP_Address,processID,time_10sec_back) == 0:   #Gets stall number from client table with timestamp less than time_10sec_back
                        stalls_10sec_ago = 0
                    else:
                        stalls_10sec_ago = int(get_youtube_stalls_10sec_ago(IP_Address,processID,time_10sec_back)[0][0])
                    print '     stalls_10sec_ago ', stalls_10sec_ago

                    #Getting data from results table   ########################
                    prev_time = get_prev_parameters(IP_Address,processID)   #Gets previous timestamp from results table that correspond to IPAddress and processID from results table
                    result_prev_state = get_prev_state(IP_Address,processID)   #Getting QoE, buffer_state, play_state from results table
                    print '     result_prev_state', result_prev_state

                    if result_prev_state != -1:
                      prev_buffer_state = result_prev_state[1]
                      prev_play_state = result_prev_state[2]
                      QoE = result_prev_state[0]
                      #print '           if result_prev_state != -1'
                    else:
                      prev_buffer_state = 0
                      prev_play_state = 'initial playing'
                      QoE = 5
                      #print '           if result_prev_state == -1'
                    
                    print '     prev_buffer_state: ',prev_buffer_state
                    print '     prev_play_state: ',prev_play_state
                    if QoE == -1: #Initial condition for QoE
                      QoE = 5
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
                      tsStallStart = int(get_event_ts(IP_Address,processID,stall,eventStart)) #Gets timestamp of when eventStart occurred
                      tsStallEnd = int(get_event_ts(IP_Address,processID,stall,eventEnd))

                      if tsStallEnd == -1 and tsStallStart > time_10sec_back:   #Buffering has started in the past 10 sec and is still going on
                        tsStallEnd = currentTime #int(get_event_end_ts(IP_Address,processID,stall,eventStart))

                      if tsStallEnd > time_10sec_back:    #If buffering ended in the last 10 sec
                        if tsStallStart < time_10sec_back:    #If buffering began in the last 10 sec too
                          tsStallStart = time_10sec_back
                        #print tsStallStart, tsStallEnd, time_10sec_back
                        stallDur = tsStallEnd - tsStallStart + 1

                        if stallDur > 0:
                          hasStalled = 1
                          if stallDur > 10:
                            stallDur = 10

                        print IP_Address, thread_id, ": Stall duration -> ", stallDur
                        QoE = interruptDQS(QoE, stall, stallDur)[-1]
                      else:
                        print "Playback without stalls!"

                
                    elif stall > stalls_10sec_ago:    #Stall(s) has occurred in the past 10 sec
                      hasStalled = 1
                      print "   New stalls (stall > stalls_10sec_ago)"
                      for itr in range(int(stalls_10sec_ago), int(stall)):
                        tsStallStart = int(get_event_ts(IP_Address,processID,itr+1,eventStart))
                        tsStallEnd = int(get_event_ts(IP_Address,processID,itr+1,eventEnd))

                        if tsStallEnd == -1 and tsStallStart >= time_10sec_back:    #If stall started in the past 10 sec and stall hasnt ended
                          tsStallEnd = currentTime
                        if tsStallEnd >= time_10sec_back:   #If stall ended in the past 10 sec
                          if tsStallStart < time_10sec_back:    #If stall started more than 10sec ago too
                            tsStallStart = time_10sec_back
                          #print tsStallStart, tsStallEnd, prev_time
                          stallDur += (tsStallEnd - tsStallStart + 1)
                          if stallDur > 10:
                            stallDur = 10
                          print IP_Address, thread_id, ": Stall duration -> ", stallDur
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


                    print runID, IP_Address, processID,thread_id, ports, buffer_state, play_state, bitrate, currentStall, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE


                    insert_into_db(runID, IP_Address, processID,thread_id, ports, buffer_state, play_state, bitrate, currentStall, stallDur, prev_QoE, prev_buffer_state, prev_play_state, queueID, QoE)
                except:
                    traceback.print_exc()
                    pass

                print '-----------------------------------------------------'

    print '========================================================================================'