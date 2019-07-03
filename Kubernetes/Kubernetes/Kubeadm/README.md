#### ref
```txt
https://kubernetes.io/zh/docs/reference/setup-tools/kubeadm/kubeadm-init/
https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/
https://segmentfault.com/a/1190000018741112?utm_source=tag-newest
https://www.jianshu.com/p/8eb81d1674dc
https://www.cnblogs.com/kuku0223/p/10474858.html
https://kubernetes.io/docs/setup/independent/high-availability/
```
#### 内核参数调整
```bash
#系统版本: Centos 7.4 Minimal (对内核版本有要求，建议使用最新发行版)
#部署前应首先关闭firewald并清空iptables的防火墙规则:iptables、关闭Selinux、进行集群节点时钟同步...
cat <<EOF > /etc/sysctl.d/k8s.conf
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 10
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
net.ipv4.neigh.default.gc_stale_time = 120
net.ipv4.conf.all.rp_filter = 0
net.ipv4.conf.default.rp_filter = 0
net.ipv4.conf.default.arp_announce = 2
net.ipv4.conf.lo.arp_announce = 2
net.ipv4.conf.all.arp_announce = 2
net.ipv4.ip_forward = 1
net.ipv4.tcp_max_tw_buckets = 5000
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 1024
net.ipv4.tcp_synack_retries = 2
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.netfilter.nf_conntrack_max = 2310720
fs.inotify.max_user_watches=89100
fs.may_detach_mounts = 1
fs.file-max = 52706963
fs.nr_open = 52706963
net.bridge.bridge-nf-call-arptables = 1
vm.swappiness = 0
vm.overcommit_memory=1
vm.panic_on_oom=0
EOF
sysctl --system
```
#### 控制平面前端代理服务
```bash
#Keepalive
global_defs {
   router_id LVS_DEVEL
}
 
vrrp_script check_haproxy {
    script "killall -0 haproxy"   #依进程名检测进程是否存活，若服务器没有该命令则安装： yum -y install psmisc
    interval 3
    weight -2
    fall 10
    rise 2
}
 
vrrp_instance VI_1 {
    state MASTER                  #本节点当前状态，其他Keepalive节点属于BACKUP
    interface eth0                #接口
    virtual_router_id 51          #router_id，所有节点需一致
    priority 100                  #优先级，越大越优先
    advert_int 1                  #通告周期
    authentication {
        auth_type PASS
        auth_pass 1111
    }
    virtual_ipaddress {
        192.168.158.138           #虚IP地址
    }
    track_script {
        check_haproxy             #Haproxy的健康检查脚本，提供检查目标进程是否存活的功能
    }

#Haproxy 所有Master配置相同
global
    log         127.0.0.1 local2
 
    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     4000
    user        haproxy
    group       haproxy
    daemon

    stats socket /var/lib/haproxy/stats

defaults
    mode                    http
    log                     global
    option                  httplog
    option                  dontlognull
    option http-server-close
    option forwardfor       except 127.0.0.0/8
    option                  redispatch
    retries                 3
    timeout http-request    10s
    timeout queue           1m
    timeout connect         10s
    timeout client          1m
    timeout server          1m
    timeout http-keep-alive 10s
    timeout check           10s
    maxconn                 3000

frontend kubernetes-apiserver
    mode                 tcp
    bind                 *:16443                  #提供服务的地址，由Keepalive代理
    option               tcplog
    default_backend      kubernetes-apiserver

backend kubernetes-apiserver
    mode        tcp
    balance     roundrobin
    server      k8s01 192.168.x.x:6443 check      #后端Master地址
    server      k8s02 192.168.x.x:6443 check      #后端Master地址
    server      k8s03 192.168.x.x:6443 check      #后端Master地址

listen stats
    bind                 *:1080                   #Haproxy状态查看页面
    stats auth           admin:awesomePassword
    stats refresh        5s
    stats realm          HAProxy\ Statistics
    stats uri            /admin?stats
```
#### 使用kubeadm部署kubenetes
```bash
#分别在Master/Node节点添加K8S集群的主机名映射
[root@node129 ~]# vim /etc/hosts
192.168.70.129 node129
192.168.70.131 node131

#在所有节点安装Docker
[root@node129 ~]# yum -y install yum-utils epel-release
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

cat > /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=cgroupfs"],
  "log-opts": {
	  "max-size": "100m",
	  "max-file": "3"
  }
}
EOF

systemctl daemon-reload && systemctl restart docker



# 列出Docker版本：  yum list docker-ce --showduplicates | sort -r
# 安装指定版本：    sudo yum install docker-ce-<VERSION_STRING>

#在Node节点安装kubeadm、kubelet
[root@node129 ~]# yum -y install docker-ce kubeadm kubelet chrony

#在Master/Node节点启动守护进程并修改内核参数
[root@node129 ~]# systemctl daemon-reload
[root@node129 ~]# systemctl enable docker --now
[root@node129 ~]# systemctl enable kubelet --now    #必要时执行"journalctl -exu kubelet"查看启动日志进行故障排查
[root@node129 ~]# systemctl start chronyd --now     #所有节点的时间必须要先进行同步
[root@node129 ~]# echo 1 > /proc/sys/net/bridge/bridge-nf-call-iptables
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

#使用阿里云的K8S源并详细输出执行细节
#这个步骤将会从指定的镜像仓库下载K8S组件以Pod方式运行所需要的镜像，如果不修改镜像源地址的话，会很慢，必须使用国内的源!
[root@node129 ~]# kubeadm init  \
--kubernetes-version=v1.14.0 \
--pod-network-cidr=10.244.0.0/16 \
--apiserver-advertise-address=192.168.70.129 \
--image-repository registry.cn-hangzhou.aliyuncs.com/google_containers -v 4  

#当执行kubeadm init ........... 如执行顺利将输出如下：
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
```
#### 总结
```bash
--------------------------------------------------------------------------------- Demo
#在执行 "kubeadm init xxx" 命令时记得加 "--pod-network-cidr" 参数
#并且pod所在网段的地址要和flannel的对应，否则容易造成部署不成功! 
#建议这里使用和flannel端一样的默认网段参数：--pod-network-cidr=10.244.0.0/16
[root@node129 ~]# kubeadm init  \
--kubernetes-version=v1.14.0 \
--pod-network-cidr=10.244.0.0/16 \
--apiserver-advertise-address=192.168.70.129 \
--image-repository registry.cn-hangzhou.aliyuncs.com/google_containers -v 4
#在执行 kubectl create -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
#时，此声明清单中的pod端的CIDR默认就是: 10.244.0.0/16 ( 如果不一样，可能会使得Node间Cluster IP不通 )

--------------------------------------------------------------------------------- HA

#在需定制场景，可使用 "kubeadm config print init-defaults" 生成初始化部署时的YAML清单，而后再此基础上进行定制
#基于这份清单，可使用 "kubeadm init --config default.yaml" 形式的命令根据这份清单进行初始化操作

# 下面注释的部分，在使用HA方式进行部署时需要忽略（具体，需要再验证...）
# apiVersion: kubeadm.k8s.io/v1beta1
# kind: InitConfiguration
# bootstrapTokens:
# - groups:
#   - system:bootstrappers:kubeadm:default-node-token
#   token: abcdef.0123456789abcdef
#   ttl: 24h0m0s                              #加入集群时使用的Token的过期时间
#   usages:                                   #Token用途
#   - signing
#   - authentication
# localAPIEndpoint:
#   advertiseAddress: 0.0.0.0                 #APIserver地址
#   bindPort: 6443                            #端口
# nodeRegistration:
#   criSocket: /var/run/dockershim.sock
#   name: node129                             #节点名称
#   taints:                                   #污点标记
#   - effect: NoSchedule
#     key: node-role.kubernetes.io/master
# 
# ---

apiVersion: kubeadm.k8s.io/v1beta1
kind: ClusterConfiguration
kubernetesVersion: v1.14.0
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controlPlaneEndpoint: 192.168.158.138         #VIP:PORT
maxPods: 100

#详细参数：https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/
apiServer:
  timeoutForControlPlane: 4m0s
  extraArgs:
    #advertise-address: 192.168.0.103
    anonymous-auth: "false"
    enable-admission-plugins: AlwaysPullImages,DefaultStorageClass
    #audit-log-path: /home/johndoe/audit.log
    certSANs:                               #有所有控制平面IP的列表，包括VIP地址
    - 192.168.70.138
    - 192.168.70.140
    - 192.168.70.141
    - 192.168.158.138
#详细参数：https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/
controllerManager: 
  extraArgs:
    bind-address: 0.0.0.0
    deployment-controller-sync-period: "50"
    #cluster-signing-key-file: /home/johndoe/keys/ca.key

#详细参数：https://kubernetes.io/docs/reference/command-line-tools-reference/kube-scheduler/
scheduler: 
  extraArgs:
    address: 0.0.0.0
    #config: /home/johndoe/schedconfig.yaml
    #kubeconfig: /home/johndoe/kubeconfig.yaml
dns:
  type: CoreDNS
etcd:
  local:
    dataDir: /var/lib/etcd
imageRepository: registry.cn-hangzhou.aliyuncs.com/google_containers        #改为国内K8S源或内网镜像仓库地址
networking:
  serviceSubnet: 10.96.0.0/12               #为Pod分片的网段
  podSubnet: 20.0.0.0/16                    #如果使用flannel方案，则推荐设为10.244.0.0/16
  dnsDomain: cluster.local

---

apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
ipvs:
  minSyncPeriod: 1s
  scheduler: rr
  syncPeriod: 10s
mode: ipvs

#部署前进行配置检查：
kubeadm init phase preflight [--config config.yml]

# 使用外部存储：( etcd 不可与 master 在相同的节点部署，这会引起kubeadm进行预检查时发生错误报告 )
# kubeadm init --external-etcd-endpoints https://192.168.1.100:2379 \
# --external-etcd-cafile /path/to/ca \
# --external-etcd-certfile /path/to/cert \
# --external-etcd-keyfile /path/to/privatekey

#部署
kubeadm init --config deploy.yaml

#当执行 "kubeadm init" 后
#Node节点用 "kubeadm join <master-ip> --token xxx --discovery-token-ca-cert-hash xxx" 的方式加入集群
#但这个token有有效期限，如果超时仍没加入集群，需要重新生成token：
[root@node129 ~]# kubeadm token create
0bzans.3e8j9x0vzpllb2si

#拷贝相关证书到master2、master3
for ip in 192.168.x.x 192.168.x.x
do
    ssh $ip "mkdir -p /etc/kubernetes/pki/etcd; mkdir -p ~/.kube/"
    scp /etc/kubernetes/pki/ca.crt $ip:/etc/kubernetes/pki/ca.crt
    scp /etc/kubernetes/pki/ca.key $ip:/etc/kubernetes/pki/ca.key
    scp /etc/kubernetes/pki/sa.key $ip:/etc/kubernetes/pki/sa.key
    scp /etc/kubernetes/pki/sa.pub $ip:/etc/kubernetes/pki/sa.pub
    scp /etc/kubernetes/pki/front-proxy-ca.crt $ip:/etc/kubernetes/pki/front-proxy-ca.crt
    scp /etc/kubernetes/pki/front-proxy-ca.key $ip:/etc/kubernetes/pki/front-proxy-ca.key
    scp /etc/kubernetes/pki/etcd/ca.crt $ip:/etc/kubernetes/pki/etcd/ca.crt
    scp /etc/kubernetes/pki/etcd/ca.key $ip:/etc/kubernetes/pki/etcd/ca.key
    scp /etc/kubernetes/admin.conf $ip:/etc/kubernetes/admin.conf
    scp /etc/kubernetes/admin.conf $ip:~/.kube/config
    ssh ${ip} "${JOIN_CMD} --experimental-control-plane"
done

#其他控制平面加入集群，形成HA：
JOIN_CMD=`kubeadm token create --print-join-command`    #获取加入集群时使用的Token （控制平面）
ssh ${ip} "${JOIN_CMD} --experimental-control-plane"    #加入集群

#设置环境变量
echo "export KUBECONFIG=/etc/kubernetes/admin.conf" > /etc/profile.d/kubeconfig.sh
source /etc/profile

#禁止master2,master3上发布应用
kubectl taint nodes master-2 node-role.kubernetes.io/master=true:NoSchedule
kubectl taint nodes master-3 node-role.kubernetes.io/master=true:NoSchedule

#部署flanneld:
kubectl apply -f "https://raw.githubusercontent.com/coreos/flannel\
/a70459be0084506e4ec919aa1c114638878db11b/Documentation/kube-flannel.yml"

#生成令牌: kubeadm token generate
#删除令牌: kubeadm token delete [token-value]
#列出需要的镜像：kubeadm config images list
#列出所有引导令牌: kubeadm token list [flags]
#打印出默认配置: kubeadm config print

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
#### kubeadm -h
```bash

```
#### 重置
```bash
kubeadm reset -f
rm -rf /etc/kubernetes/pki/
```