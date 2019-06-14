#### ref
```
https://segmentfault.com/a/1190000018741112?utm_source=tag-newest
https://www.jianshu.com/p/8eb81d1674dc
https://www.cnblogs.com/kuku0223/p/10474858.html
https://kubernetes.io/docs/setup/independent/high-availability/
```
#### Haproxy 代理 APIserver
```bash
yum install haproxy -y 

cat << EOF > /etc/haproxy/haproxy.cfg
global
    log         127.0.0.1 local2
    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     4000
    user        haproxy
    group       haproxy
    daemon

defaults
    mode                    tcp
    log                     global
    retries                 3
    timeout connect         10s
    timeout client          1m
    timeout server          1m

frontend kube-apiserver
    bind *:6443
    mode tcp
    default_backend master

backend master
    balance roundrobin
    server master1  192.168.70.138:6443 check maxconn 2000
    server master2  192.168.70.139:6443 check maxconn 2000
EOF

systemctl enable haproxy --now

netstat -lntup | grep 6443
#tcp        0      0 0.0.0.0:6443            0.0.0.0:*               LISTEN      3110/haproxy
```

#### deploy kubernetes
```bash
docker load < coredns.tar.gz
docker load < dashboard.tar.gz
docker load < etcd.tar.gz
docker load < flannel.tar.gz
docker load < kube-apiserver.tar.gz
docker load < kube-controller-manager.tar.gz
docker load < kube-proxy.tar.gz
docker load < kube-scheduler.tar.gz
docker load < pause.tar.gz

cat >> /etc/hosts <<'EOF'
192.168.70.138  node1 master1
192.168.70.139  node2 master2
192.168.70.140  node3
192.168.70.141  node4
EOF

yum -y install yum-utils epel-release
yum-config-manager --add-repo  https://download.docker.com/linux/centos/docker-ce.repo

cat > /etc/yum.repos.d/kubenetes.repo <<'EOF'
[kubenetes]
name=Kubenetes Repo
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
gpgcheck=0
enabled=1
EOF

yum -y install docker-ce kubeadm kubelet chrony kubectl

systemctl daemon-reload
systemctl enable docker --now
systemctl enable kubelet
systemctl enable chronyd --now

echo 1 > /proc/sys/net/bridge/bridge-nf-call-iptables
modprobe bridge 
swapoff -a
sed -iE "/swap/s/\(.*\)/#\1/g" /etc/fstab 
echo 0 > /proc/sys/vm/swappiness
cat > /etc/sysctl.d/kubernetes.conf <<'EOF'
net.bridge.bridge-nf-call-ip6tables=1
net.bridge.bridge-nf-call-iptables=1
net.ipv4.ip_forward=1
vm.swappiness=0
EOF

sysctl -p
systemctl restart docker

vim /etc/sysconfig/kubelet
KUBELET_EXTRA_ARGS="--fail-swap-on=false"

cat > /etc/docker/daemon.json <<'EOF'
{
  "exec-opts": ["native.cgroupdriver=cgroupfs"],
  "log-driver": "json-file",
  "log-opts": {
	  "max-size": "100m",
	  "max-file": "3"
  }
}

systemctl daemon-reload && systemctl restart docker
```
```bash
vim config.yaml

apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
ipvs:
  minSyncPeriod: 1s
  scheduler: rr
  syncPeriod: 10s
mode: ipvs
---
apiVersion: kubeadm.k8s.io/v1beta1
kind: ClusterConfiguration
kubernetesVersion: v1.14.0
controlPlaneEndpoint: 192.168.70.200:6443       #集群前端API负载的地址（先用HAproxy创建）
clusterName: kubernetes
imageRepository: 20.58.27.3:5000
scheduler:
  extraArgs:
    address: 0.0.0.0
controllerManager:
  extraArgs:
    bind-address: 0.0.0.0
external:
  endpoints:
  - https://192.168.30.94:2379
  - https://192.168.30.182:2379
  - https://192.168.30.187:2379
  #caFile: /etc/kubernetes/pki/etcd/ca.pem
  #certFile: /etc/kubernetes/pki/etcd/client.pem
  #keyFile: /etc/kubernetes/pki/etcd/client-key.pem
networking:
  dnsDomain: cluster.local
  serviceSubnet: 10.244.0.0/16
  podSubnet: 20.0.0.0/16
dns:
  type: CoreDNS

systemctl enable kubelet

export KUBE_COMPONENT_LOGLEVEL='--v=2'

#安装前进行检查：
kubeadm init phase preflight [--config config.yml]

#执行安装：( 执行后默认其所有配置信息存储在本地: /etc/kubernetes/ )
kubeadm init --config x.yaml  --experimental-upload-certs [--dry 仅测试] [--node-name指定节点名称]

# 使用外部存储：( etcd 不可与 master 在相同的节点部署，这会引起kubeadm进行预检查时发生错误报告 )
# kubeadm init --external-etcd-endpoints https://192.168.1.100:2379 \
# --external-etcd-cafile /path/to/ca \
# --external-etcd-certfile /path/to/cert \
# --external-etcd-keyfile /path/to/privatekey

#生成令牌: kubeadm token generate
#删除令牌: kubeadm token delete [token-value]
#列出需要的镜像：kubeadm config images list
#列出所有引导令牌: kubeadm token list [flags]
#打印出默认配置: kubeadm config print

#查看正在运行的集群配置信息： ( kubectl get configmaps kubeadm-config -n kube-system )
kubeadm config view 

------------------------------------------------------
You can now join any number of the control-plane node running the following command on each as root:

  # Master节点使用以下命令加入集群：
  kubeadm join 192.168.41.232:6443 --token ocb5tz.pv252zn76rl4l3f6 \
    --discovery-token-ca-cert-hash sha256:141bbeb79bf58d81d551f33ace207c7b19bee1cfd7790112ce26a6a300eee5a2 \
    --experimental-control-plane --certificate-key 20366c9cdbfdc1435a6f6d616d988d027f2785e34e2df9383f784cf6

Then you can join any number of worker nodes by running the following on each as root:

  # Node节点使用以下命令加入集群：
  kubeadm join 192.168.41.232:6443 --token ocb5tz.pv252zn76rl4l3f6 \
      --discovery-token-ca-cert-hash sha256:141bbeb79bf58d81d551f33ace207c7b19bee1cfd7790112ce26a6a300eee5a2 

#By default, kubeadm assigns a node name based on a machine’s host address. \
# You can override this setting with the --node-nameflag


#当后期新节需要点加入集群时使用如下命令输出join的token: ( 若添加主界面，需要携带参数：--experimental-control-plane )
kubeadm token create --print-join-command

#部署flanneld:
kubectl apply -f "https://raw.githubusercontent.com/coreos/flannel\
/a70459be0084506e4ec919aa1c114638878db11b/Documentation/kube-flannel.yml"
```
#### 若遇到授权问题，创建如下类似RBAC解决对应的用户授权问题
```txt
kubectl create clusterrolebinding superadmin --clusterrole=cluster-admin --user=xx:xx:<namespace>:xx
```
#### Example
```yaml
apiVersion: kubeadm.k8s.io/v1alpha1
kind: InitConfiguration
bootstrapTokens:
- groups:
  - system:bootstrappers:kubeadm:default-node-token
  token: abcdef.0123456789abcdef
  ttl: 24h0m0s
  usages:
  - signing
  - authentication
localAPIEndpoint:
  advertiseAddress: 0.0.0.0
  bindPort: 6443
nodeRegistration:
  taints:
  - effect: NoSchedule
    key: node-role.kubernetes.io/master
--- 
apiVersion: kubeadm.k8s.io/v1alpha1
kind: ClusterConfiguration
kubernetesVersion: v1.14.0
controlPlaneEndpoint: ""
controllerManager: {}
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
apiServerExtraArgs:
  endpoint-reconciler-type: lease
scheduler:
  extraArgs:
    address: 0.0.0.0
controllerManager:
  extraArgs:
    bind-address: 0.0.0.0
imageRepository: registry.cn-hangzhou.aliyuncs.com/google_containers
networking:
  dnsDomain: cluster.local
  serviceSubnet: 10.244.0.0/16
  podSubnet: 20.0.0.0/16
api:
  advertiseAddress: <address|string>
  bindPort: <int>
etcd:
  endpoints:
  - https://192.168.70.138:2379
  - https://192.168.70.140:2379
  - https://192.168.70.141:2379
dns:
  type: CoreDNS
scheduler: {}
apiServer:
  timeoutForControlPlane: 4m0s
apiServerCertSANs:
- 192.168.70.138
- 192.168.70.140
- 192.168.70.141
- 192.168.70.143
---
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
ipvs:
  minSyncPeriod: 1s
  scheduler: rr
  syncPeriod: 10s
mode: ipvs
```