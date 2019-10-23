#### logstash 中调用ruby对数据处理
```bash
input {
    ......
}

filter {

  ruby {
    path => "/mnt/elastic/logstash-6.5.1/config/test.rb"    # Cancel 90% of events
    # script_params => { "message" => "%{message}" }
  }

  json {
    source => "json"
    remove_field => ["json","message"]
  }

  mutate {
    join => {
        "model" => ","
        "versionCode" => ","
        "appKey" => ","
        "vendor" => ","
        "clientVersion" => ","
    }
}

#  date {
#    match => ["@timestamp", "yyyy-MM-dd HH:mm:ss,SSS", "UNIX"]
#    target => "@timestamp"
#    locale => "cn"
#  }
#  date {
#    match => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"]
#    默认复制给@timestamp
#    target => "@timestamp"
#    locale => "cn"
#  }
}

output {
    # elasticsearch {
    #   hosts => ["http://localhost:9200"]
    #   index => "%{[@metadata][beat]}-%{[@metadata][version]}-%{+YYYY.MM.dd}"
    # }

 # source_type是在filebeat中配置的，用于区分解析和创建elasticsearch索引
 if [fields][source_type] == "test" {
    stdout{
        codec=>rubydebug
    }
    elasticsearch {
      hosts => ["http://localhost:9200"]
      index => "test-%{+YYYY.MM.dd}"
    }
  }
}
```
#### ruby脚本: test.rb
```ruby
# the value of `params` is the value of the hash passed to `script_params`
# in the logstash configuration
def register(params)
    # 这里通过params获取的参数是在logstash文件中通过script_params传入的
    @message = params["message"]
end

# the filter method receives an event and must return a list of events.
# Dropping an event means not including it in the return array,
# while creating new ones only requires you to add a new instance of
# LogStash::Event to the returned array
# 这里通过参数event可以获取到所有input中的属性
def filter(event)
    _message = event.get('message')
    _nocache = _message.include? "All params NoCached"
    _cache = _message.include? "All params Cached"
    
    if _nocache
        idx = _message.index("All params NoCached")
        event.set('json', _message[idx + "All params NoCached: ".length,_message.length-(idx + "All params NoCached".length)+1])
        event.set('cache_type', 'NoCached')
    elsif _cache
        idx = _message.index("All params Cached")
        event.set('json', _message[idx + "All params Cached: ".length,_message.length-(idx + "All params Cached".length)+1])
        # 往event中增加新的属性
        event.set('cache_type', 'Cached')
    else
        return [] # return empty array to cancel event
    end
    
    event.set('for_time', (event.get('@timestamp').time.localtime + 8*60*60).strftime('%Y-%m-%d %H:%M:%S'))
    event.set('for_date', (event.get('@timestamp').time.localtime + 8*60*60).strftime('%Y-%m-%d'))
    return [event]
end
```