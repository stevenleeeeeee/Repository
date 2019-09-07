#### CRUD
```bash
# 判断文档是否存在 
curl -X HEAD /{index}/{type}/{id}

# 删除文档 ( 删除文档不会立即生效，它只是被标记成已删除状态。ES会在之后添加更多索引时在后台进行删除内容的清理，删除时即使文档不存在版本号也会加1 )
curl -X DELETE /{index}/{type}/{id}

# 查看文档总数量
curl -X GET /{index}/{type}/_count

# 使用非DSL语言的查询格式：
curl -XGET 'localhost:9200/index/_search?q=key=value'

# 查询response=404的信息：
curl -XGET 'localhost:9200/logstash-2015.12.23/_search?q=response=404&pretty'

# 查询来源地址:
curl -XGET 'localhost:9200/logstash-2015.12.23/_search?q=geoip.city_name=Buffalo&pretty'

# 正则表达式
{
    "query": {
            "regexp":{
                "name.first": "s.*y"
            }
    }
}

# 新增文档 ( 新增时可显式指定id，数字、字串，若不显式指定id则系统会自动生成UUID )
# 如果使用POST不指定id，这时肯定是添加操作,因为id是系统生成的 (类似关系型数据库的自增主键，属于insert操作)
# 如果使用PUT不指定id，当id没有存在时此时和post的操作效果完全一样，但若id存在则其属于更新操作，若id存在则返回409
PUT /shop/goods/1
{
    "name": "Apple/苹果 iPhone X",
    "price": 9688.00,
    "colors": ["银色", "深空灰色"],
    "is_discount": true,
    "create_date": "2018-01-31 12:10:30",
    "ip_addr": "192.168.10.1",
    "merchant": {
        "id": 2222,
        "shop_name": "水果店"
    },
    "params": [
       {"id": 1, "label":"型号", "value": "iphone x"},
       {"id": 2, "label":"品牌", "value": "Apple/苹果"}
    ]
}

# 更新文档时需注意：
# 在Elasticsearch中文档是不能直接修改的，当修改文档时ES将旧文档标为删除状态然后再将修改的文档作为1条新的文档添加进来
# 这样间接的达到更新文档的目的。被标记为删除状态的文档并不会立即消失，但也无法访问
# ES会在继续添加更多数据时在后台清理已经删除的文件。所以此种方式更新需要列举出来所有字段
# 若只更新一个字段的值，那么该文档的所有字段以及对应的值都要列举出来，因为内部更新方式是先删除文档再添加文档
# 因为是这种原理，所以也可以用于达到删除字段的目的：更新时列举除了要删除的字段的所有文档，然后进行更新

# 局部更新：
# 当字段存在时替换字段的值，当字段不存在时将字段添加到文档中。此种方式只需列举要修改的字段，不修改的字段就不需要列举出来
POST /{index}/{type}/{id}/_update       # 修改价格，大降价；修改颜色：隔壁老王绿；增加CPU字段
{
    "doc": {
      "price": 666.00,
      "colors": ["老王绿"],
      "cpu": "A11111111" 
    }
}

# 脚本更新：
# 脚本更新更加灵活，脚本语言可以在更新API中被用来修改_source中的内容，而它在脚本中被称为 ctx._source
POST /shop/goods/3/_update
{
   "script" : "ctx._source.quantity+=1"     # 使用脚本来增加库存数量：
}

# 使用脚本在颜色数组中添加新的颜色，在这个例子中把新的颜色声明为一个变量，而不是写死在脚本中
# 这样Elasticsearch就可以重新使用这个脚本进行添加新的颜色，而不用再次重新编写脚本了：
POST /shop/goods/3/_update
{
  "script": {
    "inline": "ctx._source.colors.add(params.new_color)", 
    "params": {
      "new_color": "脑残粉"
    }
  }
}

# 使用ctx.op来根据内容选择是否删除一个文档：
POST /shop/goods/3/_update
{
  "script": {
    "inline": "ctx.op = ctx._source.cpu == params.cpu ? 'delete' : 'none'", 
    "params": {"cpu": "A11111111"}
    }
}

# 当更新文档不存在时会报错，如果更新时当文档不存在时就创建可以使用upsert，指定如果文档不存在就应该先创建它：
POST /website/pageviews/1/_update
{  # 第一次运行这个请求时，upsert 值作为新文档被索引，初始化 views 字段为 1
   # 在后续的运行中，由于文档已经存在，script 更新操作将替代 upsert 进行应用，对 views 计数器进行累加。
   "script" : "ctx._source.views+=1",
   "upsert": {
       "views": 1
   }
}

```
#### 条件查询与聚合查询
```bash
# 字段解释：
#     条件查询：
#         _source：表示需要展示的字段
#     聚合查询:
#         field: 表示聚合的字段
#         size 显示条数
#         order 排序方法

# 条件查询：
{
  "_source": [
    "UUID",
    "workOrderData.appNo"
  ],
  "query": {
    "bool": {
      "must": [
        {
          "terms": {
            "workOrderData.appNo": ["2017060487300285"]
          }
        }
      ],
      "must_not": [],
      "should": []
    }
  },
  "size": 100
}

# 聚合查询 -1：
{
  "query": {
    "bool": {
      "must": [
        {
          "terms": {
            "workOrderData.center": ["7110101","7110102"]
          }
        }
      ],
      "must_not": [],
      "should": []
    }
  },
  "size": 0,
  "aggs": {
    "aggs_block": {
      "terms": {
        "field": "workOrderData.busiType"
      }
    }
  }
}


# 聚合查询 -2：
{
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "relateData.callTime": {"gte": "2016-07-26 00:00:00"}
          }
        },
        {
          "range": {
            "relateData.callTime": {"lte": "2017-08-02 23:59:59"}
          }
        }
      ]
    }
  },
  "size": 0,
  "aggs": {
    "1": {
      "terms": {
        "field": "analysisData.competitorList",
        "size": 10,
        "order": {"_count": "desc"}
      }
    }
  }
}

# should字段和must字段一起使用 ( should和must同级使用 )
#在这里should里面的条件满足一条就可以。相当于or, 但是当should与must一起使用时候就失去了should的意义 因为只要满足must的条件就可以
{
  "_source": [
    "relateData.orderNum",
    "relateDate.businessType",
    "relateData.agentGroupName",
    "relateData.agentDepartmentName",
    "relateData.acceptTime",
    "analysisData.is_rule_complain"
  ],
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "relateData.callTime": {"gte": "2017-02-22 00:00:00","lte": "2017-08-16 23:59:59"}
          }
        }
      ],
      "should": [
        {
          "term": {
            "transData.emotionList.emtionType": {"value": "2"}
          }
        },
        {
          "term": {
            "analysisData.is_rule_complain": {"value": "是"}
          }
        }
      ]
    }
  },
  "sort": {
    "relateData.acceptTime": {
      "order": "desc"
    }
  },
  "from": 0,
  "size": 10
}

# 在should里面包含bool （hould为must的上一级）
# 当我们有and 和 or 并列的查询要求时，(a==0 && b== 0 && (c==0 || d== 0))
{
  "_source": [
    "relateData.orderNum",
    "relateDate.businessType",
    "relateData.agentGroupName",
    "relateData.agentDepartmentName",
    "relateData.acceptTime",
    "analysisData.is_rule_complain"
  ],
  "query": {
    "bool": {
      "should": [
        {
          "bool": {
            "must": [
              {
                "range": {
                  "relateData.callTime": {"gte": "2017-02-22 00:00:00","lte": "2017-08-16 23:59:59"}
                }
              },
              {
                "term": {
                  "transData.emotionList.emtionType": {"value": "2"}
                }
              }
            ]
          }
        },
        {
          "bool": {
            "must": [
              {
                "range": {
                  "relateData.callTime": {"gte": "2017-02-22 00:00:00","lte": "2017-08-16 23:59:59"}
                }
              },
              {
                "term": {
                  "analysisData.is_rule_complain": {"value": "是"}
                }
              }
            ]
          }
        }
      ]
    }
  }
}


# 根据查询内容进行排序
GET zhifou/doc/_search
{
  "query": {
    "match": {
      "from": "gu"
    }
  },
  "sort": [
    {
      "age": {
        "order": "desc"
      }
    }
  ]
}
```
