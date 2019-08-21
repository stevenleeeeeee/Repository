# https://aiohttp.readthedocs.io/en/stable/

# 客户端示例：

import aiohttp
import asyncio

# 异步协程函数
async def fetch(session, url):
    async with session.get(url) as response:                # 异步方式进入aiohttp.session的上下文
        # print(resp.status)
        return await response.text()                        # 异步返回数据

# 异步协程函数
async def main():
    async with aiohttp.ClientSession() as session:          # 异步方式进入aiohttpClientSession的上下文
        html = await fetch(session, 'http://python.org')    # 异步调用协程函数fetch
        print(html)                                         # 获取协程函数异步返回的数据

loop = asyncio.get_event_loop()
loop.run_until_complete(main())                             # 执行main()返回的是异步协程task对象

# -------------------------------------------------------------------------------------------------

# 服务器示例：

from aiohttp import web

async def handle(request):
    name = request.match_info.get('name', "Anonymous")      # 获取URL信息
    text = "Hello, " + name                                 # 构造返回的数据
    return web.Response(text=text)                          # 返回数据

app = web.Application()

app.add_routes([
    web.get('/', handle),
    web.get('/{name}', handle)
])                                                          # 添加URL及对应的路由函数

web.run_app(app)


# ------------------------------------------------------------------------------------------------- Example

# 发出请求：

import aiohttp

async with aiohttp.ClientSession() as session:                  # 异步方式建立会话
    async with session.get('http://httpbin.org/get') as resp:   # 异步方式请求数据
        # 不要为每个请求创建会话，很可能每个应用程序都需要一个会话来完成所有请求
        print(resp.status)
        print(await resp.text())

# await session.close()  使用异步上下文后可略过此步骤

# ----------------------------------------------- URL传参

async with aiohttp.ClientSession() as session: 

# demo1：
    params = {'key1': 'value1', 'key2': 'value2'}
    async with session.get('http://httpbin.org/get',params=params) as r:
        expect = 'http://httpbin.org/get?key2=value2&key1=value1'                   # 最终拼接的URL
        assert str(r.url) == expect                                                 # 段妍

# demo2：
    params = [('key', 'value1'), ('key', 'value2')]
    async with session.get('http://httpbin.org/get',params=params) as r:
        expect = 'http://httpbin.org/get?key=value2&key=value1'
        assert str(r.url) == expect

# demo3 这种方式不会对URL的参数进行编码：
    async with session.get('http://httpbin.org/get',params='key=value+1') as r:
            assert str(r.url) == 'http://httpbin.org/get?key=value+1'


# -----------------------------------------------  响应内容和状态代码

async with aiohttp.ClientSession() as session: 
    async with session.get('https://api.github.com/events') as resp:
        print(resp.status)          # 状态代码
        print(await resp.text())    # 响应内容，指定解码：resp.text(encoding='windows-1251')


# ----------------------------------------------- 构造 JSON
# 所有的会话的请求方法如：request()、ClientSession.get()、ClientSesssion.post() 等接受JSON参数：

# 默认情况下会话使用python的标准json模块进行序列化：
async with aiohttp.ClientSession() as session:
    async with session.post(url, json={'test': 'object'})


# 可以使用不同的 JSON serializer
# ClientSession接受json_serialize 参数：

import ujson

async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
    await session.post(url, json={'test': 'object'})
    # ujson比json快，但有点不兼容

# ----------------------------------------------- 解析 JSON

async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
    async with session.get('https://api.github.com/events') as resp:
        print(await resp.json())
        # 如果JSON解码失败将引发异常

# ----------------------------------------------- 流媒体响应处理

async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
    async with session.get('https://api.github.com/events') as resp:
        # await resp.content.read(10)
        with open(filename, 'wb') as fd:
            while True:
                chunk = await resp.content.read(chunk_size)     # 这里chunk_size不懂...
                if not chunk:
                    break
                fd.write(chunk)


# ----------------------------------------------- 复杂POST请求
payload = {'key1': 'value1', 'key2': 'value2'}
async with session.post('http://httpbin.org/post',data=payload) as resp:
    print(await resp.text())
# 输出：
# {
#   ...
#   "form": {
#     "key2": "value2",
#     "key1": "value1"
#   },
#   ...
# }

# 如果要发送非表单编码的数据，可通过传递bytes而不是dict来完成
# 此数据将直接发布，内容类型默认设置为 "application / octet-stream" ：
async with session.post(url, data=b'\x00Binary-data\x00') as resp:
    ...

# If you want to send JSON data:
async with session.post(url, json={'example': 'test'}) as resp:
    ...

# To send text with appropriate content-type just use text attribute
async with session.post(url, data='Тест') as resp:
    ...

# POST多段编码文件:
# demo1
files = {'file': open('report.xls', 'rb')}
await session.post('http://httpbin.org/post', data=files)
# demo2
data = FormData()
data.add_field('file',open('report.xls', 'rb'),filename='report.xls',content_type='application/vnd.ms-excel')
await session.post('http://httpbin.org/post', data=data)


# ----------------------------------------------- 流媒体上传
# aiohttp 支持多种类型的流式上传，允许发送大型文件而无需将其读入内存

with open('massive-body', 'rb') as f:
   await session.post('http://httpbin.org/post', data=f)

# OR

async def file_sender(file_name=None):
    async with aiofiles.open(file_name, 'rb') as f:
        chunk = await f.read(64*1024)
        while chunk:
            yield chunk
            chunk = await f.read(64*1024)

async with session.post('http://httpbin.org/post',data=file_sender(file_name='huge_file')) as resp:
    print(await resp.text())

# ----------------------------------------------- WebSockets

async with session.ws_connect('http://example.org/ws') as ws:
    async for msg in ws:                                    # 循环接收数据
        if msg.type == aiohttp.WSMsgType.TEXT:              # 判断类型
            if msg.data == 'close cmd':
                await ws.close()
                break
            else:
                await ws.send_str(msg.data + '/answer')     # 发送数据
        elif msg.type == aiohttp.WSMsgType.ERROR:           # 判断类型
            break








