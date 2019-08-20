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
])                                                      # 添加URL及对应的路由函数

web.run_app(app)