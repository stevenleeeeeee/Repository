```txt
1. kubectl使用的集群信息配置文件需要单独再创建一份
2. 证书/TLS...
3. cgroup / systemd 那里有问题
4.
本文档参考了官方文档和Github中的K8S部署流程的开源项目，项目地址：（注意! 不同版本之间会有部分参数差异，有些会从beta版移除）
https://github.com/opsnull/follow-me-install-kubernetes-cluster/blob/master/README.md
```
#### 初始化环境
```bash
#Linux内核应大于3.10.0-327.el7.x86_64，建议使用3.10.0-957.12.1.el7.x86_64内核，或：Centos版本大于7.2，建议7.4+

#检查系统内核和模块是否适合运行 docker
curl -sL https://raw.githubusercontent.com/docker/docker/master/contrib/check-config.sh | bash

# 如果报user namespace未被启用，则执行如下命令并reboot...
# 启用：grubby --args="user_namespace.enable=1" --update-kernel="$(grubby --default-kernel)"
# 关闭：grubby --remove-args="user_namespace.enable=1" --update-kernel="$(grubby --default-kernel)"

hostnamectl --static set-hostname <NODE_NAME>
chmod a+x /etc/rc.d/rc.local

#关闭SElinux
setenforce 0
sed -i.bak "s/^SELINUX=.*/SELINUX=disabled/g" /etc/sysconfig/selinux /etc/selinux/config

#防火墙设置
systemctl disable firewalld --now
iptables -F && iptables -X && iptables -F -t nat && iptables -X -t nat
iptables -P FORWARD ACCEPT
systemctl disable dnsmasq --now

#安装基础组件
yum -y install epel-release
yum -y install yum-utils chrony lvm2 git jq unzip ipset ipvsadm conntrack libseccomp sysstat device-mapper-persistent-data nfs-utils
yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
yum makecache all
version=$(yum list docker-ce.x86_64 --showduplicates | sort -r | grep ${docker_version} | awk '{print $2}')
yum -y install --setopt=obsoletes=0 docker-ce-${version} docker-ce-selinux-${version};
#Docker要求Linux内核版本3.10+

#设置语言
echo 'LANG="en_US.UTF-8"' >> /etc/profile.d/LANG.sh
source /etc/profile

#设置时区
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
timedatectl set-timezone Asia/Shanghai
timedatectl set-local-rtc 0
systemctl enable chronyd --now 

#加载模块
modprobe bridge
modprobe br_netfilter
modprobe ip_vs
modprobe ip_vs_rr
modprobe ip_vs_wrr  
modprobe ip_vs_sh
modprobe nf_conntrack_ipv4

#关闭swap
sysctl -w vm.swappiness=0
sed -i.bak "/swap/s/\(.*\)/#\1/g" /etc/fstab && swapoff -a

#修改内核参数
cat > /etc/sysctl.d/kubernetes.conf <<'EOF'
net.bridge.bridge-nf-call-ip6tables=1
net.bridge.bridge-nf-call-iptables=1
net.netfilter.nf_conntrack_max=2310720
net.ipv4.ip_local_port_range=15000 64000
net.ipv4.neigh.default.gc_thresh1=4096
net.ipv4.neigh.default.gc_thresh2=6144
net.ipv4.neigh.default.gc_thresh3=8192
fs.file-max=6553500
fs.nr_open=6553500
fs.inotify.max_user_instances=8192
fs.inotify.max_user_watches=1048576
net.ipv4.ip_forward=1
net.ipv4.tcp_tw_recycle=0
net.ipv6.conf.all.disable_ipv6=1
net.netfilter.nf_conntrack_max=2310720
vm.swappiness=0
vm.overcommit_memory=1
vm.panic_on_oom=0
EOF

ulimit -n 655350

cat > /etc/security/limits.conf <<'EOF'
* soft nofile 655350
* hard nofile 655350
* soft nproc 655350
* hard nproc 655350
* soft memlock  unlimited
* hard memlock  unlimited
EOF

sysctl -p

#Docker自1.13+开始修改了默认防火墙规则，禁用iptables中filter表的FOWARD链，这会引起跨Node的Pod无法通信:
sed -i '/ExecStart=/iExecStartPost=/usr/sbin/iptables -P FORWARD ACCEPT' /usr/lib/systemd/system/docker.service

#修改Docker配置信息
mkdir -p /etc/docker /data/docker
sed -Ei 's|(/usr/bin/dockerd)|\1 --data-root=/data/docker|' /usr/lib/systemd/system/docker.service 
cat > /etc/docker/daemon.json <<'EOF'
{
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 5,
  "exec-opts": ["native.cgroupdriver=systemd"],
  "registry-mirrors": ["https://fz5yth0r.mirror.aliyuncs.com","https://7bezldxe.mirror.aliyuncs.com/"],
  "insecure-registries": ["192.168.1.100:80"],
  "storage-driver": "overlay2",
  "storage-opts": ["overlay2.override_kernel_check=true"],
  "log-driver": "json-file",
  "log-opts": {
	  "max-size": "100m",
	  "max-file": "5"
  }
}
EOF

systemctl daemon-reload && systemctl enable docker --now

ip addr show docker0
#输出验证：
3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN 
    link/ether 02:42:45:92:2d:b2 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 scope global docker0
       valid_lft forever preferred_lft forever

#创建Kubernetes可执行组件、配置、数据存放路径:
mkdir -p /kubernetes/{bin,config,ssl,logs} 

#主机映射
cat >> /etc/hosts <<'EOF'
192.168.70.138  node1 master
192.168.70.139  node2
192.168.70.140  node3
192.168.70.141  node4
EOF
```
#### CA
```bash
curl -sL https://pkg.cfssl.org/R1.2/cfssl_linux-amd64  -o /bin/cfssl        
curl -sL https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64  -o /bin/cfssljson  
curl -sL https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64  -o /bin/cfssl-certinfo 
chmod a+x /bin/cfss*

cd /kubernetes/ssl          # 超级用户：admin  超级用户组：system:masters  绑定：cluster-admin
cfssl print-defaults config > ca-config.json  
cfssl print-defaults csr > ca-csr.json

cat > ca-config.json <<'EOF'
{
    "signing": {
        "default": {
            "expiry": "87600h"
        },
        "profiles": {
            "kubernetes": {
                "expiry": "87600h",
                "usages": [
                    "signing",
                    "key encipherment",
                    "server auth",
                    "client auth"
                ]
            }
        }
    }
}
EOF

cat > ca-csr.json <<'EOF'   
{
    "CN": "kubernetes",
    "key": {
        "algo": "ecdsa",
        "size": 256
    },
    "names": [
        {
            "C": "CN",
            "L": "SH",
            "O":"k8s"
        }
    ]
}
EOF

cfssl gencert -initca ca-csr.json | cfssljson -bare ca -

#将Kubernetes集群所有节点IP/域名写入证书Hosts字段 ( 由etcd节点/masters&Nodes/集群service地址范围等构成 )
cat > server.json <<'EOF'
{
    "CN": "kubernetes",
    "hosts": [
        "192.168.70.138",
        "192.168.70.140",
        "192.168.70.141",
        "192.168.70.143",
        "127.0.0.1",
        "10.0.0.1",   #服务IP!!
        "kubernetes",
        "kubernetes.default",
        "kubernetes.default.svc",
        "kubernetes.default.svc.cluster",
        "kubernetes.default.svc.cluster.local"
    ],
    "key": {
        "algo": "ecdsa",
        "size": 256
    },
    "names": [
        {
            "C": "CN",
            "L": "SH",
            "O":"system:masters",
            "OU": "System"
        }
    ]
}
EOF

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes server.json | cfssljson -bare server

#Client证书不需要hosts字段，可设为："hosts": [] 此证书仅限kube-proxy使用!
#kube-apiserver预定义的 RoleBinding 将 User system:kube-proxy 与 Role system:node-proxier 绑定，该 Role 授予调用 kube-apiserver Proxy 相关 API 的权限...
cat > kube-proxy.json <<'EOF'
{
    "CN": "system:kube-proxy",
    "hosts": [],
    "key": {
        "algo": "ecdsa",
        "size": 256
    },
    "names": [
        {
            "C": "CN",
            "L": "SH",
            "O":"k8s"
        }
    ]
}
EOF

# Kubernetes version 1.14+ 默认预设了用户 system:kube-proxy 的 clusterrolebinding，验证：
# kubectl describe clusterrolebinding system:node-proxier

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes kube-proxy.json | cfssljson -bare kube-proxy

# metrics-server & .... for aggregator API !
cat > aggregator.json <<'EOF'
{
  "CN": "aggregator",
    "hosts": [],
    "key": {
        "algo": "ecdsa",
        "size": 256
    },
    "names": [
        {
            "C": "CN",
            "L": "SH",
            "O":"k8s"
        }
    ]
}
EOF

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes aggregator.json | cfssljson -bare aggregator

cat > scheduler-csr.json <<'EOF'
{
    "CN": "system:kube-scheduler",
    "hosts": [
        "127.0.0.1",
        "192.168.70.138",
        "192.168.70.140",
        "192.168.70.141",
        "192.168.70.143"
    ],
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "L": "SH",
            "O": "system:kube-scheduler",
            "OU": "Bluevitality"
        }
    ]
}
EOF

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes scheduler-csr.json | cfssljson -bare scheduler

cat > kube-controller-manager-csr.json <<EOF
{
    "CN": "system:kube-controller-manager",
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "hosts": [
        "127.0.0.1",
        "192.168.70.138",
        "192.168.70.140",
        "192.168.70.141",
        "192.168.70.143"
    ],
    "names": [
      {
        "C": "CN",
        "L": "SH",
        "O": "system:kube-controller-manager",
        "OU": "Bluevitality"
      }
    ]
}
EOF

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json \
  -profile=kubernetes kube-controller-manager-csr.json | cfssljson -bare kube-controller-manager


[root@node1 ssl]# ll
total 100
-rw-r--r-- 1 root root  412 May 11 16:17 aggregator.csr
-rw-r--r-- 1 root root  217 May 11 16:17 aggregator.json
-rw------- 1 root root  227 May 11 16:17 aggregator-key.pem            #API聚合使用 ( 预留给API聚合类资源使用! )
-rw-r--r-- 1 root root  761 May 11 16:17 aggregator.pem                #API..... ( 其使用的头部为"aggregator" )
-rw-r--r-- 1 root root  386 May 11 16:15 ca-config.json
-rw-r--r-- 1 root root  428 May 11 16:16 ca.csr
-rw-r--r-- 1 root root  213 May 11 16:16 ca-csr.json
-rw------- 1 root root  227 May 11 16:16 ca-key.pem                    #CA私钥
-rw-r--r-- 1 root root  745 May 11 16:16 ca.pem                        #CA证书
-rw-r--r-- 1 root root 1123 May 11 16:17 kube-controller-manager.csr
-rw-r--r-- 1 root root  409 May 11 16:17 kube-controller-manager-csr.json
-rw------- 1 root root 1675 May 11 16:17 kube-controller-manager-key.pem
-rw-r--r-- 1 root root 1192 May 11 16:17 kube-controller-manager.pem
-rw-r--r-- 1 root root  420 May 11 16:17 kube-proxy.csr
-rw-r--r-- 1 root root  226 May 11 16:17 kube-proxy.json
-rw------- 1 root root  227 May 11 16:17 kube-proxy-key.pem            #客户端私钥 - kube-proxy
-rw-r--r-- 1 root root  769 May 11 16:17 kube-proxy.pem                #客户端证书 - kube-proxy
-rw-r--r-- 1 root root 1094 May 11 16:17 scheduler.csr
-rw-r--r-- 1 root root  411 May 11 16:17 scheduler-csr.json
-rw------- 1 root root 1679 May 11 16:17 scheduler-key.pem
-rw-r--r-- 1 root root 1168 May 11 16:17 scheduler.pem
-rw-r--r-- 1 root root  720 May 11 16:17 server.csr
-rw-r--r-- 1 root root  583 May 11 16:16 server.json
-rw------- 1 root root  227 May 11 16:17 server-key.pem                #服务端私钥
-rw-r--r-- 1 root root 1042 May 11 16:17 server.pem                    #服务端证书

...................................................

#将生成的证书及对应的密钥分发到所有节点
HOSTS=(
192.168.70.138
192.168.70.140
192.168.70.141
192.168.70.143
)

for IP in ${HOSTS[@]}
do
  scp /kubernetes/ssl/*   root@${IP}:/kubernetes/ssl
done
```
#### etcd cluster
```bash
echo 'export PATH=$PATH:/kubernetes/bin' > /etc/profile.d/kubernetes.sh && source /etc/profile
tar -zxf ~/kubernetes-soft/etcd-v3.3.12-linux-amd64.tar.gz -C ~
mv ~/etcd-v3.3.12-linux-amd64/etcd* /kubernetes/bin/

cat > /usr/lib/systemd/system/etcd.service <<'EOF'
[Unit]
Description=Etcd Server
Documentation=https://coreos.com/etcd/docs/latest/op-guide/configuration.html
After=network.target
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/var/lib/etcd
ExecStart=/kubernetes/bin/etcd \
--name=node1 \
--listen-peer-urls=https://192.168.70.138:2380 \
--listen-client-urls=https://192.168.70.138:2379,http://127.0.0.1:2379 \ # prometheus: https://x.x.x.x:#/metrics
--advertise-client-urls=https://192.168.70.138:2379 \
--initial-advertise-peer-urls=https://192.168.70.138:2380 \
--initial-cluster=node1=https://192.168.70.138:2380,node2=https://192.168.70.140:2380,node3=https://192.168.70.141:2380 \
--initial-cluster-state=new \
--initial-cluster-token=kubernetes \
--cert-file=/kubernetes/ssl/server.pem \
--key-file=/kubernetes/ssl/server-key.pem \
--peer-cert-file=/kubernetes/ssl/server.pem \
--peer-key-file=/kubernetes/ssl/server-key.pem \
--trusted-ca-file=/kubernetes/ssl/ca.pem \
--peer-trusted-ca-file=/kubernetes/ssl/ca.pem \
--max-snapshots=10 \
--max-wals=10 \
--snapshot-count=10000 \
--heartbeat-interval=200 \
--data-dir=/var/lib/etcd \
--election-timeout=2000 \
--peer-client-cert-auth \
--client-cert-auth \
--enable-v2=true

Type=notify
Restart=on-failure
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload && systemctl enable etcd --now

export ETCDCTL_API=3

etcdctl --cacert=/kubernetes/ssl/ca.pem \
   --endpoints=https://192.168.70.138:2379,https://192.168.70.140:2379,https://192.168.70.141:2379 \
   -w table endpoint status 
+----------------------------+------------------+---------+---------+-----------+-----------+------------+
|          ENDPOINT          |        ID        | VERSION | DB SIZE | IS LEADER | RAFT TERM | RAFT INDEX |
+----------------------------+------------------+---------+---------+-----------+-----------+------------+
| https://192.168.70.138:2379 | f3ebc028ed75e1d5 | 3.3.10 |  133 MB |     false |      1046 |   15855129 |
| https://192.168.70.140:2379 | b6c6ce02ecf2d0e5 | 3.3.10 |  134 MB |     false |      1046 |   15855129 |
| https://192.168.70.141:2379 | fe52f375f370dc54 | 3.3.10 |  133 MB |      true |      1046 |   15855130 |
+----------------------------+------------------+---------+---------+-----------+-----------+------------+

#flannel network config ...
#设置的IP与docker0网桥本身的IP地址在同一网段
#写入的Pod网段必须是/16段地址且必须与kube-controller-manager的"–-cluster-cidr"一致

etcdctl --ca-file=/kubernetes/ssl/ca.pem \
  --cert-file=/kubernetes/ssl/server.pem \
  --key-file=/kubernetes/ssl/server-key.pem \
  --endpoints=https://192.168.70.138:2379,https://192.168.70.140:2379,https://192.168.70.141:2379 \
  set /atomic.io/network/config '{"Network":"172.17.0.0/16","SubnetLen":24,"Backend":{"Type":"vxlan"}}'

#清除etcd数据：etcdctl del "" --prefix
```
#### TLS && Apiserver
```bash
echo 'export PATH=$PATH:/kubernetes/bin' > /etc/profile.d/kubernetes.sh && source /etc/profile
tar -zxf ~/kubernetes-soft/kubernetes-server-linux-amd64.tar.gz -C ~

cd ~/kubernetes/server/bin/
cp -af ./{kube-apiserver,kube-scheduler,kube-controller-manager,kubectl,kubelet}  /kubernetes/bin/

#自动补全
yum install -y bash-completion
source /usr/share/bash-completion/bash_completion 
echo "source <(kubectl completion bash)" >> ~/.bashrc

cat > /usr/lib/systemd/system/kube-apiserver.service <<'EOF'
[Unit]
Description=Kubernetes API Server
Documentation=https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/
After=network.target

[Service]
ExecStart=/kubernetes/bin/kube-apiserver \
 --logtostderr=false --v=2 --log-dir=/kubernetes/logs \
 --enable-admission-plugins=NamespaceLifecycle,LimitRanger,ResourceQuota,DefaultStorageClass,ServiceAccount,NodeRestriction \
 --anonymous-auth=false \
 --authorization-mode=Node,RBAC \
 --enable-bootstrap-token-auth=true --token-auth-file=/kubernetes/config/token.csv \
 --advertise-address=0.0.0.0 --bind-address=0.0.0.0 --secure-port=6443 --insecure-port=0 \
 --service-cluster-ip-range=10.0.0.0/24 --service-node-port-range=10000-40000 \
 --allow-privileged=true \
 --apiserver-count=3 \
 --runtime-config=api/all=true \
 --requestheader-username-headers=X-Remote-User \  
#客户端证书常用名称列表，允许在--requestheader-username-headers指定的标头中提供用户名，如果为空，则允许在--requestheader-client-ca文件中通过当局验证的任何客户端证书
 --requestheader-group-headers=X-Remote-Group \  #要检查组的请求标头列表
 --requestheader-allowed-names=aggregator \
 --requestheader-client-ca-file=/kubernetes/ssl/ca.pem \
 --requestheader-extra-headers-prefix=X-Remote-Extra- \
 --proxy-client-cert-file=/kubernetes/ssl/server.pem \    #用于证明aggregator或kube-apiserver在请求期间发出呼叫的身份的客户端证书
 --proxy-client-key-file=/kubernetes/ssl/server-key.pem \ #用于证明聚合器或kube-apiserver的身份的客户端证书的私钥，当它必须在请求期间调用时使用。包括将请求代理给用户api-server和调用webhook admission插件
 --enable-aggregator-routing=true \   #打开aggregator路由请求到endpoints IP，而不是集群IP
 --enable-swagger-ui=true \
 --audit-log-maxage=30 --audit-log-truncate-enabled \
 --audit-log-maxbackup=3 --audit-log-maxsize=100 --audit-log-path=/kubernetes/logs/audit.log \
 --cert-dir=/kubernetes/ssl \
 --client-ca-file=/kubernetes/ssl/ca.pem \
 --kubelet-client-certificate=/kubernetes/ssl/server.pem \
 --kubelet-client-key=/kubernetes/ssl/server-key.pem \
 --etcd-cafile=/kubernetes/ssl/ca.pem \
 --etcd-certfile=/kubernetes/ssl/server.pem \
 --etcd-keyfile=/kubernetes/ssl/server-key.pem \
 --etcd-servers=https://192.168.70.138:2379,https://192.168.70.140:2379,https://192.168.70.141:2379 \
 --service-account-key-file=/kubernetes/ssl/ca-key.pem \
 --tls-cert-file=/kubernetes/ssl/server.pem \
 --tls-private-key-file=/kubernetes/ssl/server-key.pem \
 --kubelet-https \
 --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname

Restart=on-failure
RestartSec=5
Type=notify
LimitNOFILE=65536
[Install]
WantedBy=multi-user.target
EOF

export TOKEN=$(head -c 16 /dev/urandom | od -An -t x | tr -d ' ')
cat > /kubernetes/config/token.csv <<EOF
${TOKEN},kubelet-bootstrap,10001,"system:bootstrappers"
EOF

systemctl daemon-reload && systemctl enable kube-apiserver --now

# 允许用Token发起CSR：
# https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet-tls-bootstrapping/
kubectl create clusterrolebinding create-csrs-for-bootstrapping \
  --clusterrole=system:node-bootstrapper \
  --group=system:bootstrappers
#当Kubelet拥有签发的证书后，使用证书中的CN=system:node:(node name)/O=system:nodes的形式发起另一个CSR请求 (共3种CSR)

#kubelet - bootstrap-kubeconfig
APISERVER=https://192.168.70.138:6443
CONFIG=/kubernetes/config/bootstrap-kubeconfig
kubectl config --kubeconfig=${CONFIG} set-cluster bootstrap --server=${APISERVER} --embed-certs=true --certificate-authority=/kubernetes/ssl/ca.pem
kubectl config --kubeconfig=${CONFIG} set-credentials kubelet-bootstrap --token=${TOKEN}
kubectl config --kubeconfig=${CONFIG} set-context bootstrap --user=kubelet-bootstrap --cluster=bootstrap
kubectl config --kubeconfig=${CONFIG} use-context bootstrap

# Approve all CSRs for the group "system:bootstrappers"
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: auto-approve-csrs-for-group
subjects:
- kind: Group
  name: system:bootstrappers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: system:certificates.k8s.io:certificatesigningrequests:nodeclient
  apiGroup: rbac.authorization.k8s.io
---
# Approve renewal CSRs for the group "system:nodes"
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: auto-approve-renewals-for-nodes
subjects:
- kind: Group
  name: system:nodes
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: system:certificates.k8s.io:certificatesigningrequests:selfnodeclient
  apiGroup: rbac.authorization.k8s.io

cd /kubernetes/config

#kube-controller-manager
kubectl config set-cluster kubernetes \
  --certificate-authority=/kubernetes/ssl/ca.pem \
  --embed-certs=true \
  --server=${APISERVER} --kubeconfig=kube-controller-manager-kubeconfig

kubectl config set-credentials system:kube-controller-manager \
  --client-certificate=/kubernetes/ssl/kube-controller-manager.pem \
  --client-key=/kubernetes/ssl/kube-controller-manager-key.pem \
  --embed-certs=true --kubeconfig=kube-controller-manager-kubeconfig

kubectl config set-context system:kube-controller-manager \
  --cluster=kubernetes \
  --user=system:kube-controller-manager \
  --kubeconfig=kube-controller-manager-kubeconfig

kubectl config use-context system:kube-controller-manager --kubeconfig=kube-controller-manager-kubeconfig

#kube-scheduler
kubectl config set-cluster kubernetes \
  --certificate-authority=/kubernetes/ssl/ca.pem \
  --embed-certs=true \
  --server=${APISERVER} --kubeconfig=kube-scheduler-kubeconfig

kubectl config set-credentials kube-scheduler \
  --client-certificate=/kubernetes/ssl/server.pem \
  --client-key=/kubernetes/ssl/server-key.pem \
  --embed-certs=true --kubeconfig=kube-scheduler-kubeconfig

kubectl config set-context default \
  --cluster=kubernetes \
  --user=system:kube-scheduler \
  --kubeconfig=kube-scheduler-kubeconfig

kubectl config use-context default --kubeconfig=kube-scheduler-kubeconfig

#kube-scheduler
kubectl config set-cluster kubernetes \
  --certificate-authority=/kubernetes/ssl/ca.pem \
  --embed-certs=true \
  --server=${APISERVER} --kubeconfig=kube-proxy-kubeconfig

kubectl config set-credentials kube-proxy-kubeconfig
  --client-certificate=/kubernetes/ssl/kube-proxy.pem \
  --client-key=/kubernetes/ssl/kube-proxy-key.pem \
  --embed-certs=true --kubeconfig=kube-proxy-kubeconfig

kubectl config set-context default \
  --cluster=kubernetes \
  --user=kube-proxy --kubeconfig=kube-proxy-kubeconfig    #systm:kube-proxy?

kubectl config use-context default --kubeconfig=kube-proxy-kubeconfig

# --------------------- 将上面创建的所有kubeconfig文件分发到所有节点:
HOSTS=(
192.168.70.138
192.168.70.140
192.168.70.141
192.168.70.143
)

for IP in ${HOSTS[@]}
do
  scp  /kubernetes/config/*   root@${IP}:/kubernetes/config/
done

# 查看Apiserver注册的集群元数据:
# etcdctl --cacert=/kubernetes/ssl/ca.pem \
#    --endpoints=https://192.168.70.138:2379,https://192.168.70.140:2379,https://192.168.70.141:2379 \
#    get / --prefix --keys-only
```
#### kube-scheduler
```bash
cat > /usr/lib/systemd/system/kube-scheduler.service <<'EOF'
[Unit]
Description=Kubernetes Scheduler
Documentation=https://kubernetes.io/docs/reference/command-line-tools-reference/kube-scheduler

[Service]
ExecStart=/kubernetes/bin/kube-scheduler \
--bind-address=0.0.0.0 \
--logtostderr=false --v=2 \
--kubeconfig=/kubernetes/config/kube-scheduler-kubeconfig \
--leader-elect=true \
--log-dir=/kubernetes/logs

Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload && systemctl enable kube-scheduler --now 
```
#### kube-controller-manager
```bash
cat > /usr/lib/systemd/system/kube-controller-manager.service <<'EOF'
[Unit]
Description=Kubernetes Controller Manager
Documentation=https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager

[Service]
ExecStart=/kubernetes/bin/kube-controller-manager \
--leader-elect=true \
--logtostderr=false --v=2 --alsologtostderr=true --log-dir=/usr/local/kubernetes/logs \
--cluster-name=kubernetes \
--address=0.0.0.0 --port=10252 \
--bind-address=0.0.0.0 --secure-port=10257 \
--kubeconfig=/kubernetes/config/kube-controller-manager-kubeconfig \
--authentication-kubeconfig=/kubernetes/config/kube-controller-manager-kubeconfig \
--authorization-kubeconfig=/kubernetes/config/kube-controller-manager-kubeconfig \
--allocate-node-cidrs=true --cluster-cidr=172.17.0.0/16 --service-cluster-ip-range=10.0.0.0/24 \
--use-service-account-credentials=true \
--horizontal-pod-autoscaler-use-rest-clients=true \
--horizontal-pod-autoscaler-sync-period=60s \
--cluster-signing-cert-file=/kubernetes/ssl/ca.pem \
--cluster-signing-key-file=/kubernetes/ssl/ca-key.pem \
--feature-gates=RotateKubeletServerCertificate=true \
--controllers=*,bootstrapsigner,tokencleaner \
--experimental-cluster-signing-duration=87600h0m0s \
--service-account-private-key-file=/kubernetes/ssl/ca-key.pem \
--requestheader-client-ca-file=/kubernetes/ssl/ca.pem \
--root-ca-file=kubernetes/ssl/ca.pem \
--node-monitor-grace-period=40s \
--node-monitor-period=5s \
--pod-eviction-timeout=5m0s

Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable kube-controller-manager --now

#获取当前Leader: kubectl get endpoints kube-controller-manager --namespace=kube-system -o yaml
```
#### superuser...
```
kubectl create clusterrolebinding permissive-anonymous --clusterrole=cluster-admin --user=system:anonymous
kubectl create clusterrolebinding permissive-nodes --clusterrole=cluster-admin --user=system:nodes
kubectl create clusterrolebinding permissive-kube-controller-manager --clusterrole=cluster-admin --user=system:kube-controller-manager
kubectl create clusterrolebinding permissive-serviceaccounts --clusterrole=cluster-admin --group=system:serviceaccounts
kubectl create clusterrolebinding permissive-dashboard --clusterrole=cluster-admin --serviceaccount=kube-system:kubernetes-dashboard
```
#### kubelet
```bash
#列出所有subsystem，检查Node节点是否支持cgroup的pids (推荐使用 CentOS 7.2+ 以上版本，建议: Centos7.4 )
[root@localhost ~]# cat /proc/cgroups
#subsys_name    hierarchy       num_cgroups     enabled
cpuset  4       29      1
cpu     2       94      1
cpuacct 2       94      1
memory  3       94      1
devices 9       94      1
freezer 6       27      1
net_cls 5       27      1
blkio   8       94      1
perf_event      7       27      1
hugetlb 10      27      1
#当前内核版本"3.10.0-327.el7.x86_64"并没有pids支持

#更新内核
[root@localhost ~]# yum list kernel.x86_64  --showduplicates 2> /dev/null |awk '/kernel/{print $2}'
3.10.0-327.el7
3.10.0-957.el7
3.10.0-957.1.3.el7
3.10.0-957.5.1.el7
3.10.0-957.10.1.el7
3.10.0-957.12.1.el7
[root@localhost ~]# yum install kernel-3.10.0-957.12.1.el7
[root@localhost ~]# grub2-editenv list     #升级后查看默认使用的内核是否为3.10.0-957.12.1

#重启后查看内核版本是否支持pids subsystem：---> grep -o pids /proc/cgroups 

[root@localhost ~]# grep CGROUP_HUGETLB /boot/config-3.10.0-957.12.1.el7.x86_64 
CONFIG_CGROUP_HUGETLB=y

mkdir -p /kubernetes/{bin,config,logs,ssl}
echo 'export PATH=$PATH:/kubernetes/bin' >> /etc/profile.d/kubernetes.sh && source /etc/profile
tar -zxf ~/kubernetes-soft/kubernetes-node-linux-amd64.tar.gz -C ~
cp ~/kubernetes/node/bin/kubelet /kubernetes/bin/

systemctl stop docker

cat> /kubernetes/config/kubelet-config.yaml <<'EOF'
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
address: 0.0.0.0
port: 10250
readOnlyPort: 10255
cgroupDriver: systemd
clusterDNS: ["10.0.0.2"]
clusterDomain: cluster.local
failSwapOn: false
HealthzBindAddress: 0.0.0.0
HealthzPort: 10248
HairpinMode: promiscuous-bridge
EnforceNodeAllocatable:
  - pods
  - kube-reserved
  - system-reserved
KubeReservedCgroup: /system.slice/kubelet.service
SystemReservedCgroup: /system.slice
KubeReserved:
  cpu: 350m
  memory: 350Mi
  ephemeral-storage: 1Gi
SystemReserved:
  cpu: 350m
  memory: 350Mi
  ephemeral-storage: 1Gi
FeatureGates:
  RotateKubeletClientCertificate: true
  RotateKubeletServerCertificate: true
authentication:
  anonymous:
    enabled: true
EvictionMaxPodGracePeriod: 30
evictionSoft:
  memory.available: <10%
  nodefs.available: <10%
evictionHard:
  memory.available: <7%
  nodefs.available: <7%
EOF

cat > /usr/lib/systemd/system/kubelet.service <<'EOF'
[Unit]
Description=Kubernetes Kubelet
Documentation=https://kubernetes.io/blog/2018/07/11/dynamic-kubelet-configuration/
Documentation=https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/
After=docker.service
Requires=docker.service

[Service]
ExecStartPre=/usr/bin/mkdir -p /sys/fs/cgroup/{cpu,cpuacct,cpuset,memory,systemd}/system.slice/kubelet.service
ExecStart=/kubernetes/bin/kubelet \
--hostname-override=192.168.70.138 \
--bootstrap-kubeconfig=/kubernetes/config/bootstrap-kubeconfig \
--kubeconfig=/kubernetes/config/kubelet.kubeconfig \
--config=/kubernetes/config/kubelet-config.yaml \
--cgroups-per-qos=true \
--logtostderr=false --log-dir=/kubernetes/logs --v=2 \
--enable-load-reader=true \
--allow-privileged=true \
--resolv-conf=/etc/resolv.conf \
--rotate-certificates --rotate-server-certificates \
--pod-infra-container-image=registry.cn-hangzhou.aliyuncs.com/google-containers/pause-amd64:3.0 \
--cert-dir=/kubernetes/config/ssl \
--cni-bin-dir=/kubernetes/bin \
--cni-conf-dir=/kubernetes/config/net.d 

Restart=on-failure
KillMode=process

[Install]
WantedBy=multi-user.target
EOF

#若报告与Qos相关的错误时，确认Docker与Kubelet的驱动为systemd，并关闭两个demon后执行以下命令再重启服务，错误将会消失
rm -rf /var/lib/kubelet/* 
for i in $(systemctl list-unit-files --no-legend --no-pager -l | grep --color=never -o .*.slice | grep kubepod);
do
  systemctl stop $i;
done

systemctl daemon-reload && systemctl enable kubelet --now

# 在Master端签发Kubelet证书:
kubectl get csr | awk 'NR>1{print $1}' | xargs -n 1 kubectl certificate approve
```
#### kube-proxy
```bash
tar -zxf ~/kubernetes-soft/kubernetes-node-linux-amd64.tar.gz -C ~
cp -af ~/kubernetes/node/bin/kube* /kubernetes/bin/

cat > /usr/lib/systemd/system/kube-proxy.service <<'EOF'
[Unit]
Description=Kubernetes Kube-Proxy Server
Documentation=https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/
After=network.target

[Service]
ExecStart=/kubernetes/bin/kube-proxy \
--logtostderr=false --v=2 \
--bind-address=0.0.0.0 \
--cluster-cidr=172.17.0.0/16 \ 
--hostname-override=<当前主机地址> \
--metrics-bind-address=0.0.0.0 --metrics-port=10249 \
--healthz-bind-address=0.0.0.0 --healthz-port=10256 \
--kubeconfig=/kubernetes/config/kube-proxy-bootstrap \
--masquerade-all \
--feature-gates=SupportIPVSProxyMode=true \
--proxy-mode=ipvs \
--ipvs-min-sync-period=5s \
--ipvs-sync-period=5s \
--ipvs-scheduler=rr

Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload && systemctl enable kube-proxy --now
```
#### Flannel
```bash
tar -zxf ~/kubernetes-soft/flannel-v0.11.0-linux-amd64.tar.gz -C ~
cp ~/{flanneld,mk-docker-opts.sh} /kubernetes/bin/

systemctl stop docker

cat > /kubernetes/bin/remove-docker0.sh <<'EOF'
#!/bin/bash
# Delete default docker bridge, so that docker can start with flannel network.
set -e
rc=0
ip link show docker0 >/dev/null 2>&1 || rc="$?"
if [[ "$rc" -eq "0" ]]; then
  ip link set dev docker0 down
  ip link delete docker0
fi
EOF

mkdir -p /run/flannel
chmod +x /kubernetes/bin/remove-docker0.sh
chmod +x /kubernetes/bin/mk-docker-opts.sh 

cat > /usr/lib/systemd/system/flanneld.service <<'EOF'
[Unit]
Description=Flanneld overlay address etcd agent
Documentation=https://github.com/coreos/flannel/blob/master/Documentation/configuration.md
After=network.target
After=network-online.target
Wants=network-online.target
After=etcd.service
Before=docker.service

[Service]
Type=notify
ExecStartPre=/kubernetes/bin/remove-docker0.sh
ExecStart=/kubernetes/bin/flanneld --ip-masq \
-iface=eno16777736 \
-etcd-endpoints=https://192.168.70.138:2379,https://192.168.70.140:2379,https://192.168.70.141:2379 \
-etcd-prefix=/atomic.io/network \
-etcd-cafile=/kubernetes/ssl/ca.pem \
-etcd-certfile=/kubernetes/ssl/server.pem \
-etcd-keyfile=/kubernetes/ssl/server-key.pem

ExecStartPost=/kubernetes/bin/mk-docker-opts.sh -k DOCKER_NETWORK_OPTIONS -d /run/flannel/docker

Restart=always
RestartSec=5
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
RequiredBy=docker.service
EOF

#Docker使用Flannel为当前主机分配的子网
vim /usr/lib/systemd/system/docker.service
[Unit]
............
Requires=flanneld.service

[Service]
............
EnvironmentFile=-/run/flannel/docker
ExecStart=/usr/bin/dockerd $DOCKER_NETWORK_OPTIONS
............

systemctl daemon-reload && systemctl enable flanneld --now
systemctl start docker

[root@node1 ~]# ip addr show flannel.1
6: flannel.1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UNKNOWN 
    link/ether 5e:6d:7e:50:58:d3 brd ff:ff:ff:ff:ff:ff
    inet 172.17.72.0/32 scope global flannel.1
       valid_lft forever preferred_lft forever
    inet6 fe80::5c6d:7eff:fe50:58d3/64 scope link 
       valid_lft forever preferred_lft forever
[root@node1 ~]# ip addr show docker0 
7: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN 
    link/ether 02:42:da:91:e8:84 brd ff:ff:ff:ff:ff:ff
    inet 172.17.72.1/24 brd 172.17.72.255 scope global docker0
       valid_lft forever preferred_lft forever
```
#### Info
```
yum install -y bash-completion
source /usr/share/bash-completion/bash_completion
echo "source <(kubectl completion bash)" >> /etc/profile.d/kube_completion.sh
source /etc/profile

echo 'export KUBECONFIG=/kubernetes/config/kubelet.kubeconfig' >> /etc/profile.d/kubernetes.sh
source /etc/profile.d/kubernetes.sh

[root@node1 ~]# kubectl get cs
NAME                 STATUS    MESSAGE             ERROR
scheduler            Healthy   ok                  
controller-manager   Healthy   ok                  
etcd-1               Healthy   {"health":"true"}   
etcd-0               Healthy   {"health":"true"}   
etcd-2               Healthy   {"health":"true"} 

[root@node1 ~]# kubectl describe service/kubernetes -n default
Name:              kubernetes
Namespace:         default
Labels:            component=apiserver
                   provider=kubernetes
Annotations:       <none>
Selector:          <none>
Type:              ClusterIP
IP:                10.0.0.1
Port:              https  443/TCP
TargetPort:        6443/TCP
Endpoints:         192.168.70.138:6443
Session Affinity:  None
Events:            <none>

[root@node1 ~]# kubectl get endpoints kubernetes 
NAME         ENDPOINTS             AGE
kubernetes   192.168.70.138:6443   166m

[root@node1 ~]# kubectl get service
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
kubernetes   ClusterIP   10.0.0.1     <none>        443/TCP   167m
```