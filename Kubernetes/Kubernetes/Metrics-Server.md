`https://github.com/kubernetes-incubator/metrics-server`
#### Metric Server
```bash
#需要先下载镜像到私有仓库：registry.cn-beijing.aliyuncs.com/minminmsn/metrics-server:v0.3.1

git clone https://github.com/kubernetes-incubator/metrics-server.git  
cd metrics-server/deploy/1.8+/
[root@k8s-master 1.8+]# ll
total 28
-rw-r--r-- 1 root root 384 Apr 23 19:07 aggregated-metrics-reader.yaml
-rw-r--r-- 1 root root 308 Apr 23 19:07 auth-delegator.yaml
-rw-r--r-- 1 root root 329 Apr 23 19:07 auth-reader.yaml
-rw-r--r-- 1 root root 298 Apr 23 19:07 metrics-apiservice.yaml
-rw-r--r-- 1 root root 815 Apr 23 19:07 metrics-server-deployment.yaml
-rw-r--r-- 1 root root 291 Apr 23 19:07 metrics-server-service.yaml
-rw-r--r-- 1 root root 502 Apr 23 19:07 resource-reader.yaml

#修改 vim metrics-server-deployment.yaml
.............
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  .................
spec:
  .................
      containers:
      - name: metrics-server
        image: registry.cn-beijing.aliyuncs.com/minminmsn/metrics-server:v0.3.1     #改为国内源
        imagePullPolicy: IfNotPresent
        command:
          - /metrics-server                              #
          - --kubelet-preferred-address-types=InternalIP #确定用于连接到特定节点IP时使用的目标节点地址的优先级
          - --kubelet-insecure-tls                       #不验证Kubelet提供的服务证书的CA
          #- --kubelet-preferred-address-types=InternalIP,Hostname,InternalDNS,ExternalDNS,ExternalIP
          #- --source=kubernetes.summary_api:https://kubernetes.default?kubeletHttps=true&kubeletPort=10250&insecure=true&useServiceAccount=true
  .................

[root@k8s-master 1.8+]# kubectl apply -f .
clusterrole.rbac.authorization.k8s.io/system:aggregated-metrics-reader created
clusterrolebinding.rbac.authorization.k8s.io/metrics-server:system:auth-delegator created
rolebinding.rbac.authorization.k8s.io/metrics-server-auth-reader created
apiservice.apiregistration.k8s.io/v1beta1.metrics.k8s.io created
serviceaccount/metrics-server created
deployment.extensions/metrics-server created
service/metrics-server created
clusterrole.rbac.authorization.k8s.io/system:metrics-server created
clusterrolebinding.rbac.authorization.k8s.io/system:metrics-server created

[root@k8s-master 1.8+]# kubectl get pod -n kube-system
NAME                                 READY   STATUS    RESTARTS   AGE
calico-node-b78m4                    1/1     Running   0          176m
calico-node-r5mlj                    1/1     Running   0          3h6m
calico-node-z5tdh                    1/1     Running   0          176m
coredns-fb8b8dccf-6mgks              1/1     Running   0          3h21m
coredns-fb8b8dccf-cbtlx              1/1     Running   0          3h21m
etcd-k8s-master                      1/1     Running   0          3h20m
kube-apiserver-k8s-master            1/1     Running   0          3h20m
kube-controller-manager-k8s-master   1/1     Running   0          3h20m
kube-proxy-c9xd2                     1/1     Running   0          3h21m
kube-proxy-fp2r2                     1/1     Running   0          176m
kube-proxy-lrsw7                     1/1     Running   0          176m
kube-scheduler-k8s-master            1/1     Running   0          3h20m
metrics-server-7579f696d8-pgcc4      1/1     Running   0          99s

[root@k8s-master 1.8+]# kubectl top pod  -n kube-system
NAME                              CPU(cores)   MEMORY(bytes)   
coredns-d5947d4b-6xd2f            3m           16Mi            
coredns-d5947d4b-mctxg            3m           18Mi            
etcd-node129                      14m          52Mi            
kube-apiserver-node129            21m          286Mi           
kube-controller-manager-node129   8m           63Mi            
kube-flannel-ds-amd64-22l25       1m           15Mi            
kube-flannel-ds-amd64-gl5xb       1m           16Mi            
kube-proxy-m559m                  1m           23Mi            
kube-proxy-pm2j4                  2m           24Mi            
kube-scheduler-node129            1m           20Mi            
metrics-server-6f489d7445-vhdtv   1m           16Mi     

# HPA Demo:
# kubectl autoscale deploy Example --min=1 --max=10 --cpu-percent=80

# kubectl api-versions 只有出现  metrics.k8s.io/v1beta1 才说明部署成功。Metrics API URI 为 /apis/metrics.k8s.io/
```