```txt
目前cAdvisor集成到了kubelet组件内，可在kubelet节点使用cAdvisor提供的metrics接口获取该节点所有容器相关的性能指标数据

1.7.3版本以前:  cadvisor的metrics数据集成在kubelet的metrics中
1.7.3以后版本:  cadvisor的metrics被从kubelet的metrics独立出来，在prometheus采集的时候变成两个scrape的job

---------------------------

按新版本的标准，kubelet的cadvisor是没有对外开放4194端口的，所以只能通过apiserver提供的api做代理获取监控指标:
    cAdvisor的metrics地址:  /api/v1/nodes/[节点名称]/proxy/metrics/cadvisor
    kubelnet的metrics地址： /api/v1/nodes/[节点名称]/proxy/metrics

kubelet自身提供了几个 HTTP-API 供用户查看信息。 最简单的就是 10248 的健康检查：
    curl http://127.0.0.1:10248/healthz
    ok
```
```txt
Kubernetes从1.8开始对资源指标（如容器CPU、内存使用率）通过MetricsAPI在K8S中获取。并且Metrics-server替代了heapster
Metrics-Server实现了Resource Metrics API，是集群核心监控数据的聚合器
Metrics-Server定时从Kubelet的Summary API采集指标并将这些聚合过的数据存储在内存中，以Metric-Api的形式暴露出去!
Metrics API只可查询当前时刻的度量数据，并不保存历史数据。URI为: /apis/metrics.k8s.io/，在k8s.io/metrics维护
必须部署Metrics-server才能使用该API，Metrics-server通过调用Kubelet Summary API获取数据
MetricsAPI的URI是/apis/metrics.k8s.io/，它扩展了K8S的核心API，因此部署metrics-server前需确认集群配置了聚合层
Metrics-Server因为将指标存放在内存因此监控数据是没有持久化的，可通过第三方存储来拓展，这个和heapster是一致的
----------------------------------------
官方废弃heapster项目而使用Metrics-Server的目的就是为了将核心资源监控作为一等公民对待
即像pod、service那样直接通过api-server或client直接访问，不再是安装hepater来汇聚且由heapster单独管理
----------------------------------------
在kubernetes的新监控体系中的核心指标与自定义指标：
    Metrics-server属于Core metrics (核心指标)，提供API metrics.k8s.io 仅提供Node和Pod的CPU和内存使用情况
    而其他Custom Metrics (自定义指标) 由Prometheus等组件完成
--------------------------------------------------------------------------------
自定义metrics使用方法：
  1.控制管理器开启--horizontal-pod-autoscaler-use-rest-clients=true
  2.控制管理器的–apiserver指向API Server Aggregator
  3.在API Server Aggregator中注册自定义的metrics API
--------------------------------------------------------------------------------
关于聚合层：
聚合层运行在Apiserver进程内部，允许用户为集群安装额外的Kubernetes风格的API来扩展core API的功能
聚合层需要启动Apiserver的时候开启方可使用。在用户注册扩展资源之前，聚合层什么也不做
用户若要注册API，则必需向系统中添加一个APIService对象，它用来声明API的URL路径以及处理请求的后端APIService
此后，聚合层会将发往那个路径的所有请求:(eg:/apis/myextension.mycompany.io/v1/…)都转发给注册的APIService
一般情况下APIService对象以extension-apiserver运行在集群中的一个pod中
如果要主动管理添加的资源，extension-apiserver还需与一或多个controlller进行关联，apiserver-builder为双方提供了一个框架
Service Catalog是Kubernetes的一种API扩展实现，方便Kubernetes集群内部应用访问集群外部、由第三方管理、提供的服务
如由云供应商提供的数据库服务。Service Catalog的安装会为它所提供的服务提供extension-apiserver和controller两个扩展组件
因为Api要统一，那么如何将请求到ApiServer的/apis/metrics请求转发给MetricsServer呢? 解决方案是：kube-aggregator (聚合)
--------------------------------------------------------------------------------
核心流程：是K8S正常工作所需要的核心度量，从Kubelet、cAdvisor等获取度量，再由metrics-server提供给Dashboard、HPA等使用
监控流程：是基于核心度量构建的监控流程：
         如Prometheus从metrics-server获取核心度量，从其他数据源如Node Exporter获取非核心度量，再基于它们构建监控系统
```
#### 部署 Metrics-Server 的前提
```bash
#在部署Metrics-Server之前需要修改Apiserver配置文件，加入如下参数来启用Aggregation layer
--requestheader-client-ca-file=/etc/kubernetes/ssl/ca.pem \
--requestheader-extra-headers-prefix=X-Remote-Extra- \
--requestheader-group-headers=X-Remote-Group \
--requestheader-username-headers=X-Remote-User \
--proxy-client-cert-file=/etc/kubernetes/ssl/metrics-server.pem \
--proxy-client-key-file=/etc/kubernetes/ssl/metrics-server-key.pem \
--runtime-config=api/all=true
#--requestheader-XXX、--proxy-client-XXX:
#     是 kube-apiserver 的 aggregator layer 相关的配置参数，metrics-server & HPA 需要使用；
#--requestheader-client-ca-file：
#     用于签名 --proxy-client-cert-file 和 --proxy-client-key-file 指定的证书；在启用了 metric aggregator 时使用
#如果 kube-apiserver 机器没有运行 kube-proxy，则还需要添加 --enable-aggregator-routing=true 参数
#注意 requestheader-client-ca-file 指定的 CA 证书，必须具有 client auth and server auth

#对kube-controller-manager添加如下配置参数：
--horizontal-pod-autoscaler-use-rest-clients=true   #用于配置 HPA 控制器使用 REST 客户端获取 metrics 数据
```
#### 部署 Metrics-Server
```bash
#创建Metrics-Server使用的证书
[root@master ~]# cat > metrics-server-csr.json <<'EOF'  
{
  "CN": "aggregator",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "CN",
      "ST": "BeiJing",
      "L": "BeiJing",
      "O": "k8s",
      "OU": "System"
    }
  ]
}
EOF

#使用上面创建的证书请求文件到Kubernetes的CA机构进行签名:
[root@master ~]# cfssl gencert -ca=/etc/kubernetes/ssl/ca.pem \
   -ca-key=/etc/kubernetes/ssl/ca-key.pem \ 
   -config=/opt/ssl/config.json \
   -profile=kubernetes metrics-server-csr.json | cfssljson -bare metrics-server

#将生成的证书拷贝到所有node和master节点
[root@master ~]# cp metrics-server*.pem /etc/kubernetess/ssl/
[root@master ~]# scp metrics-server*.pem  192.168.1.8:/etc/kubernetess/ssl/

#在K8S的kube-system命名空间部署Metrics-Server：
[root@master ~]# git clone https://github.com/kubernetes-incubator/metrics-server
[root@master ~]# cd metrics-server/deploy/1.8+        
[root@master ~]# vim metrics-server-deployment.yaml   #此配置需要先修改后执行 (另外还有其他配置文件，暂使用默认即可)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: metrics-server
  namespace: kube-system
---
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: metrics-server
  namespace: kube-system
  labels:
    k8s-app: metrics-server
spec:
  selector:
    matchLabels:
      k8s-app: metrics-server
  template:
    metadata:
      name: metrics-server
      labels:
        k8s-app: metrics-server
    spec:
      serviceAccountName: metrics-server
      volumes:  # mount in tmp so we can safely use from-scratch images and/or read-only containers
      - name: tmp-dir
        emptyDir: {}
      containers:
      - name: metrics-server    #镜像访问不到时可将其替换为：daocloud.io/liukuan73/metrics-server-amd64:v0.2.1
        image: mirrorgooglecontainers/metrics-server-amd64:v0.3.1 
        imagePullPolicy: Always
        command:
        - /metrics-server
        - --kubelet-insecure-tls                          #添加参数
        - --kubelet-preferred-address-types=InternalIP    #添加参数
        #- --tls-cert-file=
        #- --tls-private-key-file=
        volumeMounts:
        - name: tmp-dir
          mountPath: /tmp

# metrics-server-deployment.yaml 说明：
# 1、metrics默认用hostname来通信，而且coredns中已经添加了宿主机的/etc/resolv.conf 
# 所以只需添加一个内部的dns服务或在pod的deployment的yaml手动添加主机解析记录,再或者改变参数为InternalIP，直接用ip来连接
# 2、kubelet-insecure-tls: 跳过验证kubelet的ca证书，暂时开启。（不推荐用于生产环境）

#可通过 kubectl proxy 来访问 Metrics API：
http://127.0.0.1:8001/apis/metrics.k8s.io/v1beta1/nodes
http://127.0.0.1:8001/apis/metrics.k8s.io/v1beta1/nodes/<node-name>
http://127.0.0.1:8001/apis/metrics.k8s.io/v1beta1/pods
http://127.0.0.1:8001/apis/metrics.k8s.io/v1beta1/namespace//pods/
http://127.0.0.1:8001/apis/metrics.k8s.io/v1beta1/namespace/<namespace-name>/pods/<pod-name>
#必须部署 metrics-server 才能使用该 API，metrics-server 通过调用 Kubelet Summary API 获取数据

#也可直接通过 kubectl 来访问这些 API:
kubectl get –raw apis/metrics.k8s.io/v1beta1/nodes
kubectl get –raw apis/metrics.k8s.io/v1beta1/pods
kubectl get –raw apis/metrics.k8s.io/v1beta1/nodes/
kubectl get –raw apis/metrics.k8s.io/v1beta1/namespace//pods/

#执行
[root@master ~]# kubectl apply -f .
```
#### 查看APIServer资源
```bash
[root@master metrics]# kubectl api-versions
...............
crd.projectcalico.org/v1 
events.k8s.io/v1beta1 
extensions/v1beta1 
metrics.k8s.io/v1beta1                            # <------- 有Metrics控制器说明部署成功
networking.k8s.io/v1 
policy/v1beta1 
rbac.authorization.k8s.io/v1 
rbac.authorization.k8s.io/v1beta1 
scheduling.k8s.io/v1beta1 
storage.k8s.io/v1 
```
#### 查看指标
```bash
#Metrics-Server从集群中每个Node的kubelet的API收集metrics数据
#通过MetricsAPI可获取Kubernetes资源的Metrics指标，MetricsAPI挂载在/apis/metrics.k8s.io/下。可使用kubectl top访问：
[root@master metrics]# kubectl top node
NAME    CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
node1   140m         14%    1285Mi          73%
node2   37m          3%     458Mi           26%
[root@master metrics]# kubectl top pod --all-namespaces
NAMESPACE       NAME                                             CPU(cores)   MEMORY(bytes)
ingress-nginx   nginx-ingress-controller-77fc55d6dd-hmlmt        3m           90Mi
ingress-nginx   nginx-ingress-controller-77fc55d6dd-htms6        2m           84Mi
ingress-nginx   nginx-ingress-default-backend-684f76869d-pxlmz   1m           1Mi
kube-system     coredns-576cbf47c7-mlfcd                         2m           13Mi
kube-system     coredns-576cbf47c7-xgqdd                         2m           10Mi
kube-system     etcd-node1                                       13m          86Mi
kube-system     kube-apiserver-node1                             23m          514Mi
kube-system     kube-controller-manager-node1                    26m          54Mi
kube-system     kube-flannel-ds-amd64-8rcq4                      1m           18Mi
kube-system     kube-flannel-ds-amd64-mhx9t                      2m           14Mi
kube-system     kube-proxy-nljs8                                 2m           30Mi
kube-system     kube-proxy-pjdsj                                 2m           19Mi
kube-system     kube-scheduler-node1                             10m          18Mi
kube-system     kubernetes-dashboard-5746dd4544-gtj65            1m           28Mi
kube-system     metrics-server-8854b78d9-nx9tx                   1m           12Mi    # <--------------------
kube-system     tiller-deploy-6f6fd74b68-mc2cw                   1m           27Mi

#在Apiserver节点为Master打开一个反向代理端口
[root@master ~]# kubectl proxy --port=8080
Starting to serve on 127.0.0.1:8080
[root@master ~]# curl http://localhost:8080/apis/metrics.k8s.io/v1beta1/nodes     #挂载在/apis/metrics.k8s.io/下
{
  "kind": "NodeMetricsList",
  "apiVersion": "metrics.k8s.io/v1beta1",
  "metadata": {
    "selfLink": "/apis/metrics.k8s.io/v1beta1/nodes"
  },
  "items": [
    {
      "metadata": {
        "name": "master",
        "selfLink": "/apis/metrics.k8s.io/v1beta1/nodes/master",
        "creationTimestamp": "2018-09-25T09:48:21Z"
      },
      "timestamp": "2018-09-25T09:48:00Z",
      "window": "1m0s",
      "usage": {
        "cpu": "211m",
        "memory": "2905388Ki"
      }
    },
    {
      "metadata": {
        "name": "node01",
        "selfLink": "/apis/metrics.k8s.io/v1beta1/nodes/node01",
        "creationTimestamp": "2018-09-25T09:48:21Z"
      },
      "timestamp": "2018-09-25T09:48:00Z",
      "window": "1m0s",
      "usage": {
        "cpu": "150m",
        "memory": "3670276Ki"
      }
    }
  ]
```
#### 基于CPU和内存使用率的自动伸缩
```bash
#并非所有系统都可仅靠CPU和内存指标来满足SLA，大多数Web应用的后端都需要基于每秒的请求数量进行弹性伸缩来处理突发流量
#对于ETL应用程序，可通过设置Job队列长度超过某个阈值来触发弹性伸缩
#可通过Prometheus来监控应用程序并暴露出用于弹性伸缩的自定义指标，对应用程序进行微调以更好地处理突发事件从而确保其高可用性

#定义一个保持最少两个副本的HPA，如果CPU平均使用量超过80％或内存超过200Mi，则最高可扩展到10个副本：
apiVersion: autoscaling/v2beta1     #使用提供自动伸缩功能的资源API，注意其属于V2版本! (HPAV2)
kind: HorizontalPodAutoscaler       #定义HPAv2资源
metadata:
  name: podinfo                     #HPAV2实例的名称
spec:
  scaleTargetRef:
    apiVersion: extensions/v1beta1  #指明对哪类API资源执行伸缩
    kind: Deployment                #执行伸缩的目标类型
    name: podinfo
  minReplicas: 2                    #最小副本数
  maxReplicas: 10                   #最大副本数
  metrics:                          #触发伸缩的指标依据
  - type: Resource                  #类型为资源
    resource:
      name: cpu                     #当CPU平均使用率超过80%时
      targetAverageUtilization: 80
  - type: Resource
    resource:
      name: memory                  #当内存平均使用率超过200Mi时
      targetAverageValue: 200Mi

#当执行几秒钟后，HPA控制器与Metrics-Server进行通信，然后获取CPU和内存使用情况：
[root@master ~]# kubectl get hpa
NAME      REFERENCE            TARGETS                      MINPODS   MAXPODS   REPLICAS   AGE
podinfo   Deployment/podinfo   2826240 / 200Mi, 15% / 80%   2         10        2          5m

[root@master ~]# kubectl describe hpa podinfo         #执行压测后查看伸缩效果
Events:
  Type    Reason             Age   From                       Message
  ----    ------             ----  ----                       -------
  Normal  SuccessfulRescale  7m    horizontal-pod-autoscaler  New size: 4; reason: cpu resource utilization (percentage of request) above target
  Normal  SuccessfulRescale  3m    horizontal-pod-autoscaler  New size: 8; reason: cpu resource utilization (percentage of request) above target
```
#### 使用 Prometheus 部署 Custom Metrics Server
```bash
#想让K8s的HPA获取核心指标以外的其它自定义指标，必须部署一套prometheus监控系统，让prometheus采集其它各种指标
#但prometheus采集到的metrics并不能直接给k8s用，因为两者数据格式不兼容
#还需另一个组件 (kube-state-metrics) 将prometheus的metrics数据格式转换成k8s API接口能识别的格式
#转换以后因为是自定义API，所以还需用 Kubernetes aggregator 在Master节点的kube-apiserver中注册以便直接通过/apis/来访问
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Kubernetes里的Custom Metrics机制是借助Aggregator APIServer扩展机制来实现的。
#原理当把Custom Metrics APIServer启动之后Kubernetes里就会出现叫作custom.metrics.k8s.io的API
#而你访问这个URL时Aggregator就会把的请求转发给Custom Metrics APIServer
#而Custom Metrics APIServer的实现其实就是一个Prometheus项目的Adaptor （最终是按照固定的格式返回给访问者）
#最普遍的做法就是让Pod里的应用本身暴露出/metrics API，然后在这个API里返回自己收到的如:HTTP的请求的数量

#cAdvisor已经内置了对Prometheus的支持。访问http://localhost:8080/metrics即可获取到标准的Prometheus监控样本输出
--------------------------------------------------------------------------------
#为了让HPA可根据自定义指标进行扩展，需要有几个组件 ( 有一些是不重要的 )：
1.node-exporter：
#它是prometheus的agent端，负责收集Node级别的监控数据
1.Prometheus :                  
#它是监控服务端，从node-exporter拉数据并存为时序数据
2.kube-state-metrics： 
#将prometheus中可以用PromQL查询到的指标数据转换成k8s对应的数据格式（用来整合数据），即
#转换成【Custerom Metrics API】接口格式的数据，但是它没有聚合进apiserver中的功能。
3.custom-metrics-apiserver: 
#使用k8s-prometheus-adapter提供的metrics来扩展Kubernetes实现自定义的指标API ( 聚合apiserver )
#prometheus是不能直接解析为k8s的指标的，需要借助k8s-prometheus-adapter转换成api
#它是一种Custom Metrics API的实现，所以需要将prometheus-adapter在Apiserver注册为Custom Metrics API
4.grafana：
#展示prometheus获取到的metrics
--------------------------------------------------------------------------------

#从K8S源码树中的addons获取prometheus相关组件的资源清单文件：prometheus、node-exporter、kube-state-metrics
https://github.com/kubernetes/kubernetes/blob/master/cluster/addons/prometheus/node-exporter-ds.yml

#k8s-prometheus-adpater的清单文件还没有找到

#对于prometheus有几点说明：
#prometheus自带的UI监听在9090端口，建议使用NodePort以便集群外访问。
#prometheus使用的volume"prometheus-storage-volume"存储所有它采集到的metrics，应该放于持久卷中


#创建 monitoring 命名空间：
[root@master ~]# $ kubectl create -f ./namespaces.yaml

#将 Prometheus v2 部署到 monitoring 命名空间：
[root@master ~]# $ kubectl create -f ./prometheus

#生成 Prometheus adapter 所需的 TLS 证书：
[root@master ~]# $ make certs

#部署custom-metrics-apiserver：
[root@master ~]# $ kubectl create -f ./custom-metrics-api

#列出由Prometheus提供的自定义指标：
[root@master ~]# $ kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1" | jq .

#获取 monitoring 命名空间中所有 pod 的 FS 信息：
[root@master ~]# $ kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/monitoring/pods/*/fs_usage_bytes" | jq .

#基于自定义指标的自动扩容:
#在 default 命名空间中部署 podinfo：
[root@master ~]# $ kubectl create -f ./podinfo/podinfo-svc.yaml,./podinfo/podinfo-dep.yaml
#podinfo应用暴露了一个自定义的度量指标：http_requests_total。
#Prometheus adapter (即:custom-metrics-apiserver) 删除了 _total 后缀并将该指标标记为: counter metric

#从自定义指标API获取每秒的总请求数：
$ kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/default/pods/*/http_requests" | jq .
{
  "kind": "MetricValueList",
  "apiVersion": "custom.metrics.k8s.io/v1beta1",
  "metadata": {
    "selfLink": "/apis/custom.metrics.k8s.io/v1beta1/namespaces/default/pods/%2A/http_requests"
  },
  "items": [
    {
      "describedObject": {
        "kind": "Pod",
        "namespace": "default",
        "name": "podinfo-6b86c8ccc9-kv5g9",
        "apiVersion": "/__internal"
      },
      "metricName": "http_requests",
      "timestamp": "2018-01-10T16:49:07Z",
      "value": "901m"                         #m表示毫，如901m表示901毫次/每秒
    },
    {
      "describedObject": {
        "kind": "Pod",
        "namespace": "default",
        "name": "podinfo-6b86c8ccc9-nm7bl",
        "apiVersion": "/__internal"
      },
      "metricName": "http_requests",
      "timestamp": "2018-01-10T16:49:07Z",
      "value": "898m"
    }
  ]
}

#创建HPA，如果请求数超过每秒10次将扩大podinfo副本：
apiVersion: autoscaling/v2beta1
kind: HorizontalPodAutoscaler
metadata:
  name: podinfo
spec:
  scaleTargetRef:
    apiVersion: extensions/v1beta1
    kind: Deployment
    name: podinfo
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Pods
    pods:
      metricName: http_requests         #指定其使用的自定义度量指标的名称
      targetAverageValue: 10            #若此值超过10则进行扩容
```
#### 备忘
```bash
#部署完成后使用下面的命令查看node相关的指标：
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/nodes"
{"kind":"NodeMetricsList","apiVersion":"metrics.k8s.io/v1beta1","metadata":{"selfLink":"/apis/metrics.k8s.io/v1beta1/nodes"},"items":[]}
#没有获取到信息，此时查看metric-server容器的日志，有下面的错误：
E1003 05:46:13.757009       1 manager.go:102] unable to fully collect metrics: [unable to fully scrape metrics from source kubelet_summary:node1: unable to fetch metrics from Kubelet node1 (node1): Get https://node1:10250/stats/summary/: dial tcp: lookup node1 on 10.96.0.10:53: no such host, unable to fully scrape metrics from source kubelet_summary:node2: unable to fetch metrics from Kubelet node2 (node2): Get https://node2:10250/stats/summary/: dial tcp: lookup node2 on 10.96.0.10:53: read udp 10.244.1.6:45288->10.96.0.10:53: i/o timeout]

#可以看到metrics-server在从kubelet的10250端口获取信息时，使用的是hostname
#而因为node1和node2是一个独立的Kubernetes演示环境，只是修改了这两个节点系统的/etc/hosts文件，而并没有内网的DNS服务器
#所以metrics-server中不认识node1和node2的名字。这里我们可以直接修改Kubernetes集群中的coredns的configmap
#修改Corefile加入hostnames插件，将Kubernetes的各个节点的主机名加入到hostnames中
#这样Kubernetes集群中的所有Pod都可以从CoreDNS中解析各个节点的名字。
kubectl edit configmap coredns -n kube-system

apiVersion: v1
data:
  Corefile: |
    .:53 {
        errors
        health
        hosts {
           192.168.61.11 node1
           192.168.61.12 node2
           fallthrough
        }
        kubernetes cluster.local in-addr.arpa ip6.arpa {
           pods insecure
           upstream
           fallthrough in-addr.arpa ip6.arpa
        }
        prometheus :9153
        proxy . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
kind: ConfigMap
#配置修改完毕后重启集群中coredns和metrics-server，确认metrics-server不再有错误日志。
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/nodes"

```