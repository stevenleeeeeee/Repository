```bash
[root@node1 ~]# cat /etc/logrotate.d/logstash     #多个文件绝对路径路径可以用空格、换行分隔
/nfsc/logtest/stg/applog/*/*out
/nfsc/logtest/stg/oslog/*/var/log/cron
/nfsc/logtest/stg/oslog/*/var/log/secure
/nfsc/logtest/stg/oslog/*/var/log/messages
{
    rotate 10       #切分后的保留的最多个数
    sharedscripts   #表示上面的日志文件全部判断后才执行  kill -HUP 命令(否则每判断一次执行一次)
    nocompress      #不压缩
    create 2775 root root   #新建并设置权限
    size 10G                #超过多大开始切分
    missingok
    notifempty              #空文件不执行
    copytruncate            #先 copy 再清空的方式，可能有少量的日志丢失
    dateext                 #以时间为后缀
    postrotate
        /bin/kill -HUP `cat /var/run/logstash.pid 2> /dev/null` 
    endscript
}

# 参数说明:
# daily			    每天轮替一次
# weekly			每周轮替一次
# monthly			每月轮替一次
# yearly			每年轮替一次
# rotate			保留几个轮替日志文件
# ifempty			不论日志是否空，都进行轮替
# notifempty		若日志为空，则不进行轮替
# create			旧日志文件轮替后创建新的日志文件
# size			    日志达到多少后进行rotate
# minsize			文件容量一定要超过多少后才进行rotate
# nocompress		轮替但不进行压缩
# compress		    压缩轮替文件
# dateext			轮替旧日志文件时，文件名添加-%Y %m %d形式日期，可用dateformat选项扩展配置。
# nodateext		    旧日志文件不使用dateext扩展名，后面序数自增如"*.log.1"
# dateformat		只允许%Y %m %d和%s指定符。注意：系统时钟需要设置到2001-09-09之后，%s才可以正确工作
# sharedscripts	    作用域下文件存在至少有一个满足轮替条件的时候，执行一次prerotate脚本和postrotate脚本。
# prerotate/endscript		在轮替之前执行之间的命令，prerotate与endscript成对出现。
# postrotate/endscript	    在轮替之后执行之间的命令，postrotate与endscript成对出现。
# olddir			将轮替的文件移至指定目录下
# missingok		    如果日志文件不存在，继续进行下一个操作，不报错

# 测试语法:
[root@node1 ~]# /usr/sbin/logrotate -d -v /etc/logrotate.conf
```
####  写入 Crontab
```bash
#logrotate提供的轮替周期参数只能精确到天，以天为轮替周期在一些情况下并不能满足我们的要求，此时可以基于crontab进行切割

*/5 * * * * logrotate    /etc/logrotate.d/logstash
```