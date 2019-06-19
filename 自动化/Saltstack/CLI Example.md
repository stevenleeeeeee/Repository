```bash
#salt可以无主方式运行：
salt-call --local state.highstate   #--local标签告诉minion在本地文件系统上寻找state tree，而不是去连接Master

--------------------------------------------------------------
# 查看所有模块列表
salt '*' sys.list_modules
# 查看指定模块的所有方法
salt '*' sys.list_functions grains
# salt 'agent1.salt' sys.doc test           #查看test所有的方法及用法
# salt 'agent1.salt' sys.doc test.ping      #test.ping具体用法查看
--------------------------------------------------------------

# the following would return disk usage on all targeted minions:
salt '*' disk.usage

#查看内存和磁盘信息
salt "*" status.meminfo
salt "*" status.diskstats

salt ‘*’ state.highstate                #通过入口文件执行安装apache的脚本 
salt ‘*’ state.highstate test=True      #生产环境上面命令很危险，要先测试

# echo
salt '*' test.echo 'foo: bar'

#将主服务器file_roots下的相关目录复制到被控主机的/minion/dest目录下
salt '*' cp.get_dir salt://path/to/dir /minion/dest

#将主控服务器file_roots下相关的文件复制成被控主机的/minion目录下的dest文件
salt '*' cp.get_file salt://path/to/file /minion/dest
#API调用：( API原理是通过调用master的client模块实例化一个LocalClient对象，再调用cmd()方法来实现的 )
client.cmd('*','cp.get_file',['salt://path/to/file','/minion/dest'])
#格式：'<操作目标>','<模块>','[参数]'
#例子：'*','cmd.run',['df -h']

# 将URL内容下载到被控主机的指定位置
salt '*' cp.get_url http://www.slaghdot.org /tmp/index.html

# Salt拥有巨大的函数库可用于执行，且Salt函数自带文档。执行 sys.doc 函数可以查看哪些函数可用：
salt '*' sys.doc

#解压所有机器上/tmp/sourcefile.txt.gz包
salt '*' archive.gunzip /tmp/sourcefile.txt.gz

#压缩所有机器上/tmp/sourcefile.txt
salt '*' archive.gzip /tmp/sourcefile.txt

#API调用示例：
client.cmd('*','archive.gunzip',['/tmp/sourcefile.txt.gz'])

#查看内存
salt '*' cmd.run 'free -m'
#API调用示例：
client.cmd('TestMinion','cmd.run',['free -m'])      #第三个参数是个列表，这说明可以进行多个命令的输入

#为所有被控主机安装PHP环境，根据不同系统发行版调用不同安装工具进行部署，如redhat平台的yum，等价于yum -y install php
salt '*' pkg.install php

#卸载所有被控主机的PHP环境
salt '*' pkg.remove php

#开启（enable）、禁用（disable）nginx开机自启动脚本
salt '*' service.enable nginx
salt '*' service.disable nginx

#针对nginx服务的reload、restart、start、stop、status操作
salt '*' service.reload nginx
salt '*' service.restart nginx
salt '*' service.start nginx
salt '*' service.stop nginx
salt '*' service.status nginx

#校验所有被控端的指定文件的hash值，算法除了md5还支持sha1,sha244,sha256等等...
salt '*' file.get_sum /etc/passwd md5

#校验所有被控端的/etc/fstab文件md5值是否是指定值，返回True和False
salt '*' file.check_hash /etc/fstab md5=xxxxxxxxx

# 执行命令：
salt '*' cmd.run 'ls -l /etc'

# 安装软件：
salt '*' pkg.install vim

# 列出minion上的所有接口，以及它们的IP地址，子网掩码，MAC地址等
salt '*' network.interfaces

# Available grains can be listed by using the 'grains.ls' module
salt '*' grain.ls

# 查看模块提供的key: ( Grains data can be listed by using the 'grains.items' module )
salt '*' grains.items

# 同步grains到客户端
salt '*' saltutil.sync_grains   

# 刷新客户端使得同步后的grains在客户端生效
salt '*' sys.reload_modules

# 获取自定义的grains
salt '*' grains.item name / salt 'cong-55' grains.get name ?区别

# 同时设置多个grains值 （ 单个值：grains.setval ）
salt '*' grains.setvals "{'key1': 'val1', 'key2': 'val2'}" 

# 设置grains
salt 'minion_id' grains.append  KEY  VALUE

# 查看minion中的pillar ( pillar默认路径是/srv/pillar )
salt "*" pillar.items    

# 更新pillar信息
salt '*' saltutil.refresh_pillar

# 查看piller
salt "*" pillar.items

#查看所有minion当前正在运行的jobs
salt-run jobs.active            

    salt '*' saltutil.running       # 查看正在运行的任务，找到jid
    salt '*' saltutil.kill_job jid  # 根据jid杀掉任务
    salt '*' saltutil.clear_cache   # 清除minion缓存

#查看所有minion状态
salt-run manage.status

#查看所有minion在线状态
salt-run manage.up

#查看所有minion不在线状态
salt-run manage.down

#执行所有top.sls
salt '*' state.apply

#执行指定环境下top.sls
salt '*' state.apply saltenv=dev

# 拷贝文件到远程
salt-cp '*' [ options ] SOURCE DEST
salt-cp -E '.*' [ options ] SOURCE DEST
salt-cp -G 'os:CentOS*' [ options ] SOURCE DEST

# cp.push 模块允许minion上传文件到master端
# cp.push功能默认不开启，需要修改配置文件:  file_recv: True
# salt '192.168.159.241' cp.push /etc/httpd/conf/httpd.conf

# 基于salt-api的文件分发代码：
# import salt.client
# local = salt.client.LocalClient()
# local.cmd('*', 'cp.get_file', ['salt://httpd/httpd.conf', '/root/aaaaaaa'])

#运行test.py脚本，其中script/test.py存放在file_roots指定的目录（默认在/srv/salt）
#该命令首先同步test.py到minion的cache目录，然后运行该脚本
salt '*' cmd.script salt://script/test.py

#下载URL内容到被控主机指定位置(/tmp/index.html)
salt '*' cp.get_url http://www.slashdot.ort /tmp/index.html

#指定被控端主机的/etc/hosts文件复制在被控端本地的salt cache目录，默认是 /var/cache/minion/localfiles/
#被复制的文件会连同其到根目录的整个路径都复制过去，也就是说这个命令执行之后看到的是xxx/localfiles/etc/hosts
salt '*' cp.cache_local_file /etc/hosts

#将主服务器file_roots下的相关目录复制到被控主机的/minion/dest目录下
salt '*' cp.get_dir salt://path/to/dir /minion/dest

# 将主控服务器file_roots下相关的文件复制成被控主机的/minion目录下的dest文件
salt '*' cp.get_file salt://path/to/file /minion/dest gzip=5    #开启压缩传输 ( 1表示最小压缩比，9为最大压缩比 )
#另外还有一个参数: makedirs=True 在路径不存在时将自动创建此目录

# 将URL内容下载到被控主机的指定位置
salt '*' cp.get_url http://www.slaghdot.org /tmp/index.html

#查看指定被控主机、root用户的crontab操作，如果目标用户没有crontab任务的话那么会导致返回码是1
salt '*' cron.raw_cron root

#为指定被控主机、root用户添加/usr/local/weekly任务 ( 最后一个参数是自动为这个crontab添加注解 )
salt 'TestMinion' cron.set_job '*' '*' '*' '*' 1 '/usr/bin/echo "Called"' 'Some Comment'

#删除指定主机的root用户的指定crontab任务
salt 'TestMinion' cron.rm_job '/usr/bin/echo "Called"'
#API调用:
client.cmd('TestMinion','cron.set_job',['root','*','*','*','*','1','/usr/bin/echo "Called"'])

#添加指定被控主机hosts的主机配置项
salt '*' dnsutil.hosts_append /etc/hosts 127.0.0.1 adl.yuk.com,ad2.yuk.com
#删除指定被控主机的hosts的主机配置项
salt '*' dnsutil.hosts_remove /etc/hosts ad1.yuk.com

#修改所有被控主机/etc/passwd文件的属组、用户权限、等价于chown root:root /etc/passwd
salt '*' file.chown /etc/passwd root root

#复制所有被控主机/path/to/src文件到本地的/path/to/dst文件
salt '*' file.copy /path/to/src /path/to/dst

#检查所有被控主机/etc目录是否存在，存在则返回True, 检查文件是否存在使用file.file_exists方法
salt '*' file.directory_exists /etc

#创建目录
salt '*' files.mkdir /opt/test

#获取所有被控主机/etc/passwd的stats信息
salt '*' file.stats /etc/passwd

#获取所有被控主机/etc/passwd的权限mode，如755，644
salt '*' file.get_mode /etc/passwd
#修改所有被控主机/etc/passwd的权限mode为0644
salt '*' file.set_mode /etc/passwd 0644

#在所有被控主机创建/opt/test目录
salt '*' file.mkdir /opt/test

#将所有被控主机/etc/httpd/httpd.conf文件的LogLevel参数的warn值修改为info
salt '*' file.sed /etc/httpd/httpd.conf 'LogLevel warn' 'LogLevel info'

#给所有被控主机的/tmp/test/test.conf文件追加内容‘maxclient 100’
salt '*' file.append /tmp/test/test.conf 'maxclient 100'

#删除所有被控主机的/tmp/foo文件
salt '*' file.remove /tmp/foo

#在所有被控主机端追加（append）、插入（insert）iptables规则，其中INPUT为输入链
salt '*' iptables.append filter INPUT rule='-m state --state RELATED,ESTABLISHED -j ACCEPT'
salt '*' iptables.insert filter INPUT position=3 rule='-m state --state RELATED,ESTABLISHED -j ACCEPT'

#在所有被控主机删除指定链编号为3（position=3）或指定存在的规则
salt '*' iptalbes.delete filter INPUT position=3
salt '*' iptables.delete filter INPUT rule='-m state --state RELATEC,ESTABLISHED -j ACCEPT'

#保存所有被控主机端主机规则到本地硬盘（/etc/sysconfig/iptables）
salt '*' iptables.save /etc/sysconfig/iptables

#在指定被控主机获取dig、ping、traceroute目录域名信息
salt 'wx' network.dig www.qq.com
salt 'wx' network.ping www.qq.com
salt 'wx' network.traceroute www.qq.com

#获取指定被控主机的mac地址
salt 'wx' network.hwaddr eth0

#检测指定被控主机是否属于10.0.0.0/16子网范围，属于则返回True
salt 'wx' network.in_subnet 10.0.0.0/16

#获取指定被控主机的网卡配置信息
salt 'wx' network.interfaces

#获取指定被控主机的IP地址配置信息
salt 'wx' network.ip_addrs

#获取指定被控主机的子网信息
salt 'wx' network.subnets

#包管理：
#pkg.install php
#pkg.remove php
#pkg.upgrade php

#network.ping 127.0.0.1　　         查看ping某个域名的情况
#network.traceroute 127.0.0.1　　   查看traceroute到某个域名的情况
#network.hwaddr eth0　　            查看eth0网卡的物理地址
#network.in_subnet 10.0.0.0/16　　  查看被控端的ip是否在指定网段内
#network.interfaces　　             查看网卡配置信息
#network.ip_addrs　　               查看IP地址配置信息
#network.subnets　　                查看子网信息

root@saltmaster:~# salt myminion grains.item pythonpath --out=pprint
{'myminion': {'pythonpath': ['/usr/lib64/python2.7',
                             '/usr/lib/python2.7/plat-linux2',
                             '/usr/lib64/python2.7/lib-tk',
                             '/usr/lib/python2.7/lib-tk',
                             '/usr/lib/python2.7/site-packages',
                             '/usr/lib/python2.7/site-packages/gst-0.10',
                             '/usr/lib/python2.7/site-packages/gtk-2.0']}}
```
#### iptables
```bash
#在所有被控主机端追加（append）、插入（insert）iptables规则，其中INPUT为输入链
salt '*' iptables.append filter INPUT rule='-m state --state RELATED,ESTABLISHED -j ACCEPT'
salt '*' iptables.insert filter INPUT position=3 rule='-m state --state RELATED,ESTABLISHED -j ACCEPT'

#在所有被控主机删除指定链编号为3（position=3）或指定存在的规则
salt '*' iptalbes.delete filter INPUT position=3
salt '*' iptables.delete filter INPUT rule='-m state --state RELATEC,ESTABLISHED -j ACCEPT'

#保存所有被控主机端主机规则到本地硬盘（/etc/sysconfig/iptables）
salt '*' iptables.save /etc/sysconfig/iptables
```