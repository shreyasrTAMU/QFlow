# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import struct
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
import mysql.connector
import threading
import random
import MySQLdb
import time
import policy_interface as PI

FLOWBAZAAR_ID = 0x00001234    #specific to each application
DATAPATH_ID = 0x000000000001  #connection between controller and access point

MAX_RETRIES = 3
MAX_OUTSTANDING_CMDS = 10000

FB_TC_CMD = 111

hostIP = "127.0.0.1"     # Database server IP
username = "root"
passwd = "cesgtamu"
db = "flow_bazaar"                  # Database name

TABLES = {}


class tcCmdResponse:
    def __init__(self, cmdID, cmdOPLen, cmdOP):
        self.commandID = cmdID
        self.ResponseLen = cmdOPLen
        self.Response = cmdOP

class fileTransferRes:
    def __init__(self, typeID, seqNo, remaining, data):
        self.fileTypeID = typeID
        self.sequenceNo = seqNo
        self.remainingChunks = remaining
        self.fileData = data

class Command:
    def __init__(self, cmdType, cmd):
        self.cmdType = cmdType
        self.cmd = cmd
        self.cmdID = random.randint(1, 1000000000)
        self.response = None
        self.retries = 0

    def send(self, datapath):
        parser = datapath.ofproto_parser
        cmdLen = len(self.cmd)
        
        data = struct.pack('>ll200s',
                           self.cmdID,
                           cmdLen,
                           self.cmd)

        exp = parser.OFPExperimenter(datapath,
                                     FLOWBAZAAR_ID,
                                     self.cmdType,
                                     data)
        
        datapath.send_msg(exp)
        #print "Sent command object to datapath!"

    def handleResponse(self, respObj):
        #Response available from experimenter handler
        self.response = respObj
        #print "Inside object handle response callback"
        #Perform specific handling in child class

    def handleError(self, datapath):
        print "Inside object handle error callback"
        if self.retries < MAX_RETRIES:
            #self.send(datapath)
            self.retries = self.retries + 1
            print "Retry sending command -> ", self.retries

    def timerCB(self,cmdList):
        print "Inside timer callback!"
        #Timeout! Flush command list
        for cmdObj in cmdList:
            del cmdObj

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = [[]]
        self.cmdList = [] 
        self.timeout = None
        self.alreadySent = False
        self.queueLen = 0
        self.pktsIn_prev = -1
        self.tsIn_prev = 0
        self.expRnd = 1

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.datapaths.insert(datapath.id,datapath)

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        print "Inside switch features handler! Inserted datapath with id %d" %datapath.id

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)
        print "Inside add flow!"



    def netem_setup(self, datapath):

        delay = 0 + self.expRnd%10
        loss = 0 + self.expRnd/10

        cmdStr = "./initialize_tc_default.sh " + str(loss) + "% " + str(delay) +"ms"
        myCmd = Command(FB_TC_CMD, cmdStr)
        myCmd.send(datapath)

        self.expRnd = self.expRnd + 1

        threading.Timer(600, self.netem_setup, [datapath]).start()


    def queue_setup(self, datapath):  #Run every 10 sec
        connexn = mysql.connector.connect(host=hostIP, user=username, passwd=passwd, db=db)
        print '################################################################################33'

      	cursor = connexn.cursor()

      	cmdStr = "tc filter del dev wlan0 pref 1"
      	myCmd = Command(FB_TC_CMD, cmdStr)
      	myCmd.send(datapath)

        query = ("SELECT DISTINCT threadID FROM `policy_table`")
        cursor.execute(query)
        threadIDs = cursor.fetchall()  #result is of the form [(x,),(y,)]

        if threadIDs:
            print 'threadIDs: ',threadIDs
            for threadID in threadIDs: #Reading information about all clients
                threadID = threadID[0]
                print 'threadID', threadID
                query = ("SELECT * FROM `policy_table` WHERE `threadID` = %s ORDER BY `timestamp` DESC LIMIT 1")
                cursor.execute(query, (threadID,))
                result = cursor.fetchall()
                IPAddress = None
                flows = None
                #print 'result: ',result
                for row in result:
                            queueID = int(row[8])
                            threadID = row[1]
                            IPAddress = threadID.split('/')[0]
                            flows = row[2]
                            portList = flows.split(',')
                            #print portList
                            for port in portList:
                                    if port == 'fc12':  #In the case of fc12 appears as a port number, ignore. Supposed to be only numbers
                                        print "fc12 seen"
                                        continue
                                    newport = ''
                                    for char in port:
                                        if char.isdigit():
                                            newport = newport + char
                                    cmdStr = "tc filter add dev wlan0 parent 1:0 protocol ip prio 1 u32 match ip dst "
                                    cmdStr = cmdStr + str(IPAddress) + "/32" + " match ip dport " + str(newport) 
                                    cmdStr = cmdStr + " 0xffff flowid " + "1:" + str(queueID) 
                                    print cmdStr
                                    myCmd = Command(FB_TC_CMD, cmdStr)
                                    myCmd.send(datapath)
        else:
            print 'No threads available right now'

	      
        cmdStr = "tc filter add dev wlan0 parent 1:0 protocol ip prio 1 u32 match ip src 192.168.1.140/32 flowid 1:10"  #Dummy filter so that all the previous filters get executed. Put in the default queueID 30
      	myCmd = Command(FB_TC_CMD, cmdStr)
      	myCmd.send(datapath)

        print "\n\n\n\nwait for setting filters again\n\n\n\n"
        threading.Timer(10, self.queue_setup, [datapath]).start()


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
        print "Inside packet in handler!"

        if self.alreadySent != True:

            self.alreadySent = True
            
            # myCmd = Command(FB_TC_CMD, "ls -l")
            # myCmd.send(datapath)

            # Start callback for setting tc queues & iptables rules
            self.queue_setup(datapath)





