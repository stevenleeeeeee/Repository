#### Notice
```bash
#Docs ref:
https://blog.csdn.net/zhonglinzhang/article/details/86236925
https://github.com/kubernetes-incubator/custom-metrics-apiserver
https://yasongxu.gitbook.io/container-monitor/jian-jie/intro
https://blog.csdn.net/u011230692/article/details/86441341           [Suggest]   kube-state-metrics
https://segmentfault.com/a/1190000017875621?utm_source=tag-newest   [Suggest]   Doc
https://www.cnblogs.com/dingbin/p/9831481.html                      [Suggest]   prometheus

#Custom Metrics Tools:
https://github.com/kubernetes/kube-state-metrics                    [Suggest]   kube-state-metrics
https://github.com/DirectXMan12/k8s-prometheus-adapter              [Suggest]   k8s-prometheus-adapter
https://github.com/stefanprodan/k8s-prom-hpa

#k8s-prometheus-adapter Docs:
https://github.com/DirectXMan12/k8s-prometheus-adapter/blob/master/docs/config.md
https://github.com/DirectXMan12/k8s-prometheus-adapter/blob/master/docs/config-walkthrough.md

#kube-state-metrics Docs:
https://blog.csdn.net/u011230692/article/details/86441341

# [node_exporter] --> [prometheus] --> [kube-state-metrics] --> [k8s-prometheus-adpater] --> [kubernetes]

#kube-state-metrics: 将可以用PromQL查询到的指标数据转成Custerom Metrics API接口格式的数据，但它不能聚合进apiserver中
#k8s-prometheus-adpater：聚合进Apiserver，即一种custom-metrics-apiserver实现，其将PromQL转为APIServer的指标接口
#prometheus: 收集apiserver，scheduler，controller-manager，kubelet、...的度量指标
#node_exporter: 收集集群中各节点数据
#alertmanager: 实现监控报警
#grafana: 实现数据可视化

#使用prometheus作为第三方metric收集器
#使用k8s-prometheus-adapter为HPA控制器提供自定义指标的client适配 (转换) 自定义APIServer通过aggregator聚合到APIserver
#自定义度量API和聚合层使得像Promethous这样的监控系统向HPA控制器公开特定于应用程序的度量成为可能

#k8s-prometheus-adapter以指定时间间隔从prometheus收集可用metrics，只考虑以下形式的指标：
# "container" metrics (cAdvisor container metrics): 
#       以container_开头的series，以及非空namespace和pod_name标签的度量
# "namespaced" metrics (metrics describing namespaced Kubernetes objects): 
#       带有非空namespace标签的series (不以container_开头)
```
#### Deploy kube-state-metrics & k8s-prometheus-adpater
```bash
#部署prometheus、node-exporter.....(略)

#部署清单获取：
#从kubernetes源码树的addons获取 prometheus相关组件的资源清单文件：prometheus、node-exporter、kube-state-metrics
#从DirectXMan12项目获取 组件k8s-prometheus-adpater的清单文件

kubectl create namespace custom-metrics 

#部署kube-state-metrics:
#注：这里使用google自带的，也可使用第三方资源清单：https://github.com/kubernetes/kube-state-metrics
U=https://github.com/kubernetes/kubernetes/blob/master/cluster/addons/prometheus/kube-state-metrics-
for i in ${U}rbac.yaml ${U}service.yaml ${U}deployment.yaml
do
  kubectl -f $i #这里统一修改后部署在custom-metrics命名空间
done

#部署k8s-prometheus-adpater:
#它是个apiserver，提供的APIServer服务名为 custom-metrics-apiserver、API组： custom.metrics.k8s.io
#它是自定义指标API：custom.metrics.k8s.io
#基于Kubernets的CA为k8s-prometheus-adapter创建自签证书
cd /etc/kubernetes/pki && (umask 077;openssl genrsa -out serving.key 1024)
openssl req -new -key serving.key -out serving.csr -subj "/CN=serving"
openssl x509 -req -in  serving.csr -CA ./ca.crt -CAkey ./ca.key -CAcreateserial -out serving.crt -days 3650

#将生成的证书导入到Secret资源中，k8s-prometheus-adapter读取名为"cm-adapter-serving-certs"的secret资源
kubectl create secret generic cm-adapter-serving-certs -n custom-metrics \
    --from-file=serving.crt=./serving.crt --from-file=serving.key=./serving.key

k8s-prometheus-adapter：https://github.com/DirectXMan12/k8s-prometheus-adapter
#清单：
#custom-metrics-apiserver-auth-delegator-cluster-role-binding.yaml
#custom-metrics-apiserver-auth-reader-role-binding.yaml
#custom-metrics-apiserver-deployment.yaml
#custom-metrics-apiserver-resource-reader-cluster-role-binding.yaml
#custom-metrics-apiserver-service-account.yaml
#custom-metrics-apiserver-service.yaml
#custom-metrics-apiservice.yaml
#custom-metrics-cluster-role.yaml
#custom-metrics-config-map.yaml
#custom-metrics-resource-reader-cluster-role.yaml
#hpa-custom-metrics-cluster-role-binding.yaml

#修改k8s-prometheus-adapter配置：
# custom-metrics-apiserver-deployment.yaml 修改/添加如下参数：
# --tls-cert-file=/var/run/serving-cert/serving.crt
# --tls-private-key-file=/var/run/serving-cert/serving.key
# --requestheader-client-ca-file=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

#部署Prometheus自定义Api适配器，注意要修改一下清单的命名空间，部署在custom-metrics ( 需事先部署prometheus )
kubectl create -f https://github.com/DirectXMan12/k8s-prometheus-adapter/tree/master/deploy/manifests/*

#获取指定命名空间中pod的自定义指标，如http_request请求数
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/<namespace>/pods/<name>/http_requests" | jq .

#验证：
kubectl api-versions | grep custom.metrics.k8s.io
kubectl get pod -n custom-metrics
#NAME                                        READY   STATUS    RESTARTS   AGE    NODE         NOMINATED NODE
#custom-metrics-apiserver-746485c45d-9dnqn   1/1     Running   0          116s   k8s-node01   <none>
#kube-state-metrics-667fb54645-xj8gr         1/1     Running   0          63m    k8s-master   <none>
#prometheus-node-exporter-d4wg7              1/1     Running   0          175m   k8s-master   <none>
#prometheus-node-exporter-tqczz              1/1     Running   0          175m   k8s-node01   <none>
#prometheus-node-exporter-wcrh6              1/1     Running   0          175m   k8s-node02   <none>
#prometheus-server-5fcbdbcc6f-nt4wj          1/1     Running   0          89m   

#k8s-prometheus-adapter 将PromQL转换为API的说明文档: /etc/adapter/config.yaml
https://github.com/DirectXMan12/k8s-prometheus-adapter/blob/master/docs/config-walkthrough.md
https://github.com/DirectXMan12/k8s-prometheus-adapter/blob/master/docs/config.md

#prometheus中的metrics在custom-metrics-API中会转换如下:
# metric名称和类型已经被确定:
#    对属于容器的metrics，将去除container_前缀
#    如果metric有_total后缀，它将被标记为 counter metric 并去掉后缀
#    如果metric有_seconds_total后缀，被标记为 seconds counter metric 并去掉后缀
#    如果metric没有以上后缀，被标记为 gauge metric，meitric名称将保持原样
# 关联资源与metric:
#    容器metric和pod关联
#    对于非容器metric，series中的每个label将被考虑
#    如果该标签表示的是一个可用resource(没有group)，metric可以和该resource关联。一个metric可以和多个resource相关联
```
#### 基于自定义指标的自动扩容
```bash
#创建podinfo nodeport服务并在default命名空间中部署：
kubectl create -f ./podinfo/{podinfo-svc.yaml,podinfo-dep.yaml}

#podinfo应用暴露了一个自定义的度量：http_requests_total （适配器删除_total后缀标记度量作为一个计数器度量）

#查看custom.metrics.k8s.io暴露的容器指标：... --raw "/apis/custom.metrics.k8s.io/v1beta1 | jq . | grep 'pods'
#从自定义度量API获取每秒的总请求数: ( kubectl get apiservice v1beta1.custom.metrics.k8s.io -o yaml  )
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/default/pods/*/http_requests" | jq .
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
      "value": "901m"       # m 代表 milli-units ，例如 901m 意味着 milli-requests 。
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
```
#### custom metrics for HPAv2
```yaml
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
      metricName: http_requests     如果请求数超过每秒10当将扩大podinfo数量：
      targetAverageValue: 10

# kubectl get hpa
# NAME      REFERENCE            TARGETS     MINPODS   MAXPODS   REPLICAS   AGE
# podinfo   Deployment/podinfo   899m / 10   2         10        2          1m

# 自动定标器不使用峰值立即做出反应。默认情况下指标30/s同步1次
```
#### k8s-prometheus-adapter ---> /etc/adapter/config.yaml
```yaml
# https://github.com/DirectXMan12/k8s-prometheus-adapter/blob/master/docs/sample-config.yaml

rules:
# this rule matches cumulative cAdvisor metrics measured in seconds
- seriesQuery: '{__name__=~"^container_.*",container_name!="POD",namespace!="",pod_name!=""}'
  resources:
    # skip specifying generic resource<->label mappings, and just
    # attach only pod and namespace resources by mapping label names to group-resources
    overrides:
      namespace: {resource: "namespace"},
      pod_name: {resource: "pod"},
  # specify that the `container_` and `_seconds_total` suffixes should be removed.
  # this also introduces an implicit filter on metric family names
  name:
    # we use the value of the capture group implicitly as the API name
    # we could also explicitly write `as: "$1"`
    matches: "^container_(.*)_seconds_total$"
  # specify how to construct a query to fetch samples for a given series
  # This is a Go template where the `.Series` and `.LabelMatchers` string values
  # are available, and the delimiters are `<<` and `>>` to avoid conflicts with
  # the prometheus query language
  metricsQuery: "sum(rate(<<.Series>>{<<.LabelMatchers>>,container_name!="POD"}[2m])) by (<<.GroupBy>>)"
```