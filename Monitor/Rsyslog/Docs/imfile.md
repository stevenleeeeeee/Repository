`一般情况的包含关系：input(ruleset(if;action(Template)))  注:若配置文件中没有 input() 则整个Rsyslog上下文作为input！`
#### imfile 参数
```bash
#此模块提供将任何标准文本文件转换为系统日志消息的功能，标准文本文件是由可打印字符组成的文件，其中行由LF分隔
#其逐行读取并将任何读取的行传递给rsyslog的规则引擎，规则引擎应用过滤条件并选择需要执行的操作
#文件监视器支持文件轮换。要完全正常工作的话rsyslogd必须在文件轮转时运行。然后读取并处理旧文件中的任何剩余行
#完成后将从头开始处理新的文件。如果在轮转期间停止rsyslogd，则会读取新文件，但无法再获取上一个文件中尚未报告的任何行消息

input(type="imfile"
    File="/var/log/nginx/scan.log"  #文件名

    freshStartTail="off"            #关闭就是从文本开头读取。要第一次读这个文本，这个才有效，读过的都有记录状态文件

    Facility="local5"               #设备类型 ( 默认是 local0 )
    Severity="info"                 #消息级别
    
    Tag="uat-scan"                  #打标签，用于消息文件原始的标签
    PollingInterval="5"             #对日志文件的轮询间隔，仅当imfile在轮询模式下运行时它才有效（建议使用inotify模式）
                                    #短轮询间隔提供更快速的消息转发，但需要更多的系统资源
    PersistStateInterval="1"        #处理多少行后写入一次状态文件，默认0意味着只有当监控文件是被关闭时才写入一个新的状态文件
                                    #此设置影响imfile的性能
    reopenOnTruncate="on"           #告诉rsyslog当被处理的文件被截断后重新打开

    discardTruncatedMsg="off"       #当消息太长时将被截断并以被截断部分作为新消息处理。当打开时截断的部分不会被处理。
    msgDiscardingError="on"         #在截断时给出错误。关闭此参数时，截断时不会显示错误

    readMode="[0-2]"                #为处理某些标准类型的多行消息提供了支持，但它不比正则表达式灵活，不过其性能更好
              # 0 ---> 基于行（每行是一条新消息）这是默认的
              # 1 ---> 段（日志消息之间有一个空行）
              # 2 ---> 缩进（新的日志消息从行的开头开始。若一行以空格或制表符"t"开头，它就是之前的日志消息的一部分）

    escapeLF=""                     #仅在要处理多行消息时才有意义，嵌入到系统日志消息中的LF字符会带来很多麻烦
              #若为"on" 则此选项通过将LF字符正确转义为4字节序列"＃012"来避免此问题，这与其他rsyslog控制字符转义一致。
              #默认情况下启用。如果将其关闭，请确保使用所有相关工具进行非常仔细的测试

    addMetadata="-1"                   #用于打开或关闭向消息对象添加元数据，It supports the following data items:
              # filename 消息源所属文件名。在使用通配符时这非常有用，访问：%$!metadata!filename%
              # fileoffset 读取消息时文件的偏移量（以字节为单位）。报告的偏移量来自该行的开头

    addCeeTag="off"                    #用于打开或关闭向消息对象添加"@cee："cookie

    startmsg.regex="[POSIX ERE regex]" #表示消息的开始，这个允许处理多行消息，当下一个被匹配住是才是新的消息的开始
                                       #因为这个参数是使用正则表达式, 相比readMode它是更加灵活的
    endmsg.regex="[POSIX ERE regex]"   #版本8.38.0新增，设当endmsg.regex的正则与标识消息结束的行匹配到时才终止消息
                                       #注意：readMode、endmsg.regex、startmsg.regex 三者不能同时定义

    readTimeout="60"                   #设置输入超时，单位秒 ( 可以与startmsg.regex一起使用，但不支持readMode )

    timeoutGranularity="60"            #多行匹配超时设置，当新的正则开头的日志进来时上一条合并才会结束! 所以要设置超时
                                       #此设置将会覆盖掉readTimeout的值

    MaxSubmitAtOnce="10"               #每次最大提交数量

    sortFiles="off"                    #按排序顺序处理文件，但由于跟踪文件所涉及的操作的固有的异步性，因此无法严格保证

    #input()中若设置了 startmsg.regex= 参数。那么将会把匹配规则的多行数据以\n作为各行之间的间隔发送出去！
    #但这样的话kibana中看到的数据将是：xxxx \\n xxxx \\n xxxx 的格式。
    #处理办法：
    #在imput调用的ruleset中添加如下，eg: 
    # template(name="nginx_access" type="string" string="%.replaced_msg %\n")
    # ruleset( name="nginx_forward" ){
    #       set $.replaced_msg = replace($msg, "\\n", "\r\n");
    #       action(type="omfwd" Target="192.168.20.223" Port="514" Protocol="tcp" template="nginx_access" )
    # stop
    # }
)
```
#### Example
```bash
#加载imfile模块并设置默认1秒读取1次文件
module(load="imfile" PollingInterval="1")

#定义格式化msg消息的模板
template(name="msg" type="string" string="%msg:1:$%\n")

#监控收集bpm的server1日志
input (type="imfile"
        File="/test/bpm/server1.log"
        Facility="local5"           #定义类型
        Severity="info"             #定义级别
        PersistStateInterval="50"
		reopenOnTruncate="on"
        Tag="server-log"
        Ruleset="fwd_bpm_log"
)
                
#监控收集proxy的日志
input (type="imfile"
        File="/test/proxy/proxy.log"
        Facility="local5"
        Severity="info"
        PersistStateInterval="50"
		reopenOnTruncate="on"
        Tag="test-log"
        Ruleset="fwd_proxy_log"
)

#bpm日志转发规则
ruleset(name="fwd_bpm_log"){
	action(
		type="omfwd"
		Target="x.x.x.x"
		Port="515"
		Protocol="tcp"
		queue.type="linkedList"
		queue.spoolDirectory="/var/lib/rsyslog"
		queue.fileName="bpm-msg-queue"
		queue.maxDiskSpace="1g"
		queue.saveOnShutdown="on"
		action.resumeRetryCount="-1"
		Template="msg"
	)
	stop
}

#proxy代理日志转发规则
ruleset(name="fwd_proxy_log"){
    action(
		type="omfwd"
        Target="x.x.x.x"
        Port="514"
        Protocol="tcp"
        queue.type="linkedList"
        queue.spoolDirectory="/var/lib/rsyslog"
        queue.fileName="proxy-msg-queue"
        queue.maxDiskSpace="1g"
        queue.saveOnShutdown="on"
        action.resumeRetryCount="-1"
        Template="msg"
    )
    stop
}

#More ......
ruleset(name="fwd_pdw_log"){
        action( type="omfwd"
                Target="x.x.x.x"
                Port="516"
                Protocol="tcp"
                queue.fileName="pdw-msg-queue"
                queue.type="linkedList"
                queue.size="600000"
                queue.dequeuebatchsize="50000"
                queue.workerthreads="4"
                queue.workerthreadminimummessages="100000"
                queue.discardseverity="3"
                queue.highwatermark="480000"
                queue.lowwatermark="120000"
                queue.checkpointinterval="10"
                #queue.timeoutshutdown="10"
                #queue.timeoutactioncompletion="10"
                #queue.timeoutworkerthreadshutdown="10"
                queue.spoolDirectory="/var/lib/rsyslog"
                queue.maxfilesize="50M"
                queue.maxDiskSpace="1g"
                queue.saveOnShutdown="on"
                action.resumeRetryCount="-1"
                Template="msg"
        )
        stop
}
```