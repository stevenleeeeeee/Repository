#### 部署前准备
```bash
系统版本: Centos 7.3 Minimal
k8s-master：    192.168.70.129
k8s-node01：    192.168.70.131

#部署前应首先关闭firewald并清空iptables的防火墙规则:iptables、关闭Selinux、进行集群节点时钟同步...

#kubeadm安装方式： 
1.在master节点上用rpm包安装：
    kubeadm
    kubectl
    kubelet         #由systemd控制
    docker          #由systemd控制

2.在master节点以pod形式运行：
    kube-apiserver
    kube-controller-manager
    kube-scheduler
    etcd
    flannel

3.在node节点：
    kube-proxy      #以Pod方式运行
    flannel         #以Pod方式运行
    kubelet         #由systemd控制
    docker          #由systemd控制 
```
#### 使用kubeadm部署kubenetes
```bash
#分别在Master/Node节点添加K8S集群的主机名映射
[root@node129 ~]# vim /etc/hosts
192.168.70.129 node129
192.168.70.131 node131

#在所有节点安装Docker
[root@node129 ~]# yum -y install yum-utils
[root@node129 ~]# yum -y install epel-release
[root@node129 ~]# yum-config-manager --add-repo  https://download.docker.com/linux/centos/docker-ce.repo

#在Master节点安装kubeadm、kubelet、kubectl. 这里使用阿里云镜像
[root@node129 ~]# cat > /etc/yum.repos.d/kubenetes.repo <<'EOF'
[kubenetes]
name=Kubenetes Repo
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
gpgcheck=0
enabled=1
EOF
[root@node129 ~]# yum -y install docker-ce kubeadm kubelet chrony kubectl

#在Node节点安装kubeadm、kubelet
[root@node129 ~]# yum -y install docker-ce kubeadm kubelet chrony

#在Master/Node节点启动守护进程并修改内核参数
[root@node129 ~]# systemctl daemon-reload
[root@node129 ~]# systemctl enable docker --now
[root@node129 ~]# systemctl enable kubelet --now    #必要时执行"journalctl -exu kubelet"查看启动日志进行故障排查
[root@node129 ~]# systemctl start chronyd
[root@node129 ~]# systemctl enable chronyd          #所有节点的时间必须要先进行同步
[root@node129 ~]# echo 1 >/proc/sys/net/bridge/bridge-nf-call-iptables
[root@node129 ~]# modprobe bridge 
[root@node129 ~]# swapoff -a
[root@node129 ~]# sed -iE "/swap/s/\(.*\)/#\1/g" /etc/fstab 
[root@node129 ~]# echo 0 > /proc/sys/vm/swappiness
[root@node129 ~]# cat /etc/sysctl.d/kubernetes.conf 
net.bridge.bridge-nf-call-ip6tables=1
net.bridge.bridge-nf-call-iptables=1
net.ipv4.ip_forward=1
vm.swappiness=0
[root@node129 ~]# sysctl -p
[root@node129 ~]# systemctl restart docker
[root@node129 ~]# vim /etc/sysconfig/kubelet
KUBELET_EXTRA_ARGS="--fail-swap-on=false"

#在Master节点执行集群初始化:
[root@node129 ~]# kubeadm config images list                #列出需下载的镜像 (先下载再导入到所有节点的仓库)
[root@node129 ~]# kubeadm config print init-defaults        #列出kubeadm执行init时使用的YAML清单
[root@node129 ~]# kubeadm init  \
--kubernetes-version=v1.14.0 \
--pod-network-cidr=10.244.0.0/16 \
--apiserver-advertise-address=192.168.70.129 \
--image-repository registry.cn-hangzhou.aliyuncs.com/google_containers -v 4  #使用阿里云的K8S源并详细输出执行细节
#这个步骤将会从指定的镜像仓库下载K8S组件以Pod方式运行所需要的镜像，如果不修改镜像源地址的话，会很慢，必须使用国内的源!

#当执行kubeadm init ........... 如执行顺利，将输出如下提示：
Your Kubernetes control-plane has initialized successfully!
To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube                                              #输出的这三条命令需要在Master节点复制并执行
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config          #用于创建config文件
  sudo chown $(id -u):$(id -g) $HOME/.kube/config                   #此文件提供了kubectl使用的集群上下文信息及证书

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

Then you can join any number of worker nodes by running the following on each as root:

#这里的输出提供了token并且提示了Node节点使用kubeadm加入集群时使用的命令:
kubeadm join 192.168.70.129:6443 --token riu0dh.hkzvjr20du2wum6j \      
    --discovery-token-ca-cert-hash sha256:b07a92d2b3c354d8aa61b4b42bdc541e13a2942692b0c21668f6a0bb1627f4a3 

[root@node129 ~]# mkdir -p $HOME/.kube
[root@node129 ~]# cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
[root@node129 ~]# chown $(id -u):$(id -g) $HOME/.kube/config
[root@node129 ~]# kubectl get cs

#在Master节点以Pod方式部署flannel
[root@node129 ~]# kubectl apply -f \
 https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
podsecuritypolicy.extensions/psp.flannel.unprivileged created
clusterrole.rbac.authorization.k8s.io/flannel created
clusterrolebinding.rbac.authorization.k8s.io/flannel created
serviceaccount/flannel created
configmap/kube-flannel-cfg created
daemonset.extensions/kube-flannel-ds-amd64 created
daemonset.extensions/kube-flannel-ds-arm64 created
daemonset.extensions/kube-flannel-ds-arm created
daemonset.extensions/kube-flannel-ds-ppc64le created
daemonset.extensions/kube-flannel-ds-s390x created

#node节点加入集群 
#建议执行前先检查Node节点的kubelet运行信息对错误进行排查: journalctl -ex -u kubelet
#若出现如下提示:
Failed to start ContainerManager failed to initialize top level QOS containers: \
failed to update top level Burstable QOS cgroup : failed to set supported cgroup subsyste
#执行一下命令进行修复并重启kubelet（建议重启主机，这有可能是缓存的原因，在Github没有找到对应的Issue，但重启可以解决）：
for i in $(systemctl list-unit-files --no-legend --no-pager -l \
| grep --color=never -o .*.slice | grep kubepod); do systemctl stop $i; done

[root@node131 ~]# kubeadm join 192.168.70.129:6443 --token riu0dh.hkzvjr20du2wum6j \
 --discovery-token-ca-cert-hash sha256:b07a92d2b3c354d8aa61b4b42bdc541e13a2942692b0c21668f6a0bb1627f4a3 
#若执行后有如下输出：   
[WARNING IsDockerSystemdCheck]: detected "cgroupfs" as the Docker cgroup driver.\
 The recommended driver is "systemd". Please follow the guide at https://kubernetes.io/docs/setup/cri/
#修改：
[root@node131 ~]#vim /var/lib/kubelet/kubeadm-flags.env  #修改--cgroup-driver=参数为"systemd"
KUBELET_KUBEADM_ARGS=--cgroup-driver=systemd --network-plugin=cni \
 --pod-infra-container-image=registry.cn-hangzhou.aliyuncs.com/google_containers/pause:3.1
```
#### 检查集群状态
```bash
#自动补全
[root@node129 ~]# source <(kubectl completion bash)

[root@node129 ~]# kubectl get pod -n kube-system -o wide
NAME                            READY STATUS   RESTARTS AGE   IP             NODE    NOMINATED NODE READINESS GATES
coredns-d5947d4b-7sxfv          1/1   Running  0        14m   10.244.0.2     node129 <none>         <none>
coredns-d5947d4b-w9qgc          1/1   Running  0        14m   10.244.0.3     node129 <none>         <none>
etcd-node129                    1/1   Running  0        13m   192.168.70.129 node129 <none>         <none>
kube-apiserver-node129          1/1   Running  0        13m   192.168.70.129 node129 <none>         <none>
kube-controller-manager-node129 1/1   Running  0        13m   192.168.70.129 node129 <none>         <none>
kube-flannel-ds-amd64-d5c59     1/1   Running  0        5m45s 192.168.70.131 node131 <none>         <none>
kube-flannel-ds-amd64-k467v     1/1   Running  0        10m   192.168.70.129 node129 <none>         <none>
kube-proxy-fvsrz                1/1   Running  0        14m   192.168.70.129 node129 <none>         <none>
kube-proxy-q4lxt                1/1   Running  0        5m45s 192.168.70.131 node131 <none>         <none>
kube-scheduler-node129          1/1   Running  0        13m   192.168.70.129 node129 <none>         <none>

[root@node129 ~]# kubectl api-versions
admissionregistration.k8s.io/v1beta1
apiextensions.k8s.io/v1beta1
apiregistration.k8s.io/v1
apiregistration.k8s.io/v1beta1
apps/v1
apps/v1beta1
apps/v1beta2
authentication.k8s.io/v1
authentication.k8s.io/v1beta1
authorization.k8s.io/v1
authorization.k8s.io/v1beta1
autoscaling/v1
autoscaling/v2beta1
autoscaling/v2beta2
batch/v1
batch/v1beta1
certificates.k8s.io/v1beta1
coordination.k8s.io/v1
coordination.k8s.io/v1beta1
events.k8s.io/v1beta1
extensions/v1beta1
networking.k8s.io/v1
networking.k8s.io/v1beta1
node.k8s.io/v1beta1
policy/v1beta1
rbac.authorization.k8s.io/v1
rbac.authorization.k8s.io/v1beta1
scheduling.k8s.io/v1
scheduling.k8s.io/v1beta1
storage.k8s.io/v1
storage.k8s.io/v1beta1
v1
```
#### 总结
```bash
#在执行 "kubeadm init xxx" 命令时，记得加上 "--pod-network-cidr" 参数，并且pod所在网段的地址要和flannel的对应，否则
#容易造成部署不成功! 建议这里使用和flannel端一样的默认网段参数：--pod-network-cidr=10.244.0.0/16 , 例:
[root@node129 ~]# kubeadm init  \
--kubernetes-version=v1.14.0 \
--pod-network-cidr=10.244.0.0/16 \
--apiserver-advertise-address=192.168.70.129 \
--image-repository registry.cn-hangzhou.aliyuncs.com/google_containers -v 4
#在执行 kubectl create -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
#时，此声明清单中的pod端的CIDR默认就是: 10.244.0.0/16 ( 如果不一样，可能会使得Node间Cluster IP不通 )

#若使用 " kubeadm config print init-defaults " 生成YAML清单并用 "kubeadm init --config default.yaml" 声明式部署时
#应该先将里面的部分配置进行修改，需修改的部分如下：
apiVersion: kubeadm.k8s.io/v1beta1
bootstrapTokens:
- groups:
  - system:bootstrappers:kubeadm:default-node-token
  token: abcdef.0123456789abcdef
  ttl: 24h0m0s
  usages:
  - signing
  - authentication
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 192.168.70.129          #这里写入APIserver的地址
  bindPort: 6443
nodeRegistration:
  criSocket: /var/run/dockershim.sock
  name: node129
  taints:
  - effect: NoSchedule
    key: node-role.kubernetes.io/master
---
apiServer:
  timeoutForControlPlane: 4m0s
apiVersion: kubeadm.k8s.io/v1beta1
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controlPlaneEndpoint: ""
controllerManager: {}
dns:
  type: CoreDNS
etcd:
  local:
    dataDir: /var/lib/etcd
imageRepository: registry.cn-hangzhou.aliyuncs.com/google_containers        #这里改为国内的K8S源
kind: ClusterConfiguration
kubernetesVersion: v1.14.0
networking:
  dnsDomain: cluster.local
  podSubnet: ""
  serviceSubnet: 10.96.0.0/12               #这里写入为Pod分片的网段
scheduler: {}
生成的文件，修改IP和镜像地址

#当执行 "kubeadm init" 后，Node节点使用 "kubeadm join <master-ip> --token xxx --discovery-token-ca-cert-hash xxx"
#的方式加入集群，但这个token是有有效期限的，如果超时仍没有加入到集群，需要重新生成token，生成Token的命令如下
[root@node129 ~]# kubeadm token create
0bzans.3e8j9x0vzpllb2si

```


#### Kubeadm 提供的参数
```bash
apiVersion: kubeadm.k8s.io/v1alpha1
kind: MasterConfiguration
api:
  advertiseAddress: <address|string>
  bindPort: <int>
etcd:
  endpoints:
  - <endpoint1|string>
  - <endpoint2|string>
  caFile: <path|string>
  certFile: <path|string>
  keyFile: <path|string>
  dataDir: <path|string>
  extraArgs:
    <argument>: <value|string>
    <argument>: <value|string>
  image: <string>
kubeProxy:
  config:
    mode: <value|string>
networking:
  dnsDomain: <string>
  serviceSubnet: <cidr>
  podSubnet: <cidr>
kubernetesVersion: <string>
cloudProvider: <string>
nodeName: <string>
authorizationModes:
- <authorizationMode1|string>
- <authorizationMode2|string>
token: <string>
tokenTTL: <time duration>
selfHosted: <bool>
apiServerExtraArgs:
  <argument>: <value|string>
  <argument>: <value|string>
controllerManagerExtraArgs:
  <argument>: <value|string>
  <argument>: <value|string>
schedulerExtraArgs:
  <argument>: <value|string>
  <argument>: <value|string>
apiServerExtraVolumes:
- name: <value|string>
  hostPath: <value|string>
  mountPath: <value|string>
controllerManagerExtraVolumes:
- name: <value|string>
  hostPath: <value|string>
  mountPath: <value|string>
schedulerExtraVolumes:
- name: <value|string>
  hostPath: <value|string>
  mountPath: <value|string>
apiServerCertSANs:
- <name1|string>
- <name2|string>
certificatesDir: <string>
imageRepository: <string>
unifiedControlPlaneImage: <string>
featureGates:
  <feature>: <bool>
  <feature>: <bool>
```
#### 当前使用的参数模板
```txt
apiVersion: kubeadm.k8s.io/v1alpha1
kind: MasterConfiguration
api:
  advertiseAddress: {{HOSTIP}}
  bindPort: 6443
etcd:
  endpoints:
  {{ETCD_ENDPOINTS}}
kubernetesVersion: {{KUBERNETES_VERISON}}
networking:
  dnsDomain: cluster.local
  serviceSubnet: {{SERVICE_SUBNET}}
  podSubnet: {{POD_SUBNET}}
token: {{JOIN_TOKEN}}
nodeName: {{HOSTNAME}}
certificatesDir: /etc/kubernetes/pki
imageRepository: ufleet.io/google_containers
```