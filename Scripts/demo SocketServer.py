#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
        +------------+
        | BaseServer |
        +------------+
              |
              v
        +-----------+        +------------------+
        | TCPServer |------->| UnixStreamServer |
        +-----------+        +------------------+
              |
              v
        +-----------+        +--------------------+
        | UDPServer |------->| UnixDatagramServer |
        +-----------+        +--------------------+

socketserver模块是基于socket而来的模块，它在socket的基础上进行了一层封装，并实现并发等功能
# https://segmentfault.com/a/1190000019023599

socketserver模块主要包含的非Unix服务器类:
    1.TCPserver
    2.UCPserver
    3.ThreadingTCPServer(ThreadingMixIn, TCPServer)
    4.ThreadingUDPServer(ThreadingMixIn, UDPServer)
    5.ForkingTCPServer(ForkingMixIn, TCPServer)
    6.ForkingUDPServer(ForkingMixIn, UDPServer)

类方法介绍：
setup()：   该方法在handle()之前调用，默认什么都不做，如果希望服务器实现更多连接设置，则无需调用该方法
handle()：  调用该方法执行实际的请求操作，调用函数可不带任何参数，默认什么都不做
finish()：  环境清理，在handle()之后执行清除操作，默认什么都不做，如果setup()和handle()方法都不生成异常则无需调用该方法
'''

# import socketserver
# import threading

# class Handler(socketserver.BaseRequestHandler):
#     def handle(self):
#         print('当前的server类型: {}'.format(self.server))
#         print('当前的socket连接对象: {}'.format(self.request))
#         print('当前的客户端地址: {}'.format(self.client_address))

#         print('线程列表: {}'.format(threading.enumerate()))
#         print('当前的线程：{}'.format(threading.current_thread()))

# server = socketserver.TCPServer(('127.0.0.1', 9000), Handler)
# server.serve_forever()

# ------------------------------------------------------------------------------------------------- Example 1

# 服务端

import SocketServer

class MyServer(SocketServer.BaseRequestHandler):
    def handle(self):
        # 重载SocketServer.BaseRequestHandler中的handle方法对数据处理逻辑进行修改
        conn = self.request                 # self.request 相当于一个socket中的conn对象
        conn.sendall('我是多线程')           # 发送数据
        Flag = True                         # 退出标记
        while Flag:
            data = conn.recv(1024)          # 接收数据
            if data == 'exit':              # 使用Flag判断是否退出，由客户端决定
                Flag = False
                conn.close()                # 关闭链接
            elif data == '0':
                conn.sendall('您输入的是0')
            else:
                conn.sendall('请重新输入.')

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True                       # 允许重用地址
    server = SocketServer.ThreadingTCPServer(('127.0.0.1',8009),MyServer)   # 个人理解MyServer在这是回调，用线程处理每个请求
    server.serve_forever()  # 大循环，一直监听是否有客户端请求到达 ...

# -------------------------------------------------

# 客户端

import socket

sk = socket.socket()
sk.connect(('127.0.0.1',8009))

while True:
    data = sk.recv(1024)
    print 'receive:',data
    inp = input('please input:')
    sk.sendall(inp)
    if inp == 'exit':
        break

sk.close()


# ------------------------------------------------------------------------------------------------- Example 2

import socketserver
import threading

class Handler(socketserver.BaseRequestHandler):
    clients = {}                                    # 类级别定义的属性被所有建立链接的对象拥有，这里存储链接对象

    def setup(self):
        super().setup()     
        self.event = threading.Event()              # 定义线程Event对象
        self.clients[self.client_address] = self.request

    def handle(self):
        super().setup()
        while not self.event.is_set():              # 使用了线程的Event事件来触发判断
            data = self.request.recv(1024).decode()
            if data == 'quit':
                break
            msg = "{} 说 {}".format(self.client_address, data).encode()
            print(self.clients)
            if self.client_address in self.clients.keys():
                self.clients[self.client_address].send(msg)
        print('server end')

    def finish(self):
        super().finish()
        self.clients.pop(self.client_address)
        self.event.set()                            # 当结束时设置Event标记，这里的结束应该是有客户端主动断开引起的

if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(('127.0.0.1', 9000), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    while True:
        cmd = input('请输入您想说的话: ').strip()
        if cmd == 'quit':
            print(cmd)
            server.shutdown()
            server.server_close()
            break
        else:
            print('您可以输入quit来停止服务器! ')