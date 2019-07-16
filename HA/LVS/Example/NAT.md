
```bash
#!/bin/sh
# description: start LVS of Nat
    VLAN-IP=202.99.59.110
    RIP1=10.1.1.2
    RIP2=10.1.1.3
    #RIPn=10.1.1.n
    GW=10.1.1.1
    . /etc/rc.d/init.d/functions
case "$1" in
    start)
        echo " start LVS of NAtServer"
        echo "1" >/proc/sys/net/ipv4/ip_forward
        echo "0" >/proc/sys/net/ipv4/conf/all/send_redirects
        echo "0" >/proc/sys/net/ipv4/conf/default/send_redirects
        echo "0" >/proc/sys/net/ipv4/conf/eth0/send_redirects
        echo "0" >/proc/sys/net/ipv4/conf/eth1/send_redirects(内网卡上的)
        #Clear IPVS table
        /sbin/ipvsadm -C
        #set LVS
        /sbin/ipvsadm -a -t 202.99.59.110:80 -r 10.1.1.2:80 -m -w 1
        /sbin/ipvsadm -a -t 202.99.59.110:80 -r 10.1.1.3:80 -m -w 1
        #Run LVS
        /sbin/ipvsadm
        #end
;;
    stop)
        echo "close LVS Nat server"
        echo "0" >/proc/sys/net/ipv4/ip_forward
        echo "1" >/proc/sys/net/ipv4/conf/all/send_redirects
        echo "1" >/proc/sys/net/ipv4/conf/default/send_redirects
        echo "1" >/proc/sys/net/ipv4/conf/eth0/send_redirects
        echo "1" >/proc/sys/net/ipv4/conf/eth1/send_redirects(内网卡上的)
        /sbin/ipvsadm -C
;;
    *)

echo "Usage: $0 {start|stop}"
exit 1
esac

#LVS-Nat 模式的后端机器不需要配置
```