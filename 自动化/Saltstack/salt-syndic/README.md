```bash
# ref: 
# https://www.cnblogs.com/bfmq/p/7919609.html

#Syndic必须运行在一个master上,然后连到最上层master（这台机器就可以管理syndic-master所管理的机器）
#Syndic节点必须运行salt-syndic和salt-master守护进程及可选的salt-minion

#组织结构: ( salt-syndic节点可以是多个，多个syndic节点所在的机器需同时部署salt-syndic/master )
[salt-master] ---> [salt-syndic]
                   [salt-master] ---> [salt-minion]

#------------------------------------------------------------ salt-master ( 最上层 )

#修改最上层Master配置文件：/etc/salt/master
order_masters: True                        #表示允许开启多层master
#当额外的数据需要发送和传递并且这个master控制的minions是被低等级的master或syndic直接管理下那么此值须设为True
#配置完成后重启salt-master
systemctl restart salt-master 

#------------------------------------------------------------ salt-syndic + salt-maste

#在代理端执行如下：( 需要注意：syndic节点的所有sls文件必须与最上层的master执行同步! )
#默认情况下Syndic的配置文件位于Master的配置文件中: /etc/salt/master
yum install salt-syndic -y

vim /etc/salt/proxy
master: 192.168.10.100                      #在salt-syndic中设置其指向的最上层salt-master的地址

vim /etc/salt/master
syndic_master: 192.168.10.100               #在salt-syndic所在的机器的salt-master中设置最上层salt-master地址
syndic_wait: 10                             #https://docs.saltstack.com/en/latest/topics/topology/syndic.html

vim /etc/salt/minion                        #在salt-syndic所在的机器与其同节点的salt-minion共用相同id!
id: syndic-master                           #

systemctl enable salt-master --now
systemctl enable salt-syndic --now

# 注意：
# 在最上层master节点执行 salt-key –L 不会看到经salt-syndic接受的minion ( 在最上层master中需要接受syndic的公钥 )
# 但是在最上层master执行 salt '*' test.ping 之类的操作时将能够被最下级的minion执行
# 由于Syndic只订阅最上层Master下发的任务, 对于文件服务等, Syndic本地需要进行配置
# syndic节点所有sls文件必须与最上层master同步，因为所有底层minion订阅到任务时都是去自己的直接上层获取sls并执行
# syndic本地会维护auth及文件服务系统。保证各个syndic与master的文件目录保持统一! 
# Syndic本质上是一个特殊的Minion ( 需保证Syndic上的file_roots及pillar_roots与顶层master是一致的! )
# 由于Syndic管理了其下Minions的认证, 因此最上层Master并不知道有多少Syndic主机，Syndic下边有多少Minions.
#------------------------------------------------------------ salt-minion 

#在minion中将master地址指向salt-syndic的地址:
vim /etc/salt/minion
master: 192.168.10.101                      #所有的minion端不再直接指向最上层master，而是指向syndic所在的节点

systemctl restart salt-minion
```
#### 注意
```bash
#在最上层master做资源管理 state （pillar grains module）时不能直接在top.sls下指定minon id 但是可直接管理minion
#在最上层master的top.sls 不能指定minon的id 但是可以直接管理minon 让他去他的master干啥（分组是可以的）

#当顶层salt-master守护程序发出命令时，它将由直接连接到它的Syndic和Minion节点接收
#Minion节点将以通常的方式处理命令。在Syndic节点上的salt-syndic将该命令中继到Syndic节点上运行的salt-master守护程序
#然后该节点将命令传播到与其连接的Minions和Syndics

# 顶层master接受syndic的key，即相当于接受此syndic下所有minion的key：
#The Master node will now be able to control the Minion nodes connected to the Syndic. 
#Only the Syndic key will be listed in the Master node's key registry 
#but this also means that key activity between the Syndic's Minions and the Syndic does not encumber the Master node. 
#In this way, the Syndic's key on the Master node can be thought of as a placeholder for the keys of all the Minion 
#and Syndic nodes beneath it, giving the Master node a clear, high level structural view on the Salt cluster.


# CONFIGURING THE SYNDIC WITH MULTIMASTER：
#Syndic with Multimaster lets you connect a syndic to multiple masters to provide an additional layer of redundancy in a syndic configuration.
#On the syndic, the syndic_master option is populated with a list of the higher level masters.
#Since each syndic is connected to each master, jobs sent from any master are forwarded to minions that are connected to each syndic. If the master_id value is set in the #master config on the higher level masters, job results are returned to the master that originated the request in a best effort fashion. Events/jobs without a master_id are #returned to any available master.
```