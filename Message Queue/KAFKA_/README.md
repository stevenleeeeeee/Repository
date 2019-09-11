#### 原理
```bash
# KAFKA是分布式、支持分区/副本，基于Zookeeper进行协调的分布式消息系统，其消息被持久化到磁盘，支持上千Client
# Kafka只是分为拥有1~N个分区的主题的集合，分区是消息的线性有序序列，Topic的每个具体的消息由它们的索引 (偏移) 标识
# 集群中所有数据都是不相连的分区联合。传入消息写在分区末尾（消息由消费者顺序读取）通过将消息复制到不同的代理提供持久性

# Topic
    消息的分类，比如page view、click日志等都能够以Topic的形式存在。Kafka集群能同时刻负责多个Topic的分发

# Broker
    消息处理结点，1个Kafka节点就是1个Broker，多个Broker组成KAFKA集群

# Zookeeper在kafka中的作用
    无论kafka集群还是producer、consumer，都依赖于zookeeper来保证系统可用性，其保存 metadata
    注: 老版本中Topic的消费和偏移信息存放在zookeeper，新版本中Topic的消费和偏移信息存放在broker的一个特殊的可压缩Topic中
    Kafka使用ZK作为其分布式协调框架，很好的将消息的生产、存储、消费的过程结合在一起
    借助zk能将生产、消费者和broker在内的组件在无状态情况下建立起生产/消费者的订阅关系/并实现生产与消费的负载均衡
    Kafka采用zookeeper作为管理，记录了producer到broker的信息以及consumer与broker中partition的对应关系
    Broker通过ZK进行 leader -> followers 选举，旧版本的消费者通过ZK保存读取的位置"Offset"及读取的topic的partition信息
    它也使用了zookeeper的watch机制来发现meta信息的变更并作出相应的动作 (如consumer失效、触发负载均衡等) 

    1. 启动zookeeper的server --->  启动kafka的server
    2. Producer若生产了数据，会先通过ZK找到broker，然后将数据存放到broker
    3. Consumer若要消费数据，会先通过ZK找对应的broker，然后消费 (消费的同时保存本次消费分区的segement中的位置)
    
# replication & partition
    如果Topic配置了复制因子"replication facto"为N 那么可以允许N-1服务器宕机而不丢失任何已经增加的消息
    每个Partition有1个leader与多个follower，producer往某个Partition中写入数据时只会往leader中写，然后数据会被异步/同步的方式复制到其他Replica
    副本数决定了有多少个Broker来存放写入的数据! 简单说副本是以Partition为单位进行复制的 ( 副本仅复制而不提供读/写能力，这与Elasticsearch的概念有区别)
    存放副本也可以这样简单的理解：根据设置的副本数备份若干数量的Partition并且其中仅有1个Partition被选为Leader用于读写!...
    Producer能决策将消息推送到Topic的哪些Partition!，并且producer能直接发送消息到对应partition的Leader处!
    kafka中相同group的consumer不可同时消费同一个partition，在同一topic中同一partition同时只能由一个Consumer消费，当同一topic同时需有多个Consumer消费时可创建更多的partition
    如果同一消费者组内的消费者数量超过其消费的Topic的分区数量，那么有一部分消费者就会被闲置!
    假设设置了数据默认副本数为3，那么会选举其中的某1个partition（备份以partition为单位）为leader，另外2个为follower!
    Replica的数量 <= Broker节点的数量!，即：以Partition为单位来说，每个Broker上最多只会有此分区的1个Replica!，因此可以使用Broker id指定Partition的Replica
    所有Partition的Replica默认情况会均匀分布到所有Broker上.

    由于Broker采用了 Topic -> Partition 的思想，使得某个分区内部的顺序可保证有序性，但分区间的数据不保证有序性!

    对相同group的consumer来说kafka可被其认为是一个队列消息服务，各consumer均衡的消费相应partition中的数据！
    因此：
    假如所有消费者都在一个消费者组中那么这就变成了queue模型!
    假如所有消费者都在不同的组那么就完全变成了发布/订阅模型!

# Partition & Segment
    Topic物理上的分组。一个Topic可分为多个Partition(分区)，每个Partition就是一个有序的队列
    Kafka仅保证Topic以不同的分区为单位从而在每个分区内进行顺序处理，不能保证跨分区的消息的先后处理顺序...
    所以如果想要顺序的处理Topic的所有消息那就只为其提供提供1个分区...
    Partition物理上又由多个Segment组成（段文件）

# offset
    每个Partition由一系列有序不可变的消息组成，这些消息被连续的追加到Partition中，并且每个消息都有个连续的序列号：offset
    offset用于在partition内部唯一标识这条消息（消费者能够以分区为单位自定义读取的位置）
    注意：
    老版本consumer的位移是提交到zookeeper中的：/consumers/<group.id>/offsets/<topic>/<partitionId>
    新版本consumer不再保存位移到zookeeper中，而是保存在KAFKA的Broker中的特殊的Topic中保存: "__consumeroffsets"
    新版本中这个特殊的"__consumers_offsets" topic配置了compact策略，使得它总是能保存最新的位移信息

            -----------------------------------------------------------------------------

# Data Replication如何处理Replica恢复
    leader挂掉后从它的follower中选举一个作为leader，并把挂掉的leader从ISR中移除，继续处理数据
    过段时间该leader重新启动时它知道它之前的数据到哪里了，尝试获取它挂掉后leader处理的数据，获取完成后它就加入了ISR

# Data Replication何时Commit
    同步复制：  只有所有的follower把数据拿过去后才commit，一致性好，可用性不高.
    异步复制：  只要leader拿到数据立即commit，等follower慢慢复制，可用性高，立即返回，一致性差.
    Commit：   是指leader告诉客户端这条数据写成功了。kafka尽量保证commit后立即leader挂掉，其他flower都有该条数据

# KAFKA不是完全意义上的同步/异步! 它在底层是一种ISR机制：
1. 每个Topic下的每个分区的leader维护着与其基本保持同步的Replica列表，该列表称为ISR (in-sync Replica)，每个Partition都有ISR，且由leader动态维护
2. 如果Topic下的某个分区的flower比leader落后了太多或超过特定时间未发起数据的Pull求，则leader将其重ISR中移除
3. 默认当ISR中所有Replica都向Leader发送ACK时leader才commit!

# 在Producer端可以设置究竟使用那种同步方式：
    request.required.asks=
        0   相当于异步，不需要leader给予回复，producer立即返回，发送就是成功
        1   当leader接收到消息之后发送ack，丢会重发，丢的概率很小
       -1   当所有的follower都同步消息成功后发送ack.  丢失消息可能性比较低
```
#### 关键字解释
```bash
AR：assigned replicas
    #通常情况下每个分区都会被分配多个副本
    #具体的副本数量由参数offsets.topic.replication.factor指定
    #分区的AR数据保存在Zookeeper的/brokers/topics/<topic>节点中

ISR：in-sync replicas
    # 与leader类型的分区副本保持同步状态的分区副本集合 (leader副本本身也在ISR中)
    # ISR数据保存在Zookeeper的/brokers/topics/<topic>/partitions/<partitionId>/state节点中

High Watermark：
    #副本高水位值简称 "HW" 它表示该分区最新的一条已经提交的消息(committed message)的位移

LEO：log end offset
    #从名字上来看似乎是日志结束位移，但其实是下一条消息的位移，即追加写下一条消息的位移
    #LEO可能会比HW大，因为对分区的leader而言它的日志随时会被追加写入新消息，而这些消息很可能还没被完全复制到其他follower
```
#### 部署
```bash
#部署JAVA （ Kafka 依赖 Java version >= 1.7 ）
#部署Kafka
[root@localhost ~]# tar -zxf kafka_2.11-1.0.1.tgz -C /home/ && ln -sv /home/kafka_2.11-1.0.1 /home/kafka

#部署Kafka自带的Zookeeper
[root@localhost ~]# cd /home/kafka/config/ && ll
-rw-r--r--. 1 root root  906 2月  22 06:26 connect-console-sink.properties
-rw-r--r--. 1 root root  909 2月  22 06:26 connect-console-source.properties
-rw-r--r--. 1 root root 5807 2月  22 06:26 connect-distributed.properties
-rw-r--r--. 1 root root  883 2月  22 06:26 connect-file-sink.properties
-rw-r--r--. 1 root root  881 2月  22 06:26 connect-file-source.properties
-rw-r--r--. 1 root root 1111 2月  22 06:26 connect-log4j.properties
-rw-r--r--. 1 root root 2730 2月  22 06:26 connect-standalone.properties
-rw-r--r--. 1 root root 1221 2月  22 06:26 consumer.properties           #消费者配置信息
-rw-r--r--. 1 root root 4727 2月  22 06:26 log4j.properties
-rw-r--r--. 1 root root 1919 2月  22 06:26 producer.properties           #生产者配置信息
-rw-r--r--. 1 root root 6852 2月  22 06:26 server.properties             #Kafka的broker配置文件
-rw-r--r--. 1 root root 1032 2月  22 06:26 tools-log4j.properties
-rw-r--r--. 1 root root 1023 2月  22 06:26 zookeeper.properties          #自带的Zookeeper的配置文件

#这里使用的是Kafka自带的ZK ( 简单的Demo，实际生产中应使用ZK集群的方式 )
[root@localhost config]# vim /home/kafka/config/zookeeper.properties     
dataDir=/var/zookeeper                      #ZK的快照存储路径
clientPort=2181                             #客户端访问端口
maxClientCnxns=0                            #最大客户端连接数

[root@localhost config]# vim /home/kafka/config/server.properties
broker.id=0                                 #Broker编号，在集群不同节点间不能重复
port=9092                                   #客户端使用端口，producer或consumer在此端口连接
host.name=192.168.133.128                   #节点主机名称，直接使用IP ( 如果不设置默认返回主机名给zk_server )
#listeners=PLAINTEXT://:9092                #新版本中使用此配置代替了旧版本的host.name字段
#advertised.listeners=PLAINTEXT://IP:9092   #新版本中使用此配置代替了旧版本，没有设置时如果配置了"listeners"就使用"listeners"的值
num.network.threads=3                       #处理网络请求的线程数，线程先将收到的消息放到内存，再从内存写入磁盘
num.io.threads=8                            #消息从内存写入磁盘时使用的线程数，处理磁盘IO的线程数
socket.send.buffer.bytes=102400             #发送套接字的缓冲区大小
socket.receive.buffer.bytes=102400          #接受套接字的缓冲区大小
socket.request.max.bytes=104857600          #请求套接字的缓冲区大小
log.dirs=/tmp/kafka-logs                    #数据存放路径（注意要先创建：mkdir -p  /tmp/kafka-logs）
replica.fetch.max.bytes=                    #默认1M，即使在Topic定义max.message.bytes=52428700，但此值不会随着更新!
replica.lag.time.max.ms=10000ms             #只要follower每10s能发FetchRequest给leader，则不会被标记dead并踢出ISR
replica.lag.max.messages=10000              #容忍follower最多与leader消息同步滞后数量，否则踢出ISR（新版本已经移除）
num.replica.fetchers=1                      #leader中进行复制的线程数，增大这个数值会增加relipca的IO
num.partitions=3                            #若创建topic时没有给出划分partitions个数，则使用此默认数值代替
log.segment.bytes=1073741824                #日志文件中每个segment文件的上限容量，默认1G
log.retention.check.interval.ms=300000      #定期检查segment文件有没有到达上面指定的限制容量的周期，单位毫秒
log.retention.hours=168                     #segment文件保留的最长时间，默认7天，超时将被删除，单位hour
num.recovery.threads.per.data.dir=1         #设置恢复和清理data下数据时使用的的线程数，用于在启动时日志恢复/关闭时刷新
log.cleaner.enable=true                     #日志清理是否打开
offsets.topic.replication.factor=1
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1
zookeeper.connect=192.168.133.130:2181      #ZK的IP:PORT，格式：IP:PORT,IP:PORT,IP:PORT,...
zookeeper.connection.timeout.ms=6000        #ZK的连接超时
delete.topic.enable=true                    #物理删除topic需设为true，否则只是标记删除!
group.initial.rebalance.delay.ms=0
#auto.offset.reset                          #默认为 latest
#   earliest    当各分区下有已提交的offset时，从提交的offset开始消费,无提交的offset时从头开始
#   latest      当各分区下有已提交的offset时，从提交的offset开始消费,无提交的offset时消费新产生的该分区下的数据 
#   none        topic各分区都存在已提交的offset时从offset后开始消费,只要有1个分区不存在已提交的offset，则抛异常

#启停
[root@localhost config]# cd /home/kafka/bin
./zookeeper-server-start.sh -daemon ../config/zookeeper.properties      #启动ZK
./kafka-server-start.sh -daemon ../config/server.properties             #启动Kafka
./kafka-server-stop.sh                                                  #停止Kafka

#注意:
# 客户端连接到zookeeper要求消费数据，zk返回broker的ip地址和端口给客户端
# 但是如果broker没有设置 host.name 和 advertised.host.name 的话，其默认返回的是自己的主机名: localhost:9092
# 这时客户端拿到这个主机名将解析到自己，操作失败。
# 所以需要配置broker的host.name参数为监听的IP，这时broker就会返回IP...
```
#### 操作备忘
```bash
#关键字：
Topic:      # 主题名称
Partition:  # 分片编号
Leader:     # 该Topic的分区的leader节点
Replicas:   # 该副本存在于哪个broker节点
Isr:        # 活跃状态的broker ( 进度已经在跟随着leader节点 )

#创建主题（保存时长：delete.retentin.ms）
./kafka-topics.sh --zookeeper 192.168.133.130:2181 --create --partitions 1 --replication-factor 1 --topic TEST \
--config delete.retention.ms=86400000    #定义保存时间（1天）
--config retention.bytes=1073741824      #定义保存容量（针对的是每个分区，因此实际占用容量=此值*分区数）

#生产建议将kafka自动创建topic功能禁用，修改conf/server.properties为手动创建："auto.create.topics.enable=false"
#parttitions和replication－factor是两个必备选项（需要严格读取Topic消息顺序的时候，只使用1个partition）
#分区是消费并行度的一个重要参数（多Partition时仅其中的learder才能进对本partiotion读写，其余都是冗余副本）
#副本极大提高了Topic的可用性.其数量默认是1，注意其值不能大于broker个数，否则报错。
#同时还可以指定Topic级别的配置，这种特定的配置会覆盖默认配置，并存储在zookeeper的/config/topics/[topic_name]节点

#主题清单
./kafka-topics.sh --zookeeper 192.168.133.130:2181 --list

#主题详情
./kafka-topics.sh --zookeeper 192.168.133.130:2181 -describe -topic ES

#删除主题，在配置中需要开启删除主题的功能：delete.topic.enable=true
./kafka-topics.sh --zookeeper 192.168.133.130:2181 --delete --topic ES

#生产者客户端命令（生产者产生信息时已经从ZK获取到了Broker的路由，因此这里要填入Broker的地址列表）
bin/kafka-console-producer.sh --broker-list 192.168.133.130:9092 --topic ES

#消费者客户端命令，若需要从头消费需添加参数：--from-beginning
#旧版本：./kafka-console-consumer.sh -zookeeper <IP>:<PORT> --topic ES --from-beginning [ --group xxx  ]
#新版本：./kafka-console-consumer.sh --bootstrap-server <IP>:<PORT> --topic ES --from-beginning [ --group xxx  ]

#为Topic增加Partition
./kafka-topics.sh –-zookeeper 127.0.0.1:2181 -–alter -–partitions 20 -–topic ES
#只能增加不能减少，若原有分散策略是hash的方式，将会受影响。发送端（默认10min会刷新本地元信息）/消费端无需重启即生效

#修改消息过期时间 (保存期限)
./kafka-topics.sh –-zookeeper 127.0.0.1:2181 –alter –-topic ES --config delete.retention.ms=1

#修改主题内的分区数
./kafka-topics.sh -–zookeeper 127.0.0.1:2181 -alter –partitions 5 –topic TEST

#查看正在进行消费的 group ID ：（旧/新）
kafka-consumer-groups.sh --zookeeper localhost:2181 --list
kafka-consumer-groups.sh --new-consumer --bootstrap-server 127.0.0.1:9292 --list

#通过 group ID 查看当前详细的消费情况（旧/新）
./kafka-consumer-groups.sh --zookeeper localhost:2181 --group TEAM1 --describe
./kafka-consumer-groups.sh --bootstrap-server 127.0.0.1:9092 --new-consumer  --group TEAM1 --describe
#消费者组                       话题id         分区id     当前已消费条数    总条数          未消费条数
#GROUP                         TOPIC          PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG      OWNER
#console-consumer-28542        test_find1     0          303094          303094          0               
#console-consumer-28542        test_find1     2          303713          303713          0  

#重平衡leader!
./kafka-preferred-replica-election.sh --zookeeper 192.168.52.130:2181

#查看所有kafka节点，在ZK的bin目录:
./zkCli.sh ---> ls /brokers/ids 就可以看到zk中存储的所有 broker id，查看：get /brokers/ids/{#}

#查看topic各个分区的消息的信息 ( 指定分组 ) 此命令在 > 0.9 的kafka版本中以不在支持 !!
./kafka-run-class.sh kafka.tools.ConsumerOffsetChecker --zookeeper `hostname -i`:2181 \
--group test --topic <TOPIC> 

#查看TOPIC在其每个分区下的消费偏移量
./kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list `hostname -i`:9092 \
--topic <TOPIC> --time -2   #输出其offset的最小值
./kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list `hostname -i`:9092 \
--topic <TOPIC> --time -1   #输出其offset的最大值

#对TOPIC添加配置：
kafka-configs.sh --zookeeper IP:port/chroot --entity-type topics --entity-name <TOPIC> --alter --add-config x=y
                 
#对TOPIC删除配置：
kafka-configs.sh --zookeeper IP:port/chroot --entity-type topics --entity-name <TOPIC> --alter --delete-config x

#--members：此选项提供使用者组中所有活动成员的列表 ( 新老版本输出差异较大 )
#注意!!  所有的KAFKA终端命令中，新版本使用: --bootstrap-server  老版本使用： --zookeeper  否则执行报错或误报!...
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group <GROUP>  \
--members --verbose [--all-topics]
CONSUMER-ID                                    HOST          CLIENT-ID       #PARTITIONS  ASSIGNMENT
consumer1-3fc8d6f1-581a-4472-bdf3-3515b4aee8c1 /127.0.0.1    consumer1       2            topic1(0), topic2(0)
consumer4-117fe4d3-c6c1-4178-8ee9-eb4a3954bee0 /127.0.0.1    consumer4       1            topic3(2)
consumer2-e76ea8c3-5d30-4299-9005-47eb41f3d3c4 /127.0.0.1    consumer2       3            topic2(1), topic3(0,1)
consumer3-ecea43e4-1f01-479f-8349-f9130b75d8ee /127.0.0.1    consumer3       0            -

./kafka-run-class.sh kafka.tools.ConsumerOffsetChecker --zookeeper `hostname -i`:2181 \
--group test --topic testKJ1  ???????????
```
#### 查看特定TOPIC分区大小
```bash
#查看某特定TOPIC在各Broker上的分区容量信息
./kafka-log-dirs.sh --bootstrap-server <broker:port>  \
--describe --topic-list <topics> --broker-list <broker.id_list> \
| grep '^{' \
| jq '[ ..|.size? | numbers ] | add'

#--bootstrap-server:     必填项, <broker:port>.
#--broker-list:  可选, 可指定查看某个broker.id上topic-partitions的size, 默认所有Broker!
#--describe:     描述
#--topic-list:   要查询的特定 topic 分区在disk上的空间占用情况，默认所有Topic

{
    "version": 1,
    "brokers": [{
        "broker": 0,
        "logDirs": [{
            "logDir": "/data/kafka-logs",
            "error": null,
            "partitions": [{
                "partition": "afei-1",
                "size": 567,            #单位byte
                "offsetLag": 0,
                "isFuture": false
            }, {
                "partition": "afei-2",
                "size": 639,            #单位byte
                "offsetLag": 0,
                "isFuture": false
            }, {
                "partition": "afei-0",
                "size": 561,            #单位byte
                "offsetLag": 0,
                "isFuture": false
            }]
        }]
    }]
}
```
#### 性能测试
```bash
#消费
./kafka-consumer-perf-test.sh --zookeeper 172.22.241.162:9092/kafka \
--messages 50000000 --topic TEST --threads 1
#输出格式
start.time,end.time, compression, message.size, batch.size, total.data.sent.in.MB, MB.sec,total.data.sent.in.nMsg, nMsg.sec

#生产
./kafka-producer-perf-test.sh --broker-list 172.22.241.162:9092 --threads 3 \
--messages 10000 --batch-size 1 --message-size 1024 --topics topic_test --sync
#--messages       生产者发送的消息总量
#--message-size   每条消息大小
#--batch-size     每次批量发送消息的数量
#--topics         生产者发送的topic
#--threads        生产者使用几个线程同时发送
#--producer-num-retries 每条消息失败发送重试次数
#--request-timeout-ms   每条消息请求发送超时时间
#--compression-codec    ?设置生产端压缩数据的codec，可选参数："none"，"gzip"， "snappy"

#--producer-props PROP-NAME = PROP-VALUE [PROP-NAME = PROP-VALUE ...]
#                 生成器相关的配置属性，如bootstrap.servers，client.id等。这些优先于通过--producer.config传递的配置
#--producer.config CONFIG-FILE
#                 生成器配置属性文件

#输出格式：
start.time,end.time, compression, message.size, batch.size, total.data.sent.in.MB, MB.sec,total.data.sent.in.nMsg, nMsg.sec
2015-05-2611:44:12:728, 2015-05-26 11:52:33:540, 0, 100, 200, 4768.37, 9.5213, 50000000,99837.8633
#replicationfactor不会影响consumer的吞吐性能，因为consumer只从每个partition的leader读数据
#一般情况下：分区越多，单线程生产者吞吐率越小，副本越多，吞吐率越低，异步生产数据比同步产生的吞吐率高近3倍
#短消息对Kafka来说是更难处理的使用方式，可以预期，随着消息长度的增大，records/second会减小
#当消息长度为10Byte时，因为要频繁入队花了太多时间获取锁，CPU成了瓶颈，并不能充分利用带宽...
```
#### 数据存储机制
```bash
log.dirs：/data/kafka           #配置文件中定义的数据存储路径
                 \
                  \             #TOPIC:TEST
                   TEST-0       #partiton:1
                        \
                         \...
                   TEST-1       #partiton:2
                        \
                         \...
                          xxxx.index     #索引
                          xxxx.log       #数据 （ 每个partition在物理存储层面由多个log file组成 （即"segment"）
```
#### logstash 消费 kafka
```bash
#Example：
input{
    kafka {
        zk_connect => "112.100.6.1:2181,112.100.6.2:2181,112.100.6.3:2181"
        group_id => "logstash"
        topic_id => "Example"
        reset_beginning => false
        consumer_threads => 5
        decorate_events => true
    }
}
```