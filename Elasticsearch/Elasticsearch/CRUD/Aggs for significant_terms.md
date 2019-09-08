#### 通过聚合发现异常指标
```bash
# significant_terms（SigTerms）聚合与其他聚合都不相同
# 目前为止我们看到的所有聚合在本质上都是简单的数学计算。将不同这些构造块相互组合在一起从而可以创建复杂的聚合以及数据报表
# significant_terms 有着不同的工作机制, 它甚至看起来有点像机器学习,因为它可以在数据集中找到一些异常的指标

# 这些统计上的异常指标通常象征着数据里的某些有趣信息:
# 假设我们负责检测和跟踪信用卡欺诈，客户打电话过来抱怨他们信用卡出现异常交易，它们的帐户已经被盗用。
# 这些交易信息只是更严重问题的症状。在最近的某些地区，一些商家有意的盗取客户的信用卡信息，或者它们自己的信息无意中也被盗取
# 我们的任务是找到危害的共同点，如果我们有100个客户抱怨交易异常，他们很有可能都属于同一商户，而这家商户有可能就是罪魁祸首
# 当然这里面还有一些特例。例如很多客户在它们近期交易历史记录中会有很大的商户如亚马逊，我们可以将亚马逊排除在外
# 然而，在最近一些有问题的信用卡的商家里面也有亚马逊
# 这是一个普通的共同商户的例子。每个人都共享这个商户，无论有没有遭受危害。我们对它并不感兴趣
# 相反我们有一些很小商户比如街角的一家药店，它们属于普通但不寻常的情况，只有一两个客户有交易记录，因此同样可以将这些商户排除
# 因为所有受到危害的信用卡都没有与这些商户发生过交易，我们可以肯定它们不是安全漏洞的责任方
# 我们真正想要的是不普通的共同商户。所有受到危害的信用卡都与它们发生过交易
# 但是在未受危害的背景噪声下，它们并不明显这些商户属于统计异常，它们比应该出现的频率要高。这些不普通的共同商户很有可能就是需要调查的

# significant_terms 聚合就是做上述这些事情:
# 它分析统计数据并通过对比正常数据找到可能有异常频次的指标
# 暴露的异常指标代表什么依赖的你数据。
# 对于信用卡数据我们可能会想找出信用卡欺诈，对于电商数据，我们可能会想找出未被识别的人口信息，从而进行更高效的市场推广。
# 如果我们正在分析日志，我们可能会发现一个服务器会抛出比它本应抛出的更多异常
# 不过 significant_terms 的应用还远不止这些! ( significant_terms 统计在背景流中显著异常的指标 )
```
#### 准备 significant_terms 分析用的数据
```python
# 因为significant_terms聚合是通过分析统计信息来工作的
# 需要为数据设置一个阀值让它们更有效。也就是说无法通过只索引少量示例数据来展示它
# 正因如此这里准备了约8000个文档的数据集并将它的快照保存在一个公共演示库中。可以通过以下步骤在集群中还原这些数据：

# 1.在 elasticsearch.yml 配置文件中增加以下配置以便将演示库加入到白名单中：
repositories.url.allowed_urls: ["http://download.elastic.co/*"]
# 2.重启 Elasticsearch
# 3.运行以下快照命令
PUT /_snapshot/sigterms                         # 注册一个新的只读地址库，并指向演示快照
{
    "type": "url",
    "settings": {
        "url": "http://download.elastic.co/definitiveguide/sigterms_demo/"
    }
}
GET /_snapshot/sigterms/_all                    # （可选）检查库内关于快照的详细信息
POST /_snapshot/sigterms/snapshot/_restore      # 开始还原过程。会在集群中创建两个索引： mlmovies 和 mlratings
GET /mlmovies,mlratings/_recovery               # （可选）使用 Recovery API 监控还原过程


# 在本演示中，看看 MovieLens 里面用户对电影的评分
# 在 MovieLens 里用户可以推荐电影并评分，这样其他用户也可以找到新的电影
# 为了演示，会基于输入的电影采用 significant_terms 对电影进行推荐

# 让我们看看示例中的数据，感受一下要处理的内容。本数据集有两个索引， mlmovies 和 mlratings 。首先查看 mlmovies ：
GET mlmovies/_search        # 注: 执行一个不带查询条件的搜索，以便能看到一组随机演示文档
{
   "took": 4,
   "timed_out": false,
   "_shards": {...},
   "hits": {
      "total": 10681,
      "max_score": 1,
      "hits": [
         {
            "_index": "mlmovies",
            "_type": "mlmovie",
            "_id": "2",                     # 电影id
            "_score": 1,
            "_source": {
               "offset": 2,
               "bytes": 34,
               "title": "Jumanji (1995)"    # 电影名称
            }
         },
...
# mlmovies 里的每个文档表示一个电影，数据有两个重要字段：电影ID _id 和电影名 title
# 可以忽略 offset 和 bytes 。它们是从原始 CSV 文件抽取数据的过程中产生的中间属性。这个样例数据集中有 10681 部影片

# 现在来看看 mlratings ：
GET mlratings/_search

{
   "took": 3,
   "timed_out": false,
   "_shards": {...},
   "hits": {
      "total": 69796,
      "max_score": 1,
      "hits": [
         {
            "_index": "mlratings",
            "_type": "mlrating",
            "_id": "00IC-2jDQFiQkpD6vhbFYA",
            "_score": 1,
            "_source": {
               "offset": 1,
               "bytes": 108,
               "movie": [122,185,231,292,   # movie 字段维护一个用户观看和推荐过的影片列表
                  316,329,355,356,362,364,370,377,420,
                  466,480,520,539,586,588,589,594,616
               ],
               "user": 1
            }
         },
...
# 这里可以看到每个用户的推荐信息。每个文档表示一个用户，用 ID 字段 user 来表示
```
#### 基于流行程度推荐 ---> Recommending Based on Popularity
```python
# 可以采取的首个策略就是基于流行程度向用户推荐影片
# 对于某部影片，找到所有推荐过它的用户，然后将他们的推荐进行聚合并获得推荐中最流行的五部
# 我们可以很容易的通过一个 terms 聚合 以及一些过滤来表示它
# 看看 Talladega Nights（塔拉迪加之夜） 这部影片，它是 Will Ferrell 主演的一部关于全国运动汽车竞赛的喜剧
# 在理想情况下，我们的推荐应该找到类似风格的喜剧（很有可能也是 Will Ferrell 主演的）

# 首先需要找到影片 <<Talladega Nights>> 的影片ID：
GET mlmovies/_search
{
  "query": {
    "match": {
      "title": "Talladega Nights"
    }
  }
}

    ...
    "hits": [
     {
        "_index": "mlmovies",
        "_type": "mlmovie",
        "_id": "46970",                 # Talladega Nights 的 ID 是 46970
        "_score": 3.658795,
        "_source": {
           "offset": 9575,
           "bytes": 74,
           "title": "Talladega Nights: The Ballad of Ricky Bobby (2006)"
        }
     },
    ...

# 有了ID，可以过滤评分，再应用 terms 聚合从喜欢 Talladega Nights 的用户中找到最流行的影片：
GET mlratings/_search
{
  "size" : 0,               # 这次查询 mlratings ， 将结果内容大小设置为0因为我们只对聚合的结果感兴趣
  "query": {                # 在 mlratings 索引下搜索，然后对影片 Talladega Nights 的 ID 使用过滤器
    "filtered": {
      "filter": {
        "term": {
          "movie": 46970    # 对影片 Talladega Nights 的 ID 使用过滤器 ( 返回的是所有看过此电影的用户信息,每个用户都有一个其所看过的所有电影组成的列表key )
        }
      }
    }
  },
  "aggs": {
    "most_popular": {
      "terms": {            # 由于聚合是针对查询范围进行操作的，它有效的过滤聚合结果从而得到只推荐 Talladega Nights 的用户
        "field": "movie",   # 最后，使用 terms 桶找到最流行的影片 ( 从所有喜欢 Talladega Nights 的用户中找到他们共同的movie列,即是大家都推荐的电影 )
        "size": 6           # 请求排名最前的六个结果，因为 Talladega Nights 本身很有可能就是其中一个结果（并不想重复推荐它）
      }
    }
  }
}

# 最后，执行 terms 聚合得到最流行的影片。 
# 返回结果就像这样：
{
...
   "aggregations": {
      "most_popular": {
         "buckets": [
            {
               "key": 46970,
               "key_as_string": "46970",
               "doc_count": 271
            },
            {
               "key": 2571,
               "key_as_string": "2571",
               "doc_count": 197
            },
            {
               "key": 318,
               "key_as_string": "318",
               "doc_count": 196
            },
            {
               "key": 296,
               "key_as_string": "296",
               "doc_count": 183
            },
            {
               "key": 2959,
               "key_as_string": "2959",
               "doc_count": 183
            },
            {
               "key": 260,
               "key_as_string": "260",
               "doc_count": 90
            }
         ]
      }
   }
...

# 根据上面返回的最流行的六个影片的ID通过一个简单的过滤查询，将得到的结果转换成原始影片名：
curl -X GET "localhost:9200/mlmovies/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "filtered": {
      "filter": {
        "ids": {
          "values": [2571,318,296,2959,260]
        }
      }
    }
  }
} '
# 最后得到以下列表：
# Matrix, The（黑客帝国）
# Shawshank Redemption（肖申克的救赎）
# Pulp Fiction（低俗小说）
# Fight Club（搏击俱乐部）
# Star Wars Episode IV: A New Hope（星球大战 IV：曙光乍现）
```
#### 基于统计的推荐 ---> Recommending Based on Statistics
```python
# 现在场景已经设定好，使用 significant_terms !!!
# significant_terms 会分析喜欢影片 Talladega Nights 的用户组（ 前景特征用户组 ），并且确定最流行的电影。
# 然后为每个用户（ 后端 用户）构造一个流行影片列表，最后将两者进行比较。

# 统计异常就是与统计背景相比在前景特征组中过度展现的那些影片。
# 理论上讲，它应该是一组喜剧，因为喜欢 Will Ferrell 喜剧的人给这些影片的评分会比一般人高。

# 让我们试一下： ( 这里概括: 即使用某个索引特定的Key的值,去分析其他索引OR查询结果中的文档中与此值相关的key的其他key的共同/异常特征 )
curl -X GET "localhost:9200/mlratings/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "size" : 0,
  "query": {
    "filtered": {
      "filter": {
        "term": {
          "movie": 46970            # 喜剧电影 Will Ferrell 的id
        }
      }
    }
  },
  "aggs": {
    "most_sig": {
      "significant_terms": {        # 几乎一模一样，只是用 significant_terms 替代了 terms
        "field": "movie",
        "size": 6
      }
    }
  }
} '

# 正如所见，查询也几乎是一样的。过滤出喜欢影片 Talladega Nights 的用户，他们组成了前景特征用户组
# 默认情况下 significant_terms 会使用整个索引里的数据作为统计背景，所以不需要特别的处理
# 与 terms 类似，结果返回了一组桶，不过有更多的元数据信息：
...
   "aggregations": {
      "most_sig": {
         "doc_count": 271,                      # 顶层 doc_count 展现了前景特征组里文档的数量
         "buckets": [
            {
               "key": 46970,
               "key_as_string": "46970",        # 可以看到获得的第一个桶是 Talladega Nights 。它在所有 271 个文档中找到，但这并不意外，因为所有的用户都是喜欢这个电影的
               "doc_count": 271,
               "score": 256.549815498155,
               "bg_count": 271
            },
            {
               "key": 52245,                    # 每个桶里面列出了聚合的键值（例如，影片的ID） 这个 ID 对应影片 Blades of Glory（荣誉之刃）
               "key_as_string": "52245",
               "doc_count": 59,                 # 桶内文档的数量 , 喜欢Talladega Nights的用户对它的推荐是59次 , 这意味着21%的前景特征用户组推荐了影片 Blades of Glory ( 59/271=0.2177 )
               "score": 17.66462367106966,
               "bg_count": 185                  # 背景文档的数量，表示该值在整个统计背景里出现的频度 (  即所有用户,包括喜欢与不喜欢这个电影的所有人 )
            },                                  # 形成对比的是 Blades of Glory 在整个数据集合中仅被推荐了185次， 只占0.26% （ 185/69796=0.00265 ）
            {                                   # 因此 Blades of Glory 是个统计异常：它在喜欢 Talladega Nights 的用户中是显著的共性。这样就找到了一个好的推荐！
               "key": 8641,
               "key_as_string": "8641",
               "doc_count": 107,
               "score": 13.884387742677438,
               "bg_count": 762
            },
            {
               "key": 58156,
               "key_as_string": "58156",
               "doc_count": 17,
               "score": 9.746428133759462,
               "bg_count": 28
            },
            {
               "key": 52973,
               "key_as_string": "52973",
               "doc_count": 95,
               "score": 9.65770100311672,
               "bg_count": 857
            },
            {
               "key": 35836,
               "key_as_string": "35836",
               "doc_count": 128,
               "score": 9.199001116457955,
               "bg_count": 1610
            }
         ]
...

# 让我们看下一个桶：键值 52245 
# 这个 ID 对应影片 Blades of Glory（荣誉之刃） ，它是一部关于男子学习滑冰的喜剧，也是由 Will Ferrell 主演。
# 可以看到喜欢 Talladega Nights 的用户对它的推荐是 59 次。 
# 这也意味着 21% 的前景特征用户组推荐了影片 Blades of Glory （ 59 / 271 = 0.2177 ）

# 形成对比的是 Blades of Glory 在整个数据集合中仅被推荐了185次， 只占0.26% （ 185/69796=0.00265 ）
# 因此 Blades of Glory 是一个统计异常：它在喜欢 Talladega Nights 的用户中是显著的共性（注：uncommonly common）。这样就找到了一个好的推荐！

# 如果看完整的列表，它们都是好的喜剧推荐（其中很多也是由 Will Ferrell 主演）：
    # Blades of Glory（荣誉之刃）
    # Anchorman: The Legend of Ron Burgundy（王牌播音员）
    # Semi-Pro（半职业选手）
    # Knocked Up（一夜大肚）
    # 40-Year-Old Virgin, The（四十岁的老处男）

# 一旦开始使用 significant_terms ，可能碰到这样的情况，我们不想要最流行的，而想要显著的共性（注：uncommonly common）
# 这个简单的聚合可以揭示出一些数据里出人意料的复杂趋势!
```