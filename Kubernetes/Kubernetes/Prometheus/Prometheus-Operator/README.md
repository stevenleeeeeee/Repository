```txt
参考：
http://www.servicemesher.com/blog/prometheus-operator-manual/
https://github.com/coreos/prometheus-operator/tree/master/Documentation
https://www.cnblogs.com/kevincaptain/p/10032694.html
https://blog.csdn.net/weixin_34399060/article/details/87643861  (kube-prometheus 提供了针对K8S的自动化监控)
https://github.com/1046102779/prometheus/blob/master/prometheus/querying/basics.md  (普罗米修斯中文说明)

cAdvisor内置对Prometheus支持

若Pod资源中运行的用户自定义指标需被监控，需对Pod或service添加注释：
  ......
  annotations:
    prometheus.io/probe: "true"
    prometheus.io/scrape: 'true'
    prometheus.io/path: '/data/metrics'
    prometheus.io/port: '80'
    prometheus.io/scheme 'http'   默认http，如果为了安全设置了https，此处改为https
  ......

    个人认为：
    如果某些部署应用只有pod没有service，那么这种情况只能在pod上加注解，通过kubernetes-pods采集metrics
    如果有service就无需在pod加注解了，直接在service上加即可。毕竟service-endpoints最终也会落到pod中
```
#### Prometheus-operator
```txt
CoreOS / Prometheus Operator 官方提供的说明：
https://github.com/coreos/prometheus-operator/blob/master/Documentation/api.md#ServiceMonitorSpec

从概念讲Operator就是针对管理特定应用程序的
它在K8S基本的Resource和Controller的概念上以扩展Kubernetes api的形式创建、配置、管理复杂的有状态应用程序
从而实现特定应用的常见操作以及运维自动化 ( K8S允许添加CRD资源并通过实现自定义的Controller来实现对其进行扩展 )
其本质就是自定义CRD资源及对应的Controller实现!，Prometheus-Operator这个controller使用BRAC授权去监听自定义资源的变化
并根据这些资源的定义自动化完成如Prometheus Server自身及配置的自动化管理工作!
简言之: Prometheus Operator 帮助自动化创建以及管理Prometheus Server和配置信息

Prometheus Operator目前提供4类资源:
  1.Prometheus：            声明式创建和管理Prometheus Server实例
  2.ServiceMonitor：        声明式管理监控配置
  3.PrometheusRule：        声明式管理告警配置
  4.Alertmanager：          声明式创建和管理Alertmanager实例
```
#### Prometheus-operator 中的 ServiceMonitor 资源说明
```txt
因为svc负载，所以在K8S里监控metrics的最小单位都是svc背后endpoint指向的对象中的target
因此prometheus-operator创建了对应CRD: ServiceMonitor 
使用ServiceMonitor资源声明要监控选中的svc的label及metrics的url路径和其所属的namespaces即可实现自动发现及拉取指标!
Prometheus Operator监听这些CRD对象的信息并根据这些资源的定义自动化的完成如Prometheus Server自身及配置的自动化管理
```
#### 部署 Prometheus Operator
```bash
git clone https://github.com/coreos/prometheus-operator.git

kubectl create namespace monitoring     #为Promethues Operator创建单独的命名空间

#部署prometheus operator
#由于需要对Prometheus Operator进行RBAC授权，而默认的bundle.yaml中使用了default命名空间
#因此在安装前要先修改bundle.yaml中ClusterRoleBinding以及ServiceAccount中的namespace定义，改为monitoring
#为了让Prometheus Operator能监听和管理K8S资源，因此bundle.yaml同时创建了单独的ServiceAccount及相关授权
kubectl apply -f bundle.yaml -n monitoring

kubectl -n monitoring get pods
#NAME                                   READY     STATUS    RESTARTS   AGE
#prometheus-operator-6db8dbb7dd-2hz55   1/1       Running   0          19s

kubectl get crd -n monitoring
#NAME                                    CREATED AT
#alertmanagers.monitoring.coreos.com     2019-05-26T11:21:11Z
#prometheuses.monitoring.coreos.com      2019-05-26T11:21:11Z
#prometheusrules.monitoring.coreos.com   2019-05-26T11:21:12Z
#servicemonitors.monitoring.coreos.com   2019-05-26T11:21:12Z

#当部署Prometheus Operator后，对部署Prometheus Server来说就变成了声明Prometheus实例：
cat > prometheus.yaml <<'EOF'
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: inst                #Prometheus实例名称
  namespace: monitoring     #本实例所属名称空间
spec:
  serviceAccountName: prometheus
  resources:
    requests:
      memory: 400Mi
EOF
kubectl apply -f prometheus.yaml

kubectl -n monitoring get statefulsets  #此时可看到Prometheus Operator自动通过Statefulset创建的Prometheus实例
#NAME              DESIRED   CURRENT   AGE
#prometheus-inst   1         1         1m

#通过port-forward访问Prometheus实例:
kubectl -n monitoring port-forward statefulsets/prometheus-inst 9090:9090   # curl -L http://localhost:9090
```
#### ServiceMonitor
```bash
#首先在集群中部署示例应用：-----------------------------------------------

kind: Service
apiVersion: v1
metadata:
  name: example-app               #Service名称为：example-app 
  labels:
    app: example-app
spec:
  selector:
    app: example-app              #关联的Pod标签
  ports:
  - name: web                     #端口名
    port: 8080
---
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: example-app               #Deployment名称
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: example-app
    spec:
      containers:
      - name: example-app         #容器名称为：example-app 
        image: fabxc/instrumented_app
        ports:
        - name: web               #端口名
          containerPort: 8080

#通过Deployment创建3个Pod示例并通过Service暴露应用访问信息:
kubectl get pods
#NAME                        READY     STATUS    RESTARTS   AGE
#example-app-94c8bc8-l27vx   2/2       Running   0          1m
#example-app-94c8bc8-lcsrm   2/2       Running   0          1m
#example-app-94c8bc8-n6wp5   2/2       Running   0          1m

#在本地通过port-forward访问任意Pod实例
$ kubectl port-forward deployments/example-app 8080:8080
#访问本地的http://localhost:8080/metrics实例应用程序会返回以下样本数据：
  # TYPE codelab_api_http_requests_in_progress gauge
  codelab_api_http_requests_in_progress 3
  # HELP codelab_api_request_duration_seconds A histogram of the API HTTP request durations in seconds.
  # TYPE codelab_api_request_duration_seconds histogram
  codelab_api_request_duration_seconds_bucket{method="GET",path="/api/bar",status="200",le="0.0001"} 0

#-------------------------------------------------------------------------- ServiceMonitor

#为了让Prometheus能采集部署在Kubernetes下应用的监控数据
#原生的Prometheus配置方式要在配置文件中定义单独的Job并在其中使用kubernetes_sd定义整个服务发现过程
#然而在Prometheus Operator中可直接声明一个ServiceMonitor对象来创建对应的配置信息传递给Prometheus：

apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: example-app
  namespace: monitoring
  labels:
    team: frontend            #这里的ServiceMonitor的标签比较重要，Promethues资源通过此标签来关联ServiceMonitor
spec:
  namespaceSelector:          #指定需要抓取的对象所属命名空间
    matchNames:               #若希望ServiceMonitor可关联任意命名空间下的标签则直接替换matchNames为"any: true"
    - default 
  selector:
    matchLabels:              #指定要抓取的目标Pod的标签
      app: example-app
  endpoints:                  #在endpoints中指定容器的port名称为web的端口，抓取指标时将通过此"web"端口进行GET请求
  - port: web                 #Name of the service port this endpoint refers to.
    scheme: HTTP
    path: /metrics
    interval: 30s
    tlsConfig:
      insecureSkipVerify: true
    bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token 

#默认ServiceMonitor和监控对象必须在相同Namespace。本例由于Prometheus部署在Monitoring命名空间
#因此为了能关联default命名空间下的对象，需要用namespaceSelector定义让其可以跨命名空间关联ServiceMonitor资源
#保存以上内容到example-app-service-monitor.yaml文件中并创建：
kubectl create -f example-app-service-monitor.yaml

#-------------------------------------------------------------------------- BasicAuth

#如果监控的Target对象启用了BasicAuth认证，那么在定义ServiceMonitor对象时可在endpoints配置中定义basicAuth：
  ......
  endpoints:
  - basicAuth:
      password:
        name: basic-auth      #名为basic-auth的Secret对象
        key: password         #该对象的Key
      username:
        name: basic-auth      #名为basic-auth的Secret对象
        key: user             #该对象的Key
    port: web
  ......

#其中的basicAuth内关联了名为basic-auth的Secret对象，用户需要手动将认证信息保存到Secret中:
apiVersion: v1
kind: Secret
metadata:
  name: basic-auth
data:
  user: YWRtaW4=              # base64编码后的用户名
  password: dG9vcg==          # base64编码后的密码
type: Opaque
```
### Prometheus server
```bash
#Prometheus Operator与ServiceMonitor部署完成后，下一步需关联ServiceMonitor与Promethues:
#ServiceMonitor与Prometheus的关联关系使用"serviceMonitorSelector"定义
#为了能让Prometheus关联到ServiceMonitor，需要在Pormtheus资源的定义中使用serviceMonitorSelector：
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: inst
  namespace: monitoring
spec:
  serviceAccountName: prometheus
  serviceMonitorSelector:     #通过标签选择当前Prometheus对象需要监控的ServiceMonitor对象
    matchLabels:              #该标签对应ServiceMonitor资源
      team: frontend          #
  resources:
    requests:
      memory: 400Mi

kubectl -n monitoring apply -f prometheus-inst.yaml

#此时查看Prometheus配置会发现配置文件中自动包含了名为monitoring/example-app/0的Job配置：
global:
  ......(略)
  external_labels:
    prometheus: monitoring/inst
    prometheus_replica: prometheus-inst-0

.........

scrape_configs:
- job_name: monitoring/example-app/0    #下面是使用ServiceMonitor声明监控对象后并且prometheus与其关联后生成的
  ......(略)
  kubernetes_sd_configs:
  - role: endpoints
    namespaces:
      names:
      - default
  relabel_configs:
  - source_labels: [__meta_kubernetes_service_label_app]
    separator: ;
    regex: example-app
    replacement: $1
    action: keep
  - source_labels: [__meta_kubernetes_endpoint_port_name]
    separator: ;
    regex: web
    replacement: $1
    action: keep
  - source_labels: [__meta_kubernetes_endpoint_address_target_kind, __meta_kubernetes_endpoint_address_target_name]
    separator: ;
    regex: Node;(.*)
    target_label: node
    replacement: ${1}
    action: replace
  - source_labels: [__meta_kubernetes_endpoint_address_target_kind, __meta_kubernetes_endpoint_address_target_name]
    separator: ;
    regex: Pod;(.*)
    target_label: pod
    replacement: ${1}
    action: replace
  - source_labels: [__meta_kubernetes_namespace]
    separator: ;
    regex: (.*)
    target_label: namespace
    replacement: $1
    action: replace
  - source_labels: [__meta_kubernetes_service_name]
    separator: ;
    regex: (.*)
    target_label: service
    replacement: $1
    action: replace
  - source_labels: [__meta_kubernetes_pod_name]
    separator: ;
    regex: (.*)
    target_label: pod
    replacement: $1
    action: replace
  - source_labels: [__meta_kubernetes_service_name]
    separator: ;
    regex: (.*)
    target_label: job
    replacement: ${1}
    action: replace
  - separator: ;
    regex: (.*)
    target_label: endpoint
    replacement: web
    action: replace

#如果细心可能会发现虽然Job配置有了但Target中并没包含任何的监控对象，查看Prometheus的Pod日志如下：
level=error ts=2018-12-15T12:52:48.452108433Z caller=main.go:240 component=k8s_client_runtime 
err="github.com/prometheus/prometheus/discovery/kubernetes/kubernetes.go:300: Failed to list *v1.Endpoints:
  endpoints is forbidden:
  User \"system:serviceaccount:monitoring:default\" cannot list endpoints in the namespace \"default\""
#由于默认创建的Prometheus实例使用monitoring命名空间下的default账号，该账号并没有权限够获取default空间下的任何资源信息
#因此需在Monitoring命名空间创建名为Prometheus的ServiceAccount，并为该账号赋予相应的集群访问权限:

apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRole
metadata:
  name: prometheus
rules:
- apiGroups: [""]
  resources:
  - nodes
  - services
  - endpoints
  - pods
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources:
  - configmaps
  verbs: ["get"]
- nonResourceURLs: ["/metrics"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: monitoring

#完成ServiceAccount创建后修改prometheus实例的YAML，添加ServiceAccount：
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: inst
  namespace: monitoring
spec:
  serviceAccountName: prometheus    #使其拥有相应RBAC权限
  serviceMonitorSelector:
    matchLabels:
      team: frontend
  resources:
    requests:
      memory: 400Mi

#等待Prometheus Operator完成配置变更后，此时就能看到当前Prometheus已经能正常的采集实例应用的相关数据了
```
#### 使用 Operator 管理监控配置
```yaml
#对Prometheus而言，原生管理方式要手动创建Prometheus告警文件并通过在Prometheus配置中声明式加载
#在Prometheus Operator中，告警规则变成了通过Kubernetes API声明式创建的一个资源：
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  labels:
    prometheus: example
    role: alert-rules
  name: prometheus-example-rules
spec:
  groups:
  - name: ./example.rules
    rules:
    - alert: ExampleAlert         #告警标题
      expr: vector(1)             #This is PromQL.....

kubectl -n monitoring create -f example-rule.yaml

#告警规则创建成功后，通过在Prometheus中使用ruleSelector通过选择需要关联的PrometheusRule即可：
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: inst
  namespace: monitoring
spec:
  serviceAccountName: prometheus
  serviceMonitorSelector:         #关联的serviceMonitor
    matchLabels:
      team: frontend
  ruleSelector:                   #关联的PrometheusRule
    matchLabels:
      role: alert-rules
      prometheus: example
  resources:
    requests:
      memory: 400Mi

#Prometheus重新加载配置后，从UI中可以查看到通过PrometheusRule自动创建的告警规则配置：
#如果查看Alerts页面，会看到告警已处于触发状态
```
#### Alertmanager
```bash
#目前为止已通过Prometheus Operator的CRD管理了Promtheus实例，监控及告警规则等资源
#通过Prometheus Operator将原本手动管理的工作全部变成声明式的管理模式，大大简化了K8S下Prometheus运维管理的复杂度
#接下来将继续使用Promtheus Operator定义和管理Alertmanager相关内容
#为了通过Prometheus Operator管理Alertmanager实例，可通过CRD资源的Alertmanager进行
apiVersion: monitoring.coreos.com/v1
kind: Alertmanager
metadata:
  name: inst
  namespace: monitoring
spec:
  replicas: 3 #通过replicas可以控制Alertmanager的实例数
#当replicas大于1时，Prometheus Operator会自动通过集群的方式创建Alertmanager
$ kubectl -n monitoring create -f alertmanager-inst.yaml

#查看Pod的情况如下所示，我们会发现Alertmanager的Pod实例一直处于ContainerCreating的状态:
$ kubectl -n monitoring get pods
NAME                                   READY     STATUS              RESTARTS   AGE
alertmanager-inst-0                    0/2       ContainerCreating   0          32s

#通过kubectl describe命令查看该Alertmanager的Pod实例状态，可看到类似以下内容的告警：
MountVolume.SetUp failed for volume "config-volume" : secrets "alertmanager-inst" not found
#这是由于通过Statefulset方式创建的Alertmanager实例在默认情况下会通过 \
#alertmanager-{ALERTMANAGER_NAME}的命名规则去查找Secret配置并以文件方式挂载
#将Secret的内容作为配置文件挂载到Alertmanager实例当中。因此这里还需要为Alertmanager创建相应的配置内容
#如下所示，是Alertmanager的配置文件：
global:
  resolve_timeout: 5m
route:
  group_by: ['job']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'webhook'
receivers:
- name: 'webhook'
  webhook_configs:
  - url: 'http://alertmanagerwh:30500/'
#将以上内容保存为文件alertmanager.yaml，并且通过以下命令创建名为alrtmanager-inst的Secret资源：
$ kubectl -n monitoring create secret generic alertmanager-inst --from-file=alertmanager.yaml

#在Secret创建成功后，查看当前Alertmanager Pod实例状态：
$ kubectl -n monitoring get pods
NAME                                   READY     STATUS    RESTARTS   AGE
alertmanager-inst-0                    2/2       Running   0          5m
alertmanager-inst-1                    2/2       Running   0          52s
alertmanager-inst-2                    2/2       Running   0          37s

$ kubectl -n monitoring port-forward statefulsets/alertmanager-inst 9093:9093
#访问http://localhost:9093/#/status并查看当前集群状态：

#接下来只需要修改的Prometheus资源定义，通过alerting指定使用的Alertmanager资源即可：
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: inst
  namespace: monitoring
spec:
  serviceAccountName: prometheus
  serviceMonitorSelector:
    matchLabels:
      team: frontend
  ruleSelector:
    matchLabels:
      role: alert-rules
      prometheus: example
  alerting:
    alertmanagers:
    - name: alertmanager-example      #这个name是alrtmanager的service的名字
      namespace: monitoring
      port: web
  resources:
    requests:
      memory: 400Mi

#等待Prometheus重新加载后，可以看到Prometheus Operator在配置文件中添加了以下配置：
  alertmanagers:
  - kubernetes_sd_configs:            #通过服务发现规则将Prometheus与Alertmanager进行了自动关联
    - role: endpoints
      namespaces:
        names:
        - monitoring
    scheme: http
    path_prefix: /
    timeout: 10s
    relabel_configs:
    - source_labels: [__meta_kubernetes_service_name]
      separator: ;
      regex: alertmanager-example
      replacement: $1
      action: keep
    - source_labels: [__meta_kubernetes_endpoint_port_name]
      separator: ;
      regex: web
      replacement: $1
      action: keep
```
#### 在 Prometheus Operator 中使用自定义配置
```yaml
#某些特殊情况下对用户而言可能希望手动管理Prometheus配置文件
#为什么? 实际上Prometheus Operator对于Job的配置只适用于在K8S中部署和管理的应用程序
#如果希望使用Prometheus监控其他资源，如AWS或其他平台中的基础设施或应用，这并不在Prometheus Operator能力范围内
#为了能在Prometheus Operator创建的Prometheus实例中使用自定义配置，需要创建1个不包含任何与配置文件内容相关的plmxs实例

apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: inst-cc
  namespace: monitoring
spec:
  serviceAccountName: prometheus    #这里不使用serviceMonitorSelector对serviceMonitor进行管关联
  resources:
    requests:
      memory: 400Mi

kubectl -n monitoring create -f prometheus-inst-cc.yaml

#查看新建Prometheus的Pod实例YAML定义，可以看到Pod中会包含一个volume配置：
......
volumes:
  - name: config
    secret:                         #配置文件实际上保存在名为 prometheus-<name-of-prometheus-object> 的Secret中
      defaultMode: 420
      secretName: prometheus-inst-cc
......

#当创建的Prometheus中关联ServiceMonitor这类会影响Prometheus的配置文件内容的定义时，Promethues Operator就会自动管理
#但是如果Prometheus中不包含任何与配置相关的定义，那么Secret的管理权限就落到了用户自己手中!
#通过修改prometheus-inst-cc的内容，从而让用户使用自定义的Prometheus配置文件
#作为示例，创建一个prometheus.yaml文件并添加以下内容：

global:
  scrape_interval: 10s
  scrape_timeout: 10s
  evaluation_interval: 10s

#生成以上文件内容的base64编码：
cat prometheus.yaml | base64
#Z2xvYmFsOgogIHNjcmFwZV9pbnRlcnZhbDogMTBzCiAgc2NyYXBlX3RpbWVvdXQ6IDEwc==

#修改名为prometheus-inst-cc的Secret内容：
kubectl -n monitoring edit secret prometheus-inst-cc
......
data:
  prometheus.yaml: "Z2xvYmFsOgogIHNjcmFwZV9pbnRlcnZhbDogMTBzCiAgc2NyYXBlX3RpbWVvdXQ6IDEwc=="
......

#通过port-forward在本地访问新建的Prometheus实例，观察配置文件变化：
kubectl -n monitoring port-forward statefulsets/prometheus-inst-cc 9091:9090
```