```bash
Kafka使用Yammer Metrics在服务器和Scala客户端中进行度量报告 ( Java客户端使用Kafka Metrics )
这是一种内置的度量标准注册表，可最大限度减少传入客户端应用程序的传递依赖性 
两者都通过JMX公开指标，并可配置为使用可插入的统计报告来报告统计数据，以连接到监控系统

所有Kafka速率指标都有相应的累积计数指标，后缀为-total
例如：记录消耗率具有名为 records-consume-total 的对应度量

查看可用指标的最简单方法是启动 jconsole 并将其指向正在运行的kafka客户端或服务器，这允许使用JMX浏览所有指标
Kafka开放了N多JMX指标，很多框架可以帮助我们实时捕获这些JMX metrics的值。
实际上Kafka还提供了一个非常方便的工具：JmxTool
严格来说，JmxTool不是框架，而是Kafka社区默认提供的一个工具，用于实时查看JMX监控指标。
如果用户一时找不到合适工具来监测JMX指标可以考虑使用该工具"临时救急"
```
#### bin/kafka-run-class.sh kafka.tools.JmxTool
```bash
# 打开终端进入到Kafka安装目录下，执行如下命令便可得到JmxTool工具的帮助信息：
bin/kafka-run-class.sh kafka.tools.JmxTool


# 假设要实时监控broker端JMX指标：消息入站速率：
bin/kafka-run-class.sh kafka.tools.JmxTool \
--object-name kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec \ 
--jmx-url service:jmx:rmi:///jndi/rmi://:9997/jmxrmi \
--date-format "YYYY-MM-dd HH:mm:ss" \
--attributes FifteenMinuteRate \
--reporting-interval 5000
# 输出：
# Trying to connect to JMX url: service:jmx:rmi:///jndi/rmi://:9997/jmxrmi.
# "time","kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec:FifteenMinuteRate"
# 2018-08-10 14:52:15,784224.2587058166
# 2018-08-10 14:52:20,1003401.2319497257
# 2018-08-10 14:52:25,1125080.6160773218
# 2018-08-10 14:52:30,1593394.1860063889
# 2018-08-10 14:52:35,1993957.4168548603
# 2018-08-10 14:52:40,2357721.0311160865
# 2018-08-10 14:52:45,2841690.084352943
# 2018-08-10 14:52:50,2965280.638911543
# 2018-08-10 14:52:55,2948852.533463836
# 2018-08-10 14:53:00,2932515.442217301
# 2018-08-10 14:53:05,2916268.8609394296
# 2018-08-10 14:53:10,2900112.2881912384

# 上述命令中的kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec可以替换成Kafka提供的其他JMX指标
# 完整的JMX指标列表：https://kafka.apache.org/documentation/#monitoring

# 消息速率：Message in rate	
kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec

# Byte in rate from clients	
kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec

# Byte out rate to clients
kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec

# Byte in rate from other brokers
kafka.server:type=BrokerTopicMetrics,name=ReplicationBytesInPerSec

# ZooKeeper connection status	
kafka.server:type=SessionExpireListener,name=SessionState
```
