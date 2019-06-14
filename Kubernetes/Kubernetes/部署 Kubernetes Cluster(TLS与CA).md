```bash
Etcd:           https://github.com/etcd-io/etcd/releases
Flannel:        https://github.com/coreos/flannel/releases
Kubernetes:     https://github.com/kubernetes/kubernetes/releases
Core-DNS:       https://github.com/coredns/deployment/blob/master/kubernetes/CoreDNS-k8s_version.md

[root@node1 ~]# ll ~/kubernetes-soft/*
-rw-r--r-- 1 root root  17109361 May  3 02:35 /root/kubernetes-soft/cni-plugins-amd64-v0.7.5.tgz
-rw-r--r-- 1 root root  11350736 Apr 20 20:26 /root/kubernetes-soft/etcd-v3.3.12-linux-amd64.tar.gz
-rw-r--r-- 1 root root   9565743 Apr 20 23:55 /root/kubernetes-soft/flannel-v0.11.0-linux-amd64.tar.gz
-rw-r--r-- 1 root root  13409649 Apr 20 20:07 /root/kubernetes-soft/kubernetes-client-linux-amd64.tar.gz
-rw-r--r-- 1 root root  97375408 Apr 20 20:21 /root/kubernetes-soft/kubernetes-node-linux-amd64.tar.gz
-rw-r--r-- 1 root root 449362332 Apr 20 20:11 /root/kubernetes-soft/kubernetes-server-linux-amd64.tar.gz
```
#### 初始化集群环境
```bash
hostnamectl --static set-hostname <NODE_NAME>
chmod a+x /etc/rc.d/rc.local

setenforce 0
sed -i.bak "s/^SELINUX=.*/SELINUX=disabled/g" /etc/sysconfig/selinux /etc/selinux/config

systemctl stop firewalld --now &&  systemctl --failed
iptables -F

yum -y install epel-release
yum -y install yum-utils chrony lvm2 git jq unzip ipset ipvsadm conntrack libseccomp
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum -y install device-mapper-persistent-data docker-ce        #Docker要求Linux内核版本3.10+

timedatectl set-timezone Asia/Shanghai
systemctl enable chronyd --now &&  systemctl --failed

modprobe br_netfilter
modprobe bridge
modprobe ip_vs

sysctl -w vm.swappiness=0
sed -i.bak "/swap/s/\(.*\)/#\1/g" /etc/fstab && swapoff -a

ulimit -n 655350

cat > /etc/sysctl.d/kubernetes.conf <<'EOF'
net.bridge.bridge-nf-call-ip6tables=1
net.bridge.bridge-nf-call-iptables=1
net.netfilter.nf_conntrack_max=2310720
net.ipv4.ip_local_port_range=15000 64000
fs.file-max=6553500
fs.nr_open=6553500
fs.inotify.max_user_watches=89100
net.ipv4.ip_forward=1
net.ipv4.tcp_tw_recycle=0
vm.swappiness=0
vm.overcommit_memory=1
vm.panic_on_oom=0
EOF

cat > /etc/security/limits.conf <<'EOF'
* soft nofile 655350
* hard nofile 655350
* soft nproc 655350
* hard nproc 655350
EOF

sysctl -p

#Docker自1.13+开始修改了默认防火墙规则，禁用iptables中filter表的FOWARD链，这会引起跨Node的Pod无法通信:
sed -i '/ExecStart=/iExecStartPost=/usr/sbin/iptables -P FORWARD ACCEPT' /lib/systemd/system/docker.service
         
systemctl daemon-reload
systemctl enable docker --now &&  systemctl --failed

ip addr show docker0
#输出验证：
3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN 
    link/ether 02:42:45:92:2d:b2 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 scope global docker0
       valid_lft forever preferred_lft forever

#在所有节点创建Kubernetes可执行组件、配置、数据存放路径:
mkdir -p /kubernetes/{bin,config,ssl,logs} 

#主机映射
cat >> /etc/hosts <<'EOF'
192.168.70.138  node1 master
192.168.70.139  node2
192.168.70.140  node3
192.168.70.141  node4
EOF
```
#### cfssl
```bash
curl -sL -o /bin/cfssl   https://pkg.cfssl.org/R1.2/cfssl_linux-amd64                    
curl -sL -o /bin/cfssljson   https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64            
curl -sL -o /bin/cfssl-certinfo   https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64
chmod a+x /bin/cfss*

cd /kubernetes/ssl
cfssl print-defaults config > ca-config.json
cfssl print-defaults csr > ca-csr.json

#用户名：admin
#组：system:masters
#绑定：cluster-admin

① O 为 system:masters ，kube-apiserver 收到该证书后将请求的 Group 设置为system:masters；
② 预定义的 ClusterRoleBinding cluster-admin 将 Group system:masters 与Role cluster-admin 绑定，该 Role 授予所有 API的权限；
③ 该证书只会被 kubectl 当做 client 证书使用，所以 hosts 字段为空；


cat > ca-config.json <<'EOF'
{
    "signing": {
        "default": {
            "expiry": "876000h"
        },
        "profiles": {
            "kubernetes": {
                "expiry": "876000h",
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
            "O":"system:masters"
        }
    ]
}
EOF

cfssl gencert -initca ca-csr.json | cfssljson -bare ca -

#将Kubernetes集群所有节点IP/域名写入证书Hosts字段 ( 其主要由etcd集群/API&master/集群的service地址范围等构成 )
cat > server.json <<'EOF'
{
    "CN": "kubernetes",
    "hosts": [
        "192.168.70.138",
        "192.168.70.140",
        "192.168.70.141",
        "192.168.70.143",
        "127.0.0.1",
        "10.0.0.0",
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

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json \
  -profile=kubernetes server.json | cfssljson -bare server

#Client证书不需要hosts字段，可设为："hosts": [] 此证书仅限kube-proxy使用!
cfssl print-defaults csr > kube-proxy.json
#kube-apiserver预定义的 RoleBinding 将 User system:kube-proxy 与 Role system:node-proxier 绑定
#该 Role 授予了调用 kube-apiserver Proxy 相关 API 的权限...
cat > client.json <<'EOF'
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

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json \
   -profile=kubernetes kube-proxy.json | cfssljson -bare kube-proxy

# metrics-server & .... for aggregator API !
cfssl print-defaults csr > aggregator.json

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

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json \
   -profile=kubernetes aggregator.json | cfssljson -bare aggregator

[root@node1 ssl]# ll
total 72
-rw-r--r-- 1 root root  412 May 10 00:23 aggregator.csr
-rw-r--r-- 1 root root  217 May 10 00:23 aggregator.json
-rw------- 1 root root  227 May 10 00:23 aggregator-key.pem            #API聚合使用 ( 预留给API聚合类资源使用! )
-rw-r--r-- 1 root root  765 May 10 00:23 aggregator.pem                #API..... ( 其使用的头部为"aggregator" )
-rw-r--r-- 1 root root  388 May 10 00:19 ca-config.json
-rw-r--r-- 1 root root  428 May 10 00:19 ca.csr
-rw-r--r-- 1 root root  212 May 10 00:19 ca-csr.json
-rw------- 1 root root  227 May 10 00:19 ca-key.pem                    #CA私钥
-rw-r--r-- 1 root root  741 May 10 00:19 ca.pem                        #CA证书
-rw-r--r-- 1 root root  226 May 10 00:21 client.json
-rw-r--r-- 1 root root  505 May 10 00:22 kube-proxy.csr
-rw-r--r-- 1 root root  287 May 10 00:21 kube-proxy.json
-rw------- 1 root root  227 May 10 00:22 kube-proxy-key.pem            #客户端私钥 - kube-proxy
-rw-r--r-- 1 root root  839 May 10 00:22 kube-proxy.pem                #客户端证书 - kube-proxy
-rw-r--r-- 1 root root  720 May 10 00:21 server.csr
-rw-r--r-- 1 root root  583 May 10 00:20 server.json
-rw------- 1 root root  227 May 10 00:21 server-key.pem                #服务端私钥
-rw-r--r-- 1 root root 1046 May 10 00:21 server.pem                    #服务端证书


#将生成的证书及对应的密钥分发到所有节点
for i in {138,140,141,143}
do
  scp /kubernetes/ssl/*  root@192.168.70.${i}:/kubernetes/ssl
done
```
#### etcd cluster
```bash
echo 'export PATH=$PATH:/kubernetes/bin' > /etc/profile.d/kubernetes.sh && source /etc/profile
mkdir -p /var/lib/etcd/
tar -zxf ~/kubernetes-soft/etcd-v3.3.12-linux-amd64.tar.gz -C ~
mv ~/etcd-v3.3.12-linux-amd64/etcd* /kubernetes/bin/

#使用变量获取主机信息导入配置
NODENAME=$(hostnamectl | awk 'NR==1{print $3}')
ETCDADDRESS="$(hostname -i)"

cat > /usr/lib/systemd/system/etcd.service <<EOF
[Unit]
Description=Etcd Server
Documentation=https://coreos.com/etcd/docs/latest/op-guide/configuration.html
After=network.target

[Service]
Type=notify
WorkingDirectory=/var/lib/etcd
Environment=SSL_DIR=/kubernetes/ssl
ExecStart=/kubernetes/bin/etcd \
 --name=${NODENAME} \
 --data-dir=/var/lib/etcd/default.etcd \
 --listen-peer-urls=https://0.0.0.0:2380 \
 --listen-client-urls=https://0.0.0.0:2379 \
 --advertise-client-urls=https://${ETCDADDRESS}:2379 \
 --initial-advertise-peer-urls=https://${ETCDADDRESS}:2380 \
 --initial-cluster=node1=https://x.x.x.x:2380,node2=https://x.x.x.x:2380,node3=https://x.x.x.x:2380 \
 --initial-cluster-token="etcd-cluster" \
 --initial-cluster-state=new \
 --cert-file=${SSL_DIR}/server.pem \
 --key-file=${SSL_DIR}/server-key.pem \
 --peer-cert-file=${SSL_DIR}/server.pem \
 --peer-key-file=${SSL_DIR}/server-key.pem \
 --trusted-ca-file=${SSL_DIR}/ca.pem \
 --peer-trusted-ca-file=${SSL_DIR}/ca.pem

Type=notify
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload && systemctl enable etcd --now &&  systemctl --failed

SSL_DIR=/kubernetes/ssl





```
#### master
```bash
echo 'export PATH=$PATH:/kubernetes/bin' > /etc/profile.d/kubernetes.sh && source /etc/profile
tar -zxf ~/kubernetes-soft/kubernetes-server-linux-amd64.tar.gz -C ~

cd ~/kubernetes/server/bin/
cp -af ./{kube-apiserver,kube-scheduler,kube-controller-manager,kubectl,kubelet}  /kubernetes/bin/

#自动补全
yum install -y bash-completion
source /usr/share/bash-completion/bash_completion 
source <(kubectl completion bash)

cat > /usr/lib/systemd/system/kube-apiserver.service <<'EOF'
[Unit]
Description=Kubernetes API Server
Documentation=https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/
After=network.target

[Service]
ExecStart=/kubernetes/bin/kube-apiserver \

 --etcd-servers=https://192.168.70.138:2379,https://192.168.70.140:2379,https://192.168.70.141:2379 \
 --anonymous-auth=true \
 --advertise-address=0.0.0.0 --bind-address=0.0.0.0 --secure-port=6443 \
 --insecure-bind-address=127.0.0.1 --insecure-port=8080 \
 --allow-privileged=true \
 --authorization-mode=RBAC,Node \
 --enable-bootstrap-token-auth --token-auth-file=/kubernetes/config/token.csv \
 --service-node-port-range=10000-50000 \



Restart=on-failure
RestartSec=5
Type=notify
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

export BOOTSTRAP_Token=$(head -c 16 /dev/urandom | od -An -t x | tr -d ' ')
cat > /kubernetes/config/token.csv <<EOF
${BOOTSTRAP_Token},kubelet-bootstrap,10001,"system:bootstrappers"
EOF

systemctl daemon-reload             
systemctl enable kube-apiserver --now &&  systemctl --failed

#允许用token发起CSR：https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet-tls-bootstrapping/
kubectl create clusterrolebinding kubernetes-bootstrap \
  --clusterrole=system:node-bootstrapper \
  --user=kubelet-bootstrap
#当Kubelet拥有签发的证书后，使用证书中的CN=system:node:(node name)/O=system:nodes的形式发起另一个CSR请求 (共3种CSR)

#创建 kubelet 使用的 bootstrapping kubeconfig
cd /kubernetes/config
export KUBE_APISERVER="https://192.168.70.138:6443"

#集群参数
kubectl config set-cluster bootstrap \
  --certificate-authority=/kubernetes/ssl/ca.pem \
  --embed-certs=true \
  --server=${KUBE_APISERVER} --kubeconfig=bootstrap-kubeconfig 
#客户端认证
kubectl config set-credentials kubelet-bootstrap \
  --token=${BOOTSTRAP_Token} --kubeconfig=bootstrap-kubeconfig
#设置上下文
kubectl config set-context bootstrap \
  --cluster=bootstrap \
  --user=kubelet-bootstrap --kubeconfig=bootstrap-kubeconfig
#默认上下文
kubectl config use-context bootstrap --kubeconfig=bootstrap-kubeconfig

#创建 kube-proxy 使用的 kube-proxy-bootstrap
kubectl config set-cluster kubernetes \
  --certificate-authority=/kubernetes/ssl/ca.pem \
  --embed-certs=true \
  --server=${KUBE_APISERVER} --kubeconfig=kube-proxy-bootstrap

kubectl config set-credentials kube-proxy-bootstrap \
  --client-certificate=/kubernetes/ssl/kube-proxy.pem \
  --client-key=/kubernetes/ssl/kube-proxy-key.pem \
  --embed-certs=true --kubeconfig=kube-proxy-bootstrap

kubectl config set-context default \
  --cluster=kubernetes \
  --user=kube-proxy --kubeconfig=kube-proxy-bootstrap

kubectl config use-context default --kubeconfig=kube-proxy-bootstrap

#创建 kube-scheduler 使用的 kubeconfig
kubectl config set-cluster kubernetes \
  --certificate-authority=/kubernetes/ssl/ca.pem \
  --embed-certs=true \
  --server=${KUBE_APISERVER} --kubeconfig=kube-scheduler.kubeconfig

kubectl config set-credentials kube-scheduler \
  --client-certificate=/kubernetes/ssl/server.pem \
  --client-key=/kubernetes/ssl/server-key.pem \
  --embed-certs=true --kubeconfig=kube-scheduler.kubeconfig

kubectl config set-context default \
  --cluster=kubernetes \
  --user=kubernetes \   #此用户名有影响吗? kubernetes-bootstrap ? [经确认使用的是CRT中的CN字段!,它还需要RBAC...]
  --kubeconfig=kube-scheduler.kubeconfig  #参考:https://www.cnblogs.com/zhaojiankai/p/7853525.html
#尝试，在集群中，为kubernetes创建最高权限，再此时排查问题

kubectl config use-context default --kubeconfig=kube-scheduler.kubeconfig

#创建 kube-controller-manager 使用的 kubeconfig
kubectl config set-cluster kubernetes \
  --certificate-authority=/kubernetes/ssl/ca.pem \
  --embed-certs=true \
  --server=${KUBE_APISERVER}  --kubeconfig=kube-controller-manager.kubeconfig

kubectl config set-credentials kube-controller-manager \
  --client-certificate=/kubernetes/ssl/server.pem \
  --client-key=/kubernetes/ssl/server-key.pem \
  --embed-certs=true  --kubeconfig=kube-controller-manager.kubeconfig

kubectl config set-context default \
  --cluster=kubernetes \
  --user=kubernetes \     #此用户名有影响吗？ kubernetes-bootstrap ? [经确认使用的是CRT中的CN字段!,它还需要RBAC...]
  --kubeconfig=kube-controller-manager.kubeconfig

kubectl config use-context default --kubeconfig=kube-controller-manager.kubeconfig

#分发到所有节点
for i in {138,140,141,143}
do
  scp /kubernetes/config/*  root@192.168.70.${i}:/kubernetes/config
done

# 为server.crt中CN创建超级管理员权限：
kubectl create clusterrolebinding kubernetes-admin --clusterrole=cluster-admin  --user=kubernetes

-------------------------------------------------- exec rbac yaml:
#创建自动批准相关CSR请求的ClusterRoleBinding (1.14+已内置相关ClusterRole)

# enable bootstrapping nodes to create CSR
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: create-csrs-for-bootstrapping
subjects:
- kind: Group
  name: system:bootstrappers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: system:node-bootstrapper
  apiGroup: rbac.authorization.k8s.io
---
# Approve all CSRs for the group "system:bootstrappers"
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
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
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
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

--------------------------------------------------

#部署 Scheduler
cat > /usr/lib/systemd/system/kube-scheduler.service <<'EOF'
[Unit]
Description=Kubernetes Scheduler
Documentation=https://kubernetes.io/docs/reference/command-line-tools-reference/kube-scheduler

[Service]
ExecStart=/kubernetes/bin/kube-scheduler \
--bind-address=0.0.0.0 \
--logtostderr=false --v=4 \
--kubeconfig=/kubernetes/config/kube-scheduler.kubeconfig \
--leader-elect=true \
--log-dir=/kubernetes/logs

Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable kube-scheduler --now &&  systemctl --failed

#部署 controller-manager
cat > /usr/lib/systemd/system/kube-controller-manager.service <<'EOF'
[Unit]
Description=Kubernetes Controller Manager
Documentation=https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager

[Service]
ExecStart=/kubernetes/bin/kube-controller-manager \
 --cluster-name=kubernetes \
 --logtostderr=false --v=4 --alsologtostderr=true \
 --log-dir=/kubernetes/logs \
 --leader-elect=true --leader-elect-renew-deadline=5s --leader-elect-lease-duration=10s \
 --address=0.0.0.0 --port=10252 \
 --bind-address=0.0.0.0 --secure-port=10257 \
 --allocate-node-cidrs=true --cluster-cidr=172.17.0.0/16 --service-cluster-ip-range=10.0.0.0/24 \
 --horizontal-pod-autoscaler-use-rest-clients=true \
 --controllers=*,bootstrapsigner,tokencleaner \
 --requestheader-client-ca-file=/kubernetes/ssl/ca.pem \
 --requestheader-allowed-names=aggregator \
 --requestheader-extra-headers-prefix=X-Remote-Extra- \
 --requestheader-username-headers=X-Remote-User \
 --requestheader-group-headers=X-Remote-Group \
 --kubeconfig=/kubernetes/config/kube-controller-manager.kubeconfig \
 --service-account-private-key-file=/kubernetes/ssl/server-key.pem \
 --use-service-account-credentials=true \
 --cluster-signing-cert-file=/kubernetes/ssl/ca.pem \
 --cluster-signing-key-file=/kubernetes/ssl/ca-key.pem \
 --root-ca-file=/kubernetes/ssl/ca.pem \
 --feature-gates=RotateKubeletServerCertificate=true \
 --experimental-cluster-signing-duration=87600h0m0s

Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable kube-controller-manager --now &&  systemctl --failed
```
#### node
```bash
mkdir -p /kubernetes/{bin,config,logs,ssl}
echo 'export PATH=$PATH:/kubernetes/bin' >> /etc/profile.d/kubernetes.sh && source /etc/profile
tar -zxf ~/kubernetes-soft/kubernetes-node-linux-amd64.tar.gz -C ~
cp ~/kubernetes/node/bin/kubelet /kubernetes/bin/

cat> /kubernetes/config/kubelet-config.yaml <<'EOF'
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
address: 0.0.0.0
port: 10250
readOnlyPort: 10255
cgroupDriver: cgroupfs
clusterDNS: ["10.0.0.2"]
clusterDomain: cluster.local
failSwapOn: false
authentication:
  anonymous:
    enabled: true
evictionHard:
    memory.available:  "200Mi"
EOF

cat > /usr/lib/systemd/system/kubelet.service <<'EOF'
[Unit]
Description=Kubernetes Kubelet
Documentation=https://kubernetes.io/blog/2018/07/11/dynamic-kubelet-configuration/ #Dynamic Kubelet Configuration
Documentation=https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/
After=docker.service
Requires=docker.service

[Service]
ExecStart=/kubernetes/bin/kubelet \
--hostname-override=master \
--cgroups-per-qos=true \
--enforce-node-allocatable=pods \
--logtostderr=false --log-dir=/usr/local/kubernetes --v=4 \
--enable-load-reader=true \
--allow-privileged=true \
--config=/kubernetes/config/kubelet-config.yaml \
--resolv-conf=/etc/resolv.conf \
--hairpin-mode=promiscuous-bridge \
--feature-gates=RotateKubeletClientCertificate=true,RotateKubeletServerCertificate=true \
--rotate-certificates --rotate-server-certificates \
--bootstrap-kubeconfig=/kubernetes/config/bootstrap-kubeconfig \
--pod-infra-container-image=registry.cn-hangzhou.aliyuncs.com/google-containers/pause-amd64:3.0 \
--cert-dir=/kubernetes/config/ssl \
--kubeconfig=/kubernetes/config/kubelet.kubeconfig \
--cni-bin-dir=/kubernetes/bin \
--cni-conf-dir=/kubernetes/config/net.d \
--healthz-port=10248

#--system-reserved=cpu=4,memory=5Gi     #系统预留资源
#--node-labels=key1=value1/key2=value2  #加入集群时自带的Lable
#--register-with-taints=XXX             #加入集群时自带的taint

Restart=on-failure
KillMode=process

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload && systemctl enable kubelet --now

#在这里如果遇到问题，执行下面的命令，但这仅限于在测试环境使用!:
#kubectl create clusterrolebinding system:anonymous  --clusterrole=cluster-admin   --user=system:anonymous

#在Master审批Node加入集群
kubectl get csr
kubectl certificate approve <XXXXID>
kubectl get node

#设置Kubernetes对CNI的支持: 
mkdir -p /kubernetes/config/net.d/
cat > /kubernetes/config/net.d/10-default.conf <<'EOF'
{
        "name": "flannel",
        "type": "flannel",
        "delegate": {
            "bridge": "docker0",
            "isDefaultGateway": true,
            "mtu": 1400
        }
}
EOF

#部署kube-proxy
tar -zxf ~/kubernetes-soft/kubernetes-node-linux-amd64.tar.gz -C ~
cp -af ~/kubernetes/node/bin/kube* /kubernetes/bin/

cat > /usr/lib/systemd/system/kube-proxy.service <<'EOF'
[Unit]
Description=Kubernetes Kube-Proxy Server
Documentation=https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/
After=network.target

[Service]
ExecStart=/kubernetes/bin/kube-proxy \
--logtostderr=false --v=4 \
--bind-address=0.0.0.0 \    #可以吗？？？
--cluster-cidr=172.17.0.0/16 \            #kube-proxy 根据 --cluster-cidr 判断集群内部和外部流量
--hostname-override=192.168.70.138 \
--kubeconfig=/kubernetes/config/kube-proxy-bootstrap \
--masquerade-all \
--feature-gates=SupportIPVSProxyMode=true \
--proxy-mode=ipvs \
--ipvs-min-sync-period=5s \
--ipvs-sync-period=5s \
--ipvs-scheduler=rr

#参数hostname-override必须与kubelet中的一致，否则kube-proxy启动后会找不到该Node从而不会创建任何ipvs规则

Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable kube-proxy --now &&  systemctl --failed

#部署flannel ( Flannel通过Etcd服务维护了一张节点间的路由表 )
#源主机的flanneld服务将原本的数据内容UDP封装后根据自己的路由表投递给目的节点的flanneld服务
#数据到达以后被解包后进入目的节点的flannel0虚拟网卡，然后被转发到目的主机的docker0虚拟网卡
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

chmod +x /kubernetes/bin/remove-docker0.sh
chmod +x /kubernetes/bin/mk-docker-opts.sh 

cat > /usr/lib/systemd/system/flanneld.service <<'EOF'
[Unit]
Description=Flanneld overlay address etcd agent
After=etcd.service
After=network.target
Before=docker.service

[Service]
Type=notify
ExecStartPre=/kubernetes/bin/remove-docker0.sh
ExecStart=/kubernetes/bin/flanneld --ip-masq \
--kube-subnet-mgr \
-iface=eno16777736 \
-etcd-endpoints=https://192.168.70.138:2379,https://192.168.70.140:2379,https://192.168.70.141:2379 \
-etcd-prefix=/atomic.io/network \
-etcd-cafile=/kubernetes/ssl/ca.pem \
-etcd-certfile=/kubernetes/ssl/server.pem \
-etcd-keyfile=/kubernetes/ssl/server-key.pem

ExecStartPost=/kubernetes/bin/mk-docker-opts.sh -k DOCKER_NETWORK_OPTIONS -d /run/flannel/docker

Restart=on-failure

[Install]
WantedBy=multi-user.target
RequiredBy=docker.service
EOF

#配置Docker使用Flannel
vim /usr/lib/systemd/system/docker.service
[Unit]
After=network-online.target firewalld.service flannel.service
Wants=network-online.target
Requires=flanneld.service

[Service]
Type=notify
#EnvironmentFile=-/run/flannel/docker     #老版本
#EnvironmentFile=/run/flannel/subnet.env  #老版本
EnvironmentFile=-/run/flannel/docker 
ExecStart=/usr/bin/dockerd $DOCKER_NETWORK_OPTIONS   #使用flannel定义的网段  ( 检查并确定/run/flannel/docker中的变量名 )


#Flannel CNI集成:
wget https://github.com/containernetworking/plugins/releases/download/v0.7.5/cni-plugins-amd64-v0.7.5.tgz
tar xf ~/cni-plugins-amd64-v0.7.5.tgz -C /kubernetes/bin
chmod +x /kubernetes/bin*

#重启flannel和docker
systemctl daemon-reload
systemctl enable flanneld --now                     #先启动flanneld再启动docker daemon
systemctl restart docker

#发现flanneld生成的IP和Docker的IP在同一个网段即成功，若不通则检查：journalctl -ex -u flanneld -l
[root@node129 ~]# ip addr show
............
3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN 
    link/ether 02:42:45:92:2d:b2 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/24 scope global docker0
       valid_lft forever preferred_lft forever
4: flannel.1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UNKNOWN 
    link/ether 72:75:29:22:86:6e brd ff:ff:ff:ff:ff:ff
    inet 172.17.41.0/32 scope global flannel.1
       valid_lft forever preferred_lft forever
    inet6 fe80::7075:29ff:fe22:866e/64 scope link 
       valid_lft forever preferred_lft forever
............
```
#### 测试
```bash
source <(kubectl completion bash)

#kubectl是Kubernetes中Apiserver的Restful-API接口客户端，它需要通过 "KUBECONFIG" 环境变量读取配置文件
echo 'export KUBECONFIG='/kubernetes/config/kubelet.kubeconfig'' >> /etc/profile.d/kubernetes.sh
source /etc/profile

#这里需要为kubectl创建kubeconfig文件使用加密端口进行通讯，这一步掠过，参考前面

kubectl config view
#输出:
apiVersion: v1
clusters:
- cluster:
    server: http://192.168.70.129:8080
  name: local
contexts:
- context:
    cluster: local
    user: ""
  name: local

#集群各组件状态检查:
systemctl status etcd
systemctl status kube-apiserver
systemctl status kube-scheduler
systemctl status kube-controller-manager
systemctl status kubelet
systemctl status flanneld
systemctl status docker

kubectl cluster-info
#输出:
Kubernetes master is running at http://192.168.70.129:8080

[root@node129 ~]# kubectl describe service/kubernetes -n default
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
Endpoints:         192.168.70.129:6443
Session Affinity:  None
Events:            <none>

kubectl get nodes
#输出:
NAME             STATUS   ROLES    AGE   VERSION
192.168.70.129   Ready    <none>   74m   v1.14.0
192.168.70.130   Ready    <none>   22m   v1.14.0
192.168.70.131   Ready    <none>   20m   v1.14.0
192.168.70.132   Ready    <none>   16m   v1.14.0
192.168.70.133   Ready    <none>   21m   v1.14.0

kubectl get cs
#输出:      
NAME                 STATUS    MESSAGE             ERROR
controller-manager   Healthy   ok                  
etcd-0               Healthy   {"health":"true"}   
scheduler            Healthy   ok 

kubectl version -o json
#输出:
{
  "clientVersion": {
    "major": "1",
    "minor": "14",
    "gitVersion": "v1.14.0",
    "gitCommit": "641856db18352033a0d96dbc99153fa3b27298e5",
    "gitTreeState": "clean",
    "buildDate": "2019-03-25T15:53:57Z",
    "goVersion": "go1.12.1",
    "compiler": "gc",
    "platform": "linux/amd64"
  },
  "serverVersion": {
    "major": "1",
    "minor": "14",
    "gitVersion": "v1.14.0",
    "gitCommit": "641856db18352033a0d96dbc99153fa3b27298e5",
    "gitTreeState": "clean",
    "buildDate": "2019-03-25T15:45:25Z",
    "goVersion": "go1.12.1",
    "compiler": "gc",
    "platform": "linux/amd64"
  }
}

kubectl api-versions
#输出:
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
#### 当部署完成并检查后，再去参考此Github路径下的：部署 CoreDNS 、 Metric Server 、 Example/Prometheus Operator ^-^
#### Istio

#### 恢复车祸现场
```txt
systemctl disable etcd
systemctl disable kube-apiserver
systemctl disable kube-scheduler
systemctl disable kube-controller-manager
systemctl disable kubelet
systemctl disable flanneld
systemctl disable docker

systemctl stop etcd
systemctl stop kube-apiserver
systemctl stop kube-scheduler
systemctl stop kube-controller-manager
systemctl stop kubelet
systemctl stop flanneld
systemctl stop docker

systemctl status etcd
systemctl status kube-apiserver
systemctl status kube-scheduler
systemctl status kube-controller-manager
systemctl status kubelet
systemctl status flanneld
systemctl status docker

rm -rf /var/lib/etcd/*
rm -rf /usr/lib/systemd/system/etcd
rm -rf /usr/lib/systemd/system/kube-apiserver
rm -rf /usr/lib/systemd/system/kube-scheduler
rm -rf /usr/lib/systemd/system/kube-controller-manager
rm -rf /usr/lib/systemd/system/kubelet
rm -rf /usr/lib/systemd/system/flanneld
rm -rf /usr/lib/systemd/system/docker
rm -rf /kubernetes/*
rm -rf /usr/lib/systemd/system/etcd.service
rm -rf /usr/lib/systemd/system/kube-apiserver.service
rm -rf /usr/lib/systemd/system/kube-controller-manager.service
rm -rf /usr/lib/systemd/system/kube-scheduler.service
rm -rf /usr/lib/systemd/system/kubelet.service
rm -rf /usr/lib/systemd/system/kube-proxy.service
rm -rf /usr/lib/systemd/system/flanneld.service

rm -rf /etc/profile.d/kubernetes.sh

yum -y remove docker-ce

注意： 安装docker-ce-17.12.1.ce版本的rpm包时，需给docker.service额外添加$DOCKER_NETWORK_OPTIONS --exec-opt native.cgroupdriver=systemd

kube-apiserver 预定义了一些 RBAC 使用的 RoleBindings:
如 cluster-admin 将 Group system:masters 与 Role cluster-admin 绑定，该 Role 授予了调用kube-apiserver 的所有 API的权限
O 指定该证书的 Group 为 system:masters，kubelet 使用该证书访问 kube-apiserver 时 ，由于证书被 CA 签名，所以认证通过
同时由于证书用户组为经过预授权的 system:masters，所以被授予访问所有 API 的权限；

#遇到的问题：
#https://bugzilla.redhat.com/show_bug.cgi?id=1508040
https://bzdww.com/article/207664/

Kubelet: failed to initialize top level QOS containers
Error reporting when restarting kubelet Failed to start ContainerManager failed to initialise top level QOS containers (see #43856 ), the temporary workaround is:

1.Increase in docker.service configuration --exec-opt native.cgroupdriver=systemd options.
2.Restart the host

This issue was fixed on April 27, 2017 (v1.7.0+, #44940 ). Updating the cluster to a new version will solve this problem.


kubelet

Failed to start ContainerManager failed to initialize top level QOS containers
failed to set supported cgroup subsystems for cgroup [kubepods burstable]: Fail
Failed to find subsystem mount for required subsystem: pids

--cgroups-per-qos=true --enforce-node-allocatable=pods


kubelet遇到这样的报错时：
  kubelet node not found
  kubectl create clusterrolebinding system:anonymous2  --clusterrole=cluster-admin   --user=system:node:master

  Error getting volume limit for plugin kubernetes.io/cinder：


执行kubectl get pods .显示 ： No resources found:
kubectl config set-cluster kubernetes --server=https://192.168.70.138:6443 --certificate-authority=/kubernetes/ssl/ca.pem --embed-certs=true




 clusterroles.rbac.authorization.k8s.io "admin" is forbidden: User "system:kube-controller-manager" cannot update resource "clusterroles" in API group "rbac.authorization.k8s.io" at the cluster scope


16516 reflector.go:126] k8s.io/client-go/informers/factory.go:133: Failed to list *v1beta1.PodDisruptionBudget: poddisruptionbudgets.policy is forbidden: User "system:anonymous" cannot list resource "poddisruptionbudgets" in API group "policy" at the cluster scope




#kubelet:
 Failed to update QoS cgroup configuration
 
 Failed to start ContainerManager failed to initialize top level QOS containers: failed to update top level Burstable QOS cgroup : failed to set supported cgroup subsystems for cgroup [kubepods burstable]: Failed to find subsystem mount for required subsystem: pids




一旦API Server发现client发起的request使用的是service account token的方式，API Server就会自动采用signed bearer token方式进行身份校验。而request就会使用携带的service account token参与验证。该token是API Server在创建service account时用kube-controller-manager启动参数：--service-account-private-key-file指定的私钥签署(sign)的，同时必须指定kube-apiserver参数--service-account-key-file（如果没指定的话，会使用–tls-private-key-file替代）为该私钥对应的公钥，用来在认证阶段验证token（You must pass a service account private key file to the token controller in the controller-manager by using the --service-account-private-key-file option. The private key will be used to sign generated service account tokens. Similarly, you must pass the corresponding public key to the kube-apiserver using the --service-account-key-file option. The public key will be used to verify the tokens during authentication），也就是说该证书对通过CN和O指定了serviceaccount的授权权限。


由于 API Server 是支持多种认证方式的，其中一种就是使用 HTTP 头中的指定字段来进行认证，相关配置如下:
--requestheader-allowed-names stringSlice
    List of client certificate common names to allow to provide usernames in headers specified by --requestheader-username-headers. If empty, any client certificate validated by the authorities in --requestheader-client-ca-file is allowed.
    当指定这个 CA 证书后，则 API Server 使用 HTTP 头进行认证时会检测其 HTTP 头中发送的证书是否由这个 CA 签发；同样它也可独立于其他 CA(可以是个独立的 CA)；
--requestheader-client-ca-file string
    Root certificate bundle to use to verify client certificates on incoming requests before trusting usernames in headers specified by --requestheader-username-headers. WARNING: generally do not depend on authorization being already done for incoming requests.

	KUBELET_ARGS="--cgroup-driver=systemd --runtime-cgroups=/systemd/system.slice --kubelet-cgroups=/systemd/system.slice  --allow-privileged=true --fail-swap-on=false --cluster-dns=10.254.0.2 --bootstrap-kubeconfig=/etc/kubernetes/bootstrap.kubeconfig --kubeconfig=/etc/kubernetes/kubelet.kubeconfig --require-kubeconfig --cert-dir=/etc/kubernetes/ssl --cluster-domain=cluster.local --hairpin-mode promiscuous-bridge --serialize-image-pulls=false"



"--cgroup-driver 配置成 systemd，不要使用cgroup，否则在 CentOS 系统中 kubelet 将启动失败（保持docker和kubelet中的cgroup driver配置一致即可，不一定非使用systemd）


				DOCKER_STORAGE_OPTIONS="--storage-driver overlay "    ？？？？？？？？？？？？？？？？？？
					修改docker pull源 vi /etc/docker/daemon.json

					{ 
						"registry-mirrors":["https://harbor.ztwltech.com"]
					}


				假如你更新kubernetes的证书，只要没有更新token.csv，当重启kubelet后，该node就会自动加入到kuberentes集群中，而不会重新发送certificaterequest，也不需要在master节点上执行kubectl certificate approve操作。前提是不要删除node节点上的/etc/kubernetes/ssl/kubelet*和/etc/kubernetes/kubelet.kubeconfig文件。否则kubelet启动时会提示找不到证书而失败。
				注意： 如果启动kubelet的时候见到证书相关的报错，有个trick可以解决这个问题，可以将master节点上的~/.kube/config文件（该文件在安装kubectl命令行工具这一步中将会自动生成）拷贝到node节点的/etc/kubernetes/kubelet.kubeconfig位置，这样就不需要通过CSR，当kubelet启动后就会自动加入的集群中。


注意： 直接ping ClusterIP是ping不通的，ClusterIP是根据IPtables路由到服务的endpoint上，只有结合ClusterIP加端口才能访问到对应的服务。



-- Unit kube-apiserver.service has begun starting up.
May 10 00:38:41 node1 kube-apiserver[10241]: Flag --enable-swagger-ui has been deprecated, swagger 1.2 support has been removed
May 10 00:38:41 node1 kube-apiserver[10241]: Flag --insecure-bind-address has been deprecated, This flag will be removed in a future version.
May 10 00:38:41 node1 kube-apiserver[10241]: Flag --insecure-port has been deprecated, This flag will be removed in a future version.
May 10 00:38:42 node1 kube-apiserver[10241]: E0510 00:38:42.131114   10241 prometheus.go:138] failed to register depth metric admission_quota_controller: duplicate metrics collector registration attempted
May 10 00:38:42 node1 kube-apiserver[10241]: E0510 00:38:42.135683   10241 prometheus.go:150] failed to register adds metric admission_quota_controller: duplicate metrics collector registration attempted
May 10 00:38:42 node1 kube-apiserver[10241]: E0510 00:38:42.136143   10241 prometheus.go:162] failed to register latency metric admission_quota_controller: duplicate metrics collector registration attempted
May 10 00:38:42 node1 kube-apiserver[10241]: E0510 00:38:42.136225   10241 prometheus.go:174] failed to register work_duration metric admission_quota_controller: duplicate metrics collector registration attempted
May 10 00:38:42 node1 kube-apiserver[10241]: E0510 00:38:42.136252   10241 prometheus.go:189] failed to register unfinished_work_seconds metric admission_quota_controller:
May 10 00:48:38 node1 kube-scheduler[21198]: E0510 00:48:38.212082   21198 reflector.go:126] k8s.io/client-go/informers/factory.go:133: Failed to list *v1.PersistentVolumeClaim: persistentvolumeclaims is forbidden: User "system:anonymous" cannot list resou
May 10 00:48:38 node1 kube-scheduler[21198]: E0510 00:48:38.213050   21198 reflector.go:126] k8s.io/client-go/informers/factory.go:133: Failed to list *v1beta1.PodDisruptionBudget: poddisruptionbudgets.policy is forbidden: User "system:anonymous" cannot li
May 10 00:48:38 node1 kube-scheduler[21198]: E0510 00:48:38.214568   21198 reflector.go:126] k8s.io/client-go/informers/factory.go:133: Failed to list *v1.ReplicaSet: replicasets.apps is forbidden: User "system:anonymous" cannot list resource "replicasets"
May 10 00:48:38 node1 kube-scheduler[21198]: E0510 00:48:38.220870   21198 reflector.go:126] k8s.io/client-go/informers/factory.go:133: Failed to list *v1.ReplicationController: replicationcontrollers is forbidden: User "system:anonymous" cannot list resou
May 10 00:48:38 node1 kube-scheduler[21198]: E0510 00:48:38.222132   21198 reflector.go:126] k8s.io/client-go/informers/factory.go:133: Failed to list *v1.Node: nodes is forbidden: User "system:anonymous" cannot list resource "nodes" in API group "" at the
May 10 00:48:38 node1 kube-scheduler[21198]: E0510 00:48:38.223414   21198 reflector.go:126] k8s.io/client-go/informers/factory.go:133: Failed to list *v1.Service: services is forbidden: User "system:anonymous" cannot list resource "services" in API group 
May 10 00:48:38 node1 kube-scheduler[21198]: E0510 00:48:38.224634   21198 reflector.go:126] k8s.io/client-go/informers/factory.go:133: Failed to list *v1.PersistentVolume: persistentvolumes is forbidden: User "system:anonymous" cannot list resource "persi
May 10 00:48:38 node1 kube-scheduler[21198]: E0510 00:48:38.226078   21198 reflector.go:126] k8s.io/client-go/informers/factory.go:133: Failed to list *v1.StatefulSet: statefulsets.apps is forbidden: User "system:anonymous" cannot list resource "statefulse
May 10 00:48:39 node1 kube-scheduler[21198]: E0510 00:48:39.211692   21198 reflector.go:126] k8s.io/client-go/informers/factory.go:133: Failed to list *v1.StorageClass: storageclasses.storage.k8s.io is forbidden: User "system:anonymous" cannot list resourc


May 10 00:50:12 node1 kube-controller-manager[21287]: W0510 00:50:12.442669   21287 authentication.go:249] No authentication-kubeconfig provided in order to lookup client-ca-file in configmap/extension-apiserver-authentication in kube-system, so client cer
May 10 00:50:12 node1 kube-controller-manager[21287]: W0510 00:50:12.443139   21287 authorization.go:146] No authorization-kubeconfig provided, so SubjectAccessReview of authorization tokens won't work.
May 10 00:50:12 node1 kube-controller-manager[21287]: I0510 00:50:12.443163   21287 controllermanager.go:155] Version: v1.14.0
May 10 00:50:12 node1 kube-controller-manager[21287]: I0510 00:50:12.443989   21287 secure_serving.go:116] Serving securely on [::]:10257
May 10 00:50:12 node1 kube-controller-manager[21287]: I0510 00:50:12.444498   21287 deprecated_insecure_serving.go:51] Serving insecurely on [::]:10252
May 10 00:50:12 node1 kube-controller-manager[21287]: I0510 00:50:12.444957   21287 leaderelection.go:217] attempting to acquire leader lease  kube-system/kube-controller-manager...
May 10 00:50:12 node1 kube-controller-manager[21287]: E0510 00:50:12.455934   21287 leaderelection.go:306] error retrieving resource lock kube-system/kube-controller-manager: endpoints "kube-controller-manager" is forbidden: User "system:anonymous" cannot 
May 10 00:50:12 node1 kube-controller-manager[21287]: I0510 00:50:12.456124   21287 leaderelection.go:222] failed to acquire lease kube-system/kube-controller-manager
May 10 00:50:15 node1 kube-controller-manager[21287]: E0510 00:50:15.869278   21287 leaderelection.go:306] error retrieving resource lock kube-system/kube-controller-manager: endpoints "kube-controller-manager" is forbidden: User "system:anonymous" cannot 
May 10 00:50:15 node1 kube-controller-manager[21287]: I0510 00:50:15.869315   21287 leaderelection.go:222] failed to acquire lease kube-system/kube-controller-manager
May 10 00:50:19 node1 kube-controller-manager[21287]: E0510 00:50:19.837661   21287 leaderelection.go:306] error retrieving resource lock kube-system/kube-controller-manager: endpoints "kube-controller-manager" is forbidden: User "system:anonymous" cannot 
May 10 00:50:19 node1 kube-controller-manager[21287]: I0510 00:50:19.837700   21287 leaderelection.go:222] failed to acquire lease kube-system/kube-controller-manager
May 10 00:50:22 node1 kube-controller-manager[21287]: E0510 00:50:22.604189   21287 leaderelection.go:306] error retrieving resource lock kube-system/kube-controller-manager: endpoints "kube-controller-manager" is forbidden: User "system:anonymous" cannot 
May 10 00:50:22 node1 kube-controller-manager[21287]: I0510 00:50:22.604213   21287 leaderelection.go:222] failed to acquire lease kube-system/kube-controller-manager
May 10 00:50:26 node1 kube-controller-manager[21287]: E0510 00:50:26.138856   21287 leaderelection.go:306] error retrieving resource lock kube-system/kube-controller-manager: endpoints "kube-controller-manager" is forbidden: User "system:anonymous" cannot 
May 10 00:50:26 node1 kube-controller-manager[21287]: I0510 00:50:26.138935   21287 leaderelection.go:222] failed to acquire lease kube-system/kube-controller-manager
May 10 00:50:29 node1 kube-controller-manager[21287]: E0510 00:50:29.690933   21287 leaderelection.go:306] error retrieving resource lock kube-system/kube-controller-manager: endpoints "kube-controller-manager" is forbidden: User "system:anonymous" cannot 
May 10 00:50:29 node1 kube-controller-manager[21287]: I0510 00:50:29.690973   21287 leaderelection.go:222] failed to acquire lease kube-system/kube-controller-manager
May 10 00:50:31 node1 kube-controller-manager[21287]: E0510 00:50:31.822496   21287 leaderelection.go:306] error retrieving resource lock kube-system/kube-controller-manager: endpoints "kube-controller-manager" is forbidden: User "system:anonymous" cannot 
May 10 00:50:31 node1 kube-controller-manager[21287]: I0510 00:50:31.822533   21287 leaderelection.go:222] failed to acquire lease kube-system/kube-controller-manager


1408374, loc:(*time.Location)(0x7ff88e0)}}, LastTimestamp:v1.Time{Time:time.Time{wall:0xbf2d351cca054307, ext:321408374, loc:(*time.Location)(0x7ff88e0)}}, Count:1, Type:"Normal", EventTime:v1.MicroTime{Time:time.Time{wall:0x0, ext:0, loc:(*time.Location)(nil)}}, Series:(*v1.EventSeries)(nil), Action:"", Related:(*v1.ObjectReference)(nil), ReportingController:"", ReportingInstance:""}': 'events is forbidden: User "system:anonymous" cannot create resource "events" in API group "" in the namespace "default"' (will not retry!)
F0510 01:01:39.196179   12233 kubelet.go:1359] Failed to start ContainerManager failed to initialize top level QOS containers: failed to update top level Burstable QOS cgroup : failed to set supported cgroup subsystems for cgroup [kubepods burstable]: Failed to find subsystem mount for required subsystem: pids
goroutine 256 [running]:


Failed to start ContainerManager failed to initialize top level QOS containers: failed to update top level Burstable QOS cgroup : failed to set supported cgroup subsystems for cgroup [kubepods burstable]: Failed to find subsystem mount for required subsystem: pids











从 v1.10 开始，kubelet 部分参数需在配置文件中配置，kubelet --help 会提示：  eg: --config=/opt/k8s/kubelet.config.json 

DEPRECATED: This parameter should be set via the config file specified by the Kubelet's --config flag
[root@kube-master ~]# mkdir /opt/kubelet
[root@kube-master ~]# cd /opt/kubelet
[root@kube-master kubelet]# vim kubelet.config.json.template

{
  "kind": "KubeletConfiguration",
  "apiVersion": "kubelet.config.k8s.io/v1beta1",
  "authentication": {
    "x509": {
      "clientCAFile": "/opt/k8s/cert/ca.pem"
    },
    "webhook": {
      "enabled": true,
      "cacheTTL": "2m0s"
    },
    "anonymous": {
      "enabled": false
    }
  },
  "authorization": {
    "mode": "Webhook",
    "webhook": {
      "cacheAuthorizedTTL": "5m0s",
      "cacheUnauthorizedTTL": "30s"
    }
  },
  "address": "##NODE_IP##",
  "port": 10250,
  "readOnlyPort": 0,
  "cgroupDriver": "cgroupfs",
  "hairpinMode": "promiscuous-bridge",
  "serializeImagePulls": false,
  "featureGates": {
    "RotateKubeletClientCertificate": true,
    "RotateKubeletServerCertificate": true
  },
  "clusterDomain": "cluster.local",
  "clusterDNS": ["10.90.0.2"]
}
```