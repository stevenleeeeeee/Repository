#### 基本使用
```bash
global (
    maxMessageSize="32m"
    workDirectory="/data1/sinawap/rsyslog"        #定义工作目录。列队写磁盘文件的存储文件夹
    preserveFQDN="on"
    action.reportSuspension="on"
)

main_queue (
    queue.filename="mainQ"
    queue.type="linkedlist"             #选择使用内存队列模式
    queue.size="600000"                 #队列大小
    queue.timeoutenqueue="1000"         #进队列超时时间（1000ms）
    queue.maxfilesize="512M"            #队列单文件尺寸大小
    queue.maxdiskspace="50G"            #限制磁盘队列大小，最大50G
    queue.dequeuebatchsize="50000"      #优化宽带，设置每批次传输元素量，尽可能每次传输更多的数据
    queue.workerthreads="4"             #队列工作线程数
    queue.workerthreadminimummessages="100000"
    queue.discardseverity="3"           #丢弃消息等级设定，数字越低丢的越多，设置为8代表禁止丢弃消息
    queue.highwatermark="480000"        #当内存队列数量达到设置的值时，开始回写磁盘
    queue.lowwatermark="120000"         #当内存队列小于设置的值时，停止回写磁盘
    queue.checkpointinterval="10"
    queue.timeoutshutdown="10"
    queue.timeoutactioncompletion="10"
    queue.timeoutworkerthreadshutdown="10"
    queue.saveonshutdown="on"

)

Module (load="imudp")	#载入UDP模块 ( 配置文件首先必须先配置模块 )
module(load="imfile" PollingInterval="5")  #PollingInterval 设置轮询间隔

Input (type="imudp" port="514")     # How to configure the input for rsyslog

# A filter always has, like a normal conditional sentence, an "if…then" part.
If $fromhost-ip == "172.19.1.135" then {
    Action(type="omfile" file="/var/log/network1.log") #操作关键字:"action"，动作类型 "omfile" 此模块用于输出到文件
}

#Example: 非syslog日志的转发，例如Tomcat应用的catalina日志:
input(
    type="imfile"
    #指定应监视的文本文件的路径和名称。文件名必须是绝对的。
    File="/var/log/foobar.log"
    #在提取的每条消息前设置个标签。如果想在标签后面加上冒号则必须设置，它不会自动添加 (服务端根据这个标签可以识别日志)
    Tag="catalina-10.139.54.53-8080"
    #rsyslog.conf中定义的rule名称
    Ruleset="remote" 
    #回写偏移量数据到文件间隔时间(秒)，根据实际情况而定
    PersistStateInterval="1" 
    #跟踪它当前在文件中的位置，此文件始终在rsyslog工作目录中创建（可通过$ WorkDirectory 配置）
    StateFile="/var/spool/rsyslog/statefile1"  # 新版本中不需要设置
    #提供同一设施的文件的alle日志消息，可选。默认所有消息都将设置为"local0"
    Facility="local7"
    #为文件的所有日志消息提供相同的严重性。这是可选的。默认所有消息都将设为"通知"。
    Severity="error"
)

local7.*  @192.168.1.25:514
```
#### 规则集 ruleset
```bash
#Rulesets内部包括了多条rule，一条rule（规则）就是rsyslog处理消息的一种方式
#一般来说，每个规则都包含一个过滤器以及当过滤器判断为True时要执行的一或多个操作 (每个规则包含filter和actions)
#可将传统的配置文件视为单个默认的规则集，它自动绑定到每个输入。
#过滤器:可像传统基于syslog优先级的过滤器一样简单（如 mail.info，也可像脚本式表达式一样复杂）
#动作:是对消息做某事的流程，如最基本的指定将消息写入某文件、将其转发到远程日志记录服务器等...
#官方强烈建议:高性能系统定义专用的规则集，每个输入使用一个专用队列。

#传统配置文件由一或多个这些规则组成:
#当消息到达时其从第1个规则开始（按rsyslog.conf中定义的顺序）并向下继续执行每个规则
#直到所有规则都已处理或发生所谓的"丢弃"操作 ( stop )，此时处理停止并丢弃消息（处理完最后1条规则后也会发生）
#用于处理不同消息格式的自定义消息解析器可以绑定到不同的规则集
#注意:如果要修改规则集内的消息对象，则无法为其定义队列 ??!!

#规则级的定义 Demo:
ruleset(name="rulesetname") {
    action(type="omfile" file="/path/to/file")
    action(type="..." ...)
    /* and so on... */
}

#Example1:
#if I want to bind a ruleset "rs1" to a input the line will look like this:
Module(load="imudp")
Ruleset(name="rs1") {    #定义规则集名称
    Action (type="omfile" file="/var/log/network1.log")  
    #A rulesset can consist of multiple rules, but without binding it to the input it is useless.
    #It can be bound to an input multiple times or even other rulesets can be called.
}
#将相应的接收器绑定到特定规则集，绑定到规则集是特定于输入的
Input(type="imudp" port="514" ruleset="rs1")    #通过input的rulesets属性，将输入流交给名为rs1的规则集处理
#"rs1"必须是在给出bind指令时已定义的规则集的名称

#将不同的输入流进入不同的队列实现并行处理，通常在ruleset或者action中配置，默认只有一个队列。例:
action(
    type="omfwd"
    target="192.168.2.11"
    port="10514"
    protocol="tcp"
    queue.filename="forwarding"
    queue.size="1000000"
    queue.type="LinkedList"
)

#Example3:
#默认情况下规则集没有自己的队列。它必须通过 $RulesetCreateMainQueue 指令激活 ( 传统 )
#或使用 rainerscript 格式 ( version 8+ )，这种格式是通过在规则集指令上指定队列参数来进行的，例:
ruleset(name="remote") {
    action( 
       type="omfwd"
       target="Rsyslog服务端主机IP"
       port="514"                                      #端口
       protocol="tcp"                                  #协议
       queue.type="linkedList"                         #使用基于内存方式的异步处理（队列类型） 
       queue.spoolDirectory="/app/wutongshu/rsyslog"   #队列目录
       queue.fileName="remoteQueue_10_139_54_53"       #队列名称
       queue.maxDiskSpace="5g"                         #队列占最大磁盘空间
       queue.saveOnShutdown="on"                       #若rsyslog关闭则保存内存数据
       action.resumeRetryCount="-1"                    #无限重试插入失败
    )
    stop        #停止针对消息向下继续执行
}


#注，调用规则集的关键字：call_indirect <ruleset_name>
```
#### 模板
```bash
#模板允许指定消息格式、也可用于动态生成日志文件名，或在规则中使用
template(name="ForwardFormat" type="string" string="<%PRI%>%TIMESTAMP:::date-rfc3339%%HOSTNAME%%syslogtag:1:32%%msg:::sp-if-no-1-SP%%MSG%")
#%syslogtag:1:32% --> 它指定获取标签特定范围内的信息，若要删除限制...只需删除它

template(name="LongTagForwardFormat" type="string" string="<%PRI%>%TIMESTAMP:::date-rfc3339%%HOSTNAME%%syslogtag%%msg:::sp-if-no-1st-sp%%MSG%")

#MSG与structured-data的区别：
# %MSG%变量代表了syslog协议的消息内容!
# %structured-data%有些log的内容使用方括号括上的，如checkpoint防火墙的log [action:denny ……]
# 这些属于%structured-data%，单独使用MSG是无法显示的!!!

#Example:
action(
    type="omfwd"
    Target="server.example.net"
    Port="10514"
    Protocol="tcp"
    Template="LongTagForwardFormat" #将转发操作绑定到定义的模板
)

#动态生成文件名:
template(name="DynFile" type="string" string="/var/log/system-%HOSTNAME%.log")  #目录/文件名部分可使用Rsyslog变量
```
#### TLS通过RELP保护系统日志 （ 包括c/s部分配置的demo ）
```bash
#在开始在任一计算机上配置rsyslog前，请确保已安装librelp（可能需要另外安装gnutls包）
./configure --prefix=/usr --enable-relp    #编译安装时需开启relp功能

#客户端配置:
#在配置文件开头有些global设置（global配置只能被设置1次并且随后不能重新设置）
maxMessageSize="25K"                  #可处理的单条日志大小，默认4K比较小，因为超出4K会被截断
global(net.aclResolveHostname=off)    #是否解析主机名到ip地址
global(net.enableDNS="on")            #是否开启dns
global(net.ipprotocol="ipv4-only")    #指定使用的协议，可以是ipv4-only，ipv6-only
global(debug.onShutdown="on")         #当为on时如果系统shutdown，rsyslog会记录系统debug信息

$InputFileTag teststring.com.cn:      #使得客户端在写入日志时附加标签字符串

module(load="imuxsock")         #提供本地系统日志记录，如支持使用logger命令模拟发送日志的功能（实际是发送到socket文件）
module(load="imklog")           #提供内核级别日志记录
#module(load"immark")           #提供标记message的能力
module(load="imudp")
module(load="omrelp")
input(type="imudp" port="514")
action(type="omrelp" target="192.168.233.144" port="2514" tls="on")

$IncludeConfig /etc/rsyslog.d/*.conf

# 以$开头的是遗留配置语句，某些插件和功能可能仍然只能通过旧格式提供! 所以还是要保留的
# ### begin forwarding rule ###
# An on-disk queue is created for this action. If the remote host is
# down, messages are spooled to disk and sent when it is up again.
#$WorkDirectory /var/lib/rsyslog     # where to place spool files ( 工作目录 )
#$ActionQueueFileName fwdRule1       # unique name prefix for spool files ( 工作目录下的队列文件名前缀 )
#$ActionQueueMaxDiskSpace 1g         # 1gb space limit (use as much as possible) ( 队列容量限制 )
#$ActionQueueSaveOnShutdown on       # save messages to disk on shutdown ( 当关闭Rsyslog时将行内存中的数据写入磁盘 )
#$ActionQueueType LinkedList         # run asynchronously ( use asynchronous processing )
#$ActionResumeRetryCount -1          # infinite retries if host is down ( 插入失败时进行不限次数的重试 )
# ### end of the forwarding rule ###

*.*   :omrelp:192.168.152.2:20514    #通过RELP模块使用TLS保护系统日志!

#服务端配置:
$AllowedSender       UDP,127.0.0.1,192.168.0.0/16   #限制允许的协议&来源地址
module(load="imuxsock")
module(load="imrelp" ruleset="relp")
input(type="imrelp" port="2514" tls="on")
ruleset(name="relp") {
    action(type="omfile" file="/var/log/relptls")
}
#请注意:  对于imrelp而言，只能将模块绑定到规则集，因此此类型的所有已创建侦听器都绑定到此单个规则集

# 一般情况下的包含关系： input(rulese(action(Template)))  注：若配置文件中没有imput() 则整个Rsyslog上下文作为input！
```
#### 将特定消息写入文件并丢弃它们
```bash
#在这个例子中，所有内容都首先写入 /var/log/other.log，然后才会再对消息内容进行检查。
#在后一种情况下，其中带有"错误"的消息将写入两个文件。

*.* /var/log/other.log

#Example1:
:msg, contains, "error" /var/log/error.log
& ~     #意思是消息执行到这里之后开始丢弃 (不做后续处理)

#Example2:
:msg, contains, "user nagios" ~     #消息中若包含user nagios关键字则忽略此记录
```
#### 将消息发送到 Rsyslog server
```bash
# this is the simplest forwarding action:
*.* action(type="omfwd" target="192.0.2.1" port="10514" protocol="tcp")
#上面等同于过时的遗留格式行: --->  *.* @@ 192.0.2.1:10514  #不要再使用它了！
#注意: 如果远程系统无法访问，处理将在此处阻塞并在一段时间后丢弃消息

#对以上问题来说更好的解决办法如下:
*.*  action(type="omfwd"
            target="192.0.2.2"
            port="10514"
            protocol="tcp"
            action.resumeRetryCount="100"       #在丢弃消息之前尝试连接100次 ( -1 特指为无限重试次数 ) 
            queue.type="linkedList"             #这将解除发送与其他日志记录操作的耦合，并防止远程系统无法访问时出现延迟
            queue.size="10000"
)
```
#### 从远程系统接收消息并存储到特定的文件
```bash
#version3之前的Rsyslog有个命令行开关 -r、-t 来激活远程监听，默认此开关仍然可用，并加载所需插件并使用默认参数对其进行配置
#但仍然需要在系统上存在插件。建议不要依赖兼容模式而是使用正确的配置

$ModLoad imtcp              #新版本：module(load="imtcp")
$InputTCPServerRun 10514    #新版本：input(type="imtcp" port="514")

# do this in FRONT of the local/regular rules
if $fromhost-ip startswith '192.0.1.' then /var/log/network1.log        #这里可以使用模板来动态生成文件名
&~

if $fromhost-ip startswith '192.0.2.' then /var/log/network2.log
&~

*.*         /var/log/syslog.log     #当以上匹配都无效时才进行以下的配置执行! 否则以下声明将忽略 ( &~ 的作用 )
*.emerg     *
authpriv.*  /var/log/secure
cron.*      /var/log/cron
mail.*      /var/log/maillog
*.info;mail.none;authpriv.none;cron.none      /var/log/messages
```
#### 为所有文件使用不同的日志格式 ( 模板 )
```bash
$template myFormat,"%rawmsg%\n"
$ActionFileDefaultTemplate myFormat  #将上面定义的新模板作为针对所有文件操作的默认模板。这使得无需使用任何单个操作行指定
#"rawmsg" ---> 包含rsyslogd接收的syslog消息的属性（从任何源"接收"，例如远程系统或本地日志套接字）
#字符串"\n"是换行符 (ASCII LF) 一个常量被添加到字符串中。通常日志行模板要以"\n"结尾，因为没有它所有日志记录都将写入一行!


*.info;mail.none;authpriv.none;cron.none      /var/log/messages

authpriv.*              /var/log/secure

mail.*                  /var/log/maillog

cron.*                  /var/log/cron       #若不指定ActionFileDefaultTemplate则需手动指定:/var/log/cron;myFormat

*.emerg                 *                   #Everybody gets emergency messages

# Save news errors of level crit and higher in a special file.
uucp,news.crit                                /var/log/spooler

# Save boot messages also to boot.log
local7.*                                      /var/log/boot.log
```
