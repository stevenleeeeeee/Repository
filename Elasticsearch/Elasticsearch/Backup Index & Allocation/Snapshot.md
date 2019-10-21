```bash
# 如果ES是集群，那么需要使用共享存储，支持的存储有：
# a、shared file system
# b、S3
# c、HDFS

# 这里使用NFS共享文件系统
# ES是使用 elasticsearch 用户启动的，要保证共享目录对 elasticsearch 用户有读写权限，不然创建仓库和快照时会报500错误

# 在nfs-server上导出共享目录的权限配置，这里将所有连接用户都压缩为root权限：
vim /etc/exports
/data/es 192.168.1.0/24((rw,sync,all_squash,anonuid=0,anongid=0,no_subtree_check) 

/etc/init.d/nfs-kernel-server reload

# 创建挂载目录，并给予权限
mkidr -pv /nh/esbk/my_backup
chmod 755 /nh/esbk/
chown elasticsearch.elasticsearch /nh/esbk/


# 各节点挂载共享目录

# vim /etc/fstab
192.168.3.97:/data02/es   /nh/esbk/my_backup    nfs    defaults    0 0
# mount -a
# df -hT


# 注册快照仓库到ES，这里是在 kibana 的 Dev Tools 上操作的，也可以使用 curl 发起请求
PUT /_snapshot/my_backup
{
  "type": "fs",
  "settings": {
        "compress": true,
        "location": "/nh/esbk/my_backup"
  }
}

# 查看仓库信息
GET /_snapshot/my_backup
# curl -u elastic -XGET 'http://192.168.xx.xx:9200/_snapshot/my_backup?pretty'
{
  "my_backup" : {
    "type" : "fs",
    "settings" : {
      "compress" : "true",
      "location" : "/nh/esbk/my_backup"
    }
  }
}

# 创建快照
PUT /_snapshot/my_backup/snapshot_1
# 这里发起请求后，会立马返回 true，并在后台执行操作。如果想等待执行完成之后再返回，可以加一个参数：
# PUT /_snapshot/my_backup/snapshot_1?wait_for_completion=true


# 查看刚才创建的快照的信息
GET /_snapshot/my_backup/snapshot_1

{
  "snapshots": [
    {
      "snapshot": "snapshot_1",
      "uuid": "xSMRNVMIRHmx_qlhX5fqfg",
      "version_id": 5040199,
      "version": "5.4.1",
      "indices": [
        ".monitoring-kibana-2-2017.07.05",
        ".monitoring-kibana-2-2017.07.11",
        "zixun-nginx-access-2017.07.12",
        ".monitoring-logstash-2-2017.07.07",
        ".monitoring-kibana-2-2017.07.07",
        "filebeat-2017.07.07",
        ".watcher-history-3-2017.07.04",
        ".watcher-history-3-2017.07.07",
        ".monitoring-es-2-2017.07.05",
        ".kibana",
        ".monitoring-data-2",
        ".watcher-history-3-2017.06.27",
        ".monitoring-logstash-2-2017.07.10",
        ".monitoring-kibana-2-2017.07.10",
        ".monitoring-es-2-2017.07.08",
        ".monitoring-logstash-2-2017.07.12",
        ".monitoring-es-2-2017.07.10",
        ".watcher-history-3-2017.07.06",
        ".monitoring-kibana-2-2017.07.09",
        ".watcher-history-3-2017.07.12",
        ".watcher-history-3-2017.07.03",
        ".monitoring-alerts-2",
        ".monitoring-logstash-2-2017.07.08",
        ".watcher-history-3-2017.07.01",
        ".watcher-history-3-2017.07.11",
        ".watcher-history-3-2017.07.05",
        ".watcher-history-3-2017.06.29",
        ".watcher-history-3-2017.06.28",
        ".monitoring-kibana-2-2017.07.08",
        ".security",
        ".monitoring-logstash-2-2017.07.11",
        ".monitoring-es-2-2017.07.11",
        ".watcher-history-3-2017.06.30",
        ".triggered_watches",
        ".watcher-history-3-2017.07.08",
        ".monitoring-es-2-2017.07.12",
        ".watcher-history-3-2017.07.09",
        ".monitoring-es-2-2017.07.09",
        ".monitoring-kibana-2-2017.07.12",
        ".monitoring-kibana-2-2017.07.06",
        ".watcher-history-3-2017.07.10",
        "test",
        ".monitoring-es-2-2017.07.07",
        ".monitoring-logstash-2-2017.07.09",
        ".watches",
        ".monitoring-es-2-2017.07.06",
        ".watcher-history-3-2017.07.02"
      ],
      "state": "SUCCESS",
      "start_time": "2017-07-12T04:19:08.246Z",
      "start_time_in_millis": 1499833148246,
      "end_time": "2017-07-12T04:20:04.717Z",
      "end_time_in_millis": 1499833204717,
      "duration_in_millis": 56471,
      "failures": [],
      "shards": {
        "total": 59,
        "failed": 0,
        "successful": 59
      }
    }
  ]
}


# 列出一个仓库里的所有快照
GET /_snapshot/my_backup/_all

# 删除一个快照
DELETE /_snapshot/my_backup/snapshot_1

# 删除一个仓库
DELETE /_snapshot/my_backup

# 恢复一个快照（支持恢复部分数据以及恢复过程中修改索引信息，具体细节参考官方文档）
POST /_snapshot/my_backup/snapshot_1/_restore

# 查看快照状态信息（比如正在创建或者创建完成等）
# a、列出所有当前正在运行的快照以及显示他们的详细状态信息
GET /_snapshot/_status

# b、查看指定仓库的正在运行的快照以及显示他们的详细状态信息
GET /_snapshot/my_backup/_status

# 查看指定快照的详细状态信息即使不是正在运行
GET /_snapshot/my_backup/snapshot_1/_status

# d、支持同时指定多个快照ID查看多个快照的信息
GET /_snapshot/my_backup/snapshot_1,snapshot_2/_status

# 如果要停止一个正在运行的snapshot任务（备份和恢复），将其删除即可。
```