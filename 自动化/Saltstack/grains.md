```bash
# grains数据的定义方式有2种，其一是在被控端定制配置文件，其二是通过主控端扩展模块API
# minion的grains信息是minion启动的时候采集汇报给master的
# grains会在minion进程启动时进行加载，并缓存在内存中。这样salt-minion进程无需每次操作都要重新检索系统来获取grain

#通过minion配置文件定义grains：
grains:
  roles:
    - webserver
    - memcache
  deployment: datacenter4
  cabinet: 13
  cab_u: 14-15
# 如果不想将自定义静态GRAINS放在minion配置文件中，也可以将它们放在/etc/salt/grain中
# 它们的配置方式与上例相同，只是没有顶级粒度key：
roles:
  - webserver
  - memcache
deployment: datacenter4
cabinet: 13
cab_u: 14-15

#获取自定义的3个grains：
[root@localhost minion.d]# salt '*' grains.item roles deployment cabinet 
TestMinion:
    ----------
    cabinet:
        13
    deployment:
        datacenter4
    roles:
        - webserver
        - memcache
```
#### sls文件中可以使用Grains进行匹配：
```bash
'node_type:web':
  - match: grain
  - webserver

'node_type:postgres':
  - match: grain
  - database

'node_type:redis':
  - match: grain
  - redis

'node_type:lb':
  - match: grain
  - lb

# 以上配置文件冗余大，可使用模板来编写sls：
# {% set openresty_version = openresty.get('version', '1.2.7.8') -%}
# {% set openresty_package = source + '/openresty-' + openresty_version + '.tar.gz' -%}
{% set the_node_type = salt['grains.get']('node_type', '') %}   # <--- 在模板中定义变量!
{% if the_node_type %}
  'node_type:{{ the_node_type }}':
    - match: grain
    - {{ the_node_type }}
{% endif %}
```
#### 主控端定义grains代码并同步到所有被控端后获取值
```python
#首先在主控端编写python代码，然后将该python文件同步到被控端主机，最后刷新生效
#创建/etc/salt/_grains，在该目录编写脚本如：demo.py （或在salt-master配置文件的file_roots指定的目录建立_grains目录）
# cat /etc/salt/master
# file_roots:
#   base:
#     - /srv/salt/base
#   test:
#     - /srv/salt/test
#   prod:
#     - /srv/salt/prod

#代码如下：
#!/usr/bin/env python
def yourfunction():
     # initialize a grains dictionary 这个字典很重要，所有的数据均从名为grains的字典中获取
     grains = {}
     # Some code for logic that sets grains like
     grains['yourcustomgrain'] = True
     grains['anothergrain'] = 'somevalue'
     return grains                      #这个值是通过在各个不同被控端上运行这个脚本获得而来的!!!

#最后同步模块到指定被控主机并刷新生效:
salt '*' saltutil.sync_grains -l debug  #同步grains到客户端
salt '*' sys.reload_modules             #刷新客户端生效
salt '*' grains.item anothergrain       #获取自定义的grains
salt '*' grains.items                   #查看所有的键值对

#在minion端测试：
salt-call --local grains.items

#执行命令salt '*' saltutil.sync_all，此命令同步了很多东西，若只想同步grains可以sync_grains:
#同步到所有被控端的 /var/cache/salt/minion/extmods/grains和/var/cache/salt/minion/files/base/_grains两个目录下
#前者是最终的存放目录而后者是临时存放位置
#同时在前者目录中还会生成对应的python字节码文件即.pyc文件

#通过grains.append key 'value' 这个命令行的方式来添加某被控端的grains，此时添加的grains被写入到/etc/salt/grains文件
#通过grains.append方法添加的grains再sync之后就会同步到位，不需重启服务
```
#### Grains的优先级问题
```txt
被控端minion的/etc/salt/minion.d/*.conf优先级最高
其次是/etc/salt/grains
再次是通过主控端脚本分发的grains
最后是系统自带的grains
```