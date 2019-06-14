#### Token &TLS Bootstrapping
```bash
#支持由 Apiserver 为客户端生成 TLS 证书的 TLS Bootstrapping 功能，这样就不需要为每个客户端生成证书了
#通过在证书里指定相关的User、Group来达到通过RBAC授权的目的 ( 当TLS解决了通讯问题后，权限问题就由RBAC解决 )
#RBAC中规定了用户或用户组(subject)具有请求哪些 api 的权限:
#在配合TLS加密时，实际上Apiserver读取客户端证书的CN字段作为用户名，读取O字段作为用户组

#自动签发证书的流程说明：
# 1. Kubelet想要与Apiserver通讯就必须采用由Apiserver CA签发的证书，这样才能形成信任关系并建立TLS连接
# 2. Kubelet通过证书中的的 "CN"、"O" 字段来提供RBAC (认证/授权) 所需的用户、组
# 3. 在Apiserver参数/配置文件中指定Token.csv ，该文件中是预设的用户配置，格式为: 【Token,用户名,UID,用户组】
#    用户的Token和Apiserver的CA证书被写入kubelet与Apiserver通讯所使用的"bootstrap.kubeconfig"配置文件中
#    kubelet首次请求时使用"bootstrap.kubeconfig"中的Apiserver CA证书来与Apiserver建立TLS通讯
#    kubelet使用"bootstrap.kubeconfig"中的用户Token向Apiserver声明自己的RBAC授权身份，此Token中有其用户身份及所属组
# 4. kubelet首次启动后，如果用户Token没问题并且RBAC也做了相应的设置，那么此时在集群内应该能看到kubelet发起的CSR请求
#    出现CSR请求后可使用kubectl手动签发 (允许) kubelet的证书 (发起的CSR请求是由kube-controller-manager来做实际签署的)
#    首次启动时可能会遇到kubelet报401无权访问Apiserver的错误，这是因为在默认情况下kubelet通过bootstrap.kubeconfig
#    中的预设用户Token声明了自己的身份，而后使用此身份创建CSR请求，但不要忘记此用户在我们不处理的情况下是没任何权限的
#    包括创建 CSR 请求，所以需要执行命令创建 "ClusterRoleBinding"
#    将预设的用户"kubelet-bootstrap"与内置的 ClusterRole: "system:node-bootstrapper" 绑定，使其能够发起CSR请求:
#    kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper \
#    --user=kubelet-bootstrap       #( --user=参数指定的用户名即Token.csv中指定的用户名:kubelet-bootstrap )
# 5. 当成功签发证书后，目标节点的kubelet会将证书写入到"--cert-dir="指定的目录；注意此时如果不做其他设置应当生成4个文件

#bootstrap.kubeconfig：
#该文件中内置了Token.csv中用户的Token，以及Apiserver CA证书。kubelet首次启动会加载此文件
#使用Apiserver CA证书建立与Apiserver的TLS通讯，使用其中的用户Token作为身份标识像Apiserver发起CSR请求

#Token.csv文件内的Token可以是任意包涵128 bit的字符串，推荐使用安全的随机数发生器生成
#此文件格式为:Token,用户名,UID,用户在K8S中所属的组，此文件在Apiserver启动时被加载，而后就相当于在集群内创建了这个用户
#接下来即可使用RBAC对此用户"kubelet-bootstrap"或组:"system:kubelet-bootstrap"进行授权
export BOOTSTRAP_Token=$(head -c 16 /dev/urandom | od -An -t x | tr -d ' ')
cat > Token.csv <<EOF
${BOOTSTRAP_Token},kubelet-bootstrap,10001,"system:kubelet-bootstrap"
EOF

#将Token.csv发到所有Master和Node的/etc/kubernetes/目录
scp Token.csv /etc/kubernetes/

# 创建 Kuberlet 使用的 bootstrapping kubeconfig 文件
$ cd /etc/kubernetes
$ export KUBE_Apiserver="https://172.20.0.113:6443"
# 设置集群参数
$ kubectl config set-cluster kubernetes \                   #为集群定义的标识
  --certificate-authority=/etc/kubernetes/ssl/ca.pem \      #CA证书路径
  --embed-certs=true \                      #将certificate-authority证书写入到生成的bootstrap.kubeconfig
  --server=${KUBE_Apiserver} \              #Apiserver的地址
  --kubeconfig=bootstrap.kubeconfig         #使用的生成的bootstrap.kubeconfig文件，里面存有认证信息
# 设置客户端认证参数                          #设置客户端认证参数时没有指定秘钥和证书，后续由 Apiserver 自动生成
$ kubectl config set-credentials kubelet-bootstrap \        #
  --token=${BOOTSTRAP_Token} \                              #使用之前在Token.csv中随机生成的Token
  --kubeconfig=bootstrap.kubeconfig
$ # 设置上下文参数
$ kubectl config set-context default \                      #定义名为defult的集群上下文
  --cluster=kubernetes \                                    #定义其使用的集群标识，其指向了一个Apiserver
  --user=kubelet-bootstrap \                                #指定kubelet使用的用于名
  --kubeconfig=bootstrap.kubeconfig                         #里面存有认证信息
# 设置默认上下文
$ kubectl config use-context default --kubeconfig=bootstrap.kubeconfig

#创建 kube-proxy 使用的 bootstrapping kubeconfig 文件
$ export KUBE_Apiserver="https://172.20.0.113:6443"
$ # 设置集群参数
$ kubectl config set-cluster kubernetes \
  --certificate-authority=/etc/kubernetes/ssl/ca.pem \
  --embed-certs=true \                                      #是否在kubeconfig配置文件中嵌入客户端证书/key
  --server=${KUBE_Apiserver} \
  --kubeconfig=kube-proxy.kubeconfig
# 设置客户端认证参数
$ kubectl config set-credentials kube-proxy \
  --client-certificate=/etc/kubernetes/ssl/kube-proxy.pem \
  --client-key=/etc/kubernetes/ssl/kube-proxy-key.pem \
  --embed-certs=true \
  --kubeconfig=kube-proxy.kubeconfig
# 设置上下文参数
$ kubectl config set-context default \
  --cluster=kubernetes \
  --user=kube-proxy \
  --kubeconfig=kube-proxy.kubeconfig
# 设置默认上下文
$ kubectl config use-context default --kubeconfig=kube-proxy.kubeconfig

#设置集群参数和客户端认证参数 --embed-certs 都为 true 时：
#会将certificate-authority、client-certificate、client-key 写入到生成的 kube-proxy.kubeconfig 文件中

#kube-proxy.pem证书中CN为"system:kube-proxy"此用户名是Kubernetes预设的
#kube-Apiserver预定义的RoleBinding cluster-admin将Usersystem:kube-proxy与Role system:node-proxier进行了绑定
#该Role授予了调用kube-Apiserver Proxy相关API的权限...

#分发kubeconfig文件:
#将两个kubeconfig文件分发到所有Node机器的/etc/kubernetes/目录...

#注:
#每个Kubernetes集群都有一个集群根证书颁发机构（CA）。集群中各组件通常用CA来验证API server的证书，由Apiserver验证组件。
#为了支持这一点，CA证书包被分发到集群中的每个节点，并作为secret附加分发到默认serviceaccount上
#想要与Apiserver通讯就必须采用由Apiserver CA签发的证书，这样才能形成信任关系建立TLS连接
#证书的CN、O字段来提供RBAC所需的用户与用户组
#kubelet发起的CSR请求都是由controller manager来做实际签署的
```
#### 手动签发
```bash
#在kubelet首次启动后，如果用户Token没问题且RBAC也做了相应的设置，那么此时在集群内应该能看到kubelet发起的CSR请求
#必须通过后kubernetes才会将该Node加入到集群。

#查看未授权的CSR请求
[root@localhost ~]# kubectl get csr
NAME                                                   AGE       REQUESTOR           CONDITION
node-csr--k3G2G1EoM4h9w1FuJRjJjfbIPNxa551A8TZfW9dG-g   2m        kubelet-bootstrap   Pending
[root@localhost ~]# kubectl get nodes
No resources found.

#通过CSR请求
[root@localhost ~]# kubectl certificate approve node-csr--k3G2G1EoM4h9w1FuJRjJjfbIPNxa551A8TZfW9dG-g
certificatesigningrequest "node-csr--k3G2G1EoM4h9w1FuJRjJjfbIPNxa551A8TZfW9dG-g" approved
[root@localhost ~]# kubectl get nodes
NAME            STATUS    ROLES     AGE       VERSION
172.20.95.174   Ready     <none>    48s       v1.10.0

#上面的操作将自动生成kubelet kubeconfig文件和公私钥：(存放路径为kubelet参数"--cert-dir="指定的目录)
[root@localhost ~]# ls -l /etc/kubernetes/kubelet.kubeconfig
-rw------- 1 root root 2280 Nov  7 10:26 /etc/kubernetes/kubelet.kubeconfig
[root@localhost ~]# ls -l /etc/kubernetes/ssl/kubelet*
-rw-r--r-- 1 root root 1046 Nov  7 10:26 /etc/kubernetes/ssl/kubelet-client.crt
-rw------- 1 root root  227 Nov  7 10:22 /etc/kubernetes/ssl/kubelet-client.key
-rw-r--r-- 1 root root 1115 Nov  7 10:16 /etc/kubernetes/ssl/kubelet.crt
-rw------- 1 root root 1675 Nov  7 10:16 /etc/kubernetes/ssl/kubelet.key

#-----------------------------------------------------------------------------------
# kubelet-client.crt      kubelet与apiserver通讯所使用的证书
# kubelet-client.key      kubelet与apiserver通讯所使用的私钥
# kubelet.crt             被用于kubelet server (10250) 做鉴权使用，这个证书是独立于Apiserver CA的自签 CA \
# kubelet.key             并且删除后 kubelet 组件会重新生成它
#-----------------------------------------------------------------------------------
```
#### 自动签发
```bash
#kubelet首次启动时会发起CSR请求，如果未做任何配置则需要手动签发，若集群庞大那么手动签发的请求就会很多
#kubelet所发起的CSR请求是由controller manager签署的；若想实现自动签发，就需让其能在kubelet发起CSR时自动签署证书
#那么controller manager不可能对所有的CSR申请都自动签署，这时就需要配置RBAC规则
#保证controller manager只对kubelet发起的特定CSR请求自动批准即可
#针对上面 提出的 3 种 CSR 请求分别给出了 3 种对应的 ClusterRole：如下示例:
#RBAC中ClusterRole只是描述或者说定义一种集群范围内的能力，这3个在 1.7之前需手动创建，在1.8后Apiserver自动创建前2个!

# A ClusterRole which instructs the CSR approver to approve a user requesting node client credentials.
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: approve-node-client-csr                 #证书签发使用，具有自动批准nodeclient类型CSR请求的能力
rules:
- apiGroups: ["certificates.k8s.io"]
  resources: ["certificatesigningrequests/nodeclient"]
  verbs: ["create"]
---
# A ClusterRole which instructs the CSR approver to approve a node renewing its own client credentials.
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: approve-node-client-renewal-csr         #具有自动批准selfnodeclient类型CSR请求的能力
rules:
- apiGroups: ["certificates.k8s.io"]
  resources: ["certificatesigningrequests/selfnodeclient"]
  verbs: ["create"]
---
# A ClusterRole which instructs the CSR approver to approve a node requesting a
# serving cert matching its client cert.
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: approve-node-server-renewal-csr         #具有自动批准selfnodeserver类型CSR请求的能力
rules:
- apiGroups: ["certificates.k8s.io"]
  resources: ["certificatesigningrequests/selfnodeserver"]
  verbs: ["create"]

#所以若想要kubelet能自动签发，那么就应当将适当的ClusterRole绑定到kubelet自动续期时所所采用的用户或者用户组身上

#CluserRole绑定:
#要实现自动签发，创建的RBAC规则则至少能满足四种情况:
自动批准kubelet首次用于与apiserver通讯证书的CSR请求(nodeclient)
自动批准kubelet首次用于10250端口鉴权的CSR请求(实际上这个请求走的也是selfnodeserver类型CSR)

#自动批准kubelet的首次CSR请求(用于与apiserver通讯的证书)
kubectl create clusterrolebinding node-client-auto-approve-csr  \
   --clusterrole=approve-node-client-csr --group=system:bootstrappers

#自动批准kubelet发起的用于10250端口鉴权证书的CSR请求(包括后续renew)
kubectl create clusterrolebinding node-server-auto-renew-crt \
   --clusterrole=approve-node-server-renewal-csr --group=system:nodes
```
#### 证书轮换
```txt
#开启证书轮换下的引导过程:   ( 使用证书轮换的前提是启用证书的自动签发 )
 1.kubelet读取bootstrap.kubeconfig，使用其CA与Token向apiserver发起第一次CSR请求 (nodeclient)
 2.apiserver根据RBAC规则手动/自动批准首次CSR请求(approve-node-client-csr)，并下发证书 (kubelet-client.crt)
 3.kubelet用刚刚签发的证书(O=system:nodes, CN=system:node:NODE_NAME)与apiserver通讯并发起申请10250 server所使用证书的CSR请求
 4.Apiserver根据RBAC规则自动批准kubelet为其10250端口申请的证书 (kubelet-server-current.crt)
 5.证书即将到期时kubelet自动向apiserver发起用于与apiserver通讯所用证书的renew CSR请求和renew本身 10250端口所用证书的CSR请求
 6.apiserver根据RBAC规则自动批准两个证书
 7.kubelet拿到新证书后关闭所有连接，reload新证书，以后便一直如此

#从以上流程可以看出实现证书轮换创建的RBAC规则，则至少能满足四种情况:
 1.自动批准kubelet首次用于与apiserver通讯证书的CSR请求(nodeclient)
 2.自动批准kubelet首次用于10250端口鉴权的CSR请求(实际上这个请求走的也是 selfnodeserver 类型CSR)
 3.自动批准kubelet后续renew用于与apiserver通讯证书的CSR请求(selfnodeclient)
 4.自动批准kubelet后续renew用于10250端口鉴权的CSR请求(selfnodeserver)

#基于以上四种情况，我们只需在开启了自动签发的基础增加一个ClusterRoleBinding：
#自动批准kubelet后续renew用于与apiserver通讯证书的CSR请求
kubectl create clusterrolebinding node-client-auto-renew-crt --clusterrole=approve-node-client-renewal-csr --group=system:nodes

#开启证书轮换的配置
kubelet启动时增加--feature-gates=RotateKubeletClientCertificate=true,RotateKubeletServerCertificate=true选项
则kubelet在证书即将到期时会自动发起一个renew自己证书的CSR请求；增加--rotate-certificates参数，kubelet会自动重载新证书
同时controller manager需要在启动时增加--feature-gates=RotateKubeletServerCertificate=true参数
再配合上面创建好的ClusterRoleBinding，kubelet client和kubelet server证才书会被自动签署；

#证书过期时间
TLS bootstrapping时的证书实际是由kube-controller-manager组件来签署的，就是说有效期是kube-controller-manager控制的
#kube-controller-manager组件提供了--experimental-cluster-signing-duration参数来设置签署的证书有效时间；默认8760h0m0s
#将其改为87600h0m0s即10年后再进行TLS bootstrapping签署证书即可
```
#### TLS Bootstrapping
```bash
kubelet首次启动通过加载bootstrap.kubeconfig中的用户Token和apiserver CA证书发起首次CSR请求
这个Token被预先内置在apiserver节点的token.csv中，其身份为kubelet-bootstrap用户和system:bootstrappers用户组
想要首次CSR请求能成功 (成功指的是不会被 apiserver 401 拒绝)
则需要先将kubelet-bootstrap用户和system:node-bootstrapper内置 ClusterRole 绑定；

对于首次CSR请求可以手动签发，也可以将system:bootstrappers用户组与approve-node-client-csr ClusterRole绑定实现自动签发

默认签署的的证书只有1年有效期，如果想要调整证书有效期可以通过设置kube-controller-manager的--experimental-cluster-signing-duration参数实现，默认为8760h0m0s

发起续期请求，则需要在 kubelet 启动时增加:
--feature-gates=RotateKubeletClientCertificate=true,RotateKubeletServerCertificate=true来实现；
想要让controller manager自动批准续签的 CSR 请求需要在 controller manager 启动时增加 
--feature-gates=RotateKubeletServerCertificate=true 参数，并绑定对应的 RBAC 规则
```