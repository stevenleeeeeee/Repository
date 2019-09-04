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


# 在索引级别设置节点分片总数，即设置索引在每个节点上最大能分配的分片个数，该配置可以使用API进行动态更新
PUT <INDEX_NAME>/_settings
{
  "index.routing.allocation.total_shards_per_node" : 3    # 1个es-data节点上最多分3个分片
}


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

#更新磁盘阈值限制
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