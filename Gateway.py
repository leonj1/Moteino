import time, sys, serial, threading
import collections
import httplib
import string
import smtplib
import re
import time #to get epoch time
import datetime
#Needed for Python 2.x to perform HTTP POST: https://docs.python.org/2/howto/urllib2.html
import urllib
import urllib2

### GENERAL SETTINGS ###
SERIALPORT = "/dev/ttyUSB0"  # the default com/serial port the receiver is connected to
BAUDRATE = 115200            # default baud rate we talk to Moteino

DEBUG = False

#To prevent spamming in MOTION alerts
ELAPSE_TIME_WINDOW=600 #5 min wait

WATER_ALERTS = ['9148151676@vtext.com', 'leonj1@gmail.com']
HOUSE_MOTION_ALERTS = ['9148151676@vtext.com', 'leonj1@gmail.com']
ALL_CAR_MOTION_ALERTS = ['9148151676@vtext.com', 'leonj1@gmail.com', '9143300602@vtext.com'] 
JOSE_CAR_MOTION_ALERTS = ['9148151676@vtext.com', 'leonj1@gmail.com' ] 

WATER_URL = 'http://joseleon.co/putWater.php'

def seconds_passed(oldepoch, expected_elapsed_seconds):
    return time.time() - oldepoch >= expected_elapsed_seconds

#email Jose function
def send_email(subject, message, to_distribution_list):
            import smtplib

            gmail_user = "leonj1@gmail.com"
            gmail_pwd = "JoseLeon123"
            FROM = 'leonj1@gmail.com'
            #TO = ['9148151676@vtext.com', 'leonj1@gmail.com'] #must be a list
	    TO = to_distribution_list
            SUBJECT = subject
            TEXT = message

            # Prepare actual message
            message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
            """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
            try:
                server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
                server.ehlo()
                server.starttls()
                server.login(gmail_user, gmail_pwd)
                server.sendmail(FROM, TO, message)
                server.close()
                print 'successfully sent the mail'
            except:
                print "failed to send mail"


#This is Python's version of a switch statement
def getOutFile(x):
    return {
        '[17]': 'motion.txt',	#MotionMotes
        '[18]': 'motion.txt',	#MotionMotes
        '[19]': 'motion.txt',	#MotionMotes
        '[20]': 'motion.txt',	#MotionMotes
        '[21]': 'motion.txt',	#MotionMotes
        '[22]': 'data.txt',	#Watermeter data
        '[23]': 'fridge_kitchen.txt',
        '[26]': 'freezer_garage.txt',
        }.get(x, '0')    # 0 is default if x not found

# Read command line arguments
if (sys.argv and len(sys.argv) > 1):
  if len(sys.argv)==2 and sys.argv[1] == "-h":
    print " -d               Set DEBUG=True"
    print " -g               Set GRAPH=True (requires these python libs: wx, numpy, matplotlib, pylab)"
    print " -s SPort         Read from serial port SPort (Default: ", SERIALPORT, ")"
    print " -b Baud          Set serial port bit rate to Baud (Default: ", BAUDRATE, ")"
    print " -emonhost HOST   Set EMONHost to HOST (Default: ", EMONHOST, ")"
    print " -emonkey  KEY    Set EMONAPIKey to KEY"
    print " -emonport PORT   Set EMONHostPort to PORT (Default: ", EMONHOSTPORT, ")"
    print " -h               Print this message"
    exit(0)
    
  for i in range(len(sys.argv)):
    if sys.argv[i] == "-d":
      DEBUG = True
    if sys.argv[i] == "-g":
      GRAPHIT = True
    if sys.argv[i] == "-s" and len(sys.argv) >= i+2:
      SERIALPORT = sys.argv[i+1]
    if sys.argv[i] == "-b" and len(sys.argv) >= i+2:
      BAUD = sys.argv[i+1]
    if sys.argv[i] == "-emonhost" and len(sys.argv) >= i+2:
      EMONHOST = sys.argv[i+1]
    if sys.argv[i] == "-emonkey" and len(sys.argv) >= i+2:
      EMONAPIKEY = sys.argv[i+1]
    if sys.argv[i] == "-emonport" and len(sys.argv) >= i+2:
      EMONHOSTPORT = sys.argv[i+1]


  #legend((voltagewatchline, ampwatchline), ('V', 'A'))
    

# open up the FTDI serial port to get data transmitted to Moteino
ser = serial.Serial(SERIALPORT, BAUDRATE, timeout=10)

#helper function
def isnumeric(s):
  try:
    float(s)
    return True
  except ValueError:
    return False

def sendMail(FROM, TO, BODY):
  server = smtplib.SMTP('smtp.gmail.com:587')
  server.ehlo()
  server.starttls()
  server.login('leonj1@gmail.com', 'JoseLeon123')
  server.sendmail(FROM, [TO], BODY)
  server.quit()
    
def MAIN():
  #global voltagedata, ampdata
  NUM_OF_MISSED_ALERTS=0
  NUM_OF_MISSED_ALERTS_MOM_CAR=0
  NUM_OF_MISSED_ALERTS_JOSE_CAR=0
  LAST_MOTION_ALERT=0
  ALL_MOTION_ALERTS=""

  #voltagedata=ampdata=VData=AData=[]
  if DEBUG: print "Start - waiting for data on ", SERIALPORT, " @ ", BAUDRATE, " baud..."
  
  while True:
    line = ser.readline()
    data = line.rstrip().split()  #no argument = split by whitespace
    
    if len(data)>=2:
      idMatch = re.match('\[([0-9]+)\]', data[0])
      
      if idMatch:
        epoch_time = int(time.time())
        
        senderID = int(idMatch.group(1))           #extract sender ID
        json = ""
        #print "SenderID is " + str(senderID) + " and 3rd token is " + data[3]
        
        for i in range(1, len(data)):
          dataParts = data[i].split(":")
          
	  #print "dataParts[0] is " + dataParts[0] + "|" + str(len(dataParts))

          if len(dataParts)==2:
            #if isnumeric(dataParts[1]):
   	    if 1==2:
              #if DEBUG: print "Length of dataParts is: " + str(len(dataParts))
              json += dataParts[0] + ":" + dataParts[1] + ","
              
              # if DEBUG: print "Temperature: ", dataParts[1], " F"
            else:
		ts = time.time()
		currenttime = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

		if DEBUG: print "What do we have here? " + str(currenttime) + " " + str(data[0]) + ' ' + str(data[1])
                result = str(epoch_time) + "," + str(data[0]) + ' ' + str(data[1]) + "\n"
                outfile=getOutFile(str(data[0]))
		#if DEBUG: print "Outfile is: " + outfile
                if (outfile != '0'):
                   currentJustTime = int(datetime.datetime.fromtimestamp(ts).strftime('%H'))
		   
                   file = open(outfile, "a")
                   file.write(result)
                   file.close()

		   if (dataParts[0]=="GLM"):
		      if DEBUG: print "We got GLM of " + str(dataParts[1])
		      #Perform HTTP POST
		      currentTimeHumanReadable = time.strftime("%Y-%m-%d %H:%M:%S")
		      print "Last Min Gallon: " + str(dataParts[1])
		      gallonsLastMinute = int(float(dataParts[1]))
		      values = {'date' : currentTimeHumanReadable, 'value' : gallonsLastMinute }
          
		      data = urllib.urlencode(values)
		      req = urllib2.Request(WATER_URL, data)
		      try:
		         response = urllib2.urlopen(req)
		      except: 
    		         print('We failed to reach a server.')
    			 
		      the_page = response.read()
		      print "Posting: " + currentTimeHumanReadable + " Value: " + str(gallonsLastMinute)

		      if gallonsLastMinute > 100:
		        message=" Was " + str(gallonsLastMinute) + " At " + str(currenttime)
     		        send_email("Water Usage", message, WATER_ALERTS)
                   elif (str(data[1])=="MOTION"):
    		      if str(data[0])=='[18]':
 			if currentJustTime >= 20 or currentJustTime <= 6:
		          message="At " + str(currenttime)
 			  send_email("MOTION MOM CAR", message, ALL_CAR_MOTION_ALERTS)
		      elif str(data[0])=='[20]':
 			if currentJustTime >= 20 or currentJustTime <= 6:
		          message="At " + str(currenttime)
		          send_email("MOTION JOSE CAR", message, JOSE_CAR_MOTION_ALERTS)
		      elif str(data[0])=='[21]':
		        print "TEST Motion 21"
		      else:
                        if str(data[0])=='[17]':
                           message="On LEFT side of house!"
                        elif str(data[0])=='[19]':
                           message="RIGHT side of house!"
                        else:
                           message=""
                        #Only send email if elapsed time has passed. To prevent spamming!
                        #ts = time.time()
                        #currenttime = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        NUM_OF_MISSED_ALERTS += 1
                        ALL_MOTION_ALERTS=ALL_MOTION_ALERTS + "\n" + str(currenttime) + " " + message
                        if (seconds_passed(LAST_MOTION_ALERT, ELAPSE_TIME_WINDOW)):
                           send_email("MOTION " + str(NUM_OF_MISSED_ALERTS), ALL_MOTION_ALERTS, HOUSE_MOTION_ALERTS)
                           NUM_OF_MISSED_ALERTS=0
                           LAST_MOTION_ALERT=epoch_time
			   ALL_MOTION_ALERTS=""
                        else:
                           if DEBUG: print "Not time to notify about motion yet. Pending alerts: " + str(NUM_OF_MISSED_ALERTS)
                else:
		   print "Not outfile defined for " + str(senderID)

        if (seconds_passed(LAST_MOTION_ALERT, ELAPSE_TIME_WINDOW) and NUM_OF_MISSED_ALERTS > 0):
           send_email("MOTION " + str(NUM_OF_MISSED_ALERTS), ALL_MOTION_ALERTS, HOUSE_MOTION_ALERTS)
           NUM_OF_MISSED_ALERTS=0
           LAST_MOTION_ALERT=epoch_time
           ALL_MOTION_ALERTS=""
        #elif (seconds_passed(LAST_MOTION_ALERT, ELAPSE_TIME_WINDOW)):
        #   if DEBUG: print "Time elapsed, but there are no alerts to send"
 
        if len(json)>0:
          result = str(epoch_time) + "," + str(data[2]) + "\n"
          outfile=getOutFile(str(data[0]))
          if (outfile != '0'): 
	     file = open(outfile, "a")
             file.write(result)
             file.close()
          
          #if DEBUG: print str(data[0]) + " Result is: " + result + " to file: " + outfile

MAIN()
