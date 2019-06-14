
##### 注意！本文档描述的是旧版本的K8S自定义度量值的处理流程! heapster从1.11开始逐渐被废弃
```bash
#从 v1.7 开始，Kubelet metrics API 不再包含 cadvisor metrics，而是提供了一个独立的 API 接口：

* Kubelet  metrics:     http://127.0.0.1:8001/api/v1/proxy/nodes/<node-name>/metrics
* Cadvisor metrics:     http://127.0.0.1:8001/api/v1/proxy/nodes/<node-name>/metrics/cadvisor

#cAdvisor已经内置了对Prometheus的支持。访问http://localhost:8080/metrics即可获取到标准的Prometheus监控样本输出
#cadvisor监听的端口将在v1.12中删除，建议所有外部工具使用Kubelet Metrics API替代。
#cAdvisor显示当前Host资源使用情况，包括 CPU、内存、网络、文件系统等（展示 Host 和容器两个层次的监控数据）
#cAdvisor的亮点是可将监控到的数据导出给第三方工具，由这些工具进一步加工处理
#可把cAdvisor定位为监控数据收集器，收集和导出数据是它的强项，而非展示数据，其支持许多第三方工具，如Prometheus
#kubelet自带cadvisor监控所有节点，可通过"--cadvisor-port="指定端口（默认4194） 注意：--privileged=true
#当前cAdvisor只支持http接口方式，也就是被监控容器应用必须提供http接口，所以能力较弱

#从 Kubernetes 1.8 开始，资源使用指标（如容器 CPU 和内存使用率）可以通过 Metrics API 在 Kubernetes 中获取!
#     这些指标可以直接被用户访问，如通过 kubectl top 命令
#     或由集群中的控制器使用，如，Horizontal Pod Autoscale 可以使用这些指标作出决策
#     例如使用 kubectl top node 和 kubectl top pod 查看资源使用情况：

$ kubectl top node
NAME              CPU(cores)   CPU%      MEMORY(bytes)   MEMORY%
192.168.123.248   245m         12%       2687Mi          34%
192.168.123.249   442m         22%       3270Mi          42%
192.168.123.250   455m         22%       4014Mi          52%

$ kubectl top pod
NAME                              CPU(cores)   MEMORY(bytes)
details-v1-64b86cd49-52g82        0m           11Mi
podinfo-6b86c8ccc9-5qr8b          0m           7Mi
podinfo-6b86c8ccc9-hlxm7          0m           12Mi
podinfo-6b86c8ccc9-qxhng          0m           6Mi
```
#### cAdvisor+Heapster+influxdb
```txt
                         [k8s-master]
                              ^
    k8s-node                  |
[kubelet(cadvisor)] ----> [Heapster] <----> [Influxdb]    （新版本中metrics-server替代了heapster）
                              ^
                              |
                     [kubelet(cadvisor)]                            

访问http://localhost:8080/metrics，可以拿到cAdvisor暴露给 Prometheus的数据

Heapster：  将每个Node上的cAdvisor的数据进行汇总后导到InfluxDB（新版本中metrics-server替代了heapster）
            前提是使用cAdvisor采集每个node上主机和容器资源的使用情况，再将所有node上的数据进行聚合。
            这样不仅可以看到Kubernetes集群的资源情况，还可以分别查看每个node/namespace及每个node/namespace下pod的资源
            可以从cluster、node、pod的各个层面提供详细的资源使用情况
            [ Kubernetes Metrics Server 是一个集群范围内的资源使用量的聚合器，它是 Heapster 的继承者! ]
nfluxDB：   时序数据库，提供数据的存储，存储在指定的目录下。
Grafana：   提供了WEB控制台，自定义查询指标，从InfluxDB查询数据并展示。
```
#### 说明
```txt
自Kubernetes 1.11版本起:
资源采集指标由Resource Metrics API（Metrics Server）和Custom metrics api（Prometheus）2种API实现，传统Heapster被废弃
Metrics Server：  主要负责采集Node、Pod的核心资源数据，如内存、CPU等
Prometheus：      主要负责自定义指标数据采集，如网卡流量，磁盘IOPS、HTTP请求数、数据库连接数等。
```
#### 自定义指标
```bash
#在kubelet启动参数里要加上--enable-custom-metrics=true
#kubelet依此参数在容器启动时对其加标签："io.cadvisor.metric.prometheus":"/etc/custom-metrics/definition.json"
#要支持custom metric，对容器也有要求，容器内/etc/custom-metrics/definition.json要有API endpoint供cAdvisor获取
#以上说明参考来源：https://blog.csdn.net/liuliuzi_hz/article/details/72846234

#在Pod内的"/etc/custom-metrics/definition.json"中：
{"endpoint":"http://192.168.10.2:8080/metrics"} 

#上面的json中的容器IP是动态写入的，在容器初始化时写入"PodIP"，其实现方法如下：
apiVersion:extensions/v1beta1
kind: Deployment
metadata:
  name: kubia
spec:
  replicas: 1
  template:
    metadata:
      name: kubia
      labels:
        app: kubia
      annotations:
        pod.beta.kubernetes.io/init-containers:'[
          {
              "name":"setup",
              "image":"busybox",
              "imagePullPolicy":"IfNotPresent",
              "command":["sh", "-c", "echo \"{\\\"endpoint\\\":\\\"http://$POD_IP:8080/metrics\\\"}\" | >/etc/custom-metrics/definition.json"],
              "env": [{
                "name":"POD_IP",
                "valueFrom": {
                  "fieldRef": {
                    "apiVersion":"v1",
                    "fieldPath":"status.podIP"
                  }
                }
              }],
              "volumeMounts": [
                  {
                      "name":"config",
                      "mountPath":"/etc/custom-metrics"
                  }
              ]
          }
        ]'
    spec:
      containers:
      - image: luksa/kubia:qps
        name: nodejs
        ports:
          - containerPort: 8080
        volumeMounts:
        - name: config
          mountPath: /etc/custom-metrics

#在容器里要提供一个restAPI服务，服务地址就是definition.json所标记地址。可以尝试curl这个地址，看是否正常获取数据：
curl http://192.168.10.2:8080/metrics
# TYPE qpsgauge                           //不能忽略该行，否则未知类型的数据会被heapster抛弃
qps 0
# TYPE testmetricgauge                    //不能忽略该行，否则未知类型的数据会被heapster抛弃
testmetric 0.41291926987469196

#然后两种方法确认cAdvisor是否正常获取该数据。
#第一种curl cAdvisor地址：
curl 10.140.163.102:4194/api/v1.0/containers/docker/44d52b9acfc334233f685c81f130cd44538602980a8bff16495d1067bf
#第二种方法访问cAdvisor GUI：10.140.163.102:4194


#关于cAdvisor支持自定义指标方式能力：
#其自身是通过容器部署时设置lable标签项：io.cadvisor.metric.开头的lable，而value则为自定义指标的配置文件，形式如下：
{
  "endpoint" : {
    "protocol": "https",
    "port": 8000,
    "path": "/nginx_status"
  },
  "metrics_config"  : [
    { "name" : "activeConnections",
      "metric_type" : "gauge",
      "units" : "number of active connections",
      "data_type" : "int",
      "polling_frequency" : 10,
      "regex" : "Active connections: ([0-9]+)"
    },
    { "name" : "reading",
      "metric_type" : "gauge",
      "units" : "number of reading connections",
      "data_type" : "int",
      "polling_frequency" : 10,
      "regex" : "Reading: ([0-9]+) .*"
    },
    { "name" : "writing",
      "metric_type" : "gauge",
      "data_type" : "int",
      "units" : "number of writing connections",
      "polling_frequency" : 10,
      "regex" : ".*Writing: ([0-9]+).*"
    },
    { "name" : "waiting",
      "metric_type" : "gauge",
      "units" : "number of waiting connections",
      "data_type" : "int",
      "polling_frequency" : 10,
      "regex" : ".*Waiting: ([0-9]+)"
    }
  ]

}

#注，在注解中：
io.cadvisor.metric.raw:         #表示其属于Cadvisor的自定义监控项（K8S目前仅支持以Prometheus格式收集自定义指标!）
io.cadvisor.metric.prometheus:  #表示其属于prometheus的自定义监控项
```