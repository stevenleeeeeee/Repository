```bash
ref: https://docs.saltstack.com/en/latest/topics/tutorials/multimaster.html#tutorial-multi-master

# When using a multi-master setup, all masters are running hot
# and any active master can be used to send commands out to the minions.
#在建立多Master的配置中，主要的一点就是所有的Master使用相同private key，这些key在Master第一次启动时自动生成。
#因此在多Master环境建立时需从原始的Master拷贝其private key至第二个Master以替换它启动时自动生成的那个, 以此类推。
#Master的private key存储在本地 pki_dir 目录下. 默认为：/etc/salt/pki/master/master.pem 和master.pub
#将这两个文件拷贝到新增的master上. 需注意在拷贝时要确保新增的master上没有minion连接进来.（最好暂时不要启动冗余master）
#Once the new key is in place, the redundant master can be safely started.

#修改minion端配置，连接多个master:
#注意在此之前确保minion的key没有存在任何master上，也就是说minion没有和任何master完成认证过?!
vim /etc/salt/minion
master_alive_interval: 30
master:
  - master1
  - master2

systemctl restart minion
#minion以串行的方式向master发送认证请求
#一般是先验证minion配置中的第一个master（master1），master1认证完成后，在向master2发送认证请求

#在两个Master间需要同步minion key：
#在所有的master节点中需要同时接受所有的minion key
#在一个主设备上接受/删除/拒绝的密钥不会在冗余的master上同步，因此需通过在两个主服务器上运行相同的salt-key命令
#或在主服务器之间共享/etc/salt/pki/master/{minions,minions_pre,minions_rejected} 目录

#在两个Master间需要同步sls:
#保持master的配置内容一致，主要是file_roots，external_auth等的配置一致，若配置了nodegroup 需保持nodegroup的文件内容及地址一致
#同步master的file_roots,可以放在第三方软件库svn、git库，也可放在一个共享的ftp等，此外还要考虑pillar数据的共享
#在使用的时候可以只调用master1，在master1无法连接时自动使用master2来控制minion
#此外，若存在访问控制，则应在Master间保持同步

# Notic:
# If using gitfs/git_pillar with the cachedir shared between masters using GlusterFS, nfs,
# or another network filesystem, and the masters are running Salt 2015.5.9 or later, 
# it is strongly recommended not to turn off gitfs_global_lock/git_pillar_global_lock as doing 
# so will cause lock files to be removed if they were created by a different master.

#此时所有Master均可以控制此minion
```