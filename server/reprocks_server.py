#/usr/bin/python

import threading
import socket
import sys,time
import select
	
global bufLen
global endflag
endflag = []
bufLen = 4*1024	

class control(threading.Thread):

	def __init__(self,server_Conn,client_Conn,server_Addr,client_Addr,clientNum):
		threading.Thread.__init__(self)
		self.server_Conn = server_Conn
		self.client_Conn = client_Conn
		self.server_Addr = server_Addr
		self.client_Addr = client_Addr
		self.clientNum = clientNum
	
	def run(self):
		global endflag 
		global bufLen
		transferDataThreads = []
		thread = 2
		flag = int(self.clientNum)
		endflag.append(False)
		
		y = transfer2Client(self.server_Conn,self.client_Conn,self.server_Addr,self.client_Addr,flag)
		y.setDaemon(True)
		z = transfer2Server(self.client_Conn,self.server_Conn,self.client_Addr,self.server_Addr,flag)
		z.setDaemon(True)
		transferDataThreads.append(y)
		transferDataThreads.append(z)
		try:
			for t in transferDataThreads:
				t.start()
		except socket.timeout:
			print "Time out occurd."
			pass
		while True:
			alive = True
			for i in range(int(thread)):
				alive = alive and transferDataThreads[i].isAlive()
				if not alive:
					time.sleep(1)
					print "\n[Link %s] closed." % (int(self.clientNum)+1)
					break
			break

				
class transfer2Client(threading.Thread):

	def __init__(self,server_Conn,client_Conn,server_Addr,client_Addr,flag):
		threading.Thread.__init__(self)
		self.server_Conn = server_Conn
		self.client_Conn = client_Conn
		self.server_Addr = server_Addr
		self.client_Addr = client_Addr
		self.flag = flag
		self.num = flag+1 
	
	def run(self):
		global bufLen
		global endflag
		while True and not endflag[self.flag]:
			buf = self.server_Conn.recv(bufLen)
			if buf == '__closed__' or len(buf)==0:
				print "[Link %s] Server %s disconnect.End current thread." % (self.num,self.server_Addr)
				time.sleep(2)
				self.server_Conn.close()
				endflag[self.flag] = True
				break
			try:    # maybe client disconnect.
				self.client_Conn.send(buf)
				print "[Link %s] %s --> %s : %s data" % (self.num,self.server_Addr,self.client_Addr,len(buf))
			except:
				self.server_Conn.send('__closed__')
				self.server_Conn.close()
				break
		

class transfer2Server(threading.Thread):

	def __init__(self,client_Conn,server_Conn,client_Addr,server_Addr,flag):
		threading.Thread.__init__(self)
		self.client_Conn = client_Conn
		self.server_Conn = server_Conn
		self.client_Addr = client_Addr
		self.server_Addr = server_Addr
		self.flag = flag
		self.num = flag+1
		
	def run(self):
		global bufLen
		global endflag
		while True and not endflag[self.flag]:
			try:
				buf = self.client_Conn.recv(bufLen)
			except:
				print "[Link %s] Client %s: disconnect.End current thread." % (self.num,self.client_Addr)
				time.sleep(2)
				self.server_Conn.send('__closed__')
				self.client_Conn.close()
				self.server_Conn.close()
				endflag[self.flag] = True
				break
			if len(buf)==0:           # means disconnect.
				self.server_Conn.send('__closed__')
				self.client_Conn.close()
				endflag[self.flag] = True
				break
			self.server_Conn.send(buf)
			print "[Link %s] %s --> %s : %s data" % (self.num,self.client_Addr,self.server_Addr,len(buf))
		
	
	
	
				
def usage():
	print """
	
	reprocks_server\tV1.0
	Code by H.K.T \t email:jlvsjp@qq.com

	usage: reprocks_server.py <ListenPort1> <ListenPort2>
	
"""
	
	
def main():
	global endflag
	if len(sys.argv)<>3:
		usage()
		sys.exit()
	else:
		port1 = int(sys.argv[1])
		port2 = int(sys.argv[2])
	
	controlThreads = []	
	try:
		socketServer = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		socketServer.bind(('',port1))
		socketServer.listen(20)
		socketClient = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		socketClient.bind(('',port2))
		socketClient.listen(20)
	
		clientNum = 0     #the number of client connection.
	
		while True:
			currentLink = clientNum +1
			print "[Link %s] Listening on port %s,waiting for server connect..." % (currentLink,port1)
			serverConn,serverAddr = socketServer.accept()
			print "[Link %s] Server %s connect! " % (currentLink,serverAddr)
			while True:
				print "[Link %s] Listening on port %s,waiting for client connect..." % (currentLink,port2)
				client_Conn,client_Addr = socketClient.accept()
				print "[Link %s] Get a client connection from %s !" % (currentLink,client_Addr)
				serverConn.send('__newLink__') # send current client info,to create a new thread in reprocks_client to connect with current reprocks_server.
				temp = control(serverConn,client_Conn,serverAddr,client_Addr,clientNum)
				temp.setDaemon(True)
				controlThreads.append(temp)
				controlThreads[clientNum].start()
				clientNum += 1
				break
	except KeyboardInterrupt:
		print "Catch ctrl+c pressed,program will exit."
		for m in endflag:
			m = True

if __name__ == '__main__':
	main()