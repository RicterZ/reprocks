#! /usr/bin/python

import threading
import socket
import sys,time
import SocketServer,struct,select

global bufLen
global endflag
global socksPort
###################
socksPort = 50000 #Default socks5 proxy port
###################
endflag = []
bufLen = 4*1024

class startThreadSoket(threading.Thread):
    def __init__(self,socksPort):
        threading.Thread.__init__(self)
        self.socksPort = socksPort

    def run(self):
        socket_bind(self.socksPort)

class control(threading.Thread):

    def __init__(self,server_Conn,client_Conn,serverAddr,clientAddr,clientNum):
        threading.Thread.__init__(self)
        self.server_Conn = server_Conn
        self.client_Conn = client_Conn
        self.server_Addr = serverAddr
        self.client_Addr = clientAddr
        self.clientNum = clientNum

    def run(self):
        global endflag
        transferDataThreads = []
        thread = 2
        flag = self.clientNum
        endflag.append(False)

        y = transfer2Server(self.server_Conn,self.client_Conn,self.server_Addr,self.client_Addr,flag)
        y.setDaemon(True)
        z = transfer2Client(self.client_Conn,self.server_Conn,self.client_Addr,self.server_Addr,flag)
        z.setDaemon(True)

        transferDataThreads.append(y)
        transferDataThreads.append(z)

        for t in transferDataThreads:
            t.start()
        while True:
            alive = True
            for i in range(int(thread)):
                alive = alive and transferDataThreads[i].isAlive()
                if not alive:
                    time.sleep(3)
                    print "[Link %s] Connection has closed." % self.clientNum
                    break
            break

class transfer2Server(threading.Thread):

    def __init__(self,server_Conn,client_Conn,server_Addr,client_Addr,flag):
        threading.Thread.__init__(self)
        self.server_Conn = server_Conn
        self.client_Conn = client_Conn
        self.server_Addr = server_Addr
        self.client_Conn = client_Conn
        self.flag = flag
        self.currentNum = self.flag+1

    def run(self):
        global bufLen
        global endflag
        servPeerName = self.server_Conn.getpeername()
        clientPeerName = self.client_Conn.getpeername()
        while True and not endflag[self.flag]:
            try:
                buf = self.client_Conn.recv(bufLen)
            except:
                print "Connection reset by peer.Program exit."
                for m in endflag:
                    m = True
                sys.exit()
            if buf == '' or buf == '__closed__':
                time.sleep(2)
                self.client_Conn.close()
                endflag[self.flag] = True
                break
            try:
                self.server_Conn.send(buf)
                print "[Link %s] %s --> %s : %s data" % (self.currentNum,clientPeerName,servPeerName,len(buf))
            except:
                endflag[self.flag] = True
                time.sleep(2)
                self.client_Conn.send('__closed__')
                self.client_Conn.close()
                break

class transfer2Client(threading.Thread):
    def __init__(self,client_Conn,server_Conn,client_Addr,server_Addr,flag):
        threading.Thread.__init__(self)
        self.client_Conn = client_Conn
        self.server_Conn = server_Conn
        self.client_Addr = client_Addr
        self.server_Addr = server_Addr
        self.flag = flag
        self.currentNum = flag+1

    def run(self):
        global bufLen
        global endflag
        servPeerName = self.server_Conn.getpeername()
        clientPeerName = self.client_Conn.getpeername()
        while True and not endflag[self.flag]:
            buf = self.server_Conn.recv(bufLen)
            if buf == '':
                print "[Link %s] Server %s disconnect.End current thread." % (self.currentNum,clientPeerName)
                time.sleep(2)
                self.server_Conn.close()
                endflag[self.flag] = True
                break
            try:
                self.client_Conn.send(buf)
                print "[Link %s] %s --> %s : %s data" % (self.currentNum,servPeerName,clientPeerName,len(buf))
            except:
                endflag[self.flag] = True
                time.sleep(2)
                self.server_Conn.close()
                break

class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass
class Socks5Server(SocketServer.StreamRequestHandler):
    def handle_tcp(self, sock, remote):
        fdset = [sock, remote]
        while True:
            r, w, e = select.select(fdset, [], [])
            if sock in r:
                if remote.send(sock.recv(4096)) <= 0: break
            if remote in r:
                if sock.send(remote.recv(4096)) <= 0: break
    def handle(self):
        try:
            pass
            sock = self.connection
            sock.recv(262)
            sock.send("\x05\x00");
            data = self.rfile.read(4)
            mode = ord(data[1])
            addrtype = ord(data[3])
            if addrtype == 1:
                addr = socket.inet_ntoa(self.rfile.read(4))
            elif addrtype == 3:
                addr = self.rfile.read(ord(sock.recv(1)[0]))
            port = struct.unpack('>H', self.rfile.read(2))
            reply = "\x05\x00\x00\x01"
            try:
                if mode == 1:
                    remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote.connect((addr, port[0]))
                    pass
                else:
                    reply = "\x05\x07\x00\x01"
                local = remote.getsockname()
                reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
            except socket.error:
                reply = '\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00'
            sock.send(reply)
            if reply[1] == '\x00':
                if mode == 1:
                    self.handle_tcp(sock, remote)
        except socket.error:
            pass
        except IndexError:
            pass

def socket_bind(socketPort):
    socks_port = int(socketPort)
    server = ThreadingTCPServer(('', socks_port), Socks5Server)
    print 'Socks5 proxy bind port : %d' % socks_port + ' ok!'
    server.serve_forever()

def usage():
    print """

    reprocks_client\t1.0
    Code by H.K.T\temail:jlvsjp@qq.com
    Thanks to ringzero@557.im for socks5 proxy module!

    usage : %s -m 1 <reprocks_server_IP> <reprocks_server_port>
            %s -m 2 <transferIP> <transferPort> <reprocks_server_IP> <reprocks_server_port>
            %s -m 3 [bind_socket_port]

    example:
            %s -m 1 123.123.123.123 1230
                  #Rebind socks5 proxy to reprocks_server.
            %s -m 2 127.0.0.1 22 123.123.123.123 1230
                  #Just port transmit in reconnection method.
            %s -m 3 7070
                  #Just start socks5 proxy.

""" % (sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0],sys.argv[0])


def main():
    global socksPort
    global endflag
    try:
        if len(sys.argv)>=3:
            if sys.argv[2]=='3':
                if len(sys.argv)==4:
                    socksPort = int(sys.argv[3])
                socket_bind(socksPort)
            elif sys.argv[2]=='1' and len(sys.argv)==5:
                socksProxy = startThreadSoket(socksPort)
                socksProxy.setDaemon(True)
                socksProxy.start()
                reproket('localhost',socksPort,sys.argv[3],sys.argv[4])
            elif sys.argv[2]=='2':
                if len(sys.argv)==7:
                    reproket(sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6])
                else:
                    usage()

        else:
            usage()
    except KeyboardInterrupt:
        print "Catch ctrl+c pressed,program will exit."
        for m in endflag:
            m = True

def reproket(transmitIP,transmitPort,clientIP,clientPort):
    serverAddr = (transmitIP,int(transmitPort))
    clientAddr = (clientIP,int(clientPort))

    serverLink = []
    clientLink = []

    socketServer = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socketServer.connect(serverAddr)
    socketClient = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        socketClient.connect(clientAddr)
    except:
        print "Cannot connect to reprocks server.Please run it fisrt or check the network!"
        time.sleep(1)
        sys.exit()
    print "Connect to reprocks server...success!!!"

    serverLink.append(socketServer)
    clientLink.append(socketClient)
    controlThreads = []
    clientNum = 0

    while True:
        try:
            newLinkFlag = clientLink[clientNum].recv(bufLen)
        except:
            print "[link %s] Connection reset by peer,program exit." % (clientNum+1)
            break

        if newLinkFlag == '__newLink__':
            nextClientLink = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            nextClientLink.connect(clientAddr)
            print "[Link %s] Make a new connection to reprocks_server ok!" % (clientNum+1)
            nextServerLink = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            nextServerLink.connect(serverAddr)
            print "[link %s] Make a new connection to socks5 proxy ok!" % (clientNum+1)
            temp = control(serverLink[clientNum],clientLink[clientNum],serverAddr,clientAddr,clientNum)
            temp.setDaemon(True)
            controlThreads.append(temp)
            controlThreads[clientNum].start()
            clientLink.append(nextClientLink)
            serverLink.append(nextServerLink)
            clientNum += 1

if __name__ == '__main__':
    main()
