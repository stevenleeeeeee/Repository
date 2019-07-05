```bash
macvlan是linxu kernel模块，其功能是允许在同一个物理网卡上配置多个 MAC 地址，即多个 interface
每个interface可配置自己的IP。macvlan本质上是一种网卡虚拟化技术 ( 物理网卡上虚拟出多个子网卡 )
macvlan最大优点是性能极好，相比其他实现，macvlan不需要创建Linux bridge，而是直接通过以太interface连接到物理网络
是比较新的网络虚拟化技术，需要较新的内核支持! Linux kernel v3.9–3.19 and 4.0+
---------------------------------------------------------

#创建macvlan网络，其中subnet是所在宿主机的接口所在网段、网管为宿主机的GW地址
#注意这里不会为macvlan创建网关，这里的网关应该是真实存在的，否则容器无法路由 ( 注意此类网路同宿主的容器间互相不可访问 )
docker network create -d macvlan --subnet=192.168.128.0/24 --gateway=192.168.128.2 -o parent=eth0 -o macvlan_mode=vepa vepamv


#创建容器时使用上述macvlan网络模型并指定其IP地址
docker run -itd --net=vepamv --ip=192.168.128.222 --name=centos1-2 f322035379ab /bin/bash

#在容器中启动HTTP服务，在宿主机中对其地址/端口进行请求
docker exec -it f322035379ab -- /bin/bash python -m SimpleHTTPServer
```
#### Macvlan几种工作模式
```bash
1.VEPA：所有接口的流量都需要到外部switch才能够到达其他接口
    macvlan设备不能直接接收在同一物理网卡的其他macvlan设备的数据包，但其他macvlan设备可以将数据包通过物理网卡发出去
    然后通过hairpin设备返回的给其他macvlan设备，用于管理内部vm直接的流量，并且需要特殊设备支持
    需要主接口连接的交换机支持 VEPA/802.1Qbg特性，即 hairpin mode 模式，此模式用在SW上需要做过滤、统计等功能的场景
    所有发送出去的报文都会经过SW，SW作为再发送到对应的目标地址（即使目标地址就是主机上的其他 macvlan 接口）
    docker network create -d macvlan --subnet=x.x.x.x/x --gateway=x.x.x.x -o parent=eth0 -o macvlan_mode=vepa vepamv

2.private：
    类似VEPA，但在VEPA基础上添加了新的特性，即如果两个macvlan在同一网卡，这两个macvlan接口无法通信
    即使用开启hairpin的交换机或路由器。仍然使用上述条件构造从192.168.128.222到192.168.128.233的arp请求报文
    可以看到192.168.128.222并没有回复192.168.128.233的arp。但从windows直接ping 192.168.128.222可通的
    主接口会过滤掉交换机返回来的来自其子接口的报文，不同子接口之间无法互相通信，接口只接受发送给自己MAC地址的报文
    private模式下隔离了来自同网卡的macvlan的广播报文

3.passthru
    该模式仅允许1块网卡上部署1个macvlan接口，其他使用macvlan的容器将启动失败，但只要不使用macvlan，该容器还是可以正常启动
    如果需要在单个物理网卡上启动多个macvlan_mode=passthru的容器，可使用子接口方式
    参见 https://blog.csdn.net/daye5465/article/details/77412619。

4.bridge：属于同一parent接口的macvlan接口间挂到同bridge上，可二层互通（经测试发现这些macvlan接口都无法与parent接口互通）
    是docker的默认模式：在这种模式下寄生在同一物理设备的macvlan设备可直接通讯，不需要外接的hairpin设备帮助
    使用bridge可以保证在不使用hairpin设备的前提下实现inter-network和external-network的连通
    使用如下的命令创建一个bridge的macvlan网络：
    docker network create -d macvlan --subnet=192.168.226.0/24 --gateway=192.168.226.2 -o parent=eth0 -o macvlan_mode=bridge bridmv


#查看网络信息：
docker network ls
docker network inspect bridmv


#查看模块是否加载
lsmod | grep macvlan （查看是否加载了）
modprobe macvlan (手动加载macvlan驱动到内核)
/drivers/net/macvlan.c (源码地址)
```
#### Example
```bash
#Bridge mode：( 不创建子接口的情况下直接去桥接物理接口。直接桥接到与宿主级的同网段 )
docker network create -d macvlan --subnet=x.x.x.x/x --gateway=x.x.x.1 -o parent=eth0 pub_net

#802.1q trunk bridge mode: (相当于为每个使用此网络的容器分配了VLAN，创建子接口去桥接物理接口)
docker network create -d macvlan --subnet=x.x.x.x/x --gateway=x.x.x.1 -o parent=eth0.50 macvlan50

#Use an ipvlan instead of macvlan: 可以使用ipvlan来获得L2桥接器，指定： -o ipvlan_mode = l2
#多个子网的 Macvlan 802.1q Trunking
docker network create -d ipvlan \
    --subnet=192.168.210.0/24 \
    --subnet=192.168.212.0/24 \
    --gateway=192.168.210.254 \
    --gateway=192.168.212.254 \
     -o ipvlan_mode=l2 ipvlan210
```

#ref
```txt
https://www.cnblogs.com/iiiiher/p/8059032.html
https://segmentfault.com/a/1190000018742817?utm_source=tag-newest
```