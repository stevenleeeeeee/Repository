# https://www.cnblogs.com/yinheyi/p/8127871.html

# 使用 selectors 实现非阻塞式编程的步骤大致如下：
# 1.创建 selectors 对象。
# 2.通过 selectors 对象为 socket 的 selectors.EVENT_READ 或 selectors.EVENT_WRITE 事件注册监听器函数。
# 3.每当 socket 有数据需要读写时，系统负责触发所注册的监昕器函数。
# 4.在监听器函数中处理 socket 通信。

import selectors
import socket

sel = selectors.DefaultSelector()

def accept(sock, mask):
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr)
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)      # 注册回调函数 read 
    # selectors.DefaultSelector().register(fileobj, events, data=None)
    # Register a file object for selection, monitoring it for I/O events.
    # fileobj is the file object to monitor. It may either be an integer file descriptor or an object with a fileno() method. 
    # events is a bitwise mask of events to monitor. data is an opaque object.

def read(conn, mask):
    data = conn.recv(1000)  # Should be ready
    if data:
        print('echoing', repr(data), 'to', conn)
        conn.send(data)  # Hope it won't block
    else:
        print('closing', conn)
        sel.unregister(conn)
        conn.close()

sock = socket.socket()
sock.bind(('localhost', 1234))
sock.listen(100)
sock.setblocking(False)
sel.register(sock, selectors.EVENT_READ, accept)        # 注册回调函数 accept

while True:

    events = sel.select()

    for key, mask in events:
        callback = key.data
        callback(key.fileobj, mask)

# sel.close()

# ----------------------------------------------------------------------------------------------
# 下面程序使用 selectors 模块实现非阻塞式通信的服务器端：

import selectors, socket
# 创建默认的selectors对象
sel = selectors.DefaultSelector()
# 负责监听“有数据可读”事件的函数
def read(skt, mask):
    try:
        # 读取数据
        data = skt.recv(1024)
        if data:
            # 将读取的数据采用循环向每个socket发送一次
            for s in socket_list:
                s.send(data)  # Hope it won't block
        else:
            # 如果该socket已被对方关闭，关闭该socket，
            # 并从socket_list列表中删除
            print('关闭', skt)
            sel.unregister(skt)
            skt.close()
            socket_list.remove(skt)
    # 如果捕捉到异常, 将该socket关闭，并从socket_list列表中删除
    except:
        print('关闭', skt)
        sel.unregister(skt)
        skt.close()
        socket_list.remove(skt)
socket_list = []
# 负责监听“客户端连接进来”事件的函数
def accept(sock, mask):
    conn, addr = sock.accept()
    # 使用socket_list保存代表客户端的socket
    socket_list.append(conn)
    conn.setblocking(False)
    # 使用sel为conn的EVENT_READ事件注册read监听函数
    sel.register(conn, selectors.EVENT_READ, read)    #②
sock = socket.socket()
sock.bind(('192.168.1.88', 30000))
sock.listen()
# 设置该socket是非阻塞的
sock.setblocking(False)
# 使用sel为sock的EVENT_READ事件注册accept监听函数
sel.register(sock, selectors.EVENT_READ, accept)    #①
# 采用死循环不断提取sel的事件
while True:
    events = sel.select()
    for key, mask in events:
        # key的data属性获取为该事件注册的监听函数
        callback = key.data
        # 调用监听函数, key的fileobj属性获取被监听的socket对象
        callback(key.fileobj, mask)

# 下面是该示例的客户端程序。该客户端程序更加简单，客户端程序只需要读取 socket 中的数据
# 因此只要使用 selectors 为 socket 注册“有数据可读”事件的监听函数即可:

import selectors, socket, threading
# 创建默认的selectors对象
sel = selectors.DefaultSelector()
# 负责监听“有数据可读”事件的函数
def read(conn, mask):
    data = conn.recv(1024)  # Should be ready
    if data:
        print(data.decode('utf-8'))
    else:
        print('closing', conn)
        sel.unregister(conn)
        conn.close()
# 创建socket对象
s = socket.socket()
# 连接远程主机
s.connect(('192.168.1.88', 30000))
# 设置该socket是非阻塞的
s.setblocking(False)
# 使用sel为s的EVENT_READ事件注册read监听函数
sel.register(s, selectors.EVENT_READ, read)    # ①
# 定义不断读取用户键盘输入的函数
def keyboard_input(s):
    while True:
        line = input('')
        if line is None or line == 'exit':
            break
        # 将用户的键盘输入内容写入socket
        s.send(line.encode('utf-8'))
# 采用线程不断读取用户的键盘输入
threading.Thread(target=keyboard_input, args=(s, )).start()
while True:
    # 获取事件
    events = sel.select()
    for key, mask in events:
        # key的data属性获取为该事件注册的监听函数
        callback = key.data
        # 调用监听函数, key的fileobj属性获取被监听的socket对象
        callback(key.fileobj, mask)

