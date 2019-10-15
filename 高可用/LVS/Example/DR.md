
```bash
------------------- DR
#!/bin/sh
VIP=192.168.0.210
RIP1=192.168.0.175
RIP2=192.168.0.145
. /etc/rc.d/init.d/functions
        case "$1" in
        start)
        echo "start LVS of DirectorServer"
        #Set the Virtual IP Address
        /sbin/ifconfig eth0:1 $VIP broadcast $VIP netmask 255.255.255.255 up
        /sbin/route add -host $VIP dev eth0:1
        #Clear IPVS Table
        /sbin/ipvsadm -C
        #Set Lvs
        /sbin/ipvsadm -A -t $VIP:80 -s rr
        /sbin/ipvsadm -a -t $VIP:80 -r $RIP1:80 -g
        /sbin/ipvsadm -a -t $VIP:80 -r $RIP2:80 -g
        #Run Lvs
        /sbin/ipvsadm
        ;;
        stop)
        echo "close LVS Directorserver"
        /sbin/ipvsadm -C
        /sbin/ifconfig eth0:1 down
        ;;
        *)
        echo "Usage： $0 {start|stop}"
        exit 1
        esac

------------------- RS

#!/bin/bash
VIP=192.168.0.210
LOCAL_Name=50bang
BROADCAST=192.168.0.255  #vip's broadcast
. /etc/rc.d/init.d/functions
case "$1" in
    start)
     echo "reparing for Real Server"
       echo "1" >/proc/sys/net/ipv4/conf/lo/arp_ignore
       echo "2" >/proc/sys/net/ipv4/conf/lo/arp_announce
       echo "1" >/proc/sys/net/ipv4/conf/all/arp_ignore
       echo "2" >/proc/sys/net/ipv4/conf/all/arp_announce
       ifconfig lo:0 $VIP netmask 255.255.255.255 broadcast $BROADCAST up
        /sbin/route add -host $VIP dev lo:0
        ;;
    stop)
        ifconfig lo:0 down
       echo "0" >/proc/sys/net/ipv4/conf/lo/arp_ignore
       echo "0" >/proc/sys/net/ipv4/conf/lo/arp_announce
       echo "0" >/proc/sys/net/ipv4/conf/all/arp_ignore
       echo "0" >/proc/sys/net/ipv4/conf/all/arp_announce
        ;;
    *)
        echo "Usage: lvs {start|stop}"
        exit 1
esac 
```

#### DR REAL
```bash
#!/bin/bash
 
SNS_VIP=10.0.2.245
 
case "$1" in
start)
       echo "1" > /proc/sys/net/ipv4/conf/lo/arp_ignore
       echo "2" > /proc/sys/net/ipv4/conf/lo/arp_announce
       echo "1" > /proc/sys/net/ipv4/conf/all/arp_ignore
       echo "2" > /proc/sys/net/ipv4/conf/all/arp_announce
       sysctl -p >/dev/null 2>&1
       ifconfig lo:0 $SNS_VIP netmask 255.255.255.255 broadcast $SNS_VIP #loopbak非本地物理接口
       /sbin/route add -host $SNS_VIP dev lo:0
       echo "RealServer Start OK"
       ;;
stop)
       ifconfig lo:0 down
       route del $SNS_VIP >/dev/null 2>&1
       echo "0" > /proc/sys/net/ipv4/conf/lo/arp_ignore
       echo "0" > /proc/sys/net/ipv4/conf/lo/arp_announce
       echo "0" > /proc/sys/net/ipv4/conf/all/arp_ignore
       echo "0" > /proc/sys/net/ipv4/conf/all/arp_announce
       echo "RealServer Stoped"
       ;;
*)
       echo "Usage: $0 {start|stop}"
       exit 1
esac
 
exit 0
```