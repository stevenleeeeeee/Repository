#### 基本组件
```bash
Elasticsearch   #提供存储、搜索...，高度可扩展的开源全文搜索和分析引擎
APM Agent       #应用侧部署agent，负责性能和错误数据，当前支持node、python、ruby、js，java和golang ( 侵入式 )
                #apm agent会检测代码并在运行时收集性能数据和错误。此数据可缓冲一小段时间并发送到APM服务器。
APM Server      #服务侧在原es基础上新增go编写的APM server服务，接受agent的打点数据
                #通过JSON HTTP API从代理接收数据，它根据该数据创建文档并将其存储在Elasticsearch中
Kibana APM UI   #与Elasticsearch协同工作，提供了对APM显示的原生适配
                #可使用Kibana中的专用APM UI或通过 APM Kibana UI直接加载的预构建的开源Kibana dashboard来可视化APM数据

#APM允许实时监控软件服务和应用程序，收集有关传入请求的响应时间，数据库查询，高速缓存调用，外部HTTP请求等的详细性能信息。
#弹性APM还会自动收集未处理的错误和异常。错误主要基于堆栈跟踪进行分组，因此可以识别出现的新错误并密切关注特定错误发生的次数
```
#### Install APM Server / Agent
```bash
#部署Server
#golang编译的binary mac本地安装
curl -L -O https://artifacts.elastic.co/downloads/apm-server/apm-server-6.3.2-darwin-x86_64.tar.gz
tar xzvf apm-server-6.3.2-darwin-x86_64.tar.gz
cd apm-server-6.3.2-darwin-x86_64/
./apm-server setup      #导入kibana apm定制的dashboard

vim apm-server.yml
#按需修改配置，默认端口8200供Agent使用
apm-server:
  host: "localhost:8200"    # Defines the host and port the server is listening on
output.elasticsearch:
  hosts: ["localhost:9200"] #Elasticsearch 地址
setup.kibana:
  host: "localhost:5602"    #Kibana地址

#启动 apm-server
./apm-server -e


#部署Agent ( 整了两个app，一个nodejs，一个python，代码如下 )
#Example-Nodejs：
➜  myapp cat node.js
// Add this to the VERY top of the first file loaded in your app
var apm = require('elastic-apm-node').start({
  // Set required service name (allowed characters: a-z, A-Z, 0-9, -, _, and space)
  serviceName: 'node-test',

  // Use if APM Server requires a token
  secretToken: '',

  // Set custom APM Server URL (default: http://localhost:8200)
  serverUrl: 'http://localhost:8200'
})
const express = require('express')
const app = express()

app.get('/', (req, res) => res.send('Hello World!'))

app.listen(3000, () => console.log('Example app listening on port 3000!'))

#事先安装俩包:
npm install elastic-apm-node --save     # apm-agent for node js
npm install express --save

#启动:
node node.js

#Example-Python:
➜  myapp cat hello.py
from flask import Flask
from elasticapm.contrib.flask import ElasticAPM
from elasticapm.handlers.logging import LoggingHandler
import os
import urllib2

app = Flask(__name__)

app.config['ELASTIC_APM'] ={
    'SERVER_URL': 'http://127.0.0.1:8200',
    'DEBUG': True
}
apm = ElasticAPM(app,service_name='python-test',logging=True)

port = 5000

@app.route('/')
def hello_world():
    contents = urllib2.urlopen("http://127.0.0.1:3000").read()

    return 'Hello World! I am running on port ' + str(port) + contents


if __name__ == '__main__':
    handler = LoggingHandler(client=apm.client)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=port)

#启动，一切顺利的，可以去kibana的界面看下数据 127.0.0.1:5621
```