```bash
ref: https://docs.saltstack.com/en/latest/topics/tutorials/multimaster.html#tutorial-multi-master

# When using a multi-master setup, all masters are running hot
# and any active master can be used to send commands out to the minions.
#在建立多Master的配置中，需注意所有Master使用相同的private key，这些key在Master第一次启动时自动生成
#因此在多Master环境建立时需从原始的Master拷贝其private key至第二个Master以替换它启动时自动生成的那个
#Master的private key存储在本地pki_dir目录. 默认：/etc/salt/pki/master/master.pem 和 master.pub
#将这两个文件拷贝到新增的master上. 需注意在拷贝时要确保新增的master上没有minion连接进来
#Once the new key is in place, the redundant master can be safely started.

#--------------------------------------------------------------- 同步两台Master的key

#将原始Master的公私钥拷贝到新的Master节点 ( 拷贝证书时新Master节点先不要启动，当拷贝完成后才可以安全的启动冗余Master )
scp /etc/salt/pki/master/master* root@<NEWMASTER>:/etc/salt/pki/master/

#在两个Master的Pillar_Roots、File_roots、external_auth、及各自配置文件等的配置一致的前提下启动冗余Master：
systemctl enable salt-master --now

#--------------------------------------------------------------- 修改minion配置

#修改minion端配置，连接多个master:
#注意在此之前确保minion的key没有存在任何master上，也就是说minion没有和任何master完成认证过?!
vim /etc/salt/minion
master_alive_interval: 30
master:
  - master1
  - master2

systemctl restart minion
#minion以串行方式向master发送认证请求
#一般是先验证minion配置的第1个master，当master1认证完成后再向master2发送认证请求

#--------------------------------------------------------------- 在冗余Master端接收minion公钥

#在两个Master间需要同步minion key：
#在所有的master节点中需要同时接受所有的minion key
#在一个主设备上接受/删除/拒绝的密钥不会在冗余的master上同步，因此需通过在两个主服务器上运行相同的salt-key命令
#或者在主服务器之间共享 /etc/salt/pki/master/{minions,minions_pre,minions_rejected} 目录

#在新的冗余Master主机中接受所有的salt-key:
salt-key -A

#在2个Master间需同步数据:
#保持master的配置内容一致，主要是file_roots，external_auth等配置，若存在nodegroup则需保持两边的nodegroup信息一致
#同步master的file_roots,可放在第三方软件库svn、git库，也可放在一个共享的ftp等，此外还要考虑pillar数据的共享
#此外若存在访问控制，则应在Master间保持同步。 在使用时可只调用master1，在master1无法连接时自动使用master2来控制minion
#这里建议使用Rsync周期同步数据：

ip=x.x.x.x
rsync -avzP --delete -e 'ssh -p 22 -o StrictHostKeyChecking=no' /etc/salt/pki/master/master* $ip:/etc/salt/pki/master/
rsync -avzP --delete -e 'ssh -p 22 -o StrictHostKeyChecking=no' /etc/salt/master $ip:/etc/salt/master
rsync -avzP --delete -e 'ssh -p 22 -o StrictHostKeyChecking=no' /srv/salt  $ip:/srv/salt
rsync -avzP --delete -e 'ssh -p 22 -o StrictHostKeyChecking=no' /srv/pillar  $ip:/srv/pillar
rsync -avzP --delete -e 'ssh -p 22 -o StrictHostKeyChecking=no' /etc/salt/roster  $ip:/etc/salt/roster
rsync -avzP --delete -e 'ssh -p 22 -o StrictHostKeyChecking=no' /etc/salt/master.d  $ip:/etc/salt/master.d

#---------------------------------------------------------------
#此时所有Master均可控制所有的minion

# Notic:
# If using gitfs/git_pillar with the cachedir shared between masters using GlusterFS, nfs,
# or another network filesystem, and the masters are running Salt 2015.5.9 or later, 
# it is strongly recommended not to turn off gitfs_global_lock/git_pillar_global_lock as doing 
# so will cause lock files to be removed if they were created by a different master.
```
#### salt-syndic + multi-master
```bash
#注意在使用这种架构时，两个syndic+master节点同时运行其中1个，否则从顶层master执行命令时在minion端会执行2次
#因为salt机制会在每个syndic都转发命令到下面的minion! 这里建议使用heartbeat做主备模式

[master] ---> [syndic+master](alive) <-----> [salt-minion]
            \ [syndic+master](down) <-----> [salt-minion]

#修改minion的配置文件加入对 salt-syndic + multi-master 的支持
vim /etc/salt/minion
master:  
    - xx.xx.xx.xx           #连接到多个master
    - xx.xx.xx.xx
    - xx.xx.xx.xx
master_type: failover		    #设置为failover minion
master_shuffle: True		    #启动时随机选择一台master
master_alive_interval: 30	  #探测master是否存活的schedule job


#当设置master_type: failover并且master_shuffle: True时这样在多master的环境中启用syndic之后将实现类似负载的功能
#顶层master发送消息到下面的syndic，每个syndic下发消息到各自的minion中去执行
```