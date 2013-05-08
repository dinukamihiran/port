#! /usr/bin/python

#===============================================================================
"""
Copyright (c) 2013 All Right Reserved, http://www.itfac.mrt.ac.lk
This source is subject to the GNU General Public Licen
</copyright>
<author>UOM.itfac</author>
<email>syscall@knnect.com</email>
<date>2013-04-25</date>
<summary>Contains a linux, (server) service for listen port 9090</summary>
 """
#===============================================================================

"""
-------------------------------
For documentation purpose
-------------------------------
-------------what is socket.accept()-------------

Accept a connection. The socket must be bound to an address and listening for connections. The return value is a pair (conn, address) where conn is a new socket object usable to send and receive data on the connection, and address is the address bound to the socket on the other end of the connection.

A pair (host, port) is used for the AF_INET address family, where host is a string representing either a hostname in Internet domain notation like 'daring.cwi.nl' or an IPv4 address like '100.50.200.5', and port is an integer.

So the second value is the port number used by the client side for the connection. When a TCP/IP connection is established, the client picks an outgoing port number to communicate with the server; the server return packets are to be addressed to that port number.

-------------Luhn algorithm-------------
From Wikipedia, the free encyclopedia

The Luhn algorithm or Luhn formula, also known as the "modulus 10" or "mod 10" algorithm, is a simple checksum formula used to validate a variety of identification numbers, 
such as credit card numbers, IMEI numbers, National Provider Identifier numbers in US and Canadian Social Insurance Numbers. 
It was created by IBM scientist Hans Peter Luhn and described in U.S. Patent No. 2,950,048, filed on January 6, 1954, and granted on August 23, 1960.

The algorithm is in the public domain and is in wide use today. It is specified in ISO/IEC 7812-1.[1] It is not intended to be a cryptographically secure hash function;
it was designed to protect against accidental errors,
not malicious attacks. Most credit cards and many government identification numbers use the algorithm as a simple method of distinguishing valid numbers from collections of random digits.

"""

#===============================================================================
# coding style CC python ie: variableName, ClassName ,functionName, _specialVariableName_
#===============================================================================

import threading
#import Queue
import socket
from fileinput import filename
try:
  import MySQLdb

except ImportError:
  #apt get code apt-get install python-mysqldb
  print "Import faild MySql Database module "
  
import time
from datetime import datetime
import os # for configure linux server
import logging # reffrence doc http://docs.python.org/2/howto/logging.html
logging.basicConfig(filename = "server_tcp.log",format ='The event %(levelname)s was occored in %(asctime)s : PID : %(process)d when executing : %(funcName)s @ line number : %(lineno)d',level = logging.DEBUG)
  
#global variables for use


def createSocket(portNumber=9090,serverIP=""):
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  serverIP = ""
  port = portNumber
  server.bind((serverIP,port))
  server.listen(5)
  server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  print "Socket created on IP {} port {} ".format(serverIP,port)
  return server


class newConnection(threading.Thread):
  def __init__(self,detailsPair,databaseIP,dbUser,dbPassword):
    channel , address = detailsPair
    self.channel = channel
    self.address = address
    self.approvedImei = False
    self.splitedGpsData = ''
    self.connectToDB(databaseIP,dbUser,dbPassword)
    threading.Thread.__init__(self)

  def connectToDB(self,databaseIP,dbUser,dbPassword):
    # Open database connection
    self.connection = MySQLdb.connect(databaseIP,dbUser,dbPassword)
    self.connection.select_db("syscall")
    self.cursor = self.connection.cursor()

  def isValidLuhnChecksum(self,card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = 0
    checksum += sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10 == 0

  def run(self):
    print "Device connected from {} via its port {}".format(self.address[0],self.address[1])
 
    #===========================================================================
    # for track startup and switch off time of GPS device , when device switch swithc on/off #to be impliment  
    #===========================================================================
#    self.cursor.execute(""" insert into vehicleStatus(imei,latestConnectionCreatedDate,currentOnlineStatus) values({imei},UTC_TIMESTAMP(),1) on duplicate key update latestConnectionCreatedDate = UTC_TIMESTAMP(),currentOnlineStatus = 1  """).format()
    
    #===========================================================================
    # to be implimented log incompatible IMEI patterns request while checking IMEI patter befor continuing
    # allow viewing server connection log via web page 
    #===========================================================================
    
    recivedDataFromGpsDevice = self.channel.recv(2048) #2048 is the buffer size
    
    try:
      self.splitedGpsData = recivedDataFromGpsDevice.split(',') #split string by ','
      imei = self.splitedGpsData[16][5:]
    except IndexError as e:
      print "exception passed",e
      self.channel.shutdown(2)
      self.channel.close()
      self.cursor.close()
      return 0
      
    
    #===========================================================================
    # Validate IMEI # and
    # check weather imei number is approved or not if it is not in approved_imei numbsers list connection will be closed
    #===========================================================================
    
    if not self.isValidLuhnChecksum(imei):
      print imei #only for debuging 
      logging.warn("invalid IMEI >"+imei)
      self.channel.shutdown(2)
      self.channel.close()
      self.cursor.close()
      return 0
      
    self.cursor.execute("select * from approved_imei")
    approvedImeiList = self.cursor.fetchall()
    print approvedImeiList
    print imei
    #assert False
    for tuple in approvedImeiList:
      try:
        if imei == tuple[0]:
          self.approvedImei = True
          break
      except IndexError:
        print "IMEI number not recognized"
        self.channel.shutdown(2)
        self.channel.close()
        self.cursor.close()
        return 0
    
    if not self.approvedImei:
      print "Not an approved IMEI number, Waiting for new connection...."
      sql = """ insert IGNORE into not_approved_imei values("{}",{},"{}") """.format(self.splitedGpsData[16][5:],0,datetime.now())
      self.cursor.execute(sql)
      self.channel.shutdown(2)
      self.channel.close()
      self.cursor.close()
      return 0
      
    #===========================================================================
    # create function for store GPS data #futher work
    #===========================================================================
      
    while True:
      #=========================================================================
      # need to debug firmware info and alarm - move, speed, batteries, help me! or "" after F or L Signal quality    F 
      #=========================================================================
      recivedDataFromGpsDevice = self.channel.recv(2048) #2048 is the buffer size
      self.splitedGpsData = recivedDataFromGpsDevice.split(',') #split string by ','

      #===============================================================================
      # Decode sat longitude and latitude
      #===============================================================================
      
      try:
        latitude = float(self.splitedGpsData[5][:2]) + float(self.splitedGpsData[5][2:])/60.0
        longitude = float(self.splitedGpsData[7][:3]) + float(self.splitedGpsData[7][3:])/60.0
        imei = self.splitedGpsData[16][5:]

      except ValueError:
        print "Device not connected to GPS satalites (lat long passing error)"
        continue #go for the next coordinate 
      
      except IndexError as ie:
        if not recivedDataFromGpsDevice:
          print "Device disconnected from server" #but can't say device is disconnected have to modify this (according to a test result)
          print "\r \n \fwaiting for new connection current connections{}".format(threading.activeCount())
          self.cursor.close()
          self.channel.shutdown(2)
          self.channel.close()
          return 0
        print "Recived TCP packet error >",ie
        continue 
     
        
      #=========================================================================
      # for debugging purpose only check weather values are in order
      #=========================================================================
#      for index in range(lengthOfTheself.splitedGpsData):
#        try:
##          print index+1,data_list[index]+" ---> "+self.splitedGpsData[index]
#  
#        except IndexError:
#          print "index mismatch error"
##          print data_list,"\n\n\n====>>",self.splitedGpsData
##          print "\n\n","length data list",len(data_list),"====>>","len splited",len(self.splitedGpsData)
#          #self.channel.close()
#          break
#      
      print "Receiving GPS coordinates....(Thread Name: {})".format(self.getName())
      
      try:
        date = self.splitedGpsData[11][4:] + self.splitedGpsData[11][2:4] + self.splitedGpsData[11][:2] 
        sat_time = date + self.splitedGpsData[3] 
      except IndexError:
        print "Satellite Time Error: Exception passed"
        pass  
        
      try:
        print sat_time
        sql = """ insert into coordinates(serial,phone_number,sat_time,sat_status,latitude,longitude,speed,bearing,imei,location_area_code,cell_id) values("{}","{}","{}",'{}',{},{},{},{},"{}","{}","{}")""".format(self.splitedGpsData[0],self.splitedGpsData[1],sat_time,self.splitedGpsData[4],latitude,longitude,float(self.splitedGpsData[9]),float(self.splitedGpsData[10]),imei,self.splitedGpsData[25],self.splitedGpsData[26])
        
      except ValueError:
        sql = ""
        print "SQL ValueError"
        continue
        
      try:
        # Execute the SQL command
        self.cursor.execute(sql)

      except :
        # Roll back in case there is any error
        print sql
        print "Mysql Execution Error"
        self.connection.rollback()
  

def configServer():
  """
  Import configuration file and set parameters 
  """
  try:
    config = open(r"./server.conf","r+")
  except IOError,e:
    print e
    return 0
  configLines = []
  try:
    while True:
      configLines.append(config.next())
  except StopIteration:
    pass
  finally:
    config.close()
  configInfo = {}
  for line in configLines:
    if line[0] == "#" or line[0] == "\n":
      continue
    configLineArgumentList = line[:-1].split("=")
    key = configLineArgumentList[0]
    value = configLineArgumentList[1]
    configInfo.update({key:value})
  logging.info("Configuration done sucssesfully")
  return configInfo
    
def main():
  configInfoDict = configServer()
  #=============================================================================
  # log programm activities 
  #=============================================================================
  
  logging.info("main process started")
  #=============================================================================
  # create new user with root privilages 
  #=============================================================================
  #os.system("sudo usermod -a -G sudo 114150B")
  
  # Set up the Socket:
  while True:
    try:
      serverSocket = createSocket(int(configInfoDict.get("serverPort")),configInfoDict.get("serverIP"))
      if serverSocket:
        break
    
    except socket.error:
        print "Delaying connection for 5 seconds due to previously failed connection attempt..."
        time.sleep(5)
        continue
    
  while True:
    print "Current Connections= {}".format(threading.activeCount())
    newConnection(serverSocket.accept(),configInfoDict.get("databaseIP"),configInfoDict.get("dbUser"),configInfoDict.get("dbPassword")).start()
    

#===============================================================================
# Standard boilerplate to call the main() function to begin the program.
#===============================================================================
  
if __name__ == "__main__":
  print ''
  print '  ____              _____     ____    ____                            '
  time.sleep(0.1)
  print ' /    \  |      |  /     \   /    \  /    \   |   |                   '
  time.sleep(0.1)
  print '|      | |      | |       | |        \     |  |   |                   '
  time.sleep(0.1)
  print '|         \____/| |          \____/   \___/\  |_  |_              v0.5'
  time.sleep(0.1)
  print '|______         | |_______                                            '
  time.sleep(0.1)
  print '       \        |         \                                           '
  time.sleep(0.1)
  print '       |        |         |                                           '
  time.sleep(0.1)
  print ' ______/   _____/   \_____/                                           '
  time.sleep(0.1)
  print 'Contact us for any bug reports at syscall@knnect.com    '
  time.sleep(0.1)
  print '\n'

  main()
