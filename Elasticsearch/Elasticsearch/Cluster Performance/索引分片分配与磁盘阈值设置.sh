#集群级别
PUT _cluster/settings
{
  "persistent": {
    "cluster": {
      "routing": {
        "allocation.cluster_concurrent_rebalance": 2,  # 最多允许多少分片同时迁移，默认2 ( 此参在关闭负载时建议不写 )
        "allocation.enable": "all"                     # 用哪种方式路由，有好几种参数 ( 关闭集群负载，使用：none )
      }
    }
  },
  "transient": {
    "cluster": {
      "routing": {
        "allocation.cluster_concurrent_rebalance": 2,
        "allocation.enable": "all"
      }
    }
  }
}


# 新加入集群的节点，分片总数远远低于其他节点。这时候如果有新索引创建，ES 的默认策略会导致新索引的所有主分片几乎全分配在这台新节点上。
# 整个集群的写入压力压在一个节点上，结果很可能是这个节点直接被压死，集群出现异常。 
# 所以对于 Elastic Stack 场景，强烈建议预先计算好索引的分片数后，配置好单节点分片的限额。比如一个5节点的集群，索引主分片10个，副本1份。则平均下来每个节点应该有4个分片，那么就配置：5
# 在索引级别设置节点分片总数，即设置索引在每个节点上最大能分配的分片个数，该配置可以使用API进行动态更新:
PUT <INDEX_NAME>/_settings
{
  "index.routing.allocation.total_shards_per_node" : 5    # 1个es-data节点上最多分5个分片
}
# 注意，这里配置的是 5 而不是 4。因为我们需要预防有机器故障，分片发生迁移的情况。如果写的是 4，那么分片迁移会失败


# Elasticsearch 中有一系列参数，相互影响，最终联合决定分片分配：
cluster.routing.allocation.balance.shard    # 节点上分配分片的权重，默认为 0.45。数值越大越倾向于在节点层面均衡分片
cluster.routing.allocation.balance.index    # 每个索引往单个节点上分配分片的权重，默认 0.55。值越大越倾向于在索引层面均衡分片



# 参考：
# https://blog.csdn.net/an74520/article/details/42871023
# 
# 在一个已创立的集群里，shard的分布总是均匀的。但是当扩容节点的时候会发现它总是先移动replica shard到新节点
# 这样就导致新节点全部分布的全是副本，主shard几乎全留在了老的节点上。
# 
# cluster.routing.allocation.balance参数，比较难找到合适的比例。
# 
# 建议一种方式是在扩容时设置 cluster.routing.allocation.enable=primaries 只允许移动主shard。
# 当你发现shard数已经迁移了一半的时改回 cluster.routing.allocation.enable=all 这样后面的全迁移的是副本shard。
# 扩容之后，shard和主shard的分布还是均匀的。
# curl -XPUT 'http://192.168.1.1:9200/_cluster/settings' -d '{
# "transient" : {
# "cluster.routing.allocation.enable" : "primaries"
# }
# }'
# 
# 那如果shard分布已经不均匀了，也可以手动进行shard迁移。
# curl -XPOST 'http://192.168.1.1:9200/_cluster/reroute' -d '{
#   "commands" : [ {
#           "move" : {
#               "index" : "index_1", "shard" : 23,
#               "from_node" : "192.168.1.1", "to_node" : "192.168.1.2"
#           }
#   } ]
# }'

# ------------------------------------------------- 设置索引分片与节点之间的绑定关系

# 创建索引时将index.routing.allocation.include.tag属性设置为value1、value2后，将会创建只部署在相应节点有相关tag的索引：
curl -XPUT localhost:9200/test/_settings -d '{
    "index.routing.allocation.include.tag" : "value1,value2"
}'

#  如果不想将索引添加到上述两个节点上，可使用index.routing.allocation.exclude.tag属性：
curl -XPUT localhost:9200/test/_settings -d '{
    "index.routing.allocation.exclude.tag" : "value1,value2"
}'

# include,exclude和require的值也支持简单的通配符，比如value1*
# 另外，_ip,_name,_id和_host这些属于特定的属性名称，它们分别匹配节点的IP地址，名称，ID和主机名
# 以上的索引配置可以使用API进行实时的更新。

# ------------------------------------------------- 基于磁盘状态的分片分配

# 修改触及"low disk watermark"阈值的磁盘使用比例（默认超过85%将不落主分片的副本）
# cluster.routing.allocation.disk.watermark.low:
# 若磁盘使用超过85%则ES不允许在分配新的分片。当配置具体的大小如100MB时，表示若磁盘空间小于100MB则不允许分配分片

# cluster.routing.allocation.disk.watermark.high:
# 磁盘空间使用高于90%时ES将尝试分配分片到其他节点

curl -XPUT 'localhost:9200/_cluster/settings' -d
'{
    "transient": {  
      "cluster.routing.allocation.disk.watermark.low": "90%",  
      "cluster.routing.allocation.disk.watermark.high"："95%"
    }
}'

# 更新磁盘阈值限制
curl -XPUT "http://localhost:9200/_cluster/settings" -d'
{
  "persistent": {
    "cluster": {
      "routing": {
        "allocation.disk.threshold_enabled": false
      }
    }
  }
}'


# 设置每个节点的磁盘写入速率，默认20MB/s
PUT /_cluster/settings
{
    "persistent" : {
        "indices.store.throttle.max_bytes_per_sec" : "100mb"
    }
}


# 如果你使用的是机械磁盘而非 SSD，需要添加下面配置到 elasticsearch.yml 里：
# 机械磁盘在并发 I/O 支持方面比较差，所以我们需要降低每个索引并发访问磁盘的线程数
index.merge.scheduler.max_thread_count: 1

# ------------------------------------------------- 强制迁移主分片

curl -XPOST 'localhost:9200/_cluster/reroute' -d '{
    "commands": [
        {
            "allocate": {
                "allow_primary": "true",
                "index": "constant-updates",
                "node": "<NODE_NAME>",
                "shard": 0
            }
        }
    ]
}'

# ------------------------------------------------- 

#将主分片分配给含有陈旧副本分片的节点
#此命令可能会导致所提供的分片ID发生数据丢失。如果稍后具有良好数据副本的节点重新加入群集，则该数据将被使用此命令强制分配的旧副本数据覆盖
#为确保这些影响得到充分理解，需要accept_data_loss明确设置专用字段才能true使其工作
{
  "commands": [
    {
      "allocate_stale_primary": {
        "index": "mail_store",
        "shard": 1,
        "node": "slave2",
        "accept_data_loss": true
      }
    }
  ]
}

# Elasticsearch Version 6.4 ( 支持 5.5.0 )
# move 将已启动的分片从一个节点移动到另一个节点。接受索引名称和分片编号
# allocate_replica 将未分配的副本分片分配给节点。接受索引名称和分片编号，以及node分配分片
POST /_cluster/reroute
{
    "commands" : [
        {
            "move" : {
                "index" : "test", "shard" : 0,
                "from_node" : "node1", "to_node" : "node2"
            }
        },
        {
          "allocate_replica" : {
                "index" : "test", "shard" : 1,
                "node" : "node3"
          }
        }
    ]
}