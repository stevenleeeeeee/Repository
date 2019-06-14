```txt
1、Volume
2、Persistent Volume
3、Persistent Volume Claim
4、Service
5、StatefulSet
```
```txt
它所管理的Pod拥有固定的Pod名称，启停顺序，在StatefulSet中，Pod名字称为网络标识(hostname)，还必须要用到共享存储。
在Deployment中，与之对应的服务是service，而在StatefulSet中与之对应的headless service，headless service，即无头服务
与service的区别就是它没有Cluster IP，解析它的名称时将返回该Headless Service对应的全部Pod的Endpoint列表。
除此之外，StatefulSet在Headless Service的基础上又为StatefulSet控制的每个Pod副本创建了一个DNS域名，这个域名的格式为：

    $(podname).(headless server name)   
    FQDN： $(podname).(headless server name).namespace.svc.cluster.local
```
#### 按分区进行更新
```txt
eg:
kubectl patch sts myapp -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":2}}}}'

#打补丁方式扩/缩容
kubectl patch sts myapp -p '{"spec":{"replicas":2}}' 
```
