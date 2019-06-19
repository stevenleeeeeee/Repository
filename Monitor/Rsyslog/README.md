`日志流向:   Rsyslog ---> Kafka ---> Logstash ---> Elasticsearch ---> Kibana `

```txt
Rsyslog已发展几十年，目前已支持3种不同的配置格式：

    1、basic: 以前称为 sysklogd 格式，是最常用于表达基本内容的格式，其语句适合单行的位置，源于最初的syslog.conf格式
              其最常见的用例是匹配 "设施.严重性" 并将匹配的消息写入日志文件
              Example： mail.info   /var/log/mail.log   <--- ( format: 选择器.操作 动作 )
                        mail.err    @@server.example.net
                        注：对于任何更高级的功能，应该使用 advanced 格式!

    2、advanced:   以前称为 RainerScript 格式，此格式首先在 version 6 提供，并且是当前最佳和最精确的格式
                   这种新的样式格式专门针对更高级的用例，如：转发到可能部分脱机的远程主机
                   Example:  mail.info action(type="omfwd" protocol="tcp" queue.type="linkedList")
                   注：Action对象描述了对消息的处理方式。它们通过输出模块 (以om开头的模块是输出专用模块) 实现 ( 翻译 )

    3、obsolete legacy:   以前简称为 legacy 格式，正如其名称所暗示的那样已过时

    实质上以 "$" 符开头的单行上写的所有内容都是传统的格式，鼓励这种格式的用户迁移到 basic 或 advanced 格式
----------------------------------------
Rsyslog的日志处理流程：
    1. 消息在输入模块的帮助下输入rsyslog。然后它们被传递到规则集，其有条件地应用规则
    2. 当规则匹配时，消息将传输到某个操作
    3. 操作会对消息执行某些操作，例如将其写入文件、数据库或转发到远程主机
```
#### 基础
```bash
#格式：（服务名称[.=!]信息等级）
    .               从指定等级开始
    =               指定等级
    !               排除等级
    
#等级：
    debug           调试信息
    info            基本信息
    notice          除info外需注意信息
    warning(warn)   警告信息，可能有问题但还不至于影响到服务
    err(error)      错误信息
    crit            严重错误
    alert           严重警告
    emerg(panic)    崩溃状态
    none            不记录...
    *               所有级别（星号代表所有设施或所有优先级，具体取决于它出现在"."的位置）
----------------------------------------
#备忘：
# 运行："rsyslogd -N 1" 检查conf文件语法，运行："rsyslogd -dn" 查看日志输出结果
# 每个输入都需要加载输入模块并为其定义一个监听器
# 输出也称为动作! 通过 action(type="type" ...) 调用动作。type指定要调用的插件的名称（如：omfile / omkafka ）
# 可在每个条目前加上减号 "-" 以避免在出现每个消息后立即同步文件（异步当时写入日志文件）
# 可使用分号 ";" 分隔符为多个选择器指定单个操作
# 若希望 syslogd 忽略此优先级和所有更高优先级，可以在优先级前加感叹号: ！
# 若希望 syslogd 仅忽略此单个优先级，甚至可以同时使用感叹号和等式符号: mail=!info
# 将消息转发到其他主机，请在主机名前添加 @、@@ (分别代表UDP/TCP方式传输)
# 紧急消息通常发送给当前在线的所有用户，此时应使用星号，如： *.emerg   *
# call 语句用于将规则集绑定在一起。它以通常的编程语言 call 语句为模型，其可用于调用任何类型的规则集
# 若规则集已分配队列，则该消息将发布到该队列并异步处理，否则将同步执行并当规则集完成执行后，再返回到调用处继续向下执行
# call 语句替换了已弃用的 omruleset 模块，并且以更有效的方式工作
# 规则集和规则构成了 rsyslog 处理的基础。简而言之规则就是是rsyslog处理特定消息的方式
# 规则集一般需要 "绑定"（或称分配）到特定的输入

Example:

    *.=crit;kern.none   /var/adm/critical           #存储优先级为crit的所有消息，但不包括任何内核消息（none即不记录）
    kern.*              /var/adm/kernel             #将内核所有级别的消息写入到文件
    kern.crit           @finlandia                  #将内核指定级别的消息重定向到远程主机
    kern.crit           /dev/console                #将内核指定级别的消息重定向到控制台
    kern.info;kern.!err /var/adm/kernel-info        #将除err级别的信息保存到文件（使用 ! 进行过滤）
    mail,news.=info    -/var/adm/info               #提取mail.info或news.info中的所有消息（"-"表示异步方式）
    *.=info;*.=notice;mail.none /var/log/messages   #将所有带有info或notice优先级的消息记录到文件，但mail设施的除外
    *.=emerg            :omusrmsg:*                 #将所有紧急消息写入所有当前登录的用户：(多个用户时使用逗号分隔)

    #调用插件的一般例子（老版本的格式）： --->  设施.级别    :模块名:参数;模板 
    *.*                 :ommysql:dbhost,dbname,dbuser,dbpassword;dbtemplate     #写入Mysql数据库

    *.alert      root,joey            #将所有优先级警报或更高级别的消息定向到用户（如果他们已登录）

    *.*       @192.168.0.10           # 单个符号表示消息将通过UDP协议
    *.*       @192.168.0.10:10514     # 带端口号
    *.*       @@192.168.0.10          # TCP

    *.*       @@(o,z9)192.168.0.1:1470  #消息通过TCP转发到目的IP:Port，并且最大的压缩级别
    #使用TCP传输时，压缩也会打开syslog-transport-tls框架:（o选项的作用）

    *.*       ^/Path/Scripts;template           #调用SHELL执行，程序将模板生成的消息作为唯一的命令行参数传递
    
    *.=crit :omusrmsg:rger                      #You can have multiple actions for a single selector 
    & root
    & /var/log/critmsgs

    *.=crit :omusrmsg:rger                      #Using multiple actions per selector (同时指定多个操作)
    *.=crit root
    *.=crit /var/log/critmsgs

    $template <模板名称>,"<%PRI%>%TIMESTAMP% %syslogtag%%msg%"
    *.*  @192.168.0.1;<模板名称>                #在对消息传输之前调用模板先进行处理

    *.* /var/log/file1                                  # 传统方式
    if $msg contains 'error' then /var/log/errlog       # 基于表达式的方式 ( 判断消息内容是否含有 error 关键字 )

    #基于表达式判断当消息是从local0发送且消息内容以 DEVNAME 开头且含有 error1 或 error0 关键字时才进行写入
    if $syslogfacility-text == 'local0' \       #注意此部分需要全部在一行!，虽然例子中进行了折行
        and $msg startswith 'DEVNAME' \
        and ($msg contains 'error1' or $msg contains 'error0') \
        then /var/log/somelog

    #若想存储除"error1"或"error0"之外的所有消息: （ 使用not进行反向匹配处理 ）
    if $syslogfacility-text == 'local0' \
        and $msg startswith 'DEVNAME' \
        and not ($msg contains 'error1' or $msg contains 'error0') \
        then /var/log/somelog

    #若要进行不区分大小写比较，请用 "contains_i" 代替 "contains"、 "startswith_i" 代替 "startswith"
    #基于表达式的过滤器当前不支持正则表达式! 稍后在函数支持添加到表达式引擎时将添加这些内容
    #原因是正则表达式将是一个单独的可加载模块，在实现之前需要一些更多的先决条件


#对日志内容/属性的比较操作:
contains	    #匹配提供的字符串值是否是属性的一部分，如果不区分大小写，使用contains_i
isequal	        #比较属性和值是否相等
startswith	    #属性是否以指定字符串开始(startswith_i)
regex	        #正则表达式(POSIX BRE 基本正则)匹配
ereregex	    #正则表达式(POSIX ERE 扩展正则)匹配
isempty	        #判断属性是否为空，不需要 value
#Example：
    :msg, contains, "error"
    :hostname, isequal, "host1"
    :msg, !regex, "fatal .* error"

#控制结构 Demo：
if ($msg contains "important") then {
   set $.foo = $.bar & $.baz;
   #每个ACTION后面都可跟1个模板名称。如果有则用于消息格式化否则使用硬编码的默认模板进行操作
   action(type="omfile" file="/var/log/important.log" template="outfmt")
} else if ($msg startswith "slow-query:") then {
   action(type="omfile" file="/var/log/slow_log.log" template="outfmt")
} else {
   set $.foo = $.quux;
   action(type="omfile" file="/var/log/general.log" template="outfmt")
}

#遍历数组，下面的collection变量是数组 ---> [1, "2", {"a": "b"}, 4]
foreach ($.i in $.collection) do {
   ...
}

foreach ($.quux in $!foo) do {
   action(type="omfile" file="./rsyslog.out.log" template="quux")
   foreach ($.corge in $.quux!bar) do {
      reset $.grault = $.corge;
      action(type="omfile" file="./rsyslog.out.log" template="grault")
      if ($.garply != "") then
          set $.garply = $.garply & ", ";
      reset $.garply = $.garply & $.grault!baz;
   }
}

# Data items in rsyslog are called "properties". They can have different origin
# The most important ones are those that stem from received messages. But there are also others
# Whenever you want to access data items, you need to access the respective property
# Rsyslog中的属性即：Rsyslog Properties。通过Rsyslog发送日志的时候不仅只发送日志原文，它还会发送和日志相关的一些属性
# 举例，当发送一条日志 "wang yu"，那么这条日志的属性大致如下：
{ 
    "msg": "wang yu", 
    "rawmsg": "wang yu", 
    "timereported": "2018-01-15T19:40:20.462759+08:00", 
    "hostname": "log", 
    "syslogtag": "a_test",  #下游接收时可以根据syslogtag属性，其依据在上游配置imfile时添加的tag来区分不同的日志文件!
    "inputname": "imfile",  #  如：input(type="imfile" File="/data/test_1.log" tag="test_1")  <---
    "fromhost": "", 
    "fromhost-ip": "", 
    "pri": "133", 
    "syslogfacility": "16", 
    "syslogseverity": "5", 
    "timegenerated": "2018-01-15T19:40:20.462759+08:00", 
    "programname": "a_test", 
    "protocol-version": "0", 
    "structured-data": "-", 
    "app-name": "a_test", 
    "procid": "-", 
    "msgid": "-", 
    "uuid": null, 
    "$!": null
}

#部分Rsyslog自带属性：( data items在rsyslog中叫做：properties，Message Properties)
    msg                 #匹配 message 中的 msg 部分
    hostname            #消息发送方主机名
    source              #发送方主机别名
    fromhost            #收到消息的来源的主机名（在中继链中，这是紧接在我们面前的系统，不一定是原始发送者）
    fromhost-IP         #与fromhost相同，不过获取的是ip。本地输入如 imklog 在此属性中使用 ---> 127.0.0.1
    syslogtag           #来自消息的Tag ( 即标签 ) message 的 tag
    PROGRAMNAME         #来自消息的Tag，但它是标签的"静态"部分，例如tag是 named[123456] 则programname是: named
    #例：在输入端打标签：$InputFileTag APPNAME / 接收端匹配：if $programname == 'APPNAME' then @<ip>:<port>;模板
                        # 1. end of tag
                        # 2. nonprintable character
                        # 3. ':'
                        # 4. '['
                        # 5. '/'
    PRI                 #PRI部分消息，未解码（单值） message的PRI 即优先级!
    pri-text            #消息的PRI部分采用文本形式，数字PRI附加在括号中（例如 "local0.err <133>"）
    app-name            #The contents of the APP-NAME field from IETF draft draft-ietf-syslog-protocol
    IUT                 #监视器InfoUnitType - 与 MonitorWare后端通信时使用（也适用于 Adiscon LogAnalyzer）
    syslogfacility      #来自消息的设施 - 以数字形式
    syslogfacility-text #来自消息的设施 - 以文本形式
    syslogseverity      #消息严重性 - 数字形式
    syslogseverity-text #消息严重性 - 文本形式
    timegenerated       #消息收到时的时间戳 ( message被本地syslog接收到的时间 )
    timereported        #消息体中的时间戳（分辨率取决于消息中提供的内容） 即 message 被创建的时间
    timestamp           #alias for timereported
    inputname           #生成消息的输入模块的名称（并非所有模块都必须提供此属性。如果未提供，则为空字符串）
    jsonmesg            #自rsyslog 8.3.0起（ 整个消息对象为JSON表示 ）

#系统属性：
    $myhostname		    #The name of the current host as it knows itself
    $bom			    #The UTF-8 encoded Unicode byte-order mask (BOM)
    $now			    #当前日期，格式 YYYY-MM-DD ,now是指当前message被处理的时间
    $year			    #当前年份 (4-digit)
    $month			    #当前月份 (2-digit)
    $day			    #当前日期 (2-digit)
    $hour			    #当前小时 (24 hour) time (2-digit)
    $hhour			    #From minute 0 to 29, this is always 0 while from 30 to 59 it is always 1.
    $minute			    #当前分钟 (2-digit)

#属性选项 (不区分大小写)：
    uppercase           #仅将属性转换为大写
    lowercase           #将属性文本仅转换为小写
    fixed-width         #更改toChar的宽度，以便在源字符串较短的情况下使用空格填充源字，最大值为toChar。在v8.13引入
    json                #对值进行编码以便在JSON字段中使用。这意味着根据JSON规范转义了几个字符如 US-ASCII LF 被"\n"替换
    jsonf[:outname]     #表示该属性应表示为JSON字段。这意味着不仅要编写属性，而且还要使用格式中的完整JSON字段
    csv                 #格式化RFC 4180中指定的CSV格式的结果字段（在所有修改之后）
    drop-last-lf            #例如： %msg:::drop-last-lf%    即：日志的完整消息文本，移出最後的換行符
    date-utc                #在输出数据之前将数据转换为UTC
    date-mysql              #格式为mysql日期
    date-rfc3164            #格式为RFC 3164日期
    date-rfc3164-buggyday   #类似date-rfc3164但模拟了常见的编码错误：RFC3164要求为1位数天写入1个空格，使用此选项将写入0
    date-rfc3339            #格式为RFC 3339日期
    date-unixtimestamp      #格式化为unix时间戳（自纪元以来的秒数）
    date-year
    date-month
    date-day
    date-hour
    date-minute
    date-second
    date-subseconds         #只是时间戳的亚秒（对于低精度时间戳，总是0）
    date-tzoffshour         #只是时间戳的时区偏移小时部分（2位数）
    date-tzoffsmin
    date-tzoffsdirection
    date-ordinal            #返回给定日期的序数，例如1月2日为2
    date-week
    date-wday
    date-wdayname
    escape-cc
    space-cc
    drop-cc
    compressspac
    sp-if-no-1st-sp
    secpath-drop
    secpath-replace         #用下划线替换字段内的斜杠（如"a/b"变为"a_b"）
```
#### 使用 stop 关键字截断处理流程...
```bash
# ... module loading ...
if $fromhost-ip == '192.0.2.1' then {
    action(type="omfile" file="/var/log/remotefile02")  # process remote messages
    stop    #是丢弃操作！其会将下面的配置信息不被匹配、执行 
}

# only messages not from 192.0.2.1 make it past this point          <-----------------
authpriv.*                            /var/log/secure
mail.*                                /var/log/maillog
*.emerg                               * # Everybody gets emergency messages
........... ( 略 )


#上游使用tag添加标识:
input(type="imfile" File="/data/test_1.log" tag="test_1")
input(type="imfile" File="/data/test_2.log" tag="test_2")
...

#下游使用syslogtag检查标识：
if ( $syslogtag == "test_1" ) then {
    action(...)
    stop
    ...
}

if ( $syslogtag == "test_2" ) then {
    action(...)
}
...
```
#### Rsyslog Modules ...
```bash
[root@localhost /]# grep "###" /etc/rsyslog.conf        #配置分段...
#### MODULES ####
#### GLOBAL DIRECTIVES ####
#### RULES ####
#### begin forwarding rule ###
#### end of the forwarding rule ###
[root@localhost /]# rpm -ql rsyslog | grep '/usr/lib64'
/usr/lib64/rsyslog
/usr/lib64/rsyslog/imdiag.so         #以 "i" 开头的是与输入相关的模块，如过滤工具
/usr/lib64/rsyslog/imfile.so
/usr/lib64/rsyslog/imjournal.so
/usr/lib64/rsyslog/imklog.so
/usr/lib64/rsyslog/immark.so
/usr/lib64/rsyslog/impstats.so
/usr/lib64/rsyslog/imptcp.so
/usr/lib64/rsyslog/imtcp.so
........... ( 略 )
/usr/lib64/rsyslog/omjournal.so      #以 "o" 开头的是与输出相关的模块...
/usr/lib64/rsyslog/ommail.so
/usr/lib64/rsyslog/omprog.so
/usr/lib64/rsyslog/omruleset.so
........... ( 略 )
```
#### Example:
```bash
#### MODULES ####
# 注（ 旧版本载入模块使用：$ModLoad <mod_name> ）
# The imjournal module bellow is now used as a message source instead of imuxsock.
$ModLoad imuxsock       #为本地系统日志记录提供支持（例如，通过记录器命令）
$ModLoad imjournal      #提供对systemd日志的访问
#$ModLoad imklog        #读取内核消息（同样从日志中读取）
#$ModLoad immark        #提供 --MARK-- 消息功能
$ModLoad ommysql        #提供将日志写入Mysql的功能

# 远程服务器接收日志 ( 老版本，新版兼容 )
$ModLoad imudp
$UDPServerRun 514                  #允许514端口监听使用UDP转发来的日志
$ModLoad imtcp
$InputTCPServerRun 514             #允许514端口监听使用TCP转发来的日志                       

#### GLOBAL DIRECTIVES ####        #定义日志格式默认模板

$WorkDirectory /var/lib/rsyslog    # Where to place auxiliary files 类似于Apache的主目录概念，其他目录相对于此

$ActionFileDefaultTemplate RSYSLOG_TraditionalFileFormat    # Use default timestamp format
   
$IncludeConfig /etc/rsyslog.d/*.conf                        #载入配置片段

# Turn off message reception via local log socket。 local messages are retrieved through imjournal now.
$OmitLocalLogging on

$IMJournalStateFile imjournal.state                     # File to store the position in the journal

#### RULES ####                                         #格式：facility.level      target...

#关于内核的所有日志都放到/dev/console (控制台)            
#kern.*                                                 /dev/console

# 发送给用户（需要在线才能收到）
*.*                                                     root,user1,user2

#忽略所有local3类型的所有级别的日志
local3.*                                                ~   #波浪号表示丢弃

#这里的 - 表示使用异步方式记录（因为日志一般比较大）
mail.*                                                  -/var/log/maillog

# 记录所有设施 >=info 级别的信息到: /var/log/messages，但mail信息，authpriv信息和crond相关的信息除外
*.info;mail.none;authpriv.none;cron.none                /var/log/messages

#文件名可以是静态的（始终相同）或动态的 （根据收到的消息而不同）
#使用定制的模板（日志文件名称）将local5的所有信息追加到此模板定义的文件名...
$template DynamicFile,"/var/log/test_logs/%$YEAR%_%$MONTH%_%$DAY%-local5.log"
local5.* -?DynamicFile              #通过指定问号"?"而不是斜杠来说明是动态生成的文件名，?后跟此动态名称的模板，- 为异步
local5.* -?DynamicFile;Mytemplate   #也可以在分号后面指定输出格式的模板

#将日志写入mysql数据库...（需加载mysql模块：$ModLoad ommysql）
#*.*      :ommysql:database-server,database-name,database-user,database-password
DEMO.*    :ommysql:127.0.0.1,Syslog,syslogwriter,topsecret

# ### begin forwarding rule ###
# An on-disk queue is created for this action. If the remote host is
# down, messages are spooled to disk and sent when it is up again.
#$ActionQueueFileName fwdRule1 # unique name prefix for spool files
#$ActionQueueMaxDiskSpace 1g   # 1gb space limit (use as much as possible)
#$ActionQueueSaveOnShutdown on # save messages to disk on shutdown
#$ActionQueueType LinkedList   # run asynchronously
#$ActionResumeRetryCount -1    # infinite retries if host is down
# remote host is: name/ip:port, e.g. 192.168.0.1:514, port optional
#*.* @@remote-host:514
# ### end of the forwarding rule ###
```
#### 模板 template
```bash
#模板由 template() 指定（新版），也可以通过 $template legacy 指定（传统），模板的关键元素是 rsyslog 属性!

#介绍：
#模板允许设置自己的格式，例如用来生成动态的日志文件名称，每个rsyslog的输出都会用到Templates
#可指定多个模板，使得不同日志输出到不同模板，若未指定 Templates 则使用默认的 Templates
#可用老版本的配置语法： $template，也可使用新版本的配置语法: template()，但是官方建议使用新语法

# 系统中有一些内置的使用RSYSLOG_开头的保留模板，如：
#   RSYSLOG_TraditionalFileFormat
#   RSYSLOG_FileFormat 
#   RSYSLOG_TraditionalForwardFormat
#   RSYSLOG_SysklogdFileFormat 
#   RSYSLOG_ForwardFormat 
#   RSYSLOG_SyslogProtocol23Format 
#   RSYSLOG_DebugFormat 

#定义模板的三种格式：
 $template name,param[,options]                 #旧版本格式
 template(parameters)                           #新版本格式 ( parameter主要的2个参数：name、type )
 template(parameters) { list-descriptions }     #新版本的扩展格式

#关键参数说明：
# name：指定一个模板名称
# type：指定模板的类型，不同类型指定了不同的模板指定方法，一般有 list、subtree、string、plugin 四中类型！
# 其中string、list两种类型最常用，两者区别如下：
# string类型是老版本的配置方式，允许使用Rsyslog提供的属性对日志进行格式化，语法如下：
# template(name="xxx" type="string" string="xxx")
# list类型可以把固定不变的内容和动态变化的内容分开:  ( list类型的template比string的更加清晰和简洁 )
# 静态内容用: constant(value="固定不变的内容" ) 表示
# 动态内容用: property(name="属性名" property statement) 表示

#调用模板的格式：
#下面的例子为分离各client汇报上来的数据，存放在不同的目录而使用模板技术:
#老版本:
#$template TmplMsg, "/var/log/rsyslog_custom/%HOSTNAME%/%PROGRAMNAME%.log" 
#新版本:
template(
    name="FTM66666"
    type="string"
    string="/var/log/rsyslog_custom/%fromhost-ip%/%$YEAR%/%$MONTH%/%$DAY%/%PROGRAMNAME%.log"
) 
*.*   ?FTM66666[;Template]

#Example:
$template SpaceTmpl,"%msg:2:$%\n" #定义模块，用于去掉占用开头2个字符的空格 (以$开头为老版本使用的格式)
$template ChannelmanageErrorDynaFile,"/app/rsyslog/%fromhost-ip%/channelmanage/error_%$YEAR%-%$MONTH%-%$DAY%.log"
:rawmsg,contains,"channe-10.139.54.53-8080" ?ChannelmanageInfoDynaFile;SpaceTmpl

template(name="tpl3" type="string" string="%TIMESTAMP:::date-rfc3339% %HOSTNAME% %syslogtag%%msg:::sp-if-no-1st-sp%%msg:::drop-last-lf%\n")
template(name="TraditionalFormat" type="string" string="%timegenerated% %HOSTNAME% %syslogtag%%msg%\\n")
template(name="DynFile" type="string" string="/var/log/system-%HOSTNAME%.log")
# %%  ---> 之间的大写变量是可以替换的
# ::: ---> 后面跟的是对应的一些属性

    #常量和属性语句，常量描述常量文本、属性描述属性访问
    #以下list类型可理解为：---> ["Syslog MSG is: '","%msg%",',"%timereported%","\n"] （也可理解为构成一个字串形式）
    template(name="tpl1" type="list") {
         constant(value="Syslog MSG is: '")
         property(name="msg")
         constant(value="', ")
         property(name="timereported" dateFormat="rfc3339" caseConversion="lower")
         constant(value="\n")
    }

    # name - 要获取的属性值的名称?
    # value - 定义一个常量值
    # outname - 输出字段名称（用于结构化输出）
    # dateformat - 使用的日期格式（仅适用于与日期相关的属性）
    # caseconversion - 转换文本大小写，支持的参数有："lower"、"upper"
    # securepath - 用于创建适合在dynafile模板中使用的路径名
    # format - 以字段为基础指定格式。支持的值是：
    #     "csv"       用于生成csv-data时使用
    #     "json"      格式化正确的json内容 (但没有字段标题)
    #     "jsonf"     格式化为完整的json字段 ( 完整的 )
    #     "jsonr"     避免双重转义值，但使json字段安全
    #     "jsonfr"    是"jsonf"和"jsonr"的组合
    # position.from - 从这个位置开始获取子串（1是第一个位置）
    # position.to - 获取到此位置的子字符串
    # position.relativeToEnd - from和to位置相对于字符串的结尾而不是通常的字符串开头。（rsyslog v7.3.10）
    # compressspace - 将字符串内的多个空格（US-ASCII SP字符）压缩为单个空格
    # field.number - 获取此字段匹配
    # field.delimiter - 字段提取的分隔符字符的十进制值
    # regex.expression - 要使用的表达式
    # regex.type - ERE或BRE
    # regex.nomatchmode - 如果我们没有匹配怎么办
    # regex.match - 匹配使用
    # regex.submatch - 要使用的子匹配
    # droplastlf - 如果存在则丢弃尾随LF

    template(name="outfmt" type="list") {
        property(name="$!usr!msgnum")
        constant(value="\n" outname="IWantThisInMyDB")
    }

    #要生成常量json字段，可以使用format参数
    template(name="outfmt" type="list" option.jsonf="on") {
       property(outname="message" name="msg" format="jsonf") #outname相当于key，输出字段名称（用于结构化输出）
       constant(outname="@version" value="1" format="jsonf") #在为结构化输出创建K/V树时将忽略没有"outname"的常量文本
    }   

    property(name="timereported" dateformat="year")         #此段模板内容将输出: YYYY-MM-DD
    constant(value="-")
    property(name="timereported" dateformat="month")
    constant(value="-")
    property(name="timereported" dateformat="day")

#每个ACTION后面都可跟1个模板名称。如果有则该模板用于消息格式化。否则使用硬编码的默认模板进行操作。

#新旧模板语法对比:
$template secureTemplate,"INSERT INTO var_log_secure (received_at, source_ip, source_hostname, logged_at, severity, service, message, severity_int, syslogtag) VALUES ('%timegenerated:::date-rfc3339%', '%fromhost-ip%', '%hostname%', '%timereported:::date-rfc3339%', '%syslogseverity-text%', '%programname%', '%msg%', '%syslogseverity%', '%syslogtag%')",STDSQL

template(name="secureTemplate" type="string" option.stdsql="on"
  string="INSERT INTO var_log_secure (received_at, source_ip, source_hostname, logged_at, severity, service, message, severity_int, syslogtag) values ('%timegenerated:::date-rfc3339%', '%fromhost-ip%', '%hostname%', '%timereported:::date-rfc3339%', '%syslogseverity-text%', '%programname%', '%msg%', '%syslogseverity%', '%syslogtag%')"
)

# 一般情况下的包含关系： input(rulese(action(Template)))  注：若配置文件中没有imput() 则整个Rsyslog上下文作为input！
```
#### Demo
```bash
#日志格式:
$EscapeControlCharactersOnReceive off     #关闭rsyslog默认转译ASCII<32的所有怪异字符，包括换行符等
$template nginx-zjzc01,"/rsyslog/data/nginx/zjzc/nginx_access01_log.%$year%-%$month%-%$day%" #定义TC 存放路径
$template nginx-zjzc02,"/rsyslog/data/nginx/zjzc/nginx_access02_log.%$year%-%$month%-%$day%" #定义TCBeta 存放路径
$template tocFormat,"%msg%\n"     #定义toc日志format
:rawmsg,contains,"nginx-zjzc01:"  -?nginx-zjzc01;tocFormat    #接受TC 日志，并应用tocFormat格式
:rawmsg,contains,"nginx-zjzc02:"  -?nginx-zjzc02;tocFormat    #接受TCBeta 日志，并应用tocFormat格式

#输出:
 www.zjcap.cn 10.168.29.17 10.171.246.184 [11/Aug/2016:12:02:20 +0800] "GET /wechat/images/index/anchor.27a8911e.png HTTP/1.1" - 304 0 "https://www.zjcap.cn/wechat/home.html?
useragent=ios_h5_zjcap&apiver=2&WKWebView=1" "ios_h5_zjcap" 0.001 -
 www.zjcap.cn 10.168.29.17 10.171.246.184 [11/Aug/2016:12:02:20 +0800] "GET /resources/images/icon/coupon.b9243e75.png HTTP/1.1" - 200 715 "https://www.zjcap.cn/resources/css/index.css?06212016" 
"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36" 0.001 -


%programname:F,59:3%               #使用分号作为分隔符，取第三列内容（推荐）
"%msg:1:2%"                        #读取从pos从1到2的数据
"%msg:::lowercase%"                #将整个消息转换为小写
"%msg:10:$%"                       #截取pos从10到最后的消息内容
"%msg:R:.*Sev:. \(.*\) \[.*–-end%" #取"*Sev:."到[.*之间。格式：R,<regexp-type>,<submatch>,<nomatch>,<match-number>
```
#### 属性替换及正则表达式
```bash
#通过将它们置于百分号之间来访问，属性可以由属性替换器修改.
%property:fromChar:toChar:options%
#FromChar和toChar用于构建子串:
#它们指定应复制的字符串中的偏移量，从1开始，需获取消息文本的前2个字符则："%msg:1:2%"
#如果不想指定from和to但又想指定选项，则仍需要包含冒号。例如将完整的消息文本转换为小写: "%msg:::lowercase%"
#如果想从一个位置提取直到字符串结尾，可以在toChar中放置符号 $ （如 %msg:10:$% ---> 从第10位提取到结尾）

#还支持正则表达式。要使用它需要在FromChar中放置1个"R"。这告诉rsyslog需要正则表达式而不是基于位置的提取。
#然后在toChar中提供实际的正则表达式。正则表达式后面必须跟字符串 "--end" 来表示正则表达式的结束，不会成为它的一部分
#如果使用正则表达式，则属性 replacer 将返回与正则表达式匹配的属性文本部分
#具有正则表达式的属性替换序列的示例是："%msg:R:.*Sev:. \(.*\) \[.*–-end%"

#可以在"R"之后指定一些参数。这些是逗号分隔的：R,<regexp-type>,<submatch>,<nomatch>,<match-number>
#regexp-type对于Posix基本正则表达式是"BRE"，对于扩展正则表达式是"ERE"。
#字符串必须以大写字母表示。默认值为"BRE"，以与不支持ERE的早期版本的rsyslog保持一致。
#子匹配标识要与结果一起使用的子匹配。支持单个数字。匹配 0 是完全匹配，而 1 到 9 是实际匹配。
#nomatch指定在未找到匹配项时应使用的内容

#如果表达式在字符串内出现多次，则 match-number 标识要使用的匹配项。注意：第一个是0号，第二个是1，依此类推，最多支持10个
#注意，在子匹配之前使用匹配编号会更自然，但这会破坏向后兼容性。因此必须在"nomatch"之后指定match-number。

#以下是ERE表达式的示例，该表达式从消息字符串中获取第一个子匹配，如果未找到匹配项，则将表达式替换为完整字段：
%msg:R,ERE,1,FIELD:for (vlan[0-9]\*):--end%     #若未匹配第一个分组则用"FIELD"字串代替

#这将获取所述表达式的第二个匹配的第一个子匹配：
%msg:R,ERE,1,FIELD,1:for (vlan[0-9]\*):--end%

#例：
%msg:R,ERE,1,FIELD:for (vlan[0-9]\*):--end%
%msg:R,ERE,1,FIELD,1:for (vlan[0-9]\*):--end%
"F,44" :
==》设置分隔符(用ACSII表示)，针对分隔符，在引用时，0代表没找到，匹配的实例从1开始数
%msg:F,59:3% :
==》以分号为分隔符，提取第三个区域的内容
"%msg:F,59,5:3,9%" :
==》以分号为分隔符，从第5个子串中，提取3-6位的字符
"%msg:F,32+:2%" :
==》如果多个分隔符(比如：日志中有n个空格作为分割，那么可以添加一个+)

---------------------------------------------------------------------

module(load="imfile" PollingInterval="10")
input(type="imfile" File="/path/to/file1" Tag="tag1" StateFile="statefile1" Severity="error" Facility="local7")  
action(type="omfwd" Target="192.168.0.1" Port="514" Protocol="tcp" )

当要截取输入日志内容的话，就需要用到过滤器例如：
$template mymark6,"%timestamp% %fromhost-ip% %msg:32:$%\n"
if $programname == 'test-run' then @@192.168.15.161:514;mymark6

当用到数据库并且默认的格式不符合我们的要求的话，我们就需要另外定义：
$template tpl6666,"insert into SystemEvents (Message, Facility, FromHost, Priority, DeviceReportedTime, \
ReceivedAt, InfoUnitID, SysLogTag) values (‘%msg%’, %syslogfacility%, ‘%HOSTNAME%’, %syslogpriority%, \
‘%timereported:::date-mysql%’, ‘%timegenerated:::date-mysql%’, %iut%, ‘%syslogtag%’)",SQL\

*.* :ommysql:localhost,Syslog,rsyslog,123456;tpl6666
```
#### 输出通道 outchannel
```bash
$outchannel name,file-name,max-size,action-on-max-size

#name       表示outchannel名称
#file-name  表示写入文件名
#max-size   表示写入最大的尺寸
#action-on-max-size 在达到最大尺寸的时候执行的动作，这个命令总是只有一个参数。

#Example:   *.* :omfile:$mychannel
```
#### 队列
```bash
#只要2个活动需松散耦合，Rsyslog就会使用队列。系统的一部分"产生"某些东西，而另一部分"消耗"
#"某事"通常是系统日志消息，但队列也可能用于其他目的。队列提供各种服务，包括支持多线程。

#最突出的例子是主消息队列。每当rsyslog收到消息时（例如，本地，通过UDP，TCP或以其他任何方式）
#它都会将这些消息放入主消息队列中。稍后，它由规则处理器出列，然后规则处理器评估要执行的操作
#在每个动作的前面还有一个队列，它将过滤处理与实际动作分离（例如，写入文件，数据库或转发到另一个主机）。
#注意：如果要修改规则集内的消息对象，则无法为其定义队列 ??!!

#【主消息队列】
#Rsyslog有1个主消息队列。所有的输入模块都要向其发送消息
#主消息队列工作程序根据Rsyslog.conf中指定的规则过滤（filter engine）消息后将它们派给各个所谓的操作队列
#消息到达操作队列后将从主消息队列中删除
#main队列(主消息队列) ---> 主要将input进rsyslog的数据放于其中，使其等待处理

#【操作队列】
#有多个操作队列，每个配置操作一个。默认情况下，这些队列以直接（非排队）模式运行
#操作队列是可由用户进行配置的，因此可以更改为最适合给定用例的任何内容（翻译）
#action队列 ---> 当message进入到main队列之后，filter engine从main队列读取并将message发到action队列
#等待action将数据通过各种不同的output发到其他日志中转介质
```
#### Rsyslog服务端根据发送端的标签生成存储路径
```txt
input(type="imfile"
      File="/tmp/logs/test.log"
      Tag="log@save;program;app1"
      stateFile="/var/lib/rsyslog/111.state"
)

template(name="common-template"
        type="string"
        string="/tmp/logs/%programname:F,59:2%/%fromhost-ip%/%programname:F,59:3%.%$now%.log"
)

if ( $programname startswith 'log@save') then {

    action(type="omfile"
           dynaFile="common-template"
           fileCreateMode="0644"
           DirCreateMode="0700"
           createDirs="on"
    )
    stop
}
```
#### 日志压缩
```bash
#!/bin/bash

#获取以前一天日志结尾的 yyyy-mm-dd.log 日志文件，并放到数组
LOGFILE=$(find . -name "*$(date '+%Y%m%d' -d '-1 day').log" -type f)

#并发20个bzip2进行日志压缩
echo ${LOGFILE[@]} | xargs -P 20 -n 1 bzip2 
```