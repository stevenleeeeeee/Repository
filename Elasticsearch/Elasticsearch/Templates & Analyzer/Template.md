#### template settings
```python
curl -XPOST -u 'username:password' -H 'Content-Type: application/json'  "http://127.0.0.1:9200/_template/errlog_example" -d \
'{
    .....
    "settings": {                           # 索引设置
      "index": {
        "search": {
          "slowlog": {                      # 关于慢查询日志的阈值设置
            "threshold": {
              "fetch": {                    # fetch 
                "warn": "1800ms",           # 超过1800ms为warn级别
                "info": "1s"                # 超过1000ms为info级别
              },
              "query": {                    # query
                "warn": "10s",              # 超过10000ms为warn级别
                "info": "6s"                # 超过6000ms为info级别
              }
            }
          }
        },
        "refresh_interval": "30s",          # 将数据持久化的间隔时间,数据刷新后将会被搜索到,默认1S,根据情况适当增加此值可提高性能,索引的刷新频率越快搜索到就越实时
        "number_of_shards": "10",           # 分片数
        "number_of_replicas": "1",          # 副本数
        "auto_expand_replicas": "1-3"
      }
    }
    "mappings": { 
        ......
```
#### template mappings
```python
curl -XPOST -u 'username:password' -H 'Content-Type: application/json'  "http://127.0.0.1:9200/_template/errlog_example" -d \
'{
    "order": 0,                               # 较高的值将会覆盖低优先级的模板
    "template": "errorlogs_*",                # 模板匹配的索引前缀
    "index_patterns": ["logs_*", "oth*"],     # 索引前缀匹配
    "settings": {                             # 索引设置
        ......
    },
    "mappings": {                             # 索引中各字段的映射定义，新版使用'_doc'代替索引类型，且用curl写入/查询时要显示指定
      "_source": {                            # 包含在索引时传递的原始JSON文档。其本身没有索引字段（因此不可搜索），但它被保存以便可以在执行时会返回 
          "enabled": false                    # 虽然非常方便但源字段确实会在索引中产生存储开销 
      },                                      # 如果该_source字段不可用，则不支持许多功能，如：The update, update_by_query, and reindex APIs....
      "dynamic": false,                       # 关闭动态映射功能
      "numeric_detection": true               # 开启字符串类型的数字检测机制
      "properties": {                         # 相关属性的类型及其他设置都在mappings.properties中进行
        "traceId": {
          "type": "keyword"                   # 字段类型：'www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html'
        },
        "instanceName": {                     # 字段名称
          "type": "keyword"                   # text、keyword、date、long、double、boolean、ip、object、nested、geo_point、geo_shape、completion
        },
        "hostIp": {
          "type": "string",                   # string类型可将字段索引为text用于全文搜索的keyword字段，以及用于排序或聚合的字段（大多数类型都通过fields参数支持多字段）
          "analyzer": "linieAnalzyer"         # 使用特定分析器：standard、english、french
        },
        "appName": {
          "type": "keyword",  
          "index": "analyzed",                # 首先分析这个字符串然后索引。换言之，以全文形式索引此字段
          "search_analyzer": "ik_max_word"    # 设置搜索时使用的分词器
        },
        "interStartTime": {
            "type": "date",                   # 设置字段类型为时间类型
            "format": "yyyyMMddHH:mm:ssSSS||yyyyMMddHH:mm:ss||date_time"  # 给定时间格式: https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-date-format.html
        },
        "errorCode": { 
          "type": "not_analyzed"              # 索引这个字段，使之可以被搜索，但是索引内容和指定值一样。不分析此字段
        },
        "errorMsg": {
          "analyzer": "ik_max_word",          # 使用特定的分词器对文本进行分词后存入倒排索引中
          "type": "text",                     #
          "store": false                      # 字段值是否应该与_source字段分开存储和检索。接受true或false（默认）
        },
        "text": { 
          "type": "text",                     # The text field uses the default standard analyzer
          "fields": {                         # 与json嵌套相似，其主要用于针对同一个字段设置不同的数据类型, 这里的text是text类型，text.english是string类型
            "english": {                      # The text.english multi-field uses the english analyzer, which removes stop words and applies stemming.
              "type": "string",
              "analyzer": "english"
            }
          }
        },
        "exceptionStack": {
          "analyzer": "ik_max_word",
          "type": "text"
        },
        "province": {
          "type": "keyword",
          "index": false                      # 不索引此字段。其不能被搜索到 This means values for the field are stored but not indexed or available for search
        },
        "systemCode": {
          "type": "long"                      # 数值类型
        }
      }
    },
    "aliases": {                              # 索引别名的相关设置
        "{index}-alias": {},                  # 该别名模板使用了索引占位符，建索引时其被替换为真实的索引名以达到模板中定义别名的唯一性
        "alias_tomcat_filter": {
            "filter": { "term": { "user_name": "tomcat" } },
            "routing": "tomcat"
        }
    }
}'
```
#### Dynamic Mapping
```python
# Dynamic参数:
# true	    新检测到的字段将添加到映射中。（默认）
# false	    新检测到的字段将被忽略且不被编入索引，因此无法搜索，但仍出现在_source返回的匹配字段中。这些字段不会添加到映射，必须显式添加新字段。
# strict	如果检测到新字段则抛出异常并拒绝该文档。必须将新字段显式添加到映射中。

curl -X PUT "localhost:9200/my_index?pretty" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "dynamic": false,               # 可以在"全局"中设置是否启用动态映射
    "properties": {
      "user": {                     # 该user对象继承了"全局"级别设置
        "properties": {
          "name": {
            "type": "text"
          },
          "social_networks": { 
            "dynamic": true,        # 该user.social_networks对象启用动态映射，因此可以将新字段添加到此内部对象中去
            "properties": {}
          }
        }
      }
    }
  }
} '
```
#### nested type
```python
# 考虑到在ES里面建立，删除和更新一个单一文本是原子性的，那么将相关实体保存在同一个文本里面是有意义的
# 因为所有内容都在同一文本里，在查询的时候就没有必要拼接blog posts,因此检索性能会更好
PUT /my_index/blogpost/1
{
  "title":"Nest eggs",
  "body":  "Making your money work...",
  "tags":  [ "cash", "shares" ],
  "comments":[
     {
	  "name":    "John Smith",
      "comment": "Great article",
      "age":     28,
      "stars":   4,
      "date":    "2014-09-01"
	 },
	 {
      "name":    "Alice White",
      "comment": "More like this please",
      "age":     31,
      "stars":   5,
      "date":    "2014-10-22"
     }
  ]
}

# 问题是上面的文档匹配这样的一个查询之后返回的结果不是想要的：
curl -XPGET 'localhost:9200/_search' -d '
{
  "query":{
     "bool":{
   "must":[
     {"match":{"name":"Alice"}},
     {"match":{"age":28}}
   ]
 }
}
# 输出：
# {
#   "title":                [ eggs, nest ],
#   "body":                 [ making, money, work, your ],
#   "tags":                 [ cash, shares ],
#   "comments.name":        [ alice, john, smith, white ],
#   "comments.comment":     [ article, great, like, more, please, this ],
#   "comments.age":         [ 28, 31 ],                             # 但是搜索时的条件中 Alice is 31,不是 28 ！
#   "comments.stars":       [ 4, 5 ],
#   "comments.date":        [ 2014-09-01, 2014-10-22 ]
# }
# 造成这种交叉对象匹配是因为结构性的JSON文档会平整成索引内的一个简单键值格式，就像上面输出的格式，其将comments中的每个字段都当作是一个数组来使用
# 显然，像这种‘Alice’/‘31’，‘john’/’2014-09-01’间的关联性就不可避免的丢失了。
# 虽然object类型的字段对于保存一个单一的object很有用，但是从检索的角度来说，这对于保存一个object数组却是无用的。

# 通过将comments字段映射为nested类型，而不是object类型，每一个nested object 将会作为一个隐藏的单独文本建立索引。如下：
# 通过分开给每个nested object建索引，object内部的字段间的关系就能保持。当执行查询时只会匹配"match"同时出现在相同的nested object的结果.
{ 
  "comments.name":    [ john, smith ],
  "comments.comment": [ article, great ],
  "comments.age":     [ 28 ],
  "comments.stars":   [ 4 ],
  "comments.date":    [ 2014-09-01 ]
}
{ 
  "comments.name":    [ alice, white ],
  "comments.comment": [ like, more, please, this ],
  "comments.age":     [ 31 ],
  "comments.stars":   [ 5 ],
  "comments.date":    [ 2014-10-22 ]
}
{ 
  "title":            [ eggs, nest ],
  "body":             [ making, money, work, your ],
  "tags":             [ cash, shares ]
}

# 这些额外的nested文本是隐藏的；我们不能直接接触。为了更新，增加或者移除一个nested对象，必须重新插入整个文本。
# 要记住一点：查询请求返回的结果不仅仅包括nested对象，而是整个文本。

# 你可能想要检索内部object同时当作nested 字段和当作整平的object字段，比如为了强调。可以通过将include_in_parent设置为true实现：

curl -XPUT 'localhost:9200/my_index' -d '
{
  "mappings":{
     "blogpost":{
	     "properties":{
		     "comments":{
			    "type":"nested",
				"include_in_parent":true,               # true
				"properties":{
				   "name":    {"type":"string"    },
				   "comment": { "type": "string"  },
                   "age":     { "type": "short"   },
                   "stars":   { "type": "short"   },
                   "date":    { "type": "date"    }
				}
			 }
		 }
	 }
  }
}

# 查询结果类似这样：
{ 
    "user.first" : "alice",
    "user.last" :  "white"
}
{ 
    "user.first" : "john",
    "user.last" :  "smith"
}
{ 
    "group" :        "fans",
    "user.first" : [ "alice", "john" ],
    "user.last" :  [ "smith", "white" ]
}

# nested 字段可能会包含其他的nested 字段
# include_in_parent object关联字段的直接上层，而include_in_root仅仅关联"根"obejct或文本
```

#### <index>/_doc
```bash
# 在7.0中_doc表示端点名称而不是文档类型。该_doc组件是文件路径的永久组成部分
# In 7.0, index APIs must be called with the {index}/_doc path for automatic generation of the _id and {index}/_doc/{id} with explicit ids.

# Example:
PUT index/_doc/1
{
  "foo": "baz"
}

# {
#   "_index": "index",
#   "_id": "1",
#   "_type": "_doc",
#   "_version": 1,
#   "result": "created",
#   "_shards": {
#     "total": 2,
#     "successful": 1,
#     "failed": 0
#   },
#   "_seq_no": 0,
#   "_primary_term": 1
# }

# Similarly, the get and delete APIs use the path {index}/_doc/{id}:
GET index/_doc/1
```