#### Prometheus 自动发现 Kubernetes 资源
```yaml
#参考：https://stackoverflow.com/questions/53365191/monitor-custom-kubernetes-pod-metrics-using-prometheus
#普罗米修斯可直接通过K8S的API接口发现要监控的目标
#若Pod资源中运行的用户自定义指标需要被监控，则对该资源添加如下注释：
#  annotations:
#    prometheus.io/probe: "true"
#    prometheus.io/scrape: 'true'
#    prometheus.io/path: '/data/metrics'
#    prometheus.io/port: '80

apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |-
    global:
      scrape_interval:     15s 
      evaluation_interval: 15s

    scrape_configs:

    - job_name: 'kubernetes-nodes'
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: node    #指定模式为node，会自动发现所有node节点作为当前Job监控的Target

    #支持的发现类型:
    - job_name: 'kubernetes-service'
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: [pod/service/endpoints/ingress/pod]

#通过Promdash的Service Discovery页面可看到当前Prometheus通过Kubernetes发现的所有资源对象
#同时Prometheus会自动将该资源所有元信息以标签形式体现在Target对象上。如下所示是Promthues获取到的Node节点的标签信息：
#   __address__="192.168.99.100:10250"
#   __meta_kubernetes_node_address_Hostname="minikube"
#   __meta_kubernetes_node_address_InternalIP="192.168.99.100"
#   __meta_kubernetes_node_annotation_alpha_kubernetes_io_provided_node_ip="192.168.99.100"
#   __meta_kubernetes_node_annotation_node_alpha_kubernetes_io_ttl="0"
#   __meta_kubernetes_node_annotation_volumes_kubernetes_io_controller_managed_attach_detach="true"
#   __meta_kubernetes_node_label_beta_kubernetes_io_arch="amd64"
#   __meta_kubernetes_node_label_beta_kubernetes_io_os="linux"
#   __meta_kubernetes_node_label_kubernetes_io_hostname="minikube"
#   __meta_kubernetes_node_name="minikube"
#   __metrics_path__="/metrics"
#   __scheme__="https"
#   instance="minikube"
#   job="kubernetes-nodes"
```
#### 监控Kubernetes集群监控的各个维度以及策略
目标 | 服务发现模式 |  监控方法 | 数据源  
-|-|-|-
从各节点的kubelet获取节点kubelet的基本运行状态 | node | 白盒监控 | kubelet
从各节点的kubelet内置的cAdvisor获取节点运行容器的监控 | node | 白盒监控 | kubelet
从运行在各节点的Node Exporter采集主机资源相关的信息 | node | 白盒监控 | node exporter
对内置Promthues支持的应用，需从Pod实例中采集其自定义指标 | pod | 白盒监控  | custom pod
获取API Server地址并从中获取K8S集群相关运行指标 | endpoints | 白盒监控 | api server
获取Service访问地址并通过Blackbox Exporter获取网络探测指标 | service | 黑盒监控 | blackbox exporter
获取Ingress访问信息并通过Blackbox Exporter获取网络探测指标 | ingress | 黑盒监控 | blackbox exporter
#### 从Kubelet获取节点运行状态
```yaml
#基于Node模式，Prometheus会自动发现Kubernetes中所有Node节点信息并作为监控的目标Target
#而这些Target的访问地址实际上就是Kubelet的访问地址，并且Kubelet直接内置了对Promtheus的支持
#修改prometheus.yml配置文件，并添加以下采集任务配置：

#第一种方式：
- job_name: 'kubernetes-kubelet'
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      insecure_skip_verify: true        #由于当前使用ca证书中不包含节点地址信息，直接跳过ca证书校验过程
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    kubernetes_sd_configs:
    - role: node                        #使用Node模式自动发现集群中所有Kubelet作为监控的数据采集目标
    relabel_configs:
    - action: labelmap                  #通过labelmap步骤将Node节点上的标签作为样本的标签保存到时间序列当中
      regex: __meta_kubernetes_node_label_(.+)

#第二种方式:
#不直接通过kubelet的metrics采集，而是通过Kubernetes的api-server提供的代理API访问各个节点中的metrics：
- job_name: 'kubernetes-kubelet'
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    kubernetes_sd_configs:
    - role: node
    relabel_configs:
    - action: labelmap
      regex: __meta_kubernetes_node_label_(.+)
    - target_label: __address__         #将默认地址__address__的值替换为kubernetes.default.svc:6443
      replacement: kubernetes.default.svc:6443
    - source_labels: [__meta_kubernetes_node_name]
      regex: (.+)
      replacement: /api/v1/nodes/${1}/proxy/metrics
      target_label: __metrics_path__    #将__metrics_path__替换为Apiserver中node的代理地址
```
#### 从Kubelet获取cAdvisor指标
```yaml
#各节点kubelet除包含自身监控指标信息外，还内置对cAdvisor的支持
#cAdvisor能获取当前节点运行的所有容器的资源情况，通过访问kubelet的"/metrics/cadvisor"可获取到cadvisor指标
#因此和获取kubelet监控指标类似，这里同样通过node模式自动发现所有的kubelet信息
#与采集kubelet自身监控指标相似，这里也有两种方式采集cadvisor中的监控指标
#通过适当的relabel修改监控采集任务的配置：

#第一种方式：
    - job_name: 'kubernetes-cadvisor'
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: node
      relabel_configs:                  #直接访问kubelet的/metrics/cadvisor地址，需跳过ca证书认证
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        replacement: metrics/cadvisor
        target_label: __metrics_path__
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

#第二种方式：
    - job_name: 'kubernetes-cadvisor'
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - target_label: __address__       #通过api-server提供的代理地址访问kubelet的/metrics/cadvisor地址
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics/cadvisor
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
```
#### 使用NodeExporter监控集群资源使用情况
```yaml
#为了采集集群中各节点的资源使用情况，需在各节点部署Node Exporter，此时需使用Daemonset控制器
#Daemonset确保在集群中所有（也可以指定）节点上运行唯一的Pod实例：

apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: node-exporter
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: 'true'
        prometheus.io/port: '9100'
        prometheus.io/path: 'metrics'
      labels:
        app: node-exporter
      name: node-exporter
    spec:
      containers:
      - image: prom/node-exporter
        imagePullPolicy: IfNotPresent
        name: node-exporter
        ports:
        - containerPort: 9100
          hostPort: 9100
          name: scrape
      hostNetwork: true                 #让Pod能够以主机网络以及系统进程的形式运行
      hostPID: true                     #


#创建daemonset的同时YAML中也创建了NodeExporter相应的Service。这样通过Service就可以访问到对应的NodeExporter实例
#接下来只需要通过Prometheus的pod服务发现模式找到当前集群中部署的Node Exporter实例即可

#为Prometheus创建监控采集任务kubernetes-pods：
  - job_name: 'kubernetes-pods'
    #https://github.com/prometheus/prometheus/blob/master/documentation/examples/prometheus-kubernetes.yml
    kubernetes_sd_configs:  
    - role: pod
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
    - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
      action: replace
      regex: ([^:]+)(?::\d+)?;(\d+)
      replacement: $1:$2
      target_label: __address__
    - action: labelmap
      regex: __meta_kubernetes_pod_label_(.+)
    - source_labels: [__meta_kubernetes_namespace]
      action: replace
      target_label: kubernetes_namespace
    - source_labels: [__meta_kubernetes_pod_name]
      action: replace
      target_label: kubernetes_pod_name

#通过以上relabel过程实现对Pod实例的过滤以及采集任务地址替换，从而实现对特定Pod实例监控指标的采集
#对于任意Pod实例，只要其提供了对Prometheus的支持度量路径，都可以通过为Pod添加注解的形式实现指标采集的支持
```
#### 获取kube-apiserver的度量指标
```yaml
#一般来说Service有两个主要的使用场景：

#1. 代理对集群内部应用Pod实例的请求：当创建Service时如果指定标签选择器，Kubernetes会监听集群中所有的Pod变化情况
#   通过Endpoints自动维护满足标签选择器的Pod实例的访问信息

#2. 代理对集群外部服务的请求：当创建Service时若不指定任何的标签选择器，那么需要手动创建Service对应的Endpoint
#   一般来说为了确保数据的安全通将数据库服务部署到集群外
#   这是为了避免集群内的应用硬编码数据库的访问信息，这是就可以通过在集群内创建Service，并指向外部的数据库服务实例

#kube-apiserver扮演了整个Kubernetes集群管理的入口的角色，负责对外暴露API
#kube-apiserver组件一般独立部署在集群外，为了能让部署在集群内的应用（K8S插件或用户应用）能与kube-apiserver交互
#Kubernetes会默认在命名空间下创建名为kubernetes的服务，如下所示：
$ kubectl get svc kubernetes -o wide
NAME                  TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE       SELECTOR
kubernetes            ClusterIP   10.96.0.1       <none>        443/TCP          166d      <none>
#该kubernetes服务代理的后端实际地址通过endpoints进行维护，如下所示：
$ kubectl get endpoints kubernetes
NAME         ENDPOINTS        AGE
kubernetes   10.0.2.15:8443   166d
#通过这种方式集群内的应用或系统主机就可以通过集群内部DNS：kubernetes.default.svc访问到外部的kube-apiserver
#因此如果要监控kube-apiserver相关的指标，只需要通过endpoints资源找到kubernetes对应的所有后端地址即可
#如下所示，创建监控任务kubernetes-apiservers，这里指定了服务发现模式为endpoints
#Promtheus会查找当前集群中所有的endpoints配置，并通过relabel进行判断是否为apiserver对应的访问地址：
- job_name: 'kubernetes-apiservers'
  kubernetes_sd_configs:
  - role: endpoints
  scheme: https
  tls_config:
    ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
  bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
  relabel_configs:
  - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
    action: keep
    regex: default;kubernetes;https           #判断当前endpoints是否为kube-apiserver的地址
  - target_label: __address__
    replacement: kubernetes.default.svc:443   #替换监控采集地址"__address_"到"kubernetes.default.svc:443"即可
```
#### 对Ingress和Service进行网络探测
```yaml
#为对Ingress和Service进行探测，需要在集群部署Blackbox Exporter实例。 如下所示:
apiVersion: v1
kind: Service
metadata:
  labels:
    app: blackbox-exporter
  name: blackbox-exporter
spec:
  ports:
  - name: blackbox
    port: 9115
    protocol: TCP
  selector:
    app: blackbox-exporter
  type: ClusterIP
---
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  labels:
    app: blackbox-exporter
  name: blackbox-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: blackbox-exporter
  template:
    metadata:
      labels:
        app: blackbox-exporter
    spec:
      containers:
      - image: prom/blackbox-exporter
        imagePullPolicy: IfNotPresent
        name: blackbox-exporter
#部署Blackbox Exporter的Pod，同时通过在集群内暴露地址：blackbox-exporter.default.svc.cluster.local
#对于集群内的任意服务都可以通过该内部DNS域名访问Blackbox Exporter实例：
$ kubectl get pods
NAME                                 READY     STATUS        RESTARTS   AGE
blackbox-exporter-f77fc78b6-72bl5    1/1       Running       0          4s

$ kubectl get svc
NAME                     TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)     AGE
blackbox-exporter        ClusterIP   10.109.144.192   <none>        9115/TCP    3m

#为了能让Prometheus能自动的对Service进行探测，需要通过服务发现自动找到所有的Service信息：
    - job_name: 'kubernetes-services'
      metrics_path: /probe
      params:
        module: [http_2xx]
      kubernetes_sd_configs:
      - role: service   #通过指定kubernetes_sd_config的role为service指定服务发现模式：
      relabel_configs:
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_probe]
        action: keep    #为区分集群中需进行探测的Service，通过标签"prometheus.io/probe: true"过滤需要探测的实例
        regex: true
      - source_labels: [__address__]   
        target_label: __param_target    #将通过服务发现获取到的Service实例地址__address__转换为获取监控的请求参数
      - target_label: __address__
        replacement: blackbox-exporter.default.svc.cluster.local:9115
      - source_labels: [__param_target] #将__address执行Blackbox Exporter实例的访问地址，并重写标签instance的内容
        target_label: instance
      - action: labelmap                #最后为监控样本添加了额外的标签信息：
        regex: __meta_kubernetes_service_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_service_name]
        target_label: kubernetes_name

#对于Ingress而言也是一个类似的过程，这里给出对Ingress探测的Promthues任务配置作为参考：
    - job_name: 'kubernetes-ingresses'
      metrics_path: /probe
      params:
        module: [http_2xx]
      kubernetes_sd_configs:
      - role: ingress
      relabel_configs:
      - source_labels: [__meta_kubernetes_ingress_annotation_prometheus_io_probe]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_ingress_scheme,__address__,__meta_kubernetes_ingress_path]
        regex: (.+);(.+);(.+)
        replacement: ${1}://${2}${3}
        target_label: __param_target
      - target_label: __address__
        replacement: blackbox-exporter.default.svc.cluster.local:9115
      - source_labels: [__param_target]
        target_label: instance
      - action: labelmap
        regex: __meta_kubernetes_ingress_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_ingress_name]
        target_label: kubernetes_name
```
#### relabel_config Example
```txt
# The source labels select values from existing labels. Their content is concatenated
# using the configured separator and matched against the configured regular expression
# for the replace, keep, and drop actions.
[ source_labels: '[' <labelname> [, ...] ']' ]

# Separator placed between concatenated source label values.
[ separator: <string> | default = ; ]

# Label to which the resulting value is written in a replace action.
# It is mandatory for replace actions. Regex capture groups are available.
[ target_label: <labelname> ]

# Regular expression against which the extracted value is matched.
[ regex: <regex> | default = (.*) ]

# Modulus to take of the hash of the source label values.
[ modulus: <uint64> ]

# Replacement value against which a regex replace is performed if the
# regular expression matches. Regex capture groups are available.
[ replacement: <string> | default = $1 ]

# action定义当前relabel_config对Metadata标签的处理方式，默认的action行为为replace
# replace行为会根据regex的配置匹配source_labels标签的值（多个source_label的值会按照separator进行拼接）
# 并将匹配到的值写入到target_label中，如果有多个匹配组，则可使用${1}, ${2}确定写入的内容
# 如果没匹配到任何内容则不对target_label进行重写
# repalce操作允许用户根据Target的Metadata标签重写或者写入新的标签键值对
# 在多环境的场景下可以帮助用户添加与环境相关的特征维度，从而可以更好的对数据进行聚合
[ action: <relabel_action> | default = replace ]

# 在action中除了使用replace以外，还可以定义action的配置为labelmap
# 与replace不同的是，labelmap根据regex的定义去匹配Target中所有标签名称，并以匹配到的内容为新的标签名，其值为新标签的值


#使用labelkeep或者labeldrop则可以对Target标签进行过滤，仅保留符合过滤条件的标签：

    relabel_configs:
      - regex: label_should_drop_(.+)
        action: labeldrop

#如果我们只希望采集数据中心dc1中的Node Exporter实例的样本数据，那么可以使用如下配置：

    relabel_configs:
    - source_labels:  ["__meta_consul_dc"]
      regex: "dc1"
      action: keep
```