```bash
[root@mreald.com  logstash_conf]# cat /etc/logrotate.d/logstash 
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
```
####  写入 Crontab
```bash
*/5 * * * * logrotate    /etc/logrotate.d/logstash
```