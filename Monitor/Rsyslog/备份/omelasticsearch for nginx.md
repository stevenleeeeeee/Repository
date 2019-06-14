#### Nginx.conf 日志格式设置
```bash
log_format ngx_accss_json '{
      "@timestamp": "$time_iso8601", '
      '"@fields": { '
          '"remote_addr": "$remote_addr", '
          '"server_name": "$server_name", '
          '"server_port": "$server_port", '
          '"scheme": "$scheme", '
          '"server_protocol": "$server_protocol", '
          '"body_bytes_sent": "$body_bytes_sent", '
          '"request_time": "$request_time", '
          '"status": "$status", '
          '"request": "$request", '
          '"uri": "$uri", '
          '"request_method": "$request_method", '
          '"http_referrer": "$http_referer", '
          '"host": "$host", '
          '"http_user_agent": "$http_user_agent" 
      } 
}';

access_log syslog:server=127.0.0.1:514,facility=local7,tag=nginx,severity=info ngx_accss_json;
```
#### Rsyslog
```bash
# 配置 rsyslog 推送到ElasticSearch, 这里我们启用了 DA 模式;
$template rawmsg,"%msg%"    # 原始消息已为json格式

#此模板定义了 ElasticSearch 索引名称:  YYYY.MM.DD
template(name="nginx-index" type="list") {
    constant(value="nginx-")
    property(name="timereported" dateFormat="rfc3339" position.from="1" position.to="4")
    constant(value=".")
    property(name="timereported" dateFormat="rfc3339" position.from="6" position.to="7")
    constant(value=".")
    property(name="timereported" dateFormat="rfc3339" position.from="9" position.to="10")
}

# 
if $syslogfacility-text == "local7" and $syslogtag == "nginx:" then {
    local7.* action(
                    type="omelasticsearch"
                    template="rawmsg"
                    searchIndex="nginx-index"
                    dynSearchIndex="on"
                    server="127.0.0.1"
                    bulkmode="on"
                    action.resumeretrycount="-1"
                    queue.fileName="nginx_access"
                    queue.maxDiskSpace="5g"
                    queue.saveOnShutdown="on"
             )
    stop
}
```

`参考：https://blog.csdn.net/force_eagle/article/details/52354484`