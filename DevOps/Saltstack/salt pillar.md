```bash
#Minion中pillar为Python字典, Minion启动时默认连接master获取最新的pillar数据
#Pillar是Salt用来分发全局变量到所有minions的一个接口 ( pillar需编写入口文件top.sls且这个文件是在配置项pillar_roots内 )
#Salt Master服务器维护了一个pillar_roots设置. Pillar数据被映射到基于入口文件"top.sls"匹配到的Minion上
#pillar相关的文件中可基于jinja语法对grains数据调用，也就是说pillar数据定义可基于grains数据!
#当定义pillar的时候不必限制在sls文件，也可以从外部资源获得数据。这对于架构信息存储于其它地方的情况下非常有用。

#salt-master的配置文件中定义了pillar存放路径，此示例配置声明基本环境(base)将位于/srv/pillar目录：
pillar_roots:
  base:
    - /srv/pillar

#Example:
cat /srv/pillar/top.sls
base:
  '*':              #'*'代表所有被控端都有的pillar数据，这些数据被定义在了与top.sls同级目录的packages文件里
    - packages      # ---> /srv/pillar/packages.sls
  'web*':
    - vim
dev:
  'os:Debian':
    - match: grain
    - servers

cat /srv/pillar/packages.sls
{% if grains['os'] == 'RedHat' %}   #pillar中可以调用Grains!
apache: httpd
git: git
{% elif grains['os'] == 'Debian' %}
apache: apache2
git: git-core
{% endif %}
company: Foo Industries
appname: website
flow:
  maxconn: 30000
  maxmem: 6G

#sls文件中引用pillar:
git:
  pkg.installed:
    - name: {{ pillar['git'] }}

#Pillar的sls文件可包含其他pillar文件，和State文件类似。两个语法可以实现这个目的：
include:
  - users

# or:

include:
  - users:
      defaults:
          sudo: ['bob', 'paul']
      key: users

#如果在pillar中有这样的一个结构：
foo:
  bar:
    baz: qux
#在sls公式或文件模板中从原始pillar中提取数据是通过这种方式完成的:
{{ pillar['foo']['bar']['baz'] }}

#新版本的 pillar.get 函数：数据可安全的收集和设置设置一个默认，当值不可用时允许模板回滚。
{{ salt['pillar.get']('foo:bar:baz', 'qux') }}  #这使得处理嵌套结构更加容易
```
```bash
#demo
#一个简单的声明：
cat /srv/salt/edit/vim.sls
vim:
  pkg:
    - installed

/etc/vimrc:
  file.managed:
    - source: salt://edit/vimrc
    - mode: 644
    - user: root
    - group: root
    - require:
      - pkg: vim

#可以简单地转换成一个强大的、参数化的公式：
cat /srv/salt/edit/vim.sls
vim:
  pkg:
    - installed
    - name: {{ pillar['pkgs']['vim'] }}

/etc/vimrc:
  file.managed:
    - source: {{ pillar['vimrc'] }}
    - mode: 644
    - user: root
    - group: root
    - require:
      - pkg: vim

#这时vimrc的src地址现在就可以通过pillar来改变了：
cat /srv/pillar/edit/vim.sls

{% if grain['id'].startswith('dev') %}
vimrc: salt://edit/dev_vimrc
{% elif grain['id'].startswith('qa') %}
vimrc: salt://edit/qa_vimrc
{% else %}
vimrc: salt://edit/vimrc
{% endif %}
```

```txt
1.使用grains参数获取本地IP：   {{ grains['fqdn_ip4'][0] }}
2.使用salt远程执行模块获取网卡MAC:  {{ salt['network.hw_addr']('eth0') }}
3.使用pillar参数：  {{ pillar['apache'] }}
```