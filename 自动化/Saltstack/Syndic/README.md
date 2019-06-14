```bash
#Syndic必须运行在一个master上,然后连到另外一个更高级的master（这台机器就可以管理syndic-master所管理的机器）

#修改最上层的Master配置文件：/etc/salt/master
order_masters: True                        #表示允许开启多层master


#在代理端执行如下：
yum install salt-syndic -y
cd /etc/salt/
grep "^[a-Z]" proxy
#master: 192.168.56.11

grep "^[a-Z]" master
#syndic_master: 192.168.56.11 

systemctl enable salt-master.service --now
systemctl enable salt-syndic.service --now

#在minion中将master地址指向syndic:
grep "^[a-Z]" /etc/salt/minion
#master: 192.168.56.12     
```