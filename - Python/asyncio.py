# 关于asyncio的关键字的说明：
# event_loop     事件循环：程序开启一个无限循环，把一些函数注册到事件循环上，当满足事件发生的时候，调用相应的协程函数
# coroutine      协程，使用async关键字定义的函数，调用其不会立即执行而是会返回协程对象。它需注册到事件循环由事件循环调用
# task           任务：一个协程对象就是一个原生可以挂起的函数，任务则是对协程进一步封装，其中包含了任务的各种状态
# future:        代表将来执行或没有执行的任务的结果。它和task上没有本质上的区别
# async/await    关键字：python3.5用于定义协程的关键字，async定义一个协程，await用于挂起阻塞的异步调用接口


#旧语法：
@asyncio.coroutine
def hello():
    print("Hello world!")
    r = yield from asyncio.sleep(1)
    print("Hello again!")

#新语法：
async def hello():
    print("Hello world!")
    r = await asyncio.sleep(1)
    print("Hello again!")


#-------------------------------------------------------------------------

import asyncio


async def coroutine():      # 定义协程函数
    print('in coroutine')
    return 'result'


if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()   # 创建默认的事件循环
    try:
        print('starting')
        result = event_loop.run_until_complete(coroutine())    # 通过调用事件循环的 run_until_complete() 启动协程
        print(f'it returned: {result}')
    finally:
        print('closing')
        event_loop.close()      # 关闭事件循环

# 输出:
# starting
# in coroutine
# it returned: result
# closing

#-------------------------------------------------------------------------
#协程可以启动另外的协程并等待结果, 这样可以让各个协程专注于自己的工作, 这也是实际开发中需要用到的模式

import asyncio

async def main():           # 定义协程函数
    print('waiting for chain1')
    result1 = await chain1()            # await --> 
    print('waiting for chain2')
    result2 = await chain2(result1)
    return (result1, result2)

async def chain1():         # 定义协程函数
    print('chain1')
    return 'result1'

async def chain2(arg):      # 定义协程函数
    print('chain2')
    return f'Derived from {arg}'

if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()   # 创建事件循环
    try:
        return_value = event_loop.run_until_complete(main())    #并发执行各协程函数
        print(f'return value: {return_value}')
    finally:
        event_loop.close()

# 输出:
# waiting for chain1
# chain1
# waiting for chain2
# chain2
# return value: ('result1', 'Derived from result1')

#-------------------------------------------------------------------------

import asyncio
import time


now = lambda :time.time()

start = now()

async def do_some_work(x):
    print("Waiting:",x)
    await asyncio.sleep(x)
    return "Done after {}s".format(x)

coroutine1 = do_some_work(1)
coroutine2 = do_some_work(2)
coroutine3 = do_some_work(4)

#ensure_future: 使用其包装 coroutine object ( 协程对象 )
tasks = [asyncio.ensure_future(coroutine1),asyncio.ensure_future(coroutine2),asyncio.ensure_future(coroutine3)]

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
#loop.close()   #关闭事件循环

for task in tasks:
    print("Task ret:",task.result())

print("Time:",now()-start)

# 运行结果：
# Waiting: 1
# Waiting: 2
# Waiting: 4
# Task ret: Done after 1s
# Task ret: Done after 2s
# Task ret: Done after 4s
# Time: 4.004154920578003























































import asyncio

#用asyncio的异步网络连接来获取sina、sohu和163的网站首页


@asyncio.coroutine      #把generator标记为coroutine类型 ( 协程 )
def wget(host):
    print('wget %s...' % host)
    connect = asyncio.open_connection(host, 80)
    reader, writer = yield from connect
    header = 'GET / HTTP/1.0\r\nHost: %s\r\n\r\n' % host
    writer.write(header.encode('utf-8'))
    yield from writer.drain()
    while True:
        line = yield from reader.readline()
        if line == b'\r\n':
            break
        print('%s header > %s' % (host, line.decode('utf-8').rstrip()))
    # Ignore the body, close the socket
    writer.close()

loop = asyncio.get_event_loop()

tasks = [wget(host) for host in ['www.sina.com.cn', 'www.sohu.com', 'www.163.com']]

loop.run_until_complete(asyncio.wait(tasks))

loop.close()

# -------------------------------------------------------------------------
# 执行结果如下：

# wget www.sohu.com...
# wget www.sina.com.cn...
# wget www.163.com...
# (等待一段时间)
# (打印出sohu的header)
# www.sohu.com header > HTTP/1.1 200 OK
# www.sohu.com header > Content-Type: text/html
# ...
# (打印出sina的header)
# www.sina.com.cn header > HTTP/1.1 200 OK
# www.sina.com.cn header > Date: Wed, 20 May 2015 04:56:33 GMT
# ...
# (打印出163的header)
# www.163.com header > HTTP/1.0 302 Moved Temporarily
# www.163.com header > Server: Cdn Cache Server V2.0
# ...