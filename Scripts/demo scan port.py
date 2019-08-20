#!/usr/bin/env python
#coding:utf8
__author__ =  'luodi'

from socket import *
import threading

def Scanports(serverHost,port):
    try:
        socketobj= socket(AF_INET, SOCK_STREAM)
        sresult=socketobj.connect_ex((serverHost, port))
        if sresult ==0:
            print "Server %s open %s" %(serverHost,port)
    except:
        print "socket异常!!!!"
    socketobj.close()


if __name__ == '__main__':
    hostip="192.168.2.232"
    for port in range(0,65535):
        t=threading.Thread(target=Scanports,args=(hostip,port))
        t.start()


#   --------------------------------------------------------------------------------------

#!/usr/bin/env python

import socket

def check_server(address,port):
    s=socket.socket()
    try:
        s.connect((address,port))
        return True
    except socket.error,e:
        return False

if __name__=='__main__':
    from optparse import OptionParser
    parser=OptionParser()
    parser.add_option("-a","--address",dest="address",default='localhost',help="Address for server",metavar="ADDRESS")
    parser.add_option("-s","--start",dest="start_port",type="int",default=1,help="start port",metavar="SPORT")
    parser.add_option("-e","--end",dest="end_port",type="int",default=1,help="end port",metavar="EPORT")
    (options,args)=parser.parse_args()
    print 'options: %s, args: %s' % (options, args)
    port=options.start_port
    while(port<=options.end_port):
        check = check_server(options.address, port)
        if (check):
            print 'Port  %s is on' % port
        port=port+1
        
        










