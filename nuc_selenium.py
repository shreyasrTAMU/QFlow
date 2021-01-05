import datetime
import os
import httplib
import MySQLdb
import random
import shutil
import socket
import signal
import sys
import time
import thread
import threading
import psutil
import traceback
import mysql.connector
from mysql.connector import errorcode
from subprocess import check_output

from array import *
from urllib2 import urlopen
from constants import *
from random import randrange
from threading import Timer
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.command import Command
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from subprocess import PIPE, Popen

YT_URL_LIST = [
"https://www.youtube.com/watch?v=ND8PduJlN6A",
"https://www.youtube.com/watch?v=2xc3EP_dJDs",
"https://www.youtube.com/watch?v=ewrEhrGWKf4",
"https://www.youtube.com/watch?v=Vd7z3GignNU",
"https://www.youtube.com/watch?v=yBvyYixwuIk",
"https://www.youtube.com/watch?v=dQv3t5VCc3U",
"https://www.youtube.com/watch?v=4w_Vc_7irhM",
"https://www.youtube.com/watch?v=dFccny3iGbo",
"https://www.youtube.com/watch?v=8P4Hi99hUJc",
"https://www.youtube.com/watch?v=r4KyslvtOk4",
"https://www.youtube.com/watch?v=0xyR8IgjzMA",
"https://www.youtube.com/watch?v=wufWxldBWsU",
"https://www.youtube.com/watch?v=ebiGew8mYr0",
"https://www.youtube.com/watch?v=y4CIn0jweuc",
"https://www.youtube.com/watch?v=3MrYk3kCUGk",
"https://www.youtube.com/watch?v=0TuMvWCbM-g",
"https://www.youtube.com/watch?v=KO0rEwwyB0g",
"https://www.youtube.com/watch?v=v3_EezKE0WI",
"https://www.youtube.com/watch?v=P2gHUcwZbYk",
"https://www.youtube.com/watch?v=J9aV4Zn8JJE",
"https://www.youtube.com/watch?v=DqVPVRmRIU8",
"https://www.youtube.com/watch?v=hKsGmyhsKFA",
"https://www.youtube.com/watch?v=ynHIlx5RgtI",
"https://www.youtube.com/watch?v=sL4JK_bDo0A",
"https://www.youtube.com/watch?v=1U0N4SGL46A"
]


ips = check_output(['hostname', '--all-ip-addresses'])
IPAddress = ips.split()[0]
IPAddress = '192.168.1.130'

flows = []
bitrate = '?'


def yt_session(dt, process_id, driver, threadID, directory, start_time):
    print "Entering yt_session for ",threadID
    time.sleep(0.1)
    path_to_extension = '/home/ndn3/Downloads/gighmmpiobklfepjocnamgkkbiglidom/4.17.0_0'
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_argument('load-extension=' + path_to_extension)
    prefs = {"download.default_directory" : directory}
    chromeOptions.add_experimental_option("prefs",prefs)
    chromedriver = '/home/ndn3/Downloads/chromedriver'
    driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)
    yt_open_video(dt, process_id, driver, threadID, start_time)


def yt_open_video(dt, process_id, driver, threadID, start_time):
	print "Entering yt_open_video for:",threadID

	try:
		idx = randrange(0,len(YT_URL_LIST))
		time.sleep(5)
		driver.get(YT_URL_LIST[idx])
		print 'get url for', threadID
		if( len(driver.window_handles) == 2):
			driver.switch_to.window(driver.window_handles[1])
			print 'switch to 1 for ',threadID
			driver.close();
			print 'driver close for ', threadID
			driver.switch_to.window(driver.window_handles[0])
	except:
		traceback.print_exc()
		yt_open_video(dt, process_id, driver, threadID, start_time)

	process_id = driver.service.process.pid
	yt_set_vq(dt, driver, process_id, threadID, start_time, idx)


def yt_set_vq(dt, driver, process_id, threadID, start_time, idx):
    print "Entering yt_set_vq for ",threadID
    numberoftimes_vq = 0
    url_playing = driver.current_url
    numberoftimes_vq += 1
    qualityandautoplay = False
    try:
        elem = driver.find_element_by_class_name('videoAdUi')	#If there is an advertisement
        time.sleep(1)
        ad_skip_button = driver.find_element_by_css_selector('.videoAdUiSkipButton.videoAdUiAction')
        ad_skip_button.click()

    except:
        pass
    try:
        url_playing = driver.current_url
    except:
        yt_set_vq(dt, driver, process_id, threadID, start_time, idx)

    while not qualityandautoplay and numberoftimes_vq < 6:

	    try:
	    	#Sets the video quality to the highest possible
	        time.sleep(1) #In this block of codes, sleeping 1 second is absolutely necessary since youtube has UI response delay.


	        setting_button = driver.find_element_by_css_selector('.ytp-button.ytp-settings-button')
	        setting_button.click()
	        time.sleep(1)
	        quality_option_button = driver.find_element_by_xpath('//div[text()="Quality"]')
	        quality_option_button.click()
	        time.sleep(1)
	        quality_button = driver.find_elements_by_css_selector('div.ytp-menuitem-label')	#Selects highest quality possible of video 
	        quality_button[0].click()
	        time.sleep(1)

	        setting_button = driver.find_element_by_css_selector('.ytp-button.ytp-settings-button')
	        setting_button.click()
	        time.sleep(1)
	        autoplay_option_button = driver.find_element_by_xpath('//div[text()="Autoplay"]')
	        autoplay_option_button.click()
	        time.sleep(1)

	        qualityandautoplay = True
	    except:
	    	traceback.print_exc()
	    	numberoftimes_vq += 1


    yt_logger = Timer(dt, yt_session_logger, [round(time.time()), dt, 0, driver, process_id, threadID, url_playing, start_time, idx,0,'initial_buffering','no dqs state'])
    yt_logger.start()


lock = threading.Lock()
def yt_session_logger(start, interval, count, driver, process_id, threadID, url_playing, start_time,idx,rebufNo,state,dqs_state):
	print "Entering yt_session_logger for ",threadID
	ticks = time.time()
	ticks_int = int(time.time())
	time.sleep(1)

	try:

		p = psutil.Process(driver.service.process.pid)
		p_children = p.children(recursive=True)
		process_id = p_children[0].pid

		global flows
		global bitrate
		#flows = []
		for entry in p_children:
			test = entry.pid
			cmd_sentense = "lsof -Pan -p " + str(test) + " -i"    #Lists information about PID such as command, user, type, node, name
			flows.extend(cmdline(cmd_sentense))

		flows = list(set(flows))	#Converts list to set (sorts and removes duplicates) and then back to a list

		bitrate = find_bitrate(driver)
		cancel_button = driver.find_element_by_class_name('ytp-upnext-cancel')
		time.sleep(1)
		cancel_button.click()

		yt_logger = Timer(interval - (ticks-start-count*interval), yt_open_video, [interval, process_id, driver, threadID, start_time])
		yt_logger.start()
		time.sleep(2)

	except:
		#Comes here when
		#traceback.print_exc()
		try:

			buffering_boolean = driver.find_element_by_class_name('buffering-mode')
			

			global lock
			lock.acquire()
			try:
				#IF BUFFERING ################################################
				print 'state when entering buffering: ',state
				if state == 'initial_buffering':
					dqs_state = "startup delay"			

				elif state == "playing" or "playing" in dqs_state:
					rebufNo = rebufNo+1
					#print threadID, " -> New stall"
					if rebufNo == 1:
						dqs_state = "first rebuffering"
					elif rebufNo > 1:
						dqs_state = "multiple rebuffering"

				state = "buffering"
				print('BUFFERING ')

				print_fields(IPAddress, process_id, threadID, flows, bitrate, state, dqs_state, '?', rebufNo,  url_playing)
				insert_into_mysql(IPAddress, process_id, threadID, str(flows), bitrate,state, dqs_state, '?', rebufNo)

			#except:
				#traceback.print_exc()

			finally:
				lock.release()
			yt_logger = Timer(interval - (ticks-start-count*interval), yt_session_logger, [start, interval, count, driver, process_id, threadID, url_playing, start_time, idx, rebufNo,state,dqs_state])
			yt_logger.start()

		except:
			#traceback.print_exc()
			try:
				#IF PLAYING ##########################################################################
				state = "playing"

				test = driver.find_element_by_class_name('html5-video-player')
				test.click()
				test.click()

				#seconds played/total video length
				playProgress_to_TotalVideo = driver.find_element_by_class_name('ytp-play-progress').get_attribute('style').split('(')[1].split(')')[0]
				#seconds loaded/total video length	
				loadProgress_to_TotalVideo = driver.find_element_by_class_name('ytp-load-progress').get_attribute('style').split('(')[1].split(')')[0]

				progress_bar = driver.find_element_by_class_name('ytp-progress-bar')
				max_progress = progress_bar.get_attribute('aria-valuemax')
				seconds_loaded = float(loadProgress_to_TotalVideo) * float(max_progress)	#number of seconds the video has loaded
				seconds_played = progress_bar.get_attribute('aria-valuenow')	#number of seconds the video has played

				videoParametersInSeconds = str([float(seconds_played), float(seconds_loaded)])

				if rebufNo == 0:
					dqs_state = "initial playing"
				elif rebufNo == 1:
					dqs_state = "first rebuffering playing"
				elif rebufNo > 1:
					dqs_state = "multiple rebuffering playing"

				insert_into_mysql(process_id, threadID, str(flows), bitrate, state, dqs_state, videoParametersInSeconds, rebufNo)
				print_fields(process_id, threadID, flows, bitrate, state, dqs_state, videoParametersInSeconds, rebufNo,  url_playing)

				yt_logger = Timer(interval - (ticks-start-count*interval), yt_session_logger, [start, interval, count, driver, process_id, threadID, url_playing, start_time, idx, rebufNo,state,dqs_state])
				yt_logger.start()

				
			except:
				traceback.print_exc()
				print "No clue what to do", process_id, threadID
				sys.exit()
				pass


def get_status(driver):
	print("Entering get_status")
	try:
	    driver.execute(Command.STATUS)
	    return "Alive"
	except:
	    return "Dead"

def cmdline(command):
    process = Popen(
        args=command,
        stdout=PIPE,
        shell=True
    )
    lsof = process.communicate()[0]
    lsof_length = len(lsof.split('\n'))
    lsof_entries = lsof.split('\n')
    dictionary = []
    for each_entry in lsof_entries[1:(lsof_length-1)]:
        dictionary.append(each_entry.split(':')[1])
    flows_ = []
    for each_entry in dictionary:
        flows_.append(each_entry.split(' ')[0])
    flows = []
    for each_entry in flows_:
        flows.append(each_entry.split('->')[0])
    return flows

def find_bitrate(driver):
	html = driver.page_source
	try:
		index1080p = html.find("""qualityLabel\\":\\"1080p""")
		extractedstring = html[index1080p: index1080p + 250]
		bitrateindex = extractedstring.find('averageBitrate')
		bitratestring = extractedstring[bitrateindex : bitrateindex + 30]
		res = [i for i in bitratestring if i.isdigit()] 
		bitrate = ''.join(res)
		return bitrate
	except:
		traceback.print_exc()
		return '?'

def print_fields(process_id, threadID, flows, bitrate, state, dqs_state, videoParametersInSeconds, rebufNo,  url_playing):

	print 'process id: ',process_id
	print 'thread id: ',threadID
	print 'flows: ',flows
	print 'bitrate: ', bitrate
	print 'state: ',state
	print 'dqs state: ',dqs_state
	print 'video parameters in seconds: ',videoParametersInSeconds
	print 'number of rebuffering: ',rebufNo
	print 'url_playing: ',url_playing
	
	if state == "playing":
		print "----------------------------------------------------------------------------"
	else:
		print '==================================================================================='
	
	

def session_decider(process_id, driver, threadID, directory,):
	print("Entering session_decider")
	try:
		while os.path.isdir(directory):
			try:
				shutil.rmtree(directory)	#Deletes the entire directory tree
			except:
				print("Error: shutil.rmtree")
	except:
		print("Error: os.path.isdir")

		if(not os.mkdir(directory)):
			try:
				os.mkdir(directory)
			except:
				print("Error: Not able to make directory: ",directory)
				pass

	while get_status(driver) is 'Alive':
		try:
			print("status of driver is alive")
			driver.quit()
			driver.close()
		except:
			pass

	start_time = time.time()
	process_id = 0
	dt = 1
	thread.start_new_thread(yt_session, (dt, process_id, driver, threadID, directory, start_time))

def insert_into_mysql(processID, threadID, ports, bitrate, video_player_state, dqs_state, load_and_play_state, stallNo):
	_timestamp = int(time.time())
	hostIP = "192.168.1.218"      # Database server IP
	username = "ndn3"
	passwd = "cesgtamu"
	db = "flow_bazaar"                 # Database name
	try:
		con = mysql.connector.connect(user=username, password=passwd,host=hostIP, database=db)

		cur = con.cursor()
		cur.execute("INSERT INTO client_table(processID, threadID, ports, bitrate, video_player_state, dqs_state, load_and_play_state, stallNo, `timestamp`) values (%s, %s, %s, %s, %s, %s, %s, %s, %s) ", (processID, threadID, ports, bitrate, video_player_state, dqs_state, load_and_play_state, stallNo, _timestamp))
		con.commit()
		con.close()

	except:
		traceback.print_exc()

			


try:

	directory1 = '/home/nuc4/Documents/seleniumstuff/1'
	directory2 = '/home/nuc4/Documents/seleniumstuff/2'


	if( len(sys.argv) !=1 ):
		threadName = IPAddress + '/' + str(sys.argv[1])
	else:
		threadName = IPAddress + '/1'
 
 	threadName.strip()
	threadName = str(threadName)
	t1 = threading.Thread(target=session_decider, args = ("0","0",threadName,directory1))
	t1.start()

except Exception, exc:
    print exc

while 1:
    pass