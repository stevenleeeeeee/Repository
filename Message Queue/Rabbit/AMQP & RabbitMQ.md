#### AMQP: Advanced Message Queuing Portocol
```txt
Advanced Message Queuing Portocol：
是提供统一消息服务的应用层标准高级消息队列协议，是应用层协议的一个开放标准、为面向消息的中间件设计。
基于此协议的客户端与消息中间件可传递消息，并不受客户端/中间件同产品，不同的开发语言等条件的限制

生产者(producer):           
向Exchage发布消息的应用

消费者(Consumer):           
从消息队列中消费消息的应用。

消息(Message):
传输的内容,消息实际上包含了两部分的内容
1.有效载荷(Payload)也就是要传输的数据，数据类型可以纯文本，也可以是JSON
2.标签(Lable)包含交换机的名字和可选的主题(topic)标记等

交换器(Exchage)：           
若干路由组件，接收生产者发送的消息并根据路由键将消息路由转发给绑定的消息队列 (它是算法、逻辑，它其实不是必备的)
消息在到达队列前是通过交换机(器)进行路由的。RabbitMQ为典型的路由逻辑提供了多种内置交换机类型。
如果有更复杂的路由需求，可以将这些交换机组合起来使用，甚至可以实现自己的交换机类型并当做RabbitMQ的插件使用
交换机与队列通过binding key(路由键)进行binding!，binding key就是路由到具体队列的匹配规则
当消息进入Exchange时：Exchange根据消息携带的routing key进行binding
exchange有四种类型：direct、topic、fanout、header
可以这样理解：
    1、routing key是跟消息关联的
    2、binding key是与队列关联的
    3、exchange就是比较这两者的组件


绑定器(Binding)：           
消息队列和交换器直接的关联

消息队列(Message Queue):    
属于服务器组件，用于保存消息，直到发送给消费者。队列可以在集群中的机器上进行镜像，以确保在硬件问题下还保证消息安全
支持多种消息队列协议

虚拟主机(Virtual Host):     
一批交换器，消息队列和相关对象的抽象集合。
虚拟主机共享相同身份认证和加密环境独立的独立服务器域，客户端应用程序在登录到服务器之后可以选择一个虚拟主机。
RabbitMQ支持多租户，每个租户表示为一个vhost，其本质是个独立的小型逻辑RabbitMQ服务器，内部有独立的队列、交换器及绑定关系等
并且拥有自己独立的权限。vhost就像是物理机中的虚拟机，它们在各实例间提供逻辑上的分离，为不同程序安全保密地允许数据
它既能将同一RabbitMQ中的众多客户区分，又可以避免队列和交换器等命名冲突。
Exchange和Message Queue被包含在Virtual host的作用域范围之内 ( virtual host 类似C++的命名空间 )

连接(Connection):           
一个网络连接，比如TCP/IP套接字连接。

信道(Channel)：             
多路复用连接中的一条独立的双向数据流通道，为会话提供物理传输介质
```
#### 其他说明
```txt
RabbitMQ提供了许多插件，来从多方面进行扩展，也可以编写自己的插件
RabbitMQ是典型的点对点模式，而Kafka是典型的发布订阅模式。但RabbitMQ可通过设置交换器类型来实现发布订阅模式而达到广播消费
RabbitMQ对MQTT协议的支持使其其在物联网应用中获得一席之地。还有的消息中间件是基于其本身的私有协议运转的，典型的如Kafka
RabbitMQ提供身份认证（TLS/SSL、SASL）和权限控制（读、写操作）的安全机制。
流量削峰是消息中间件的一个非常重要的功能，而这个功能其实得益于其消息堆积能力。


Publisher、Consumer：
Publisher和Consumer与Server保持连接，Publiser那一侧只需与Exchange进行保持连接，Publisher和Consumer登录时需指定virtual host
当Publisher有消息投递时，需携带Exchange进行binding需要的routingkey，并指定message投递到具体Exchange名字
这意味着Pushlisher并不直接和Message Queue有关联，消息投递时只需要跟Exchange那一侧交互即可
相关投递细节还有消息的持久化，消息投递的确认机制，消息投递的事务的操作等
Consumer通常会创建具体的queue和exchange然后将其binding，根据不同的业务消费不同的消息
Consumer具体其他细节还有消费确认，Qos操作、Cancel、事务操作等


消息中间件的吞吐量始终会受到硬件层面的限制：
以网卡带宽为例，如果单机单网卡的带宽为1Gbps，如果要达到百万级的吞吐，那么消息体大小不得超过(1Gb/8)/100W，即约等于134B
换句话说如果消息体大小超过134B，那么就不可能达到百万级别的吞吐。这种计算方式同样可以适用于内存和磁盘

AQMP是实现消息机制的一种协议，消息队列主要有以下几种应用场景：
1、异步处理
2、应用解耦
3、流量缓冲
4、日志处理

RabbitMQ 基础组件：
    Server
    Connection
    Channel
    Virtual Host
    Exchange
    Message
    Binding
    Routing Key
    Binding Key
    Message Queue
    Exchange Type (direct topic fanout)
    Producer- Consumer
    Publisher- Subscriber (topic Exchange Type)

RabbitMQ 特性：
    Persistent：持久化，需要message、exchange、queue同时支持持久化才能达到持久化的操作
    Confirm：发送确认
    Quality of Service：消费者可以指定Qos操作，操作预取，节省带宽
    Acknowledgements：消费确认
    Transaction：事务操作，支持一组消息的发送，和消费，支持回滚操作
```
#### RabbitMQ
```txt
RabbitMQ是实现了高级消息队列协议（AMQP）的开源消息代理软件（亦称面向消息的中间件）、是采用Erlang语言编写的
```