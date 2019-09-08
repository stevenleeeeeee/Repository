#### 聚合语法
```txt
Docs:   https://www.elastic.co/guide/cn/elasticsearch/guide/current/_building_bar_charts.html

"aggregations" : {
    "<aggregation_name>" :          { <!--聚合的名字 -->
        "<aggregation_type>" :      { <!--聚合的类型 -->
            <aggregation_body>      <!--聚合体：对哪些字段进行聚合 -->
        }
        [,"meta" : {  [<meta_data_body>] } ]?           <!--元 -->
        [,"aggregations" : { [<sub_aggregation>]+ } ]?  <!--在聚合里面在定义子聚合 -->
    }
    [,"<aggregation_name_2>" : { ... } ]*               <!--聚合的名字 -->
}

# 聚合分析是数据库中重要的功能特性，完成对一个查询的数据集中数据的聚合计算，如：找出某字段（或计算表达式的结果）的最大值、最小值，计算和、平均值等。ES作为搜索引擎兼数据库，同样提供了强大的聚合分析能力。
# 对一个数据集求最大、最小、和、平均值等指标的聚合，在ES中称为指标聚合   metric
# 而关系型数据库中除了有聚合函数外，还可以对查询出的数据进行分组group by，再在组上进行指标聚合。在 ES 中group by 称为分桶，桶聚合 bucketing
# ES中还提供了矩阵聚合（matrix）、管道聚合（pipleline），但还在完善中。 
```
#### 聚合分桶的使用说明
```python
# 聚合是在特定搜索结果背景下执行的， 这也就是说它只是查询请求的另外一个顶层参数（例如使用 /_search 端点）
# 聚合可以与查询结对使用

GET /cars/transactions/_search
{
    "size" : 0,                         # 设为 0 可提高查询速度，但不会有返回结果
    "aggs" : {                          # 聚合操作被置于顶层参数aggs之下（完整形式 aggregations 同样有效）
        "popular_colors" : {            # 可以为聚合指定一个我们想要名称，本例: popular_colors
            "terms" : {                 # 定义单个桶的类型 terms、terms 桶会为每个碰到的唯一词项动态创建新的桶
              "field" : "color"         # 因为我们告诉它使用 color 字段，所以 terms 桶会为每个颜色动态创建新桶
            }
        }
    }
}

# 输出：
# {
# ...
#    "hits": {
#       "hits": []                      # 因为设置了 size 参数，所以不会有 hits 搜索结果返回
#    },
#    "aggregations": {
#       "popular_colors": {             # popular_colors 是作为 aggregations 字段的一部分被返回的，它是自定义的名字
#          "buckets": [                 # 具体的桶的列表
#             {
#                "key": "red",          # 每个桶的 key 都与 color 字段里找到的唯一词对应
#                "doc_count": 4         # 它总会包含 doc_count 字段，告诉我们包含该词项的文档数量
#             },
#             {
#                "key": "blue",         # 每个桶的 key 都与 color 字段里找到的唯一词对应
#                "doc_count": 2         # 每个桶的数量代表该颜色的文档数量
#             },
#             {
#                "key": "green",
#                "doc_count": 2
#             }
#          ]
#       }
#    }
# }

```
#### 为聚合添加度量指标
```python
# 我们的应用需要提供更复杂的文档度量。 例如每种颜色汽车的平均价格是多少？
# 为了获取更多信息，需告诉 Elasticsearch 使用哪个字段计算何种度量，这需要将度量嵌套在桶内，度量会基于桶内文档计算统计结果

GET /cars/transactions/_search
{
   "size" : 0,
   "aggs": {
      "colors": {                       # 聚合名称为 colors ，基于color字段进行分桶/分组
         "terms": {"field": "color" },  # 在colors的每个桶中定义新的聚合层...
         "aggs": {                      # 为度量新增 aggs 层
            "avg_price": {              # 为度量指定名字： avg_price
               "avg": {                 # 为 price 字段定义 avg 度量
                  "field": "price"      # 
               }
            }
         }
      }
   }
}

# 输出：
# {
# ...
#    "aggregations": {
#       "colors": {
#          "buckets": [
#             {
#                "key": "red",
#                "doc_count": 4,
#                "avg_price": { 
#                   "value": 32500
#                }
#             },
#             {
#                "key": "blue",
#                "doc_count": 2,
#                "avg_price": {
#                   "value": 20000
#                }
#             },
#             {
#                "key": "green",
#                "doc_count": 2,
#                "avg_price": {
#                   "value": 21000
#                }
#             }
#          ]
#       }
#    }
# ...
# }
```
#### 桶嵌套
```python
# 真正令人激动的分析来自于将桶嵌套进 另外一个桶 所能得到的结果。 现在我们想知道每个颜色的汽车制造商的分布：
curl -X GET "localhost:9200/cars/transactions/_search?pretty" -H 'Content-Type: application/json' -d'
{
   "size" : 0,
   "aggs": {
      "colors": {
         "terms": {
            "field": "color"
         },
         "aggs": {                      #  一个聚合的每个层级都可以有多个度量或桶
            "avg_price": {              # avg_price 聚合
               "avg": {
                  "field": "price"
               }
            },                          # 新增的这个make聚合是一个terms桶（嵌套在 colors/terms 桶内），与avg_price聚合同级
            "make": {                   # 这意味着它会为数据集中的每个唯一组合生成（color、 make）元组
                "terms": {
                    "field": "make"     # 这个聚合是 terms 桶，它会为每个汽车制造商生成唯一的桶
                }
            }
         }
      }
   }
} '

# 输出:
# {
# ...
#    "aggregations": {
#       "colors": {
#          "buckets": [
#             {
#                "key": "red",
#                "doc_count": 4,
#                "make": {                  # 现在我们看见按不同制造商分解的每种颜色下车辆信息
#                   "buckets": [
#                      {
#                         "key": "honda", 
#                         "doc_count": 3
#                      },
#                      {
#                         "key": "bmw",
#                         "doc_count": 1
#                      }
#                   ]
#                },
#                "avg_price": {             # 看到前例中的每种颜色的 avg_price 度量仍然维持不变
#                   "value": 32500 
#                }
#             },
# ...
# }

# 基于不同的颜色分组后在为每个汽车生成商计算最低和最高的价格，注意，这里的avg_price与make是平级的:
curl -X GET "localhost:9200/cars/transactions/_search?pretty" -H 'Content-Type: application/json' -d'
{
   "size" : 0,
   "aggs": {
      "colors": {
         "terms": {
            "field": "color"
         },
         "aggs": {
            "avg_price": { "avg": { "field": "price" }                  # avg_price 与 make 平级
            },      
            "make" : {                                                  # make 与 avg_price 平级
                "terms" : {     
                    "field" : "make"                                    # 依据 make 字段对制造商分桶
                },
                "aggs" : {                                              # 根据 make 的分桶做嵌套分桶
                    "min_price" : { "min": { "field": "price"} },       # 最低价格
                    "max_price" : { "max": { "field": "price"} }        # 最高价格
                }
            }
         }
      }
   }
} '

# {
# ...
#    "aggregations": {
#       "colors": {
#          "buckets": [
#             {
#                "key": "red",
#                "doc_count": 4,
#                "make": {
#                   "buckets": [
#                      {
#                         "key": "honda",
#                         "doc_count": 3,
#                         "min_price": {
#                            "value": 10000 
#                         },
#                         "max_price": {
#                            "value": 20000 
#                         }
#                      },
#                      {
#                         "key": "bmw",
#                         "doc_count": 1,
#                         "min_price": {
#                            "value": 80000
#                         },
#                         "max_price": {
#                            "value": 80000
#                         }
#                      }
#                   ]
#                },
#                "avg_price": {
#                   "value": 32500
#                }
#             },
# ...
# }

# 有了这两个桶，我们可以对查询的结果进行扩展并得到以下信息：
# 有四辆红色车。
# 红色车的平均售价是 $32，500 美元。
# 其中三辆红色车是 Honda 本田制造，一辆是 BMW 宝马制造。
# 最便宜的红色本田售价为 $10，000 美元。
# 最贵的红色本田售价为 $20，000 美元。
```
#### 常用聚合的简单例子
```python
# 指标聚合: max min sum avg
# 查询所有客户中余额的最大值
POST /bank/_search
{
  "size": 0, 
  "aggs": {
    "masssbalance": {
      "max": {
        "field": "balance"
      }
    }
  }
}
# 输出:
# {
#   "took": 2080,
#   "timed_out": false,
#   "_shards": {
#     "total": 5,
#     "successful": 5,
#     "skipped": 0,
#     "failed": 0
#   },
#   "hits": {
#     "total": 1000,
#     "max_score": 0,
#     "hits": []
#   },
#   "aggregations": {
#     "masssbalance": {
#       "value": 49989
#     }
#   }
# }

# 查询年龄为24岁的客户中的余额最大值:
POST /bank/_search
{
  "size": 2, 
  "query": {
    "match": {
      "age": 24
    }
  },
  "sort": [
    {
      "balance": {
        "order": "desc"
      }
    }
  ],
  "aggs": {
    "max_balance": {
      "max": {
        "field": "balance"
      }
    }
  }
}

# 值来源于脚本，查询所有客户的平均年龄是多少，并对平均年龄加10
POST /bank/_search?size=0
{
  "aggs": {
    "avg_age": {
      "avg": {
        "script": {
          "source": "doc.age.value"
        }
      }
    },
    "avg_age10": {
      "avg": {
        "script": {
          "source": "doc.age.value + 10"
        }
      }
    }
  }
}

# 指定field，在脚本中用_value 取字段的值
POST /bank/_search?size=0
{
  "aggs": {
    "sum_balance": {
      "sum": {
        "field": "balance",
        "script": {
            "source": "_value * 1.03"
        }
      }
    }
  }
}

# 为没有值字段指定值。如未指定，缺失该字段值的文档将被忽略
POST /bank/_search?size=0
{
  "aggs": {
    "avg_age": {
      "avg": {
        "field": "age",
        "missing": 18
      }
    }
  }
}

# 统计银行索引bank下年龄为24的文档数量
POST /bank/_doc/_count
{
  "query": {
    "match": {
      "age" : 24
    }
  }
}

# 统计某字段有值的文档数
POST /bank/_search?size=0
{
  "aggs": {
    "age_count": {
      "value_count": {
        "field": "age"
      }
    }
  }
}

# 值去重计数 ( cardinality )
POST /bank/_search?size=0
{
  "aggs": {
    "age_count": {
      "cardinality": {
        "field": "age"
      }
    },
    "state_count": {
      "cardinality": {
        "field": "state.keyword"
      }
    }
  }
}

#  stats 统计 count max min avg sum 5个值
POST /bank/_search?size=0
{
  "aggs": {
    "age_stats": {
      "stats": {
        "field": "age"
      }
    }
  }
}

# 输出:
# {
#   "took": 7,
#   "timed_out": false,
#   "_shards": {
#     "total": 5,
#     "successful": 5,
#     "skipped": 0,
#     "failed": 0
#   },
#   "hits": {
#     "total": 1000,
#     "max_score": 0,
#     "hits": []
#   },
#   "aggregations": {
#     "age_stats": {
#       "count": 1000,
#       "min": 20,
#       "max": 40,
#       "avg": 30.171,
#       "sum": 30171
#     }
#   }
# }

# Extended stats 高级统计，比stats多4个统计结果： 平方和、方差、标准差、平均值加/减两个标准差的区间
POST /bank/_search?size=0
{
  "aggs": {
    "age_stats": {
      "extended_stats": {
        "field": "age"
      }
    }
  }
}

# 输出:
# {
#   "took": 7,
#   "timed_out": false,
#   "_shards": {
#     "total": 5,
#     "successful": 5,
#     "skipped": 0,
#     "failed": 0
#   },
#   "hits": {
#     "total": 1000,
#     "max_score": 0,
#     "hits": []
#   },
#   "aggregations": {
#     "age_stats": {
#       "count": 1000,
#       "min": 20,
#       "max": 40,
#       "avg": 30.171,
#       "sum": 30171,
#       "sum_of_squares": 946393,
#       "variance": 36.10375899999996,
#       "std_deviation": 6.008640362012022,
#       "std_deviation_bounds": {
#         "upper": 42.18828072402404,
#         "lower": 18.153719275975956
#       }
#     }
#   }
# }

# Percentiles 占比百分位对应的值统计
# 对指定字段（脚本）的值按从小到大累计每个值对应的文档数的占比（占所有命中文档数的百分比），返回指定占比比例对应的值。
# 默认返回[ 1, 5, 25, 50, 75, 95, 99 ]分位上的值。
# 如下中间的结果，可以理解为：占比为50%的文档的age值 <= 31，或反过来：age<=31的文档数占总命中文档数的50%
POST /bank/_search?size=0
{
  "aggs": {
    "age_percents": {
      "percentiles": {
        "field": "age"
      }
    }
  }
}
# 输出:
# {
#   "took": 87,
#   "timed_out": false,
#   "_shards": {
#     "total": 5,
#     "successful": 5,
#     "skipped": 0,
#     "failed": 0
#   },
#   "hits": {
#     "total": 1000,
#     "max_score": 0,
#     "hits": []
#   },
#   "aggregations": {
#     "age_percents": {
#       "values": {
#         "1.0": 20,
#         "5.0": 21,
#         "25.0": 25,
#         "50.0": 31,
#         "75.0": 35.00000000000001,
#         "95.0": 39,
#         "99.0": 40
#       }
#     }
#   }
# }
# 解释: 占比为50%的文档的age值 <= 31，或反过来：age<=31的文档数占总命中文档数的50%


# 指定分位值:
POST /bank/_search?size=0
{
  "aggs": {
    "age_percents": {
      "percentiles": {
        "field": "age",
        "percents" : [95, 99, 99.9] 
      }
    }
  }
}
# 输出:
# {
#   "took": 8,
#   "timed_out": false,
#   "_shards": {
#     "total": 5,
#     "successful": 5,
#     "skipped": 0,
#     "failed": 0
#   },
#   "hits": {
#     "total": 1000,
#     "max_score": 0,
#     "hits": []
#   },
#   "aggregations": {
#     "age_percents": {
#       "values": {
#         "95.0": 39,
#         "99.0": 40,
#         "99.9": 40
#       }
#     }
#   }
# }

# Percentiles rank 统计值小于等于指定值的文档占比:
# 统计年龄小于25和30的文档的占比，和第7项相反
POST /bank/_search?size=0
{
  "aggs": {
    "gge_perc_rank": {
      "percentile_ranks": {
        "field": "age",
        "values": [
          25,
          30
        ]
      }
    }
  }
}
# 输出:
# {
#   "took": 8,
#   "timed_out": false,
#   "_shards": {
#     "total": 5,
#     "successful": 5,
#     "skipped": 0,
#     "failed": 0
#   },
#   "hits": {
#     "total": 1000,
#     "max_score": 0,
#     "hits": []
#   },
#   "aggregations": {
#     "gge_perc_rank": {
#       "values": {
#         "25.0": 26.1,
#         "30.0": 49.2
#       }
#     }
#   }
# }

# 查询每日的客户数
GET /es-customer/_search
{
    "size" : 0,
    "aggs" : {
        "days" : {                          # 分桶/组的名称是自定义的
          "date_histogram": {               # 按照日期分桶，使用关键字 key ---> date_histogram
            "field": "createTime",          # 指定field
            "interval": "day"               # 指定分桶依据的间隔
          },        
          "aggs": {     
            "distinct_name" : {             # 分桶/组的名称是自定义的
                "cardinality" : {           # 在上面分好的每个桶内按照姓名来去重来计算客户数
                  "field" : "firstName"
                }
            }
        }
      }
    }
}

# 输出：
# {
#   "took": 0,
#   "timed_out": false,
#   "_shards": {
#     "total": 2,
#     "successful": 2,
#     "skipped": 0,
#     "failed": 0
#   },
#   "hits": {
#     "total": 9,
#     "max_score": 0,
#     "hits": []
#   },
#   "aggregations": {
#     "days": {
#       "buckets": [
#         {
#           "key_as_string": "2019-04-10 00:00:00",
#           "key": 1554854400000,
#           "doc_count": 9,
#           "distinct_name": {
#             "value": 6
#           }
#         }
#       ]
#     }
#   }
# }


# 计算每个tag下的商品数量
GET /ecommerce/product/_search
{
  "aggs": {
    "group_by_tags": {
      "terms": { "field": "tags" }
    }
  }
}

# 将文本field的fielddata属性设置为true
PUT /ecommerce/_mapping/product
{
  "properties": {
    "tags": {
      "type": "text",
      "fielddata": true     
    }
  }
}

GET /ecommerce/product/_search
{
  "size": 0,
  "aggs": {
    "all_tags": {
      "terms": { "field": "tags" }          # 以tags字段作为聚合搜索的条件
    }
  }
}

# 返回：
# {
#   "took": 20,
#   "timed_out": false,
#   "_shards": {
#     "total": 5,
#     "successful": 5,
#     "failed": 0
#   },
#   "hits": {
#     "total": 4,
#     "max_score": 0,
#     "hits": []
#   },
#   "aggregations": {
#     "group_by_tags": {
#       "doc_count_error_upper_bound": 0,
#       "sum_other_doc_count": 0,
#       "buckets": [
#         {
#           "key": "fangzhu",
#           "doc_count": 2
#         },
#         {
#           "key": "meibai",
#           "doc_count": 2
#         },
#         {
#           "key": "qingxin",
#           "doc_count": 1
#         }
#       ]
#     }
#   }
# }

# 对名称中包含yagao的商品，计算每个tag下的商品数量
GET /ecommerce/product/_search
{
  "size": 0,
  "query": {
    "match": {
      "name": "yagao"
    }
  },
  "aggs": {
    "all_tags": {
      "terms": {
        "field": "tags"
      }
    }
  }
}

# 先分组，再算每组的平均值，计算每个tag下的商品的平均价格
GET /ecommerce/product/_search
{
    "size": 0,
    "aggs" : {
        "group_by_tags" : {
            "terms" : { "field" : "tags" },
            "aggs" : {
                "avg_price" : {
                    "avg" : { "field" : "price" }
                }
            }
        }
    }
}

# 返回：
# {
#   "took": 8,
#   "timed_out": false,
#   "_shards": {
#     "total": 5,
#     "successful": 5,
#     "failed": 0
#   },
#   "hits": {
#     "total": 4,
#     "max_score": 0,
#     "hits": []
#   },
#   "aggregations": {
#     "group_by_tags": {
#       "doc_count_error_upper_bound": 0,
#       "sum_other_doc_count": 0,
#       "buckets": [
#         {
#           "key": "fangzhu",
#           "doc_count": 2,
#           "avg_price": {
#             "value": 27.5
#           }
#         },
#         {
#           "key": "meibai",
#           "doc_count": 2,
#           "avg_price": {
#             "value": 40
#           }
#         },
#         {
#           "key": "qingxin",
#           "doc_count": 1,
#           "avg_price": {
#             "value": 40
#           }
#         }
#       ]
#     }
#   }
# }

# 计算每个tag下的商品的平均价格，并且按照平均价格降序排序
GET /ecommerce/product/_search
{
    "size": 0,
    "aggs" : {
        "all_tags" : {
            "terms" : { "field" : "tags", "order": { "avg_price": "desc" } },
            "aggs" : {
                "avg_price" : {
                    "avg" : { "field" : "price" }
                }
            }
        }
    }
}

# 按照指定的价格范围区间进行分组，然后在每组内再按照tag进行分组，最后再计算每组的平均价格
GET /ecommerce/product/_search
{
  "size": 0,
  "aggs": {
    "group_by_price": {         # 分组名称
      "range": {
        "field": "price",       # 按照指定的价格范围区间进行分组
        "ranges": [
          {
            "from": 0,
            "to": 20
          },
          {
            "from": 20,
            "to": 40
          },
          {
            "from": 40,
            "to": 50
          }
        ]
      },
      "aggs": {                     # 在每组内再按照tag进行分组
        "group_by_tags": {          # 分组名称
          "terms": {
            "field": "tags"         # 分组依据
          },
          "aggs": {
            "average_price": {      # 分组名称
              "avg": {
                "field": "price"    # 对每组的price字段求平均值
              }
            }
          }
        }
      }
    }
  }
}
}
```
#### 条形图
```python
# 聚合还有一个令人激动的特性就是能够十分容易地将它们转换成图表和图形
# 直方图 histogram 特别有用，它本质上是一个条形图，
# 创建直方图需要指定一个区间，如果我们要为售价创建一个直方图，可以将间隔设为 20,000
# 这样做将会在每个 $20,000 档创建一个新桶，然后文档会被分到对应的桶中

# 希望知道每个售价区间内汽车的销量。还会想知道每个售价区间内汽车所带来的收入，可以通过对每个区间内已售汽车的售价求和得到
# 可以用 histogram 和一个嵌套的 sum 度量得到我们想要的答案
curl -X GET "localhost:9200/cars/transactions/_search?pretty" -H 'Content-Type: application/json' -d'
{
   "size" : 0,
   "aggs":{
      "price":{                         
         "histogram":{                  # histogram 桶要求两个参数：一个数值字段以及一个定义桶大小间隔
            "field": "price",           # 字段
            "interval": 20000           # 间隔
         },
         "aggs":{                       # 根据上面的分桶/分组进行总和计算
            "revenue": {
               "sum": {                 # sum 度量嵌套在每个售价区间内，用来显示每个区间内的总收入
                 "field" : "price"
               }
             }
         }
      }
   }
} '

# 如我们所见，查询是围绕 price 聚合构建的，它包含一个 histogram 桶。它要求字段的类型必须是数值型、同时需设定分组的间隔
# 间隔设置为 20,000 意味着将会得到如 [0-19999, 20000-39999, ...] 这样的区间。
# 接着在直方图内定义嵌套的度量，这个 sum 度量会对落入某一具体售价区间的文档中 price 字段的值进行求和。
# 这可以为我们提供每个售价区间的收入，从而可以发现到底是普通家用车赚钱还是奢侈车赚钱

# 响应结果如下：
# {
# ...
#    "aggregations": {
#       "price": {
#          "buckets": [
#             {
#                "key": 0,              # 键 0 代表区间 0-19999
#                "doc_count": 3,
#                "revenue": {
#                   "value": 37000
#                }
#             },
#             {
#                "key": 20000,          # 键 20000 代表区间 20000-39999
#                "doc_count": 4,
#                "revenue": {
#                   "value": 95000
#                }
#             },
#             {
#                "key": 80000,
#                "doc_count": 1,
#                "revenue": {
#                   "value": 80000
#                }
#             }
#          ]
#       }
#    }
# }
# 可能会注意到空的区间，比如：$40000-60000，没有出现在响应中。 histogram 默认会忽略，因为它有可能会导致潜在的错误输出
```
#### 统计：stats & 扩展统计： extended_stats 
```python
GET /cars/transactions/_search
{
  "size" : 0,
  "aggs": {
    "makes": {
      "terms": {
        "field": "make",
        "size": 10
      },
      "aggs": {
        "stats": {
          "extended_stats": {
            "field": "price"
          }
        }
      }
    }
  }
}

# stats 说明：
{
    "aggs" : {
        "stats" : { "stats" : { "field" : "grade" } }    # stats 会在请求后会直接显示多种聚合结果
    }
}
# {
#     ...
#     "aggregations": {
#         "grades_stats": {
#             "count": 6,
#             "min": 60,
#             "max": 98,
#             "avg": 78.5,
#             "sum": 471
#         }
#     }
# }

# extended_stats 说明：
{
    "aggs" : {
        "stats" : { "extended_stats" : { "field" : "grade" } }   # extended_stats 在统计基础上增加了多种复杂统计信息
    }
}
# {
#     ...
#     "aggregations": {
#         "grade_stats": {
#            "count": 9,
#            "min": 72,
#            "max": 99,
#            "avg": 86,
#            "sum": 774,
#            "sum_of_squares": 67028,
#            "variance": 51.55555555555556,
#            "std_deviation": 7.180219742846005,
#            "std_deviation_bounds": {
#             "upper": 100.36043948569201,
#             "lower": 71.63956051430799
#            }
#         }
#     }
# }
```
#### 按时间统计
```python
# 假设数据带时间戳。无论什么数据（Apache日志、股票买卖交易时间、棒球运动时间）只要有时间戳都可以进行date_histogram分析
# 当数据有时间戳，你总是想在时间维度上构建指标分析：
# 1、今年每月销售多少台汽车？
# 2、这只股票最近12小时的价格是多少？
# 3、我们网站上周每小时的平均响应延迟时间是多少？
# 虽然通常的直方图都是条形图，但date_histogram倾向于转换成线状图以展示时间序列。 

# 许多公司用Elasticsearch 仅仅只是为了分析时间序列数据。date_histogram分析是最基本的需要
# date_histogram与通常的histogram类似。但不是在代表数值范围的数值字段上构建buckets。因此每个桶都被定义成特定的日期大小（如1个月或2天）

# 构建一个简单的折线图来回答如下问题：每月销售多少台汽车？
# 此查询只有一个聚合，每月构建一个 bucket。这样可以得到每个月销售的汽车数量。另外还提供了额外的 format 参数以便 buckets 有"好看的"键值
GET /cars/transactions/_search
{
   "size" : 0,
   "aggs": {
      "sales": {                        # 分桶名称
         "date_histogram": {
            "field": "sold",            # 依据的字段
            "interval": "month",        # 时间间隔要求是日历术语 (如每个 bucket 1 个月)
            "format": "yyyy-MM-dd"      # 提供日期格式以便 buckets 的键值便于阅读
         }
      }
   }
}

# 输出:
# {
#    ...
#    "aggregations": {
#       "sales": {
#          "buckets": [
#             {
#                "key_as_string": "2014-01-01",     # 这里的 key_as_string 是按照format参数的值格式化后展示的
#                "key": 1388534400000,
#                "doc_count": 1
#             },
#             {
#                "key_as_string": "2014-02-01",
#                "key": 1391212800000,
#                "doc_count": 1
#             },
#             {
#                "key_as_string": "2014-05-01",
#                "key": 1398902400000,
#                "doc_count": 1
#             },
#             {
#                "key_as_string": "2014-07-01",
#                "key": 1404172800000,
#                "doc_count": 1
#             },
#             {
#                "key_as_string": "2014-08-01",         # 注意下面没有9月份的分桶，因为没有此时间范围内(9月份)的数据
#                "key": 1406851200000,
#                "doc_count": 1
#             },
#             {
#                "key_as_string": "2014-10-01",
#                "key": 1412121600000,
#                "doc_count": 1
#             },
#             {
#                "key_as_string": "2014-11-01",
#                "key": 1414800000000,
#                "doc_count": 2
#             }
#          ]
# ...
# }

# 返回空 Buckets：
# 上面的结果少了一些月份！ date_histogram和histogram一样默认只会返回文档数目非零的 buckets：
# 这意味着你的 histogram 总是返回最少结果。通常你并不想要这样。对于很多应用可能想直接把结果导入到图形库中，而不想做任何后期加工
# 即使 buckets 中没有文档我们也想返回。可以通过设置两个额外参数来实现这种效果：
GET /cars/transactions/_search
{
   "size" : 0,
   "aggs": {
      "sales": {
         "date_histogram": {
            "field": "sold",
            "interval": "month",
            "format": "yyyy-MM-dd",
            "min_doc_count" : 0,            # 这个参数强制返回空 buckets
            "extended_bounds" : {           # 这个参数强制返回整年
                "min" : "2014-01-01",
                "max" : "2014-12-31"
            }
         }
      }
   }
}
# 这两个参数会强制返回一年中所有月份的结果，而不考虑结果中的文档数目。
# min_doc_count 非常容易理解：它强制返回所有 buckets，即使 buckets 可能为空。
# extended_bounds 参数需要一点解释：
# min_doc_count 参数强制返回空 buckets，但是 Elasticsearch 默认只返回你的数据中最小值和最大值之间的 buckets
# 因此如果你的数据只落在了 4 月和 7 月之间，那么你只能得到这些月份的 buckets（可能为空也可能不为空）
# 因此为了得到全年数据，要告诉 Elasticsearch 想要全部 buckets，即便buckets可能落在最小日期之前或最大日期之后 

# Example ....:
GET /cars/transactions/_search
{
   "size" : 0,
   "aggs": {
      "sales": {
         "date_histogram": {
            "field": "sold",
            "interval": "quarter", 
            "format": "yyyy-MM-dd",
            "min_doc_count" : 0,
            "extended_bounds" : {
                "min" : "2014-01-01",
                "max" : "2014-12-31"
            }
         },
         "aggs": {
            "per_make_sum": {
               "terms": {
                  "field": "make"
               },
               "aggs": {
                  "sum_price": {
                     "sum": { "field": "price" } 
                  }
               }
            },
            "total_sum": {
               "sum": { "field": "price" } 
            }
         }
      }
   }
}

# 输出：
# {
# ....
# "aggregations": {
#    "sales": {
#       "buckets": [
#          {
#             "key_as_string": "2014-01-01",
#             "key": 1388534400000,
#             "doc_count": 2,
#             "total_sum": {
#                "value": 105000
#             },
#             "per_make_sum": {
#                "buckets": [
#                   {
#                      "key": "bmw",
#                      "doc_count": 1,
#                      "sum_price": {
#                         "value": 80000
#                      }
#                   },
#                   {
#                      "key": "ford",
#                      "doc_count": 1,
#                      "sum_price": {
#                         "value": 25000
#                      }
#                   }
#                ]
#             }
#          },
# ...
# }
```
#### 范围限定的聚合与全局桶
```python
# 聚合可以与搜索请求同时执行，但是我们需要理解一个新概念：范围
# 默认情况下聚合与查询是对同一范围进行操作的，也就是说聚合是基于我们查询匹配的文档集合进行计算的

# 下面的例子：
GET /cars/transactions/_search
{
    "size" : 0,
    "aggs" : {
        "colors" : {
            "terms" : {
              "field" : "color"
            }
        }
    }
}
# 从上面的例子可以看到聚合是隔离的
# 现实中，Elasticsearch 认为 "没有指定查询" 和 "查询所有文档" 是等价的。上面这个查询内部会转化成下面的这个请求：
GET /cars/transactions/_search
{
    "size" : 0,
    "query" : {
        "match_all" : {}  
    },  # 因为聚合总是对查询范围内的结果进行操作的，所以一个隔离的聚合实际上是在对 match_all 的结果范围操作
    "aggs" : {
        "colors" : {
            "terms" : {
              "field" : "color"
            }
        }
    }
}

# 利用范围，我们可以问福特在售车有多少种颜色？诸如此类的问题
GET /cars/transactions/_search
{
    "query" : {
        "match" : {
            "make" : "ford"
        }
    },
    "aggs" : {
        "colors" : {
            "terms" : {
              "field" : "color"
            }
        }
    }
}

# 输出:
# {
# ...
#    "hits": {
#       "total": 2,
#       "max_score": 1.6931472,
#       "hits": [
#          {
#             "_source": {
#                "price": 25000,
#                "color": "blue",
#                "make": "ford",
#                "sold": "2014-02-12"
#             }
#          },
#          {
#             "_source": {
#                "price": 30000,
#                "color": "green",
#                "make": "ford",
#                "sold": "2014-05-18"
#             }
#          }
#       ]
#    },
#    "aggregations": {
#       "colors": {
#          "buckets": [
#             {
#                "key": "blue",
#                "doc_count": 1
#             },
#             {
#                "key": "green",
#                "doc_count": 1
#             }
#          ]
#       }
#    }
# }

# 全局桶
# 通常我们希望聚合是在查询范围内的，但有时我们也想要搜索它的子集，而聚合的对象却是所有数据。
# 例如我们想知道福特汽车与所有汽车平均售价的比较。我们可以用普通的聚合（查询范围内的）得到第一个信息，然后用全局桶获得第二个信息
# 全局桶包含所有的文档，它无视查询的范围。因为它还是一个桶! 我们可以像平常一样将聚合嵌套在内：
GET /cars/transactions/_search
{
    "size" : 0,
    "query" : {
        "match" : {
            "make" : "ford"
        }
    },
    "aggs" : {
        "single_avg_price": {                       # 自定义聚合名称，此查询是基于查询范围内的所有文档，即所有福特汽车
            "avg" : { "field" : "price" }           # 聚合操作在查询范围内
        },
        "all": {                                    # 自定义聚合名称
            "global" : {},                          # global 全局桶没有参数 !!!
            "aggs" : {                              
                "avg_price": {                      # 它是嵌套在全局桶下的，这意味着完全忽略范围并对所有文档进行计算
                    "avg" : { "field" : "price" }   # 在使用了global参数之后聚合操作针对所有文档，忽略汽车品牌
                }

            }
        }
    }
}
```
#### 过滤和聚合
```python
# 聚合范围限定还有一个自然的扩展就是过滤。因为聚合是在查询结果范围内操作的，任何可以适用于查询的过滤器也可以应用在聚合上!

# 如果我们想找到售价在 $10000 之上的所有汽车同时也为这些车计算平均售价
# 可以简单地使用一个 constant_score 查询和 filter 约束：
curl -X GET "localhost:9200/cars/transactions/_search?pretty" -H 'Content-Type: application/json' -d'
{
    "size" : 0,
    "query" : {
        "constant_score": {                     # constant_score关键字能忽略词频和评分
            "filter": {                         # 使用 filtering query 会忽略评分，并有可能会缓存结果数据等等...
                "range": {
                    "price": {
                        "gte": 10000
                    }
                }
            }
        }
    },
    "aggs" : {                                  # 查询（包括了一个过滤器）返回一组文档的子集，聚合正是操作这些文档
        "single_avg_price": {
            "avg" : { "field" : "price" }
        }
    }
} '

# 对桶进行过滤
# 如果我们只想对聚合结果过滤怎么办？ 
# 假设正在为汽车经销商创建一个搜索页面， 希望显示用户搜索的结果
# 同时也想在页面上提供更丰富的信息，包括（与搜索匹配的）上个月度汽车的平均售价
# 为了解决这个问题，可以用一种特殊的桶，叫做 filter （注：过滤桶）
# 这个 filter 桶和其他桶的操作方式一样，所以可以随意将其他桶和度量嵌入其中。所有嵌套的组件都会 "继承" 这个过滤
# 我们可以指定一个过滤桶，当文档满足过滤桶的条件时将其加入到桶内:
curl -X GET "localhost:9200/cars/transactions/_search?pretty" -H 'Content-Type: application/json' -d'
{
   "size" : 0,
   "query":{
      "match": {
         "make": "ford"                 # 所有的福特车
      }
   },
   "aggs":{
      "recent_sales": {                 # 分桶的名称
         "filter": {                    # 使用过滤桶在查询范围基础上应用过滤器。注意这里的 filter 关键字!
            "range": {
               "sold": {
                  "from": "now-1M"      # 这里的聚合限定了上个月的福特车
               }
            }
         },
         "aggs": {                      # 分桶的名称
            "average_price":{
               "avg": {
                  "field": "price"      # avg 度量只会对上个月售出的福特车文档计算平均售价
               }
            }
         }
      }
   }
} '
```
#### 多桶排序
```python
# 多值桶（ terms、histogram、date_histogram ）动态生成很多桶。 Elasticsearch 是如何决定这些桶展示给用户的顺序呢？
# 默认的桶会根据 doc_count 降序排列。这是一个好的默认行为,因为通常我们想要找到文档中与查询条件相关的最大值：售价、人口数、频率
# 但有时希望能修改这个顺序，不同的桶有不同的处理方式

# 这些排序模式是桶固有的能力：
# 它们操作桶生成的数据 ，比如 doc_count 。它们共享相同的语法，但是根据使用桶的不同会有些细微差别
curl -X GET "localhost:9200/cars/transactions/_search?pretty" -H 'Content-Type: application/json' -d'
{
    "size" : 0,
    "aggs" : {
        "colors" : {
            "terms" : {
              "field" : "color",
              "order": {
                "_count" : "asc" 
              }
            }
        }
    }
} '
# 在这里为聚合引入一个 order 对象， 它允许我们可以根据以下几个值中的一个值进行排序
# _count：  按文档数排序。对terms、histogram、date_histogram有效
# _term：   按词项的字符串值的字母顺序排序。只在 terms 内使用
# _key：    按每个桶的键值数值排序（理论上与 _term 类似）。 只在 histogram 和 date_histogram 内使用


# 度量按排序
# 有时我们会想基于度量计算的结果值进行排序
# 在汽车销售分析仪表盘中，我们可能想按照汽车颜色创建一个销售条状图表，但按照汽车平均售价的升序进行排序。
# 我们可以增加一个度量 "avg_price"，指定再 order 参数引用这个度量名称即可：
curl -X GET "localhost:9200/cars/transactions/_search?pretty" -H 'Content-Type: application/json' -d'
{
    "size" : 0,
    "aggs" : {
        "colors" : {
            "terms" : {
              "field" : "color",
              "order": {
                "avg_price" : "asc"                 # 桶按照计算平均值的升序排序
              }
            },
            "aggs": {
                "avg_price": {
                    "avg": {"field": "price"}       # 计算每个桶的平均售价
                }
            }
        }
    }
} '
# 我们可以采用这种方式用任何度量排序，只需简单的引用度量的名字
# 不过有些度量会输出多个值。 extended_stats 度量是一个很好的例子：它输出好几个度量值。
# 如果我们想使用多值度量进行排序， 我们只需以关心的度量为关键词使用点式路径：
curl -X GET "localhost:9200/cars/transactions/_search?pretty" -H 'Content-Type: application/json' -d'
{
    "size" : 0,
    "aggs" : {
        "colors" : {
            "terms" : {
              "field" : "color",
              "order": {
                "stats.variance" : "asc" 
              }
            },
            "aggs": {
                "stats": {
                    "extended_stats": {"field": "price"}
                }
            }
        }
    }
} '

# 基于"深度"度量排序
# 在前面的示例中，度量是桶的直接子节点。平均售价是根据每个 term 来计算的
# 在一定条件下，我们也有可能对更深的度量进行排序，比如孙子桶或从孙桶。
# 需要提醒的是嵌套路径上的每个桶都必须是单值的
# filter桶生成一个单值桶：所有与过滤条件匹配的文档都在桶中。 多值桶（如terms）动态生成许多桶，无法通过指定一个确定路径来识别
curl -X GET "localhost:9200/cars/transactions/_search?pretty" -H 'Content-Type: application/json' -d'
{
    "size" : 0,
    "aggs" : {
        "colors" : {
            "histogram" : {
              "field" : "price",
              "interval": 20000,
              "order": {
                "red_green_cars>stats.variance" : "asc"                     # 按照嵌套度量的方差对桶的直方图进行排序。
              }
            },
            "aggs": {
                "red_green_cars": {
                    "filter": { "terms": {"color": ["red", "green"]}},      # 因为我们使用单值过滤器 filter ，我们可以使用嵌套排序
                    "aggs": {
                        "stats": {"extended_stats": {"field" : "price"}}    # 按照生成的度量对统计结果进行排序
                    }
                }
            }
        }
    }
} '
```
#### 近似聚合
```python
# Docs:   https://www.elastic.co/guide/cn/elasticsearch/guide/current/cardinality.html
# 仅了解即可,其能够在丢失极小精度的情况下极大的提高Elasticsearch的查询性能
```
#### 百分位聚合
```python
# Elasticsearch 提供的另外一个近似度量就是 percentiles 百分位数度量
# 百分位数展现某以具体百分比下观察到的数值。例如第95个百分位上的数值，是高于 95% 的数据总和
# 百分位数通常用来找出异常。在（统计学）的正态分布下，第 0.13 和 第 99.87 的百分位数代表与均值距离三倍标准差的值
# 任何处于三倍标准差之外的数据通常被认为是不寻常的，因为它与平均值相差太大
# 更具体的说，假设我们正运行一个庞大的网站，一个很重要的工作是保证用户请求能得到快速响应
# 因此我们就需要监控网站的延时来判断响应是否能保证良好的用户体验。
# 在此场景下一个常用的度量方法就是平均响应延时。
# 但这并不是一个好的选择（尽管很常用），因为平均数通常会隐藏那些异常值， 中位数有着同样的问题。 
# 我们可以尝试最大值，但这个度量会轻而易举的被单个异常值破坏

# 加载一个新的数据集，索引一系列网站延时数据然后运行一些百分位操作进行查看：
curl -X POST "localhost:9200/website/logs/_bulk?pretty" -H 'Content-Type: application/json' -d'
{ "index": {}}
{ "latency" : 100, "zone" : "US", "timestamp" : "2014-10-28" }
{ "index": {}}
{ "latency" : 80, "zone" : "US", "timestamp" : "2014-10-29" }
{ "index": {}}
{ "latency" : 99, "zone" : "US", "timestamp" : "2014-10-29" }
{ "index": {}}
{ "latency" : 102, "zone" : "US", "timestamp" : "2014-10-28" }
{ "index": {}}
{ "latency" : 75, "zone" : "US", "timestamp" : "2014-10-28" }
{ "index": {}}
{ "latency" : 82, "zone" : "US", "timestamp" : "2014-10-29" }
{ "index": {}}
{ "latency" : 100, "zone" : "EU", "timestamp" : "2014-10-28" }
{ "index": {}}
{ "latency" : 280, "zone" : "EU", "timestamp" : "2014-10-29" }
{ "index": {}}
{ "latency" : 155, "zone" : "EU", "timestamp" : "2014-10-29" }
{ "index": {}}
{ "latency" : 623, "zone" : "EU", "timestamp" : "2014-10-28" }
{ "index": {}}
{ "latency" : 380, "zone" : "EU", "timestamp" : "2014-10-28" }
{ "index": {}}
{ "latency" : 319, "zone" : "EU", "timestamp" : "2014-10-29" }　'

# 数据有三个值：延时、数据中心的区域、时间戳。
# 下面对数据全集进行百分位操作以获得数据分布情况的直观感受：
curl -X GET "localhost:9200/website/logs/_search?pretty" -H 'Content-Type: application/json' -d'
{
    "size" : 0,
    "aggs" : {
        "load_times" : {
            "percentiles" : {
                "field" : "latency"         # percentiles 度量被应用到 latency 延时字段
            }
        },
        "avg_load_time" : {
            "avg" : {
                "field" : "latency"         # 为了比较，我们对相同字段使用 avg 度量
            }
        }
    }
} '

# 默认情况下，percentiles 度量会返回一组预定义的百分位数值： [1, 5, 25, 50, 75, 95, 99] 
# 它们表示了人们感兴趣的常用百分位数值，极端的百分位数在范围的两边，其他的一些处于中部。
# 在返回的响应中可以看到最小延时在 75ms 左右，而最大延时差不多有 600ms
# 与之形成对比的是，平均延时在 200ms 左右， 信息并不是很多：
# ...
# "aggregations": {
#   "load_times": {
#      "values": {
#         "1.0": 75.55,
#         "5.0": 77.75,
#         "25.0": 94.75,
#         "50.0": 101,
#         "75.0": 289.75,
#         "95.0": 489.34999999999985,
#         "99.0": 596.2700000000002
#      }
#   },
#   "avg_load_time": {
#      "value": 199.58333333333334
#   }
# }
# 所以显然延时的分布很广，让我们看看它们是否与数据中心的地理区域有关：
curl -X GET "localhost:9200/website/logs/_search?pretty" -H 'Content-Type: application/json' -d'
{
    "size" : 0,
    "aggs" : {
        "zones" : {
            "terms" : {
                "field" : "zone"                        # 首先根据区域我们将延时分到不同的桶中。
            },
            "aggs" : {
                "load_times" : {
                    "percentiles" : {                   # 再计算每个区域的百分位数值。
                      "field" : "latency",
                      "percents" : [50, 95.0, 99.0]     # percents 参数接受想返回的一组百分位数，因为只对长的延时感兴趣
                    }
                },
                "load_avg" : {
                    "avg" : {
                        "field" : "latency"
                    }
                }
            }
        }
    }
} '
# 在下面的响应结果中发现欧洲区域（EU）要比美国区域（US）慢很多
# 在美国区域（US），50 百分位与 99 百分位十分接近，它们都接近均值
# 与之形成对比的是，欧洲区域（EU）在 50 和 99 百分位有较大区分
# 现在显然可以发现是欧洲区域（EU）拉低了延时的统计信息，我们知道欧洲区域的 50% 延时都在 300ms+
# ...
# "aggregations": {
#   "zones": {
#      "buckets": [
#         {
#            "key": "eu",
#            "doc_count": 6,
#            "load_times": {
#               "values": {
#                  "50.0": 299.5,
#                  "95.0": 562.25,
#                  "99.0": 610.85
#               }
#            },
#            "load_avg": {
#               "value": 309.5
#            }
#         },
#         {
#            "key": "us",
#            "doc_count": 6,
#            "load_times": {
#               "values": {
#                  "50.0": 90.5,
#                  "95.0": 101.5,
#                  "99.0": 101.9
#               }
#            },
#            "load_avg": {
#               "value": 89.66666666666667
#            }
#         }
#      ]
#   }
# }
# ...

# 百分位等级:
# 这里有另外一个紧密相关的度量叫 percentile_ranks
# percentiles 度量告诉落在某个百分比以下的所有文档的最小值。如果 50 百分位是 119ms，那么有 50% 的文档数值都不超过 119ms
# percentile_ranks 告诉某个具体值属于哪个百分位。119ms 的 percentile_ranks 是在 50 百分位。
# 这两个度量基本是个双向关系，例如：
#   50 百分位是 119ms
#   119ms 百分位等级是 50 百分位

# 所以假设网站必须维持的服务等级协议（SLA）是响应时间低于 210ms。
# 然后开个玩笑，老板警告我们如果响应时间超过 800ms 会把我开除。
# 可以理解的是，我们希望知道有多少百分比的请求可以满足 SLA 的要求（并期望至少在 800ms 以下！）。
# 为了做到这点，我们可以应用 percentile_ranks 度量而不是 percentiles 度量：
curl -X GET "localhost:9200/website/logs/_search?pretty" -H 'Content-Type: application/json' -d'
{
    "size" : 0,
    "aggs" : {
        "zones" : {
            "terms" : {
                "field" : "zone"
            },
            "aggs" : {
                "load_times" : {
                    "percentile_ranks" : {      # percentile_ranks 度量接受一组我们希望分级的数值。
                      "field" : "latency",
                      "values" : [210, 800] 
                    }
                }
            }
        }
    }
} '
# 输出:
# "aggregations": {
#   "zones": {
#      "buckets": [
#         {
#            "key": "eu",
#            "doc_count": 6,
#            "load_times": {
#               "values": {
#                  "210.0": 31.944444444444443,     # 在欧洲（EU），210ms 的百分位等级是 31.94% 
#                  "800.0": 100                     # 在欧洲（EU），800ms 的百分位等级是 100%
#               }
#            }
#         },
#         {
#            "key": "us",
#            "doc_count": 6,
#            "load_times": {
#               "values": {
#                  "210.0": 100,                    # 在美国（US），210ms 的百分位等级是 100% 
#                  "800.0": 100                     # 在美国（US），800ms 的百分位等级是 100%
#               }
#            }
#         }
#      ]
#   }
# }
# 通俗的说:
# 在欧洲区域（EU）只有 32% 的响应时间满足服务等级协议（SLA），而美国区域（US）始终满足服务等级协议的。
# 幸运的是，两个区域所有响应时间都在 800ms 以下，所以我们还不会被炒鱿鱼（至少目前不会）。
# percentile_ranks 度量提供了与 percentiles 相同的信息，但以不同方式呈现，如果对某个具体数值更关心，使用它会更方便
```