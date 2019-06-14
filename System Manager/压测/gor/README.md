```txt
Gor是go语言实现的简单的http流量复制工具，它的主要目的是使你的生产环境HTTP真实流量在测试环境和预发布环境重现。
只需要在 LB 或 Varnish 入口服务器上执行一个进程就可以把生产环境的流量复制到任何地方
完美解决了 HTTP 层实时流量复制和压力测试的问题
对比在Nginx通过编写lua脚本进行流量拷贝要更加简单便捷，下载解压后就可马上使用。
```
`官方文档：https://github.com/buger/goreplay/wiki`
```bash
#下载地址：https://github.com/buger/goreplay/releases

#将本机上80端口的流量全部复制到192.168.0.100的8080端口
gor --input-raw :80 --output-http 'http://192.168.0.100:8080'


#将本机上80端口的流量复制到192.168.0.100的8080端口，每秒请求不超过10个
gor --input-tcp :80 --output-http "http://192.168.0.100:8080|10"

#将本机上80端口的流量复制到192.168.0.100的8080端口，每秒请求不超过总数的10%
gor --input-raw :80 --output-http "http://192.168.0.100:8080|10%"

#HTTP流量复制输出到文件
gor --input-raw :80 --output-file requests.log

#HTTP流量复制输出到文件
gor --input-raw :80 --output-file requests.log

#通过HTTP流量回放进行压力测试
gor --input-file 'request.gor|200%' --output-http 'http://192.168.0.100:8080'


#过滤指定url，进行HTTP流量复制
gor --input-raw :80 --output-http 'http://192.168.0.100:8080' --http-original-host --output-http-url-regexp test

#过滤请求头，进行HTTP流量复制
gor --input-raw :80 --output-http 'http://192.168.0.100:8080' --http-allow-header api-version:^1\.0\d

#过滤http方法，进行HTTP流量复制
gor --input-raw :80 --output-http "http://192.168.0.100:8080" --http-allow-method GET --http-allow-method OPTIONS

#将流量复制两份到不同的测试服务
gor --input-tcp :28020 --output-http "http://staging.com" --output-http "http://dev.com"

#将HTTP流量进行url重写后再复制
gor --input-raw :80 --output-http 'http://192.168.0.100:8080' --http-rewrite-url /v1/user/([^\\/]+)/ping:/v2/user/$1/ping

#注入改变请求流量header
gor –input-raw :80 –output-http "http://staging.server” –output-http-header “User-Agent: Replayed by Gor” –output-http-header “Enable-Feature-X: true"

#将流量像负载均衡一样分配到不同的服务器
gor --input-tcp :28020 --output-http "http://staging.com" --output-http "http://dev.com" --split-output true
```
#### help
```txt
$ gor --help
-cpuprofile string
write cpu profile to file
-debug verbose
打开debug模式，显示所有接口的流量
-http-allow-header value
用一个正则表达式来匹配http头部，如果请求的头部没有匹配上，则被拒绝
gor --input-raw :8080 --output-http staging.com --http-allow-header api-version:^v1 (default [])
-http-allow-method value
类似于一个白名单机制来允许通过的http请求方法，除此之外的方法都被拒绝.
gor --input-raw :8080 --output-http staging.com --http-allow-method GET --http-allow-method OPTIONS (default [])
-http-allow-url value
一个正则表达式用来匹配url， 用来过滤完全匹配的的url，在此之外的都被过滤掉
gor --input-raw :8080 --output-http staging.com --http-allow-url ^www. (default [])
-http-disallow-header value
用一个正则表达式来匹配http头部，匹配到的请求会被拒绝掉
gor --input-raw :8080 --output-http staging.com --http-disallow-header "User-Agent: Replayed by Gor" (default [])
-http-disallow-url value
用一个正则表达式来匹配url，如果请求匹配上了，则会被拒绝
gor --input-raw :8080 --output-http staging.com --http-disallow-url ^www. (default [])
-http-header-limiter value
读取请求，基于FNV32-1A散列来拒绝一定比例的特殊请求
gor --input-raw :8080 --output-http staging.com --http-header-imiter user-id:25% (default [])
-http-original-host
在--output-http的输出中，通常gor会使用取代请求的http头，所以应该禁用该选项，保留原始的主机头
-http-param-limiter value
Takes a fraction of requests, consistently taking or rejecting a request based on the FNV32-1A hash of a specific GET param:
gor --input-raw :8080 --output-http staging.com --http-param-limiter user_id:25% (default [])
-http-rewrite-url value
Rewrite the request url based on a mapping:
gor --input-raw :8080 --output-http staging.com --http-rewrite-url /v1/user/([^\/]+)/ping:/v2/user/$1/ping (default [])
-http-set-header value
Inject additional headers to http reqest:
gor --input-raw :8080 --output-http staging.com --http-set-header 'User-Agent: Gor' (default [])
-http-set-param value
Set request url param, if param already exists it will be overwritten:
gor --input-raw :8080 --output-http staging.com --http-set-param api_key=1 (default [])
-input-dummy value
Used for testing outputs. Emits 'Get /' request every 1s (default [])
-input-file value
从一个文件中读取请求
gor --input-file ./requests.gor --output-http staging.com (default [])
-input-http value
从一个http接口读取请求
# Listen for http on 9000
gor --input-http :9000 --output-http staging.com (default [])
-input-raw value
Capture traffic from given port (use RAW sockets and require *sudo* access):
# Capture traffic from 8080 port
gor --input-raw :8080 --output-http staging.com (default [])
-input-tcp value
用来在多个gor之间流转流量
# Receive requests from other Gor instances on 28020 port, and redirect output to staging
gor --input-tcp :28020 --output-http staging.com (default [])
-memprofile string
write memory profile to this file
-middleware string
Used for modifying traffic using external command
-output-dummy value
用来测试输入，打印出接收的数据. (default [])
-output-file value
把进入的请求写入一个文件中
gor --input-raw :80 --output-file ./requests.gor (default [])
-output-http value
转发进入的请求到一个http地址上
# Redirect all incoming requests to staging.com address
gor --input-raw :80 --output-http http://staging.com (default [])
-output-http-elasticsearch string
把请求和响应状态发送到ElasticSearch:
gor --input-raw :8080 --output-http staging.com --output-http-elasticsearch 'es_host:api_port/index_name'
-output-http-redirects int
设置多少次重定向被允许
-output-http-stats
每5秒钟输出一次输出队列的状态
-output-http-timeout duration
指定http的request/response超时时间，默认是5秒
-output-http-workers int
gor默认是动态的扩展工作者数量，你也可以指定固定数量的工作者
-output-tcp value
用来在多个gor之间流转流量
# Listen for requests on 80 port and forward them to other Gor instance on 28020 port
gor --input-raw :80 --output-tcp replay.local:28020 (default [])
-output-tcp-stats
每5秒钟报告一次tcp输出队列的状态
-split-output true
By default each output gets same traffic. If set to true it splits traffic equally among all outputs.
-stats
打开输出队列的状态
-verbose
Turn on more verbose output
```