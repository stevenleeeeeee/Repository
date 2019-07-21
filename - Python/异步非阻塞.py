############################### server端 ###########################################
# selectors模块应用
# 通过 selectors 模块允许 socket 以非阻塞方式进行通信，selectors 相当于一个事件注册中心
# 程序只要将 socket 的所有事件注册给 selectors 管理
# 当 selectors 检测到 socket 中特定事件后程序就调用相应的监听方法进行处理

# selectors 主要支持两种事件：
# selectors.EVENT_READ：     当 socket 有数据可读时触发该事件。当有客户端连接进来时也会触发该事件。
# selectors.EVENT_WRITE：    当 socket 将要写数据时触发该事件。

import threading
import selectors
import socket

# 平台自适应、选择对应平台提供的多路复用模型，比如linux就会选择epoll
sel = selectors.DefaultSelector()

# 监听"客户端连接进来"事件的函数
def accept(sock, mask):
    conn, addr = sock.accept()                      # 接收链接 Should be ready，这里创建了建立链接的对象"conn"
    conn.setblocking(False)
    #print('accepted', conn, 'from', addr)
    sel.register(conn, selectors.EVENT_READ, read)  # 注册以建立链接的对象 "conn" 和读事件，并指定回调对象"read"

# 监听"有数据可读"事件的函数
def read(conn:socket.socket, mask):
    try:
        data = conn.recv(1000)      # 接收数据 Should be ready 
        if not data:                # 没有数据时抛出异常
            raise Exception
        print('echoing', repr(data), 'to', conn)
        conn.send(data)             # 发送数据 Hope it won't block
    except Exception as e:          # 捕获异常后取消注册并关闭conn对象的TCP链接
        print('closing', conn)
        sel.unregister(conn)        # 注销一个已经注册过的文件对象
        conn.close()

# 创建socket监听对象
sock = socket.socket()
sock.bind(('localhost', 8090))
sock.listen(100)

# 使其工作在非阻塞状态 (运行 sock.accept() 时不会卡住，交给事件来处理) 
sock.setblocking(False)

# 在selectors中注册被监听的对象"sock"，监听其读事件，并指定回调对象"accept"
sel.register(sock, selectors.EVENT_READ, accept)

e = threading.Event()

def work(event:threading.Event):
    '''
    为了不断地提取 selectors 中的事件，使用循环不断提取sel对象的事件
    只有当事件（如有客户端连接、有数据可读）发生时，accept、read方法才会调用，这样就避免了阻塞式编程
    '''
    while not event.is_set():
        events = sel.select()           # 监听是否有连接进来 (优先使用epoll)，当没有新连接进入时其将一直阻塞住
        for key, mask in events:        # 一旦条件满足，则events中将有值 (将产生事件的对象返回)
            callback = key.data         # key.data为在selectors中注册的回调函数 (accpet or read) 相当于调accept函数
            callback(key.fileobj, mask) # key.fileobj为在selectors中注册的对象，开始调用并进行处理 (回调)

# 交由工作线程去处理，不要把主线程给阻塞住
threading.Thread(target=work,args=(e,)).start()

############################### Client端 ###########################################

import socket

sk=socket.socket()

sk.connect(("127.0.0.1",8090))

while 1:
    inp=input(">>>")
    sk.send(inp.encode("utf8"))
    data=sk.recv(1024)
    print(data.decode("utf8"))