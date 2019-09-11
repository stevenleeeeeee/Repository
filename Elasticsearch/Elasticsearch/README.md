```txt
Elasticsearch是实时的分布式搜索和分析引擎，可用于全文搜索，结构化搜索以及分析。
建立在全文搜索引擎 Apache Lucene 基础上，使用 Java 编写。

ES Version >= 5.x 的 head 不能放在ES的plugins、modules下且不再用 "elasticsearch-plugin install" ( 作为独立软件 )

Elastic v5.5.0  
其他依赖和插件：
    Jdk1.8   注: ES 7.0+版本自带jdk，不需要另外在安装了
    Nodejs   作为head插件的依赖
    Head     提供Node管理及可视化RestfulAPI接口
    Kibana   提供数据可视化、搜索、开发者工具等功能
    x-pack   必须运行与ES版本相匹配的X-Pack版本 ( Elasticsearch自7.x版本开始，X-pack安全功能部分免费使用 )
    ik       同上，此插件需maven进行打包...
```
#### Software
```txt
Download: https://www.elastic.co/cn/downloads/

  173M    jdk.tar.gz
   32M    elasticsearch-x.x.0.tar.gz
  3.2M    elasticsearch-analysis-ik-x.x.0.zip
  812K    elasticsearch-head-master.tar.gz
   16M    node-v8.1.4-linux-x64.tar.gz
  153M    x-pack-x.x.0.zip   (7.x版本之后自带X-pack模块，部分功能实现免费)
```
#### Setup Elasticsearch x.x
```bash
# ES5.X依赖JAVA Version >= 1.8，注! ES不能运行在CentOS7以下的版本上
# 集群中的节点可分为：Master nodes、Data nodes、Client node、...
# 在配置文件中使用Zen发现"Zen discovery"机制来管理不同节点，Zen发现是ES自带的默认发现机制，其用多播发现其它节点
# 只要启动1个新的Elastic节点并设置和集群相同的名称，此节点即被加入到集群
# ES需运行在非Root用户下

tar -zxf jdk.tar.gz -C /
ln -s /jdk1.8.0_101 /jdk

cat > /etc/profile.d/java.sh <<'EOF'
export JAVA_HOME=/jdk
export PATH=$JAVA_HOME/bin:$PATH
EOF

. /etc/profile

# Elastic对内核ulimit有要求
# 需先使用Root权限对运行ES的用户修改ulimit配额，最终使用非root账户启动ES
ulimit -SHn 655350

cat > /etc/security/limits.conf <<'EOF'
* soft nofile 655350
* hard nofile 655350
* soft nproc 655350
* hard nproc 655350
* soft memlock unlimited    # 防止内存锁定失败
* hard memlock unlimited    # memory locking requested for elasticsearch process but memory is not locked
EOF

cat >> /etc/sysctl.conf <<'EOF'
fs.file-max = 1000000       # 系统最大打开文件描述符数
vm.max_map_count=262144     # 进程能拥有的最多内存区域
vm.swappiness = 1           # 当为1时其表示进行最少量的交换，而不禁用交换
EOF

#添加or修改如下1行参数
cat >> /etc/security/limits.d/90-nproc.conf <<'EOF'
* soft nproc 102400
EOF

sysctl -p

# Elasticsearch 三个配置文件说明
# config/elasticsearch.yml      主配置文件
# config/jvm.options            JVM参数配置，需要将-Xms的值与-Xmx的值相等，建议最大不要超过32G
# cofnig/log4j2.properties      日志配置

#部署 Master Node
tar -zxf elasticsearch-x.x.0.tar.gz -C ~/

vim ~/elasticsearch-x.x.0/config/elasticsearch.yml
ES_HEAP_SIZE=32g                        # 设置ES_HEAP_SIZE 为机器内存的1/2 但不要超过32G
ES_JAVA_OPTS="-Xms32g"                  # 如果遇到性能问题，最好的方法是安排更好的数据布局和增加节点数目
MAX_LOCKED_MEMORY=unlimited
MAX_OPEN_FILES=65535

vim ~/elasticsearch-x.x.0/config/elasticsearch.yml

cluster.name: ES-Cluster                # Elastic Cluster Name
node.name: "node1"                      # Node Name
node.master: true                       # 是否Master节点
node.data: false                        # 是否Data节点 ( 是否允许该节点存储数据 )
node.max_local_storage_nodes: 3         # 限制单节点上可以开启的ES存储实例的最大数
# node.attr.rack: n2                    # 指定节点的部落属性，这是一个比集群更大的范围
# node.rack: rack314                    # 指定节点所在机架的属性，用于分片策略
# node.tag: value1                      # 为节点打tag
network.host: 0.0.0.0                   # 与其他节点交互时使用的地址
transport.tcp.port: 9300                # 参与集群事物的端口
transport.tcp.compress: true            # 是否开启TCP传输时压缩
http.port: 9200                         # 接收用户请求，提供Restfule-API接口的端口
http.cors.enabled: true                 # 支持跨域访问
http.cors.allow-origin: "*"             # 
path.data: /home/elastic/elasticsearch-5.5.0/data     # 数据存储路径，建议配置多个路径以充分利用多个磁盘的IO
path.logs: /home/elastic/elasticsearch-5.5.0/logs     # 日志存储路径
bootstrap.memory_lock: true             # 设置memory_lock来锁定进程的物理内存地址,JVM会在开启时锁定堆大小 (Xms==Xmx)
# discovery.type: single-node           # 使用单节点模式运行Elasticsearch，主要用于测试
discovery.zen.minimum_master_nodes: 2   # Master 最小存活数量, 应该是有资格成为master的node数量的/2+1
discovery.seed_hosts:                   # 传递初始主节点列表以在启动此节点时执行发现（7.X版本）
    - "node1"
    - "node2"
    - "node3"
cluster.initial_master_nodes:           # 设置一系列符合主节点条件的节点的主机名或 IP 来引导启动集群（7.X版本）
    - "node1"
    - "node2"
    - "node3"
xpack.security.enabled: true                    # 启用X-pack的安全认证功能 ( 7.x版本之前需先破解X-pack ) 
xpack.security.transport.ssl.enabled: true      # 启用传输层安全通信功能
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.keystore.path: elastic-certificates.p12
xpack.security.transport.ssl.truststore.path: elastic-certificates.p12
xpack.security.audit.enabled: false     # 是否启用审计日志，默认路径：ES_HOME/logs/<clustername>_audit.json
action.destructive_requires_name: true
# xpack.watcher.enabled: false
# xpack.monitoring.exporters.my_local:
#   type: local
#   index.name.time_format: YYYY.MM
# index.number_of_shards:3           #
# index.number_of_replicas:1         #
# index.refresh_interval:120s        #
# cluster.routing.allocation.node_initial_primaries_recoveries: 4   # 初始化数据恢复时并发恢复线程数,默认 4 
# cluster.routing.allocation.node_concurrent_recoveries: 2          # 添加删除节点或负载均衡时并发恢复线程数,默认 2 

# 在 Elasticsearch 主节点启动之前配置 TLS，其他主节点可使用此节点生成的 "elastic-certificates.p12" 其内含公私钥:
cd ~/elasticsearch-x.x.0
bin/elasticsearch-certutil cert -out config/elastic-certificates.p12 -pass ""   # 拷贝到所有节点的config下
bin/elasticsearch-users useradd NAME -p PASS -r superuser     # 新增ES用户（在所有节点执行）
bin/elasticsearch-users list                                  # 查看用户列表

# 安装HEAD插件
tar -zxf elasticsearch-head-master.tar.gz -C ~/elasticsearch/
ln -s ~/elasticsearch/elasticsearch-head-master ~/elasticsearch/head
# 安装Nodejs（HEAD插件依赖）
cd ~ && tar -zxf node-v8.1.4-linux-x64.tar.gz -C ~/elasticsearch/
cat > /etc/profile.d/nodejs.sh <<'EOF'
export NODE_HOME=/home/elastic/elasticsearch/node-v8.1.4-linux-x64/
export PATH=$NODE_HOME/bin:$PATH
EOF

. /etc/bash_profile             # 验证：node -v && npm -vs

#由于head的代码还是2.6版本，有很多限制，如无法跨机器访问。因此要修改两个地方:
[wangyu@localhost ~]$ vim +92 ~/elasticsearch/head/Gruntfile.js
connect: {
    server: {
        options: {              #约92行附近，增加hostname字段
            hostname: '*',      #
            port: 9100,
            base: '.',
            keepalive: true
        }
    }
}

#注意! 最小化安装的系统在执行如下命令前须开启root安装bzip2，npm下载文件时会使用其对文件进行解压
sed -i '4354s/localhost/10.0.0.4/' ~/elasticsearch/head/_site/app.js 
npm install -g cnpm --registry=https://registry.npm.taobao.org    #若报错多执行几次
cd ~/elasticsearch/head/ ; cnpm install                           #根据此目录的XXX.js下载

#安装IK分词，其版本须与Elastic严格一致，地址：https://github.com/medcl/elasticsearch-analysis-ik/tree/x.x
cd ~ && unzip elasticsearch-analysis-ik-5.5.0.zip -d ~/
cd ~/elasticsearch-analysis-ik-5.5.0
mvn package #使用maven对源码进行打包，内存较小的话比较耗时
mkdir -p ~/elasticsearch-5.5.0/plugins/ik
unzip -d ~/elasticsearch-5.5.0/plugins/ik ./target/releases/elasticsearch-analysis-ik-5.5.0.zip

# 启动 Elastic
cd ~/elasticsearch-5.5.0/bin/
nohup ./elasticsearch -d &> /dev/null &

# 启动 HEAD
cd ~/elasticsearch/head/node_modules/grunt/bin/
nohup ./grunt server &> /dev/null &
```
#### 测试IK插件的分词功能
```bash
curl -XGET 'http://10.0.0.3:9200/_analyze?pretty&analyzer=ik_max_word' -d '这是一个测试'
curl -XGET 'http://10.0.0.3:9200/_analyze?pretty&analyzer=ik_smart' -d '这是一个测试'
{
  "tokens" : [
    {
      "token" : "这是",
      "start_offset" : 0,
      "end_offset" : 2,
      "type" : "CN_WORD",
      "position" : 0
    },
    {
      "token" : "一个",
      "start_offset" : 2,
      "end_offset" : 4,
      "type" : "CN_WORD",
      "position" : 1
    },
    {
      "token" : "测试",
      "start_offset" : 4,
      "end_offset" : 6,
      "type" : "CN_WORD",
      "position" : 2
    }
  ]
}
```
####  Shard / Segment
```txt
一个Shard ( 分片 ) 就是个Lucene实例，Lucene实例就是一个完整的搜索引擎
一个索引可以只包含1个Shard，不过用多个分片可以拆分索引到不同的节点来分担索引的压力

elasticsearch中每个分片中又包含了多个segment，每个segment都是一个倒排索引! ---> Shard( segment <=> 倒排索引 )

在查询的时，会把在所有的segment中的查询结果汇总归并后最为最终的分片查询结果返回
在创建索引时elasticsearch会把文档信息写到内存buffer中（为了安全也同时写到translog）
elasticsearch定时（可配置）把数据写到segment缓存小文件中，然后刷新查询，使刚写入的segment可提供查询
虽然写入的segment可查询，但是还没有持久化到磁盘上。因此还是会存在丢失的可能性
所以elasticsearch会执行flush操作把segment持久化到磁盘并清除translog数据（因为此时数据已经写到磁盘，不在需要了） 

当索引数据不断增长时，对应的segment也会不断的增多，查询性能可能就会下降。
因此，Elasticsearch会触发segment合并的线程，把很多小的segment合并成更大的segment，然后删除小的segment。 
segment是不可变的，当我们更新一个文档时，会把老的数据打上已删除的标记，然后写一条新的文档。
在执行flush操作的时候，才会把已删除的记录物理删除掉。
```
#### kibana
```bash
Download：https://artifacts.elastic.co/downloads/kibana/kibana-7.3.0-x86_64.rpm
yum install -y kibana-6.0.0-x86_64.rpm 

cat /etc/kibana/kibana.yml 
server.port: 5601
server.host: "192.168.56.11"
elasticsearch.url: "http://192.168.56.11:9200"
elasticsearch.username: "user"
elasticsearch.password: "pass"

systemctl enable kibana --now

#监听端口:
ss -tnl src :5601             
```