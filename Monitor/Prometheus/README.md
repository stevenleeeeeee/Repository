##### https://yunlzheng.gitbook.io/prometheus-book/
```txt
Prometheus基本原理是通过HTTP周期性抓取被监控组件的状态：
    支持通过配置文件、文本文件、Zookeeper、Consul、DNS SRV Lookup等方式指定或动态发现抓取目标
    采用PULL方式监控，即服务器直接通过目标PULL数据，或在exporter端通过中间网关"PushGateway"来Push数据
    PushGateway支持Client主动推送metrics到PushGateway，而Prometheus只是定时去Gateway上抓取数据
    默认在本地存储抓取的所有数据并通过一定规则进行清理、整理，把得到的结果存储到新的时间序列中
    任意组件只要提供对应的HTTP接口规范就可以接入Prometheus监控
    通过提供的PromQL和其他API能可视化地展示收集的数据
    支持很多方式的图表可视化，如Grafana、Promdash以及自身提供的模版引擎等，还提供HTTP API的查询方式，自定义需要的输出
    社区提供了大量官方以及第三方Exporters以满足Prometheus的采纳者快速实现对关键业务及基础设施的监控需求

Exporter:
    输出被监控组件信息的HTTP接口被叫做exporter
    目前互联网公司常用的组件大部分都有exporter可以直接使用
    如:Varnish、Haproxy、Nginx、MySQL、Linux系统信息 (包括磁盘、内存、CPU、网络等等)

Alert Manager:
    是独立于Prometheus的组件，基于查询语句，提供十分灵活的报警方式

Console Template:
    允许用户通过Go模板语言创建任意的控制台界面，并且通过Prometheus Server对外提供访问路径
    https://prometheus.io/docs/visualization/consoles/
    https://yunlzheng.gitbook.io/prometheus-book/part-ii-prometheus-jin-jie/grafana/use-console-template
```
![prometheus](https://prometheus.io/assets/architecture.png)