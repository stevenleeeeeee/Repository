```
参考：
https://github.com/kubernetes/dashboard
https://blog.csdn.net/Excairun/article/details/88989706
https://github.com/kubernetes/dashboard/wiki/Integrations

需准备的镜像：
  k8s.gcr.io/kubernetes-dashboard-amd64:v1.10.1           
  k8s.gcr.io/heapster-amd64:v1.5.4                        
  k8s.gcr.io/heapster-influxdb-amd64:v1.5.2               
  k8s.gcr.io/heapster-grafana-amd64:v5.0.4
```

#### Download Dashboard Images
```bash
#!/bin/bash
DASHDOARD_VERSION=v1.10.1
HEAPSTER_VERSION=v1.5.4
GRAFANA_VERSION=v5.0.4
INFLUXDB_VERSION=v1.5.2
username=registry.cn-hangzhou.aliyuncs.com/google_containers

images=(
    kubernetes-dashboard-amd64:${DASHDOARD_VERSION}
    heapster-grafana-amd64:${GRAFANA_VERSION}
    heapster-amd64:${HEAPSTER_VERSION}
    heapster-influxdb-amd64:${INFLUXDB_VERSION}
)

for image in ${images[@]}
do
    docker pull ${username}/${image}
    docker tag  ${username}/${image} k8s.gcr.io/${image}
    docker rmi  ${username}/${image}
done

#注：heapster-amd有问题，使用下面的地址：
registry.cn-hangzhou.aliyuncs.com/magina-k8s/heapster-amd64:v1.5.1
registry.cn-hangzhou.aliyuncs.com/google_containers/heapster-influxdb-amd64:v1.3.3
```
```bash
#官方文件中只包含了kubernetes-dashboard.yaml，且kubernetes在1.6以后启用了RBAC，直接使用官方版会出现访问权限不足的报错

#这里使用另一个作者修改过的yaml文件:
git clone https://github.com/chopperchan/k8s-dashboard.git
cd k8s-dashboard/

#修改:
cat > heapster-rbac.yaml <<'EOF'
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: kubernetes-dashboard-admian
  labels:
    k8s-app: kubernetes-dashboard
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: heapster
  namespace: kube-system
EOF

vim heapster.yaml    #https://github.com/kubernetes/dashboard/wiki/Integrations
......
 command:
 - /heapster
 - --source=kubernetes:https://10.96.0.1:443    #这里地址为：kubectl get svc 看到的kubernetes地址和端口
 - --sink=influxdb:http://monitoring-influxdb.kube-system.svc:8086  #后端存储是个问题
......

kubectl apply -f .
# clusterrolebinding.rbac.authorization.k8s.io/heapster created
# serviceaccount/heapster created
# deployment.extensions/heapster created
# service/heapster created
# serviceaccount/kubernetes-dashboard-admin created
# clusterrolebinding.rbac.authorization.k8s.io/kubernetes-dashboard-admin created
# secret/kubernetes-dashboard-certs created
# serviceaccount/kubernetes-dashboard created
# role.rbac.authorization.k8s.io/kubernetes-dashboard-minimal created
# rolebinding.rbac.authorization.k8s.io/kubernetes-dashboard-minimal created
# deployment.apps/kubernetes-dashboard created
# service/kubernetes-dashboard-external created

kubectl get svc -n kube-system
#NAME                            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                  AGE
#heapster                        ClusterIP   10.110.35.204   <none>        80/TCP                   9m32s
#kube-dns                        ClusterIP   10.96.0.10      <none>        53/UDP,53/TCP,9153/TCP   7d2h
#kubernetes-dashboard-external   NodePort    10.108.93.78    <none>        9090:31666/TCP           9m31s
#metrics-server                  ClusterIP   10.109.6.115    <none>        443/TCP                  31m
```
#### 将证书导入浏览器 ( 非kubeadm环境下使用 )
```bash
#!/bin/bash
grep 'client-certificate-data' ~/.kube/config | head -n 1 | awk '{print $2}' | base64 -d >> kubecfg.crt
grep 'client-key-data' ~/.kube/config | head -n 1 | awk '{print $2}' | base64 -d >> kubecfg.key
openssl pkcs12 -export -clcerts -inkey kubecfg.key -in kubecfg.crt -out kubecfg.p12 -name "kubernetes-client"

echo "Genereated kubecfg certificates under $(pwd): "
ls -ltra kubecfg*
echo "Please install the kubecfg.p12 certificate in your browser, and then restart browser."

最后导入Token
```
#### dashboard Token settings
```bash
kubectl -n kube-systemcreate serviceaccount dashboard

kubectl create clusterrolebinding dasboard \
  --clusterrole=cluster-admin \
  --serviceaccount=kube-system:dashboard-admin

kubectl -n kube-system describe secrets dashboard-token-xl9p2 	#不要用get....这样get得到的token不是原始的
```