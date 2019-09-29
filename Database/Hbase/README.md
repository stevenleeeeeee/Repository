#### Hbase 备忘
```txt
Hbase是bigtable的开源山寨版。建立在HDFS之上，是高可靠、高性能、面向列、可伸缩、实时读写的数据库系统
介于Nosql和RDBMS之间，仅能通过主键 (row key) 和主键的range来检索数据，主要用来存储非结构化和半结构化的松散数据
仅支持单行事务 (可通过hive支持来实现多表join等复杂操作)。处理由成千上万的行/列组成的大型数据（大规模结构化存储集群）
与Hadoop一样，Hbase依靠横向扩展，通过不断增加廉价的商用服务器来增加计算和存储能力
HBase的row key天生自带索引，并且按字节顺序排列，且天然分布式。因此设计RowKey就成了用好HBase的关键
HBase以表的形式存储数据。表由行、列组成。列划分为若干列族(row family)
HBase中的存储一切皆是字节，HBase的RowKey会按照字节顺序排序，并且添加索引
HBase会按照row数量自动切割成Region，保持负载均衡与冗余 (策略可改)

HBase的存储机制：
HBase是面向列的数据库，在表中它由行排序。表模式定义只能列族，也就是键值对。
一个表有多个列族以及每一个列族可以有任意数量的列。后续列的值连续存储在磁盘上。表中每个单元格值都有时间戳，总之在HBase中：
    1 表是行集合
    2 行是列族集合
    3 列族是列集合
    4 列是键值对集合


HBase中的表一般有这样的特点：
    1 大：一个表可以有上亿行，上百万列
    2 面向列: 面向列(族)的存储和权限控制，列(族)独立检索。
    3 稀疏: 对于为空(null)的列并不占用存储空间，因此表可以设计的非常稀疏

Row Key：
Table中的所有行都按照row key的字典序排列，Table在行的方向上分割为多个Hregion
Table在行的方向上分隔为多个Region。Region是HBase中分布式存储和负载的最小单元 ( 不同region可分布在不同Region Server上 )
与nosql数据库类似的，row key是用来检索记录的主键。访问hbase table中的行只有三种方式：
    1 通过单个row key访问
    2 通过row key的range
    3 全表扫描

列族：
hbase表中的每个列都归属与某个列族。列族是表的chema的一部分，而列不是
列族必须在使用表之前定义，列名都以列族作为前缀。
例如：courses:history、courses:math 都属于 courses 这个列族

时间戳：
HBase中通过row和columns确定的唯一的存贮单元称为cell。每个cell都保存着同一份数据的多个版本。
版本通过时间戳来索引。时间戳的类型是64位整型。
时间戳可以由hbase(在数据写入时自动)赋值，此时时间戳是精确到毫秒的当前系统时间。时间戳也可以由客户显式赋值。
每个cell中不同版本的数据按照时间倒序排序，即最新的数据排在最前面。
为了避免数据存在过多版本造成的的管理 (包括存贮和索引)负担，hbase提供了两种数据版本回收方式：
    1 保存数据的最后n个版本
    2 保存最近一段时间的版本（如最近七天）。用户可针对每个列族进行设置

Cell：
由 {row key, column(=<family>+<label>), version} 唯一确定的单元
其中数据没有类型，全是字节码形式存贮
```

#### 架构
```txt
Client:
包含访问hbase的接口，client维护着一些cache来加快对hbase的访问，如regione的位置信息

HBase依赖项 Zookeeper:
1 保证任何时候集群中只有一个Master(可启动多个HMaster，通过Zookeeper的Master Election机制保证总有一个Master在运行)
2 存贮所有Region的寻址入口(主要负责Table和Region的管理工作)
3 实时监控Region Server的状态，将Region server的上线和下线信息实时通知给Master
4 存储Hbase的schema,包括有哪些table，每个table有哪些column family

主节点 Hmaster：
HMaster没有单点问题，可启动多个HMaster，通过Zookeeper的Master Election机制保证总有一个Master在运行
1 为Region server分配region
2 负责region server的负载均衡
3 发现失效的region server并重新分配其上的region
4 GFS上的垃圾文件回收
5 处理schema更新请求

从节点 Hregion Server：
每个HRegion对应Table中一个Region
每个HRegion由多个HStore组成
每个HStore对应Table中一个Column Family的存储
Column Family就是一个集中的存储单元，故将具有相同IO特性的Column放在一个Column Family会更高效
1 Region server维护Master分配给它的region，处理对这些region的IO请求
2 Region server负责切分在运行过程中变得过大的region

其他：
master仅仅维护者table和region的元数据信息，负载很低
client访问hbase上数据的过程并不需要master参与（寻址访问zookeeper和region server，数据读写访问regione server）
```