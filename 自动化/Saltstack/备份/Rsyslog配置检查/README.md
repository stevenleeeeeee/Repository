#### 在master中创建grains脚本存放路径
```bash
mkdir /srv/salt/_grains
```
#### grains脚本代码
```python
#!/usr/bin/env python
#-- coding:utf-8 --

import os
import commands


def ver():
    grains={}
    rsyslog_server_address='20.58.9.132'

    ps_rsyslog,_ = commands.getstatusoutput(" ps -ef | grep -v grep | grep '/usr/sbin/rsyslogd' ")
    if not ps_rsyslog == 0:
        grains['接入日志']=0
        return grains

    _,confs = commands.getstatusoutput(" find /etc/rsyslog.conf /etc/rsyslog.d/ -name '*conf' ")
    
    for i in confs.split('\n'):
        #print "grep @{address} {file}".format(address=rsyslog_server_address,file=i)
        status,_ = commands.getstatusoutput("grep @{address} {file}".format(address=rsyslog_server_address,file=i))
        if status == 0:
            grains['接入日志']=1
            return grains
    grains['接入日志']=0
    return grains

ver()
```
#### 将grains脚本同步到所有minion并测试
```bash
[root@node2 _grains]# salt '*' saltutil.sync_grains -l debug    #同步grains脚本到minion
[root@node2 _grains]# salt '*' sys.reload_modules               #重载grains脚本
node2:
    True
[root@node2 _grains]# salt '*' grains.item 接入日志              #查看grains返回值
node2:
    ----------
    接入日志:
        1
```