# https://curio.readthedocs.io/en/latest/index.html

# 这是一个使用套接字和curio实现的简单TCP echo服务器：

from curio import run, spawn
from curio.socket import *

async def echo_server(address):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(5)
    print('Server listening at', address)
    async with sock:
        while True:
            client, addr = await sock.accept()
            await spawn(echo_client, client, addr)

async def echo_client(client, addr):
    print('Connection from', addr)
    async with client:
         while True:
             data = await client.recv(100000)
             if not data:
                 break
             await client.sendall(data)
    print('Connection closed')

if __name__ == '__main__':
    run(echo_server, ('',25000))

# -------------------------------------------------------------------------------------------------
# Of course, if you prefer something a little higher level
# you can have curio take of the fiddly bits related to setting up the server portion of the code:

from curio import run, tcp_server

async def echo_client(client, addr):
    print('Connection from', addr)
    while True:
        data = await client.recv(100000)
        if not data:
            break
        await client.sendall(data)
    print('Connection closed')

if __name__ == '__main__':
    run(tcp_server, '', 25000, echo_client)