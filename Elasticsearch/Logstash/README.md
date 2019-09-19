###### filebeat --->  kafka --->  logstash --->  Elasticsearch --->  Kibana
#### Filebeat
```bash
filebeat:
  registry_file: .filebeat              # 记录filebeat处理日志文件的位置的文件，默认在启动的根目录下
  prospectors: 
    - paths: 
        - /home/wangyu/Test/*.log 
      input_type: log 
      document_type: oslog              # 输出时的document的type字段，在logstash中使用 [type] 对其值进行判断
      scan_frequency: 10s               # Every 10s scan ..
      encoding: plain 
      include_lines: ["^ERR", "^WARN"]  # 含正则列表的行（默认所有）include_lines执行之后会执行exclude_lines
      exclude_lines: ["^DBG"]           # 要排除的行
      exclude_files: [".gz$"]           # 忽略掉符合正则表达式列表的文件
      close_older: 1h                   # 若文件在某个时间段内没有发生更新则关闭监控的文件handle（默认1h）
      max_bytes: 10485760               # 增加1行算1个事件，max_bytes限制在1次日志事件中最多上传的字节，多出的被丢弃
      tail_files: false                 # 是否从文件尾部开始监控文件新增内容
      backoff: 1s                       # 检测到了EOF（文件结尾）后，每次等待多久再去检测文件是否有更新，默认1s
      fields:                           # 添加额外的信息
         level: debug                   # 新增一个JSON的key
output.kafka:  
  enabled: true  
  hosts: ["10.0.0.3:9092"] 
  topic: ES                             # MQ Topic
  partition.round_robin: 
    required_acks: 1                    # Need kafka Ack
    max_message_bytes: 1000000
#output.console:
#    pretty: true
```
#### Kafka
```bash
# 在Kafka的Broker端创建"Logstash"消费的主题
kafka-topics.sh --create --zookeeper 10.0.0.3:21811 --replication-factor 1 --partitions 1 --topic ES
```
#### Logstash
```bash
# 注:
# logstash的 --config.test_and_exit 选项解析配置文件并报告任何错误 )
# logstash的 --config.reload.automatic 选项启用自动配置重新加载，因此每次修改配置文件时都不必停止并重新启动Logstash
# logstash的名为@metadata的特殊字段的内容在输出时不会成为你的任何事件的一部分！
# 这使得它很适合用于条件或者扩展和构建带有字段引用和sprintf格式的事件字段
# logstash中的@metadata包含的字段默认不会作为事件的一部分输出!
# 如果指定了metadata => true 时，只有 rubydebug codec 允许显示 @metadata 字段的内容。

# logstash的logstash.yml文件还支持bash风格的通过环境变量插值设置值：
pipeline:
  batch:
    size: ${BATCH_SIZE}
    delay: ${BATCH_DELAY:50}  # 此处当未设置BATCH_DELAY环境变量时，将使用默认值："50"
node:
  name: "node_${LS_NODE_NAME}"
path:
   queue: "/tmp/${QUEUE_DIR:queue}"

# logstash的判断语法格式：
if "_grokparsefailure" not in [tags] {
  ......
} else if [status] !~ /^2\d\d/ and [url] == "/noc.gif" {
  ......
} else {
  ......
}

# logstash条件类似于编程语言。条件支持if、else if、else语句，可以嵌套：
# 比较操作如下： 
    # 相等:           ==, !=, <, >, <=, >= 
    # 正则:           =~(匹配正则), !~(不匹配正则) 
    # 包含:           in(包含), not in(不包含) 
    # 布尔操作：      and(与), or(或), nand(非与), xor(非或) 
    # 一元运算：      !"取反"、()"复合表达式"、!()"对复合表达式结果取反"

# 在logstash中引用字段内容使用："%{foo}" 引用字段使用: [foo]


# 生成带日期的索引的2种方式：
# 方式1：
output {
    elasticsearch {
        hosts => ["127.0.0.1"]
        index => "logs-%{+YYYY.MM.dd}"
        document_type => "logs_type"
    }
}
# 方式2：( 推荐使用ruby插件进行时间的解析，它解决了时区的问题 )
filter {
    ruby {
            code => "event['index_day'] = event['@timestamp'].localtime.strftime('%Y.%m.%d')"
    }
}
# 输出:
{
       "message" => "test",
      "@version" => "1",
    "@timestamp" => "2015-03-30T05:27:06.310Z",
          "host" => "BEN_LIM",
     "index_day" => "2015.03.29"
}

# logstash的input中的路径匹配的几种方式：
"/var/log/*.log"            # 在指定的路径中匹配以.log结尾的日志文件。
"/var/log/**/*.log"         # 匹配以指定路径下的子目录中的.log结尾的日志文件。
"/path/to/logs/{app1,app2,app3}/data.log"   # 匹配指定路径下的app1，app2和app3子目录中的应用程序日志文件。

# 在logstash的配置文件中引用变量的方式: "%{[varname]}，若引用系统的环境变量则: "${TCP_PORT:default_value}"
$ export ENV_TAG="tag2"

filter {
  mutate {
    add_tag => [ "tag1", "${ENV_TAG}" ] # 使用系统环境变量设置标签值
  }
}

output {
  elasticsearch {
    action => "%{[@metadata][action]}"
    document_id => "%{[@metadata][_id]}"
    hosts => ["example.com"]
    index => "index_name"
    protocol => "http"
  }
}

# Example:
input{
    kafka {
        bootstrap_servers => "10.0.0.3:9092"    # Kafka Address
        group_id => "logstash"                  # 要启用消费组，同组的消费者间"竞争"消费相同主题的1个消息
        topics => "ES"                          # 消费主题，生产环境中可使用列表类型来订阅多个主题
        consumer_threads => 2 
        decorate_events => true                 # 将当前topic、offset、group、partition等信息也写入message
        auto_commit_interval_ms => 1000         # 消费间隔，毫秒
        auto_offset_reset => latest             # 从最后消费
        codec => "json"                         # 将Filebeat传输的消息解析为JSON格式
    }
}

filter{
    grok {
        match => { 
            # Grok从message语义中按Patterns获取并分割成Key，其表达式很像C语言中的宏定义
            "message" => '%{IP:client} - \[%{DATA:time}\] "%{DATA:verb} %{DATA:url_path}
            %{DATA:httpversion}" %{NUMBER:response} %{NUMBER:} "-" \"%{DATA:agent}\"
            "-" \"%{NUMBER:request_time}\" -' 
        }
    }
    mutate{ 
        remove_field => ["tags","topic","source","version","name"]  # 删除Logstash中部分不需要的"语义"Key
        add_field => [ "log_ip", "10.0.0.3" ]                       # 添加指定KEY
    }
}

output{
    if [type] == "log" {
        elasticsearch {
            hosts => ["10.0.0.3:9200"]          # 会根据请求体中提供的数据自动创建映射 (由Logstash端创建)
            index => "es"
            timeout => 300
            flush_size：100                     # 默认500，logstash攒够500条数据再一次性向es发送
            idle_flush_time：2                  # 默认1s，如果1s内没攒够500条还是会一次性将攒的数据发出去给es
        }
    }
    stdout {
        codec => "rubydebug"
    }
}

# execute ...
cd ~/logstash
nohup bin/logstash -f run-configs/demo.config \
--path.data=run.data/demo/ -l run-logs/demo/ --node.name=demo -u 200 -b 2000 &

# -u 提交间隔
# -b 每次提交的数量
# –configtest 或 -t            测试配置文件的语法
# –pipeline-workers 或 -w      运行 filter / output 的pipeline线程数，默认是CPU核数
# –pipeline-batch-size 或 -b   
# 每个pipeline线程在执行具体的filter和output前最多能累积的日志条数。默认125条。越大性能越好，但会消耗更多JVM内存
# –pipeline-batch-delay 或 -u  
# 每个pipeline线程在打包批量日志时最多等待几毫秒，默认5ms
```
#### Kibana 监控 Logstash
```bash
# 在logstash/config/logstash.yml中增加如下：
# logstash把自身监控数据发送到es的index中，kibana读取该index获取数据
xpack.monitoring.enabled: true
xpack.monitoring.collection.interval: 10s
xpack.monitoring.elasticsearch.url: http://172.19.52.87:9211    #ES节点地址
http.host: "172.19.72.65"   #本机地址
```
#### logstash 从日志获取时间
```bash
# 配置：
input { stdin { } }
filter {
    grok { match => [ "message", "%{HTTPDATE:[@metadata][timestamp]}" ] }
    date { match => [ "[@metadata][timestamp]", "dd/MMM/yyyy:HH:mm:ss Z" ] }
}
output {
    stdout { codec => rubydebug }
}

# 输出：
$ bin/logstash -f ../test.conf
Pipeline main started
02/Mar/2014:15:36:43 +0100
{
    "@timestamp" => 2014-03-02T14:36:43.000Z,
      "@version" => "1",
          "host" => "example.com",
       "message" => "02/Mar/2014:15:36:43 +0100"
}
```
#### logstash piplines.yml
```yml
# 当logstash有很多个input类型需要处理，或者说要在同一进程中运行多个管道时:
# Logstash提供了一种通过名为pipelines.yml的配置文件来完成此操作的方法
# 为更方便管理，需要使用一个.conf(input->filter->output)配置文件来对应一个pipeline。
# 在不带参数的情况下启动Logstash时，它将读取pipelines.yml文件并实例化文件中指定的所有管道
# 当使用-e或-f时，Logstash会忽略pipelines.yml文件并记录警告

- pipeline.id: nginx_local
  pipeline.workers: 1
  path.config: "/usr/local/pkg/logstash/conf.d/nginx_local.conf"

- pipeline.id: nignx_kibana
  pipeline.workers: 1
  path.config: "/usr/local/pkg/logstash/conf.d/kibana_nginx.conf"

# pipeline.id
# 标识位，用于区分不同的pipeline。
# 如果所有的conf配置文件都使用一个id的话，那么input数据流就会流进各个output中。从而导致所有index数据一致。

# path.config
# 每一个不同id位的conf生效文件。绝对路径

# 测试一下：bin/logstash --config.reload.automatic
```
#### Java堆栈跟踪 / 多行日志处理
```bash
# Java堆栈跟踪由多行组成，每行以最后一行开头，如下例所示：
Exception in thread "main" java.lang.NullPointerException
        at com.example.myproject.Book.getTitle(Book.java:16)
        at com.example.myproject.Author.getBookTitles(Author.java:25)
        at com.example.myproject.Bootstrap.main(Bootstrap.java:14)
# 要将这些行整合到Logstash中的单个事件中，请对多行编解码器使用以下配置：
input {
  stdin {
    codec => multiline {        #此配置将以空格开头的所有行合并到上一行
      pattern => "^\s"
      what => "previous"
    }
  }
}

# 来自Elasticsearch等服务的活动日志通常以时间戳开始，然后是关于特定活动的信息，如下例所示：
[2015-08-24 11:49:14,389][INFO ][env ] [Letha] using [1] data paths, mounts [[/
(/dev/disk1)]], net usable_space [34.5gb], net total_space [118.9gb], types [hfs]
# 要将这些行整合到Logstash中的单个事件中，请对多行编解码器使用以下配置：
input {
  file {
    path => "/var/log/someapp.log"
    codec => multiline {
      pattern => "^%{TIMESTAMP_ISO8601} "
      negate => true
      what => previous
    }
  }
}
```
#### Kibana ( X-pack )
```bash
xpack.monitoring.elasticsearch.url: "http://10.40.23.79:9200" 
# xpack.monitoring.elasticsearch.username: "logstash_system" 
# xpack.monitoring.elasticsearch.password: "changeme"
```
#### logstash 参数说明
```bash
--node.name NAME  #指定此Logstash实例的名称。 如果没有赋值，它将默认为当前主机名。
-f, --path.config CONFIG_PATH   #从特定文件或目录加载Logstash配置。 如果给出了一个目录，那么该目录中的所有文件将按字典顺序连接，然后解析为一个配置文件。 不支持多次指定此标志。 如果多次指定此标志，则Logstash会使用最后一次出现（例如，-f foo -f bar与-f bar相同）。
#你可以指定通配符（globs），任何匹配的文件将按照上面描述的顺序加载。 例如，您可以使用通配符功能按名称加载特定文件：bin/logstash --debug -f '/tmp/{one,two,three}'使用此命令，Logstash会连接三个配置文件/tmp/one，/tmp/two和/tmp/three，并将其解析为单个配置。
-e, --config.string CONFIG_STRING   #使用给定的字符串作为配置数据。 与配置文件相同的语法。 如果没有指定输入，则使用以下内容作为默认输入：input {stdin {type => stdin}}，如果没有指定输出，则使用以下内容作为默认输出：output {stdout {codec => rubydebug}}。 如果您希望使用这两个默认值，请使用-e标志的空字符串。 缺省值是零。
--modules  #启动指定的模块。 与-M选项一起使用可将值分配给指定模块的默认变量。 如果在命令行中使用了--modules，那么logstash.yml中的任何模块都将被忽略，其中的任何设置都将被忽略。 这个标志与-f和-e标志是互斥的。 只能指定-f，-e或--modules之一。 可以通过用逗号分隔多个模块，或通过多次调用--modules标志来指定多个模块
-M, --modules.variable   #为模块的可配置选项分配一个值。 对于Logstash变量，赋值变量的格式是-M“MODULE_NAME.var.PLUGIN_TYPE.PLUGIN_NAME.KEY_NAME = value”。 对于其他设置，它将是-M“MODULE_NAME.KEY_NAME.SUB_KEYNAME =值”。 -M标志可以根据需要多次使用。 如果未指定-M选项，则将使用该设置的默认值。 -M标志仅与--modules标志结合使用。 如果--modules标志不存在，它将被忽略。
-w, --pipeline.workers COUNT  #设置要运行的管道worker的数量。 此选项设置将并行执行管道的过滤和输出阶段的工作人员数量。 如果发现事件正在备份，或CPU未饱和，请考虑增加此数字以更好地利用机器处理能力。 默认值是主机CPU内核的数量。
-b, --pipeline.batch.size SIZE  #该选项定义了在尝试执行过滤器和输出之前，单个工作线程从输入中收集的最大事件数量。 默认是125个事件。 较大的批量大小一般来说效率更高，但是以增加的内存开销为代价。 您可能必须通过设置LS_HEAP_SIZE变量来有效使用该选项来增加JVM堆大小。
-u, --pipeline.batch.delay DELAY_IN_MS  #在创建管道批次时，轮询下一个事件需要多长时间。 此选项定义在将过小的批次分配给过滤器和工作人员之前轮询下一个事件时需要等待多长时间（以毫秒为单位）。 默认是250ms。
--pipeline.unsafe_shutdown   #强制Logstash在关机过程中退出，即使内存中仍存在飞行事件。 默认情况下，Logstash将拒绝退出，直到所有收到的事件都被推送到输出。 启用此选项可能会导致关机期间数据丢失。
--path.data PATH     #这应该指向一个可写的目录。 Logstash会在需要存储数据时使用这个目录。 插件也可以访问这个路径。 默认值是Logstash home下的数据目录。
-p, --path.plugins PATH   #一个找到自定义插件的路径。 这个标志可以多次给定，以包含多个路径。 预期插件位于特定的目录层次结构中：PATH/logstash/TYPE/NAME.rb其中TYPE是输入，过滤器，输出或编解码器，NAME是插件的名称。
-l, --path.logs PATH   #目录将Logstash内部日志写入。
--log.level LEVEL   #设置Logstash的日志级别。 可能的值是：fatal，error,warn,info,debug,trace
--config.debug   #将完全编译的配置显示为调试日志消息（您还必须启用--log.level = debug）。 警告：日志消息将包括以明文形式传递给插件配置的所有密码选项，并可能导致明文密码出现在您的日志中！ 
-i, --interactive SHELL   #Drop to shell instead of running as normal. Valid shells are "irb" and "pry".
-V, --version   #版本信息
-t, --config.test_and_exit  #检查配置的有效语法，然后退出。 请注意，grok模式不检查与此标志的正确性。 Logstash可以从目录中读取多个配置文件。 如果将此标志与--log.level = debug结合使用，则Logstash将记录组合的配置文件，并使用它来自的源文件注释每个配置块。
-r, --config.reload.automatic   #监视配置更改，并在配置更改时重新加载。 注：使用SIGHUP手动重新加载配置。 默认值是false。
--config.reload.interval RELOAD_INTERVAL   #轮询轮询配置位置以进行更改的频率。 默认值是“3s”。
--http.host HTTP_HOST   #Web API绑定主机。 此选项指定度量标准REST端点的绑定地址。 默认值是“127.0.0.1”。
--http.port HTTP_PORT   #Web API http端口。 此选项为指标REST端点指定绑定端口。 默认是9600-9700。 该设置接受9600-9700格式的范围。 Logstash会拿起第一个可用的端口。
--log.format FORMAT    #指定Logstash是否应以JSON形式（每行一个事件）或纯文本（使用Ruby的Object＃inspect）编写自己的日志。 默认是“plain”。
--path.settings SETTINGS_DIR   #设置包含logstash.yml设置文件的目录以及log4j日志记录配置。 这也可以通过LS_SETTINGS_DIR环境变量来设置。 默认是Logstash home下的config目录
-h, --help   #打印帮助
```