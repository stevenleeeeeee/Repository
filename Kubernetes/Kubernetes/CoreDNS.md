```txt
Service: 		10.0.0.0/24
cluster-dns：	10.0.0.2
Domain:		cluster.local
```
```txt
Coredns与 kubernetes版本匹配：
https://github.com/coredns/deployment/blob/master/kubernetes/CoreDNS-k8s_version.md
```
#### CoreDNS
```bash
wget https://github.com/coredns/deployment/archive/master.zip
unzip master.zip
cd deployment-master/kubernetes
ls -l
total 44
-rw-r--r-- 1 root root 3378 May  1 22:50 CoreDNS-k8s_version.m
-rw-r--r-- 1 root root 3771 May  1 22:50 coredns.yaml.sed
drwxr-xr-x 3 root root   63 May  1 22:50 corefile-tool
-rwxr-xr-x 1 root root 3791 May  1 22:50 deploy.sh
-rw-r--r-- 1 root root 4985 May  1 22:50 FAQs.md
drwxr-xr-x 3 root root  110 May  1 22:50 migration
-rw-r--r-- 1 root root 2706 May  1 22:50 README.md
-rwxr-xr-x 1 root root 1337 May  1 22:50 rollback.sh
-rw-r--r-- 1 root root 7159 May  1 22:50 Scaling_CoreDNS.md
-rw-r--r-- 1 root root 7911 May  1 22:50 Upgrading_CoreDNS.md

#deploy.sh:
#是用于在已经运行kube-dns的集群中生成运行CoreDNS部署文件"manifest"的工具
#使用"coredns.yaml.sed"作为模板，创建ConfigMap和CoreDNS的deployment
#然后更新集群中已有的kube-dns服务的selector使用CoreDNS的deployment
#重用已有的服务不会在服务的请求中发生冲突

usage: ./deploy.sh [ -r REVERSE-CIDR ] [ -i DNS-IP ] [ -d CLUSTER-DOMAIN ] [ -t YAML-TEMPLATE ]

    -r : Define a reverse zone for the given CIDR. You may specifcy this option more
         than once to add multiple reverse zones. If no reverse CIDRs are defined,
         then the default is to handle all reverse zones (i.e. in-addr.arpa and ip6.arpa)
    -i : Specify the cluster DNS IP address. If not specificed, the IP address of
         the existing "kube-dns" service is used, if present.
    -s : Skips the translation of kube-dns configmap to the corresponding CoreDNS Corefile configuration.

#删除已经存在的DNS服务
kubectl get pods -o wide -n=kube-system
kubectl delete -n kube-system deployment ****-dns


#生成声明文件：
./deploy.sh -i 10.0.0.2 -d cluster.local -t coredns.yaml.sed -s > coredns.yaml
#修改生成的YAML文件将镜像改为为国内源：registry.cn-hangzhou.aliyuncs.com/google_containers/

#部署
kubectl apply -f coredns.yaml
serviceaccount/coredns created
clusterrole.rbac.authorization.k8s.io/system:coredns created
clusterrolebinding.rbac.authorization.k8s.io/system:coredns created
configmap/coredns created
deployment.apps/coredns created
service/kube-dns created

#验证服务
kubectl get svc -o wide -n=kube-system

#查看详细信息
kubectl get pods -o wide -n=kube-system
NAME               READY STATUS    RESTARTS AGE  IP            NODE           NOMINATED NODE  READINESS GATES
coredns-b97f7df6d  1/1   Running   0        15h  10.254.100.3  172.20.101.166 <none>          <none>
coredns-b97f7df6d  1/1   Running   0        15h  10.254.87.3   172.20.101.160 <none>         

#修改Master节点和所有node节点的systemd管理下的kubelet配置文件：
以下配置需要与Corefile配置文件中的值对应:
CLUSTER_CIDR：  10.254.0.0/16
CLUSTER_DNS：   10.254.0.10

#kubelet添加内容如下：
--cluster-dns=10.3.0.10 --cluster-domain=cluster.local.
```