#### Install Master/minion
```bash
# 设置防火墙：
# 由于salt并不是依赖于SSH进行通信的，所以要开通额外的端口，默认配置下master走4505，minion走4506这两个端口
# Centos 7:
# firewall-cmd --permanent --zone=<zone> --add-port=4505-4506/tcp
# firewall-cmd --reload

# Centos 6:
# iptables -A INPUT -m state --state new -m tcp -p tcp --dport 4505 -j ACCEPT
# iptables -A INPUT -m state --state new -m tcp -p tcp --dport 4506 -j ACCEPT

[root@localhost ~]# yum -y install epel-release

#Master
[root@localhost ~]# echo '192.168.70.129 master.salt.com' >> /etc/hosts
[root@localhost ~]# cat /etc/sysconfig/network   
HOSTNAME=master.salt.com
[root@localhost ~]# yum install -y salt-master salt-minion salt-ssh salt-api    
[root@localhost ~]# systemctl enable salt-master    #Master占用4505和4506端口。
ot@localhost ~]# systemctl start salt-master

#Slave
[root@localhost ~]# echo '192.168.70.129 slave.salt.com' /etc/hosts
[root@localhost ~]# cat /etc/sysconfig/network   
HOSTNAME=salve.salt.com
[root@localhost ~]# yum install -y salt-minion
[root@localhost ~]# systemctl enable salt-minion    #Minion有无Salt Master时都可运作!
[root@localhost ~]# systemctl start salt-minion     
#Minion启动后会产生用于标识自身的id编号，除非已在之前运行过程中产生并缓存在配置路径下，默认为：/etc/salt
#Minion用id为名称尝试去master进行验证 (每个minion使用唯一的minion ID注册自身，也可直接修改minion配置中的id来明确定义)

# When a minion starts, by default it searches for a system that resolves to the salt hostname
# 因此也可以将DNS的salt映射改为salt master主机的IP地址
[root@localhost ~]# cat /etc/salt/minion | grep master:
master: saltmaster.example.com
```
#### 说明
```bash
1.Salt的执行程序可以写为纯Python模块。其运行快，安装简单，高度可定制
2.数据在miniion执行的过程可以发送回master服务端或者发送到任何其他的任意程序...
3.Salt可从简单的Python API调用、从命令行调用、可用来执行一次性命令，也可作为一个更大的应用程序的组成部分

#salt可以无主方式运行： ( salt-call 命令通常在minion执行，minion自己执行可执行模块，不是通过master下发job )
salt-call --local state.highstate #--local标签告诉minion在本地文件系统上寻找state tree，而不是去连接Master

#若master的file_roots设置如下，运行时若想指定dev环境的话，使用参数: salt '*' state.sls top saltenv='dev' 
#Salt文件服务器的默认环境为为base环境，base环境必须定义，因为当环境没有明确指定时，文件下载就是从base环境中去找的
file_roots:
  base:
    - /srv/salt/  
  dev:
    - /srv/salt/dev/

```
#### 配置认证、Example
```bash
[root@localhost ~]# salt-key -L
Accepted Keys:      #认证通过的
Denied Keys:        #被拒绝的
Unaccepted Keys:    #未进行认证的
minion.salt.com
Rejected Keys:      #
[root@localhost ~]# salt-key -A -y    #自动接受所有证书签名请求。
[root@localhost ~]# salt-key -L       #查看证书签发状态
Accepted Keys:
minion.salt.com
Denied Keys:
Unaccepted Keys:
Rejected Keys:

#备忘: ----------------------------------------- ( 一般而言master必须有minion的证书的情况下才能顺利地进行通信 )
salt-key -L              #查看所有minion-key
salt-key -A              #接受所有的minion-key
salt-key -A -y           #自动接受所有证书签名请求
salt-key -a <key-name>   #接受某个minion-key
salt-key -D              #删除所有的minion-key
salt-key -d <key-name>   #删除某个minion-key
------------------------------------------------
# Saltstack对target的几种匹配方式：
#
#     通配符匹配:   salt "*" test.ping
#     正则表达式:   salt -E "linux-node[0-1].example.com" test.ping
#     Grains匹配:   salt -G 'os:CentOS' test.ping
#     IP地址匹配:   salt -S "192.168.56.0/24" test.ping
#     列表支持:     salt -L "node1,node2" "test.ping"
#     复合匹配:     salt -C 'S@192.168.56.11 or E@linux-node[0-2].example.com' test.ping

#     G -- 针对 Grains 键值匹配，例如：G@os:Ubuntu
#     P -- 针对 Grains 正则匹配，例如：P@os:(RedHat|Fedora|CentOS)
#     E -- 针对 minion 正则匹配，例如：E@web\d+.(dev|qa|prod).loc
#     L -- 针对 minion 组成列表，例如：L@minion1.example.com,minion3.domain.com or bl*.domain.com
#     I -- 针对 Pillar 单个匹配，例如：I@pdata:foobar
#     S -- 针对子网或IP匹配，例如：S@192.168.1.0/24 or S@192.168.1.100
#     R -- 针对客户端范围匹配，例如： R@%foo.bar

#定义主机组时也支持上述方式:
nodegroups:
  group1: 'L@foo.domain.com,bar.domain.com,baz.domain.com and bl*.domain.com'
  group2: 'G@os:Debian and foo.domain.com'
  group3: 'G@os:Debian and N@group1'
------------------------------------------------
# salt-run [options] [runner.func] 该命令执行runner，通常在master端执行。
salt-run manage.status   #查看所有minion状态
salt-run manage.down     #查看所有没在线minion
salt-run manged.up       #查看所有在线minion

#使用 test.ping 是确认与minion是否正常通讯的好方法 ( 实际执行的不是一个真正的Ping )：
[root@localhost ~]# salt '*' test.ping --out=json   #格式： salt 'target' module.function args
{
    "minion.salt.com": true
}
[root@localhost salt]# cd /srv/salt && cat top.sls 
base:
  '*':          #通过正则去匹配所有minion
    - nginx     #用户定义的状态文件名称，若"nginx"是目录，则此目录内若有init.sls文件则会将加载此目录所有的sls文件!

  my_app:       #通过分组名进行匹配，分组必须要实现在master的配置文件中事先定义: nodegroup
    - match: nodegroup  #匹配分组名为my_app的主机
    - nginx

  'os:Redhat':  #通过grains匹配，必须要定义match:grain
    - match: grain  #!
    - nginx

  'webserver* and G:CentOS or L@127.0.0.1,test1':   #复合匹配 "eg： salt -C 'xxxxxx' "
    - match: compound
    - webserver


#"include" 即包含某个文件，比如新建的一个my_webserver.sls文件内就可继承nginx和php相关模块配置而不必重新编写
[root@localhost salt]# cat my_webserver.sls 
include:    #这里需要注意，invlude的路径是salt://开始的，即默认的：/srv/salt/
  - nginx
  - php

#"watch" 即在某个state变化时运行此模块，文中配置为相关文件变化后立即执行相应操作:
- watch:
  - file: /etc/nginx/nginx.conf
  - file: /etc/nginx/fastcgi.conf
  - pkg: nginx

#"order" 优先级比require和watch低，有order指定的state比没有order指定的优先级高
#假如一个state模块内安装多个服务，或者其他依赖关系，可以使用:
nginx:
  pkg.installed:
    - order: 1    #想让某个state最后运行，可用 last ( 数字越小越先执行 )


#master    秘钥对默认存储在:    /etc/salt/pki/master/master.pub  /etc/salt/pki/master/master.pem
#master    端认证的公钥存储在:  /etc/salt/pki/master/minions/
#minion    秘钥对默认存储在:    /etc/salt/pki/minion/minion.pub  /etc/salt/pki/minion/minion.pem
#minion    存放的master公钥:   /etc/salt/pki/minion/minion_master.pub
#minion_id 默认存储在:         /etc/salt/minion_id
```
#### Grains / pillar
```bash
# grains / pillar 比较：
# 1.grains存储静态、不常变化的内容，而pillar相反
# 2.grains存储在minion本地，而pillar存储在master本地
# 3.minion有权限操作自己的grains值，如增、删，但对于pillar来说它只能查看属于自己的pillar信息而且无权修改
# 4.GRAINS在MINION启动时加载，运行过程中不发生变化，所以称为静态数据!
# 5.GRAINS中包含诸如运行的内核版本，操作系统等信息...
# 6.这些静态"属性"可以在minion配置文件中设置，也可以通过grains.setval函数设置

[root@localhost ~]# salt '*' grains.items   #查看grains提供的KEY
[root@localhost ~]# salt '*' sys.list_functions grains #查看grains提供的函数
minion.salt.com:
    - grains.append
    - grains.delval
    - grains.filter_by
    - grains.get
    - grains.get_or_set_hash
    - grains.has_value
    - grains.item
    - grains.items
    - grains.ls
    - grains.remove
    - grains.setval
    - grains.setvals

# grains的定义方式：
# 1.通过minion配置文件定义
# 2.通过grains相关模块定义
# 3.通过python脚本定义

[root@localhost minion.d]# cd /etc/salt/minion.d && cat example.conf     #自定义Grains
grains:
  name: wy      #k:v
  age: 18
  more:
    - a
    - b
[root@localhost minion.d]# salt '*' saltutil.sync_grains    #同步grains到客户端
minion.salt.com:
[root@localhost minion.d]# salt '*' sys.reload_modules      #刷新客户端生效
minion.salt.com:
    True
[root@localhost minion.d]# salt '*' grains.item name        #获取自定义的grains
minion.salt.com:
    ----------
    name:
        wy

# Pillar ----------------------------------------------------------------------------
[root@localhost salt]# salt "*" pillar.items    #查看minion中的pillar
#pillar和state tree的结构相似，由sls文件组成，并有1个top.sls，这和state tree类似。pillar默认路径是：/srv/pillar。

#通过master配置文件定义Pillar相关参数： --->  pillar_roots: /srv/pillar
[root@localhost pillar]# cd /srv/pillar && cat top.sls      #针对不同主机的pillar的入口文件
base:
  '*':
    - data
[root@localhost pillar]# cat data.sls   #键值定义 /srv/pillar/data.sls
mykey: myvalue
[root@localhost pillar]# salt '*' saltutil.refresh_pillar   #使pillar更新K:V
minion.salt.com:
    True
[root@localhost pillar]# salt "*" pillar.items      #查看piller
minion.salt.com:
    ----------
    mykey:
        myvalue
```
#### sls and Jinja demo:
```bash
# sls文件是Saltstack的核心。它描述了目标状态，由格式简单的数据构成，在master的配置文件中使用 "file_roots:" 定义其位置
# sls文件本质上是python嵌套字典 (键值)，由 master 以广播形式传递给 minion，因此sls文件也可以用python进行编写 (run函数)
# 就像调用test.ping或disk.usage执行模块一样，state.sls也是一种执行模块，它将SLS文件的名称作为参数
# 流程为：通过sls文件告知使用哪个模块的哪个函数，参数有哪些，然后在salt-minion一侧进行函数调用
# 冒号用来分隔键和值，冒号:与后面的单词如果在一行，一定要有一个空格
# 一个单词后面是否有冒号取决于这个单词是否是key, 后面是否有值或者是嵌套的内容
# 短横杠 "-" 表示这项是个列表项，短横杠与后面的单词有一个空格
# 缩进：本层与下一层要有缩进，缩进不能用tab (需要使用2个空格). 相同缩进表示相同层级
# 当目录内的sls文件名为"init.sls"时将继承包含它的目录下的所有sls文件的名称。可通过直接引用此文件所在目录的名字进行Include!
# state组件的整体架构和pillar有些类似，其入口文件也是top.sls

#Example:
[root@linux-node1 web]# cat lamp.sls 
lamp-install:       #sls文件的id，它在sls文件中不能重复!
  pkg.installed:    #pkg是salt的包管理模块，对应位置为: /usr/lib/python2.6/site-packages/salt/states/pkg.py
    - pkgs:         #installed是pkg模块下的函数，id(httpd)作为installed的参数进行调用，下面的是此函数参数...
      - httpd
      - php
      - php-pdo
      - php-mysql

/etc/http/conf/http.conf:
  file.managed:
    - names:                              #当对状态模块内函数的name不赋值时，其将调用此task的id作为name的值
      - /etc/salt/master.d/master.conf:   #salt://指的是工作目录..
        - source: salt://saltmaster/master.conf
      - /etc/salt/minion.d/minion-99.conf:
        - source: salt://saltmaster/minion.conf
    - source: salt://apache/http.conf     #此处的source没有name参数指定存放路径，将使用任务id值作为路径部署
    - user: root
    - group: root
    - unless: "this is shell command.."   #执行其命令并判断返回值是否为false，为false才执行，onlyif与其想反
    - mode: 644
    - attrs: ai
    - backup: minion                      #当文件更新、修改、等操作时备份文件的方式，minion是本地进行备份（带时间戳）
    - template: jinja                     #salt使用jinja模块对配置文件模板进行渲染!
    - defaults:
        custom_var: "default value"
        IPADDR: {{ grains['fqdn_ip4'][0] }}  #支持python语法，可以花括号内容直接写在模板里但不建议，因为结构不清晰 
        other_var: 123                       # {{ var }} 变量很强大 支持 cmd.run 返回结果等等
{% if grains['os'] == 'Ubuntu' %}         #调用grains判断操作系统类型
    - context:                            #覆盖传递给模板的默认上下文变量（当OS类型为ubuntu时）
        custom_var: "override"
{% endif %}
    - require:                            #依赖的含义，要运行此id的task，必须在名为lamp-install的id的pkg完成才行
      - pkg: lamp-install
    - watch:                              #表示对文件/etc/my.cnf的监控   
      - file: /etc/my.cnf

/srv/stuff/substuf:                       #创建目录
  file.directory:
    - user: fred
    - group: users
    #- mode: 755
    - file_mode: 744
    - dir_mode: 755
    - makedirs: True
    - recurse:
      - user
      - group
      - mode

/etc/motd:                                #Multi-line example
  file.append:
    - text: |
        Thou hadst better eat salt with the Philosophers of Greece,
        than sugar with the Courtiers of Italy.
        - Benjamin Franklin

/etc/motd:                                #从多个模板文件中收集文本进行追加
  file:
    - append
    - template: jinja
    - sources:
      - salt://motd/devops-messages.tmpl
      - salt://motd/hr-messages.tmpl
      - salt://motd/general-messages.tmpl

#Jinja template Example1:
{%- for username, details in pillar['addusernames'].iteritems() %}  #是一个字典...
  {{ username }}:
    user.present:
      - groups:
        - your_groups
      - expire: {{ details['ExpireDate'] }}
      - password: {{ details['passwd'] }}
      - unless: cat /etc/passwd | grep {{ username }}
{% endfor %}

#Jinja template Example2:
{% for key, value in values.items() -%}
  {{ key }}={{ value }}
{% endfor -%}

{% if salt['cmd.run']('uname -i') == 'x86_64' %}
hadoop:
 user.present:
   - shell: /bin/bash
   - home: /home/hadoop
{% elif salt['cmd.run']('uname -i') == 'i386' %}
openstack:
 user.present:
   - shell: /bin/bash
- home: /home/openstack
{% else %}
django:
 user.present:
   - shell: /sbin/nologin
{% endif %}

#注：
#在sls文件中定义变量: {% set appname = 'foo-service' %}
#在sls文件中定义变量: {% set settings = salt['pillar.get']('host') %}
#在sls文件中引入其他文件内应以的变量例子：{% import_yaml 'xx/var.yaml' as var_settings %} 
#或：{% from "host/map.jinja" import settings with context %}  , 注意as和with的区别!
#在sls中调用变量： {{ var }} 注意! 默认不能传递给 include 到本sls文件的变量

#require：    声明本状态依赖于指定的状态
#require_in： 声明本状态被指定状态依赖：  A require B <=> B require_in A

#watch和watch_in是require和require_in的扩展，唯一区别是watch和watch_in会额外的调用状态组件中的mod_watch函数
#如果状态组件没有提供该函数，那么它和require, require_in的行为完全一样。
#watch:       声明若其指定的对象发生变化，则会被触发
#watch_in:    声明它应该被什么服务watch

# require,watch 是指依赖，依赖别的状态执行成功
# require_in,watch_in 是指被依赖，其中包含的状态依赖于本状态执行成功
```
#### 模块参考
[file](https://docs.saltstack.com/en/latest/ref/states/all/salt.states.file.html)
#### salt-ssh
```bash
[root@linux-node1 ~]# vim /etc/salt/roster 
linux-node1:
  host: 192.168.56.11
  user: root
  priv: /root/.ssh/id_rsa
  minion_opts:
    grains:
      k8s-role: master
      etcd-role: node
      etcd-name: etcd-node1

linux-node2:
  host: 192.168.56.12
  user: root
  priv: /root/.ssh/id_rsa
  minion_opts:
    grains:
      k8s-role: node
      etcd-role: node
      etcd-name: etcd-node2

linux-node3:
  host: 192.168.56.13
  user: root
  priv: /root/.ssh/id_rsa
  minion_opts:
    grains:
      k8s-role: node
      etcd-role: node
      etcd-name: etcd-node3

# salt-ssh '*'  test.ping -i              #第一次连接会自动安装公钥到客户端上 
# salt-ssh '*'  -r ifconfig               # -r 后面可以直接写命令 
# salt-ssh '*'  state.highstate           #读取top.sls并执行
# salt-ssh '*'  state.sls web.apache      #执行指定执行状态文件

#salt-ssh第一次执行是根据roster文件里配置的账号密码推送密码，来实现自动交互的。
#执行完了后会在目标服务器里面，追加master端（即源机器）的key。
#然后就可以删除roster里面的passwd密码条目了，删除roster文件里的密码条目后，不影响后批量操作的执行。
```
#### 在外部系统中存储作业结果 - Salt Returner
```bash
#作业执行后，每个Salt Minion将作业结果返回给Salt Master。这些结果存储在 默认作业缓存中。
#除默认作业缓存之外，Salt还提供了两种额外的机制来将作业结果发送到其他系统：数据库、本地系统日志和其他系统
#配置外部作业缓存后数据像往常一样返回Master上的默认作业缓存，然后使用Minion上运行的Salt返回器模块将结果发送到外部作业缓存
# 优点：存储数据时不会在Master上增加额外负载。
# 缺点：每个Minion都连接到外部作业缓存，这可能会导致大量连接。还需要额外的配置才能在所有Minions上获得返回者模块设置
# 所有minion需要事先安装mysql-python模块! yum -y install MySQL-python

#创建库名:
CREATE DATABASE  `salt`
  DEFAULT CHARACTER SET utf8 
  DEFAULT COLLATE utf8_general_ci;

#创建jid表 ( 可以把它简单理解为一个任务编号 )
USE `salt`;
DROP TABLE IF EXISTS `jids`;
CREATE TABLE `jids` (
   `jid` varchar(255) NOT NULL,
   `load` mediumtext NOT NULL,
   UNIQUE KEY `jid` (`jid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#创建return表，存放返回的数据：
DROP TABLE IF EXISTS `salt_returns`;
CREATE TABLE `salt_returns` (
    `fun` varchar(50) NOT NULL,
    `jid` varchar(255) NOT NULL,
    `return` mediumtext NOT NULL,
    `id` varchar(255) NOT NULL,
    `success` varchar(10) NOT NULL,
    `full_ret` mediumtext NOT NULL,
    `alter_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY `id` (`id`),
    KEY `jid` (`jid`),
    KEY `fun` (`fun`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#创建事件表
DROP TABLE IF EXISTS `salt_events`;
CREATE TABLE `salt_events` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `tag` varchar(255) NOT NULL,
    `data` mediumtext NOT NULL,
    `alter_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `master_id` varchar(255) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `tag` (`tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

#授权访问
grant all on salt.* to salt@'%' identified by 'salt123';
flush  privileges;

#For example, MySQL requires:
mysql.host: 'salt'
mysql.user: 'salt'
mysql.pass: 'salt'
mysql.db: 'salt'
mysql.port: 3306

#要将返回者作为外部作业缓存（Minion端）启用，需要将以下行添加到Salt Master配置文件中：
ext_job_cache: mysql

#要将返回者作为主作业缓存（主方）启用，请将以下行添加到Salt Master配置文件中：
master_job_cache: mysql

#需要确保在进行配置更改后重启salt-master
#执行：salt '*' test.ping --return mysql  #注：--return syslog  表示minion将结果返回给自己的syslog
```
#### 附：
```bash
#use声明可以简化配置，复用指定状态的配置。例如：
/etc/foo.conf:
  file.managed:
    - source: salt://foo.conf
    - template: jinja
    - mkdirs: True
    - user: apache
    - group: apache
    - mode: 755
 
/etc/bar.conf
  file.managed:
    - source: salt://bar.conf
    - use:
      - file: /etc/foo.conf

#以上等价于:
/etc/foo.conf:
  file.managed:
    - source: salt://foo.conf
    - template: jinja
    - mkdirs: True
    - user: apache
    - group: apache
    - mode: 755
 
/etc/bar.conf
  file.managed:
    - source: salt://bar.conf
    - template: jinja
    - mkdirs: True
    - user: apache
    - group: apache
    - mode: 755

#require_in/watch_in:
{% from "supervisor/map.jinja" import supervisor with context %}
supervisor-config:
  file.managed:
    - name: {{ supervisor.config }}
    - source: salt://supervisor/templates/supervisord.conf.tmpl
    - template: jinja
    - mode: 644
    - user: root
    - group: root
    - require_in:
      - service: supervisor.service
    - watch_in:
      - service: supervisor.service
{% if 'programs' in supervisor -%}
{% for program,values in supervisor.programs.items() -%}
supervisor-program-{{ program }}:
  file.managed:
    - name: {{ supervisor.program_dir }}/{{ program }}-prog.conf
    - source: salt://supervisor/templates/program.conf.tmpl
    - template: jinja
    - mode: 644
    - user: root
    - group: root
    - defaults:
        program: {{ program }}
        values: {{ values }}
    - watch_in:
      - service: supervisor.service
{% endfor -%}
{% endif -%}

#在sls中引入在其他文件中定义的键值对变量：
{% from "host/map.jinja" import settings with context %}
{% if 'tasks' in settings %}
  {% for task,task_options in settings.tasks.iteritems() %}
    host.{{ task }}:
        host.{{ task_options.type | default('present') }}:    #此处设置了变量不存在时的默认值!
            - name: '{{ task_options.name }}'
            - ip: '{{ task_options.ip }}'
  {% endfor %}
{% endif %}
#--------------------------------------------------
{% from "supervisor/map.jinja" import supervisor with context %}
supervisor.service:
  service.running:
    - name: {{ supervisor.service.name }}
    - enable: True
```
#### Salt API
```python
#API原理是通过调用client模块，实例化LocalClient对象，再调用cmd()方法来实现的，比如test.ping功能，其实现的原理：

import salt.client
client = salt.client.LocalClient()
ret = client.cmd('*','test.ping')
print ret

#返回的ret是字典格式的字符串: '{"estMinion":True}'
#cmd内格式：'<操作目标>','<模块>','[参数]'。例：'*','cmd.run',['df -h']
```
#### 自定义模块
```bash
# 在 Master上创建存放模块的目录:
# mkdir -pv /srv/salt/_modules  ( 通常所有自定义模块放在/srv/salt/_modules/下 )
# cd /srv/salt/_modules

#编写模块：
vim mathmagic.py
#!/usr/bin/env python

def pow(x, exp=2):
    return x**exp

#同步到minion:
salt '*' saltutil.sync_modules

#mimion 端存放路径： 
/var/cache/salt/minion/extmods/_modules/mathmagic.py     #扩展模块存放位置 
/salt/var/cache/salt/minion/files/_modules/mathmagic.py  #临时存放位置

#在Master端调用：
salt "*" mathmagic.pow 5
```
```python
-*- coding: utf-8 -*-
'''
   support for yum of RedHat family!
   __virtual__函数通常用来匹配是否满足该模块的环境，如果满足return出来的字符串作为该模块的名字而不是文件名
   如果return的是False代表的此模块无效，不能使用
'''
def __virtual__():
   '''
   Only RedHat family os can use it.
   在自定义模块中:
   __grains__   是一个包含了minion 所有grains的字典
   __pillar__   是包含了所有Pillar的grains字典
   __salt__     是所有可执行函数对象的字典
   '''
   if __grains__.get('os_family', 'unkown') == 'RedHat':
       return 'yum'
   else:
       return False

def install(rpm):
   cmd = 'yum -y install {0}'.format(rpm)
   #通过__salt__执行了cmd.run这个函数来运行yum命令
   ret = __salt__['cmd.run'](cmd)

#测试执行： salt '*' yum.install ftp
```
```bash
#!/usr/bin/env python
import os
import commands
import time

def version():
    version = commands.getoutput('nginx -v')
    if  'version' in version:
        return version
    return False

def service(cmd):
    parm = ['start','stop','status','restart','reload']
    if cmd not in parm:
        return 'command  not exists'
    command = commands.getoutput('/etc/init.d/nginx %s' % cmd)
    return command


#同步到minion:
salt '*' saltutil.sync_modules

salt -N node nginx.version
# 
# 192.168.2.67:
#     nginx version: nginx/1.10.2
# 192.168.2.81:
#     nginx version: nginx/1.10.2
# 192.168.15.73:
#     nginx version: nginx/1.10.2

salt -N node nginx.service status
# 
# 192.168.2.67:
#     nginx (pid  17398) is running...
# 192.168.2.81:
#     nginx (pid  28472) is running...
# 192.168.15.73:
#     nginx (pid  16823) is running...
```
#### 使用 gitfs 做 fileserver
```bash
#用gitfs后，master会从git服务器取回文件缓存，minion不会直接联系git服务器，修改master配置文件/etc/salt/master
fileserver_backend:
 - git                                      #需要python的模块: GitPython >= 0.3.0
gitfs_remotes:  
 - git://github.com/saltstack/saltstack.git
 - git://github.com/example/test1.git       #可以多个git
 - file:///root/td                          #可以使用本地git


#Example:
/tmp/a.txt:
 file.managed:
   - source: salt://bfile                   #这里从Git获取!
ftp:
 pkg:
   - installed
```
#### deploy.sls demo
```bash
#1.修改master的配置文件，指定base环境路径，base环境是必须指定的
[root@salt-master salt]# vi /etc/salt/master
file_roots:
  base:
    - /srv/salt/base

#2. 高级状态的使用需要在master配置文件里面打开state_top: top.sls
[root@salt-master salt]# grep -n ^state_top /etc/salt/master 
329:state_top: top.sls

#3. 重启salt-master服务
[root@salt-master salt]# /bin/systemctl restart salt-master.service

#4. 创建目录     
[root@salt-master salt]# mkdir -p /srv/salt/base/

#5. 在base目录下创建top.sls文件，创建web目录及创建apache.sls文件
[root@salt-master salt]# tree
.
└── base
    ├── top.sls
    └── web
        └── apache.sls

[root@salt-master salt]# vi /srv/salt/base/top.sls 
base:
  '*':
    - web.apache

[root@salt-master salt]# vi /srv/salt/base/web/apache.sls 
apache-install:         #id,名字自己取，需见名知意
  pkg.installed:        #pkg是状态模块，installed是模块里面的方法
    - name: httpd       #httpd是方法里面的参数
apache-service:
  service.running:
    - name: httpd
    - enable: True       #设置开机启动

#6. 执行状态模块部署服务，状态模块会到base目录下找到top.sls，文件编排告诉每个minion需要干什么
[root@salt-master salt]# salt '*' state.highstate 
```
#### 部署多 Master
```bash
#安装Master
yum -y install salt-master
scp /etc/salt/pki/master/master* newmaster:/etc/salt/pki/master/  #将原来master上的master密钥拷贝到新的master一份
service salt-master start

#修改minion配置文件/etc/salt/minion设置两个master
master:
  - master1
  - master2
#重启minion: service salt-minion restart

#在新的master上接受所有key：salt-key -A -y

#注意:
# 1.2个master并不会共享Minion keys，一个master删除了一个key不会影响另一个
# 2.不会自动同步File_roots,所以需要手动去维护，如果用git就没问题了
# 3.不会自动同步Pillar_Roots，所以需要手工去维护，也可以用git
# 4.Master的配置文件也是独立的
```
#### 定时任务 Scheduler
```bash
#在日常的运维工作中经常会遇到需要定时定点启动任务，首先会考虑到crontab，但是通过crontab的话需要每台机器下进行设置
#这样统一管理的话比较复杂；通过google发现saltstack有scheduler的功能

#Salt本身提供多方面的Scheduler的配置，分别有3种配置方式：
　　# 1、从Master配置端；
　　# 2、Master Pillar端；
　　# 3、Minion配置端或者Minion.d下配置文件下配置
　　# 在这里介绍pillar方式；官方文档：https://docs.saltstack.com/en/latest/topics/jobs/index.html

#首先创建 /srv/salt/pillar/top.sls
[root@test pillar]# cat /srv/salt/pillar/top.sls
base:
  "*":
    - schedule

#然后创建 /srv/salt/pillar/schedule.sls
[root@test tmp]# cat /srv/salt/pillar/schedule.sls
schedule:
  testcase:
    function: cmd.run     #这个调度任务的意思是：每隔10秒在/tmp目录下的test.cmd.log文件中记录一条时间
    seconds: 10
    args:
      - 'date >> /tmp/test.cmd.log'
    kwargs:
      stateful: False

#创建完文件之后执行下面的命令把pillar的修改刷到minion端: salt "*" saltutil.refresh_pillar

#查看minion端都有哪些计划任务可以执行如下命令：
[root@test pillar]# salt "*" pillar.get schedule
192.168.1.88:
    ----------
    __mine_interval:
        ----------
        function:
            mine.update
        jid_include:
            True
        maxrunning:
            2
        minutes:
            60
        name:
            __mine_interval
    testcase:
        ----------
        args:
            - date >> /tmp/test.cmd.log
        function:
            cmd.run
        jid_include:
            True
        kwargs:
            ----------
            stateful:
                False
        maxrunning:
            1
        name:
            testcase
        seconds:
            10
```
#### state.sls与state.highstate
```txt
state.sls与state.highstate区别大致如下：

state.highstate会读取所有环境（包括base环境）的top.sls文件
并且执行top.sls文件内容里面定义的sls文件，不在top.sls文件里面记录的sls则不会被执行

state.sls默认读取base环境，但是它并不会读取top.sls文件。你可以指定state.sls执行哪个sls文件，只要它在base环境下存在
state.sls也可以指定读取哪个环境：state.sls salt_env='prod' xxx.sls，这个xxx.sls可以不在top.sls中记录
state.sls执行的xxx.sls会被下发到minion端，而state.highstate则不会
```
