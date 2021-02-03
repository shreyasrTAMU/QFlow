import MySQLdb
import time
import mysql.connector




hostIP = "127.0.0.1"     # Database server IP
username = "root"
passwd = "cesgtamu"
db = "flow_bazaar"                  # Database name

def fill_to_table():
	connexn = mysql.connector.connect(host=hostIP, user=username, passwd=passwd, db=db)
	cursor = connexn.cursor()
	print('waiting to insert')
	query = ("SELECT DISTINCT threadID FROM `policy_table`")
	cursor.execute(query)
	threadIDs = cursor.fetchall()  #result is of the form [(x,),(y,)]

	print('threadIDs: ',threadIDs)

	prevbuffers = []
	currentbuffers = []
	actions = []
	highqueueNOs = []
	for client in threadIDs: #Reading information about all clients


		threadID = client[0]
		print ('threadID: ',threadID)
		query = ("SELECT * FROM `policy_table` WHERE `threadID` = %s ORDER BY `timestamp` DESC LIMIT 1")
		cursor.execute(query, (threadID,))
		result = cursor.fetchall()
		#print 'result: ',result
		processID = 0
		#print '	',len(result)
		row = result[0]
		#print '		',row

		action = int(row[4])
		processID = row[1]

		print ('	processID: ',processID)
		query = ("SELECT * FROM `results_table` WHERE `threadID` = %s AND `processID` = %s ORDER BY `timestamp` DESC LIMIT 1")
		cursor.execute(query, (threadID,processID))
		result = cursor.fetchall()	
		row = result[0]
		#print '		',row
		currentbuffers.append(float(row[5]))
		prevbuffers.append(float(row[11]))
		actions.append(action)


		print(prevbuffers)
		print(currentbuffers)
		print(actions)
		highqueue = actions.count(10)
		# print highqueue
		highqueueNOs = [highqueue] * len(actions)
		print highqueueNOs
		print('========================================================')

		for i in range(len(actions)):
			cursor.execute("INSERT INTO flow_bazaar.model_table(prevbuffer, currentbuffer, action, highqueueNO) values (%s, %s, %s, %s)", (prevbuffers[i], currentbuffers[i], actions[i], highqueueNOs[i]))
			connexn.commit()

