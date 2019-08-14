#### Role & ClusterRole
```bash
#角色 "Role" 代表权限集合，权限只有被授予，而没有被拒绝的设置
#在Kubernetes中有2类角色: 普通的属于名称空间内的角色:"Role"、属于集群级别的角色:"ClusterRole"
#通过Role定义在某个命名空间内的角色，或使用ClusterRole定义作用于整个集群范围内的角色

---------------------------------------------------------------------------------
#Example:  下面定义的角色能在default名称空间内访问Pod及Pod下的log子资源，但不能创建或修改Pod资源

kind: Role                                          #普通角色
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: default                                #Role所属的名称空间
  name: pod-reader                                  #角色名字
rules:
- apiGroups: [""]                                   #API组，如果是核心API组，则为空
  resources: ["pods","pods/log"]                    #API组之下的资源类型
  verbs: ["get", "watch", "list"]                   #能够对此资源进行的各类CRUD操作的清单

---------------------------------------------------------------------------------
#Example:  ClusterRole能访问集群范围的资源（类似于Node）、非资源端点（类似于"/healthz"）、集群中所有命名空间的资源

kind: ClusterRole                                   #其本身的作用范围是集群级别
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: secret-reader                               #元数据中只有其名字而没有所属名称空间，因为它是集群级别的
rules:
- apiGroups: [""]
  resources: ["secrets"]                            #明确资源类型，授予集群角色读取秘密字典文件访问权限
  verbs: ["get","watch","list"]                     #定义可以对此资源进行的CRUD操作

---------------------------------------------------------------------------------
#Example:   创建服务账户

apiVersion: v1
kind: ServiceAccount                                #服务账户的资源类型为:"ServiceAccount"
metadata:
  name: admin-user                                  #服务账户名称
  namespace: kube-system                            #所属名称空间

#注：
#指定ServiceAccount创建的Pod实例会自动将用于访问Kubernetes API的CA证书及当前账户对应的访问令牌文件挂载到Pod实例的
#/var/run/secrets/kubernetes.io/serviceaccount/目录下
```
#### RoleBinding & ClusterRoleBinding
```bash
#角色绑定用于将角色与一个或一组用户进行绑定从而实现将对用户进行授权的目的
#授权的主体分为：用户、组、服务帐户。绑定分为: 普通角色绑定、集群角色绑定。其中角色绑定只能关联属于同一命名空间的Role

---------------------------------------------------------------------------------
#Example:   在"default"命名空间中角色绑定将"jane"用户和"pod-reader"角色进行了绑定
            #This role binding allows "jane" to read pods in the "default" namespace...

kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: read-pods                                   #名称
  namespace: default                                #此绑定特定于哪个名称空间（在哪个名称空间中进行绑定）
subjects:                                           #主体
- kind: User                                        #绑定的主体的类型为"用户"，此外还有User Group、Service Account
  name: jane                                        #因绑定的主题类型为用户，这里即用户名，若使用CRT证书则使用CN字段
  apiGroup:rbac.authorization.k8s.io
roleRef:                                            #这里的"roleRef"段即关联角色/集群角色
  kind: Role                                        #关联的角色类型为Role，此外还有ClusterRole...
  name: pod-reader                                  #关联的Role的名称
  apiGroup: rbac.authorization.k8s.io

---------------------------------------------------------------------------------
#Example:   虽然是引用了集群角色的权限，但是其所属名称空间为"development"因此其进作用于此名称空间内
            # This role binding allows "dave" to read secrets in the "development" namespace.

kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: read-secrets                                #名称
  namespace: development                            #这里仅授予访问"development"名称空间的权限
subjects:                                           #主体 ( 主体可以是用户、组、服务帐户 )
- kind: User                                        #主体类型为用户
  name: dave                                        #用户名，此名称可由APIServer从客户端证书中的CN字段中提取出来
  apiGroup: rbac.authorization.k8s.io
roleRef:                                            #这里的"roleRef"段即关联角色/集群角色
  kind: ClusterRole                                 #关联的类型为集群角色
  name: secret-reader                               #集群角色实例对象名称
  apiGroup: rbac.authorization.k8s.io

---------------------------------------------------------------------------------
#Example:   集群角色主要被用来在集群层面和整个命名空间进行授权

kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: read-secrets-global                         #名称
subjects:                                           #主体 ( 主体可以是用户、组、服务帐户 )
- kind: Group                                       #注意这里的主体对象 (类型) 是用户组
  name: manager                                     #组名称
  apiGroup: rbac.authorization.k8s.io
roleRef:                                            #这里的"roleRef"段即关联角色/集群角色
  kind: ClusterRole                                 #关联的类型为集群角色
  name: secret-reader                               #集群角色实例对象名称
  apiGroup: rbac.authorization.k8s.io
```
#### resourceNames
```bash
#可通过 "resourceNamess" 指定特定的资源实例，以限制角色只能够对实例进行访问控制

kind:Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: default                                #本Role所属名称空间 (注意: ClusterRole的metadata不存在此资源 )
  name: configmap-updater
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["my-configmap"]                   #这里指定的是资源下的特定的某个实例!
  verbs: ["update","get"]
```
#### subjects Example:
```bash
subjects:
- kind: User                                        #主体类型
  name: "alice@example.com"                         #名称为 "alice@example.com" 的用户
  apiGroup: rbac.authorization.k8s.io
---------------------------------------------------------------------------------
subjects:
- kind: Group                                       #主体类型
  name: "frontend-admins"                           #名称为 "frontend-admins" 的组
  apiGroup: rbac.authorization.k8s.io
---------------------------------------------------------------------------------
subjects:
- kind: ServiceAccount                              #主体类型
  name: default                                     #在kube-system命名空间中，名称为"default"的服务帐户
  namespace: kube-system
---------------------------------------------------------------------------------
subjects:
- kind: Group                                       #主体类型
  name: system:serviceaccounts:qa                   #在"qa"命名空间中的所有的服务帐户
  apiGroup: rbac.authorization.k8s.io
---------------------------------------------------------------------------------
subjects:
- kind: Group                                       #主体类型
  name: system:serviceaccounts                      #所有的服务帐户
  apiGroup: rbac.authorization.k8s.io
---------------------------------------------------------------------------------
subjects:                                           #所有用户....
- kind: Group
  name: system:authenticated                        #所有被认证的用户
  apiGroup: rbac.authorization.k8s.io
- kind: Group
  name: system:unauthenticated                      #所有未被认证的用户
  apiGroup: rbac.authorization.k8s.io
```
#### 默认的subjects Group/Role
```bash
#APIserver內建一组默认的clusterrole和clusterrolebinding供预留系统使用，其中多数都以 "system:" 为前缀
#另外还有一些非以 "system:" 为前缀的默认的role资源，其是为面向用户的需求设定的，包括超级用户角色 (cluster-admin)
#用于授权集群级别权限的 clusterrolebinding (cluster-status) 
#以及授权特定名称空间级别权限的 rolebinding (admin、edit、view)

#ClusterRole:
cluster-admin                               #超级用户角色
system: master                              #组中用户将具有集群的超级管理权限
system: node                                #定义了kubelets的权限

#Group:
system: authenticated                       #所有被认证的用户
system: unauthenticated                     #所有未被认证的用户
system: serviceaccounts                     #所有的服务帐户
system: kubelet-bootstrap                   #用于自动为节点签发证书
```
#### 命令行工具
```bash
---------------------------------------------------------------------------------
#kubectl create rolebinding

#在"acme"命名空间中，将"admin"集群角色授予"bob"用户:
kubectl create rolebinding bob-admin-binding --clusterrole=admin --user=bob --namespace=acme
#在"acme"命名空间中，将"admin"集群角色授予"acme:myapp"服务帐户：
kubectl create rolebinding myapp-view-binding --clusterrole=view --serviceaccount=acme:myapp --namespace=acme

---------------------------------------------------------------------------------
#kubectl create clusterrolebinding

#在整个集群中授予"cluster-admin"集群角色给"root"用户：
kubectl create clusterrolebinding root-cluster-admin-binding --clusterrole=cluster-admin --user=root
#在整个集群中，授予"system:node"集群角色给"kubelet"用户:
kubectl create clusterrolebinding kubelet-node-binding --clusterrole=system:node --user=kubelet
#在整个集群中，授予"view"集群角色给"acme:myapp"服务帐户:
kubectl create clusterrolebinding myapp-view-binding --clusterrole=view --serviceaccount=acme:myapp


#在kube-system命名空间中很多插件使用"default"服务帐户进行运行。
#为了允许超级用户访问这些插件，在"kube-system"命名空间中授予"cluster-admin"角色给"default"帐户:
kubectl create clusterrolebinding add-on-cluster-admin \ 
--clusterrole=cluster-admin --serviceaccount=kube-system:default

#如果希望在一个命名空间中的所有应用都拥有一个角色，而不管它们所使用的服务帐户，可以授予角色给服务帐户组:
#例如，在my-namespace命名空间中将"view"集群角色授予"system:serviceaccounts:my-namespace"组：
kubectl create rolebinding serviceaccounts-view \ 
--clusterrole=view --group=system:serviceaccounts:my-namespace --namespace=my-namespace

#在整个集群中授予超级用户访问所有的服务帐户 (强烈不推荐)
kubectl create clusterrolebinding serviceaccounts-cluster-admin \ 
--clusterrole=cluster-admin --group=system:serviceaccounts 

#下面的策略允许所有的服务帐户作为集群管理员。
#在容器中运行的应用将自动的收取到服务帐户证书，并执行所有的API行为。包括查看保密字典恩将和修改权限，这是不被推荐的:
kubectl create clusterrolebinding permissive-binding \ 
--clusterrole=cluster-admin \ 
--user=admin \ 
--user=kubelet \ 
--group=system:serviceaccounts


#这个例子是使用名为solinx的服务账户在default名称空间中对pod资源进行操作:
kubectl get po --as system:serviceaccount:default:solinx
```
#### Example
```yaml
# Dashboard Service Account
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system
---
# Dashboard Role
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: kubernetes-dashboard-minimal
  namespace: kube-system
rules:
  # Allow Dashboard to create 'kubernetes-dashboard-key-holder' secret.
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["create"]
  # Allow Dashboard to create 'kubernetes-dashboard-settings' config map.
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["create"]
  # Allow Dashboard to get, update and delete Dashboard exclusive secrets.
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["kubernetes-dashboard-key-holder", "kubernetes-dashboard-certs"]
  verbs: ["get", "update", "delete"]
  # Allow Dashboard to get and update 'kubernetes-dashboard-settings' config map.
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["kubernetes-dashboard-settings"]
  verbs: ["get", "update"]
  # Allow Dashboard to get metrics from heapster.
- apiGroups: [""]
  resources: ["services"]
  resourceNames: ["heapster"]
  verbs: ["proxy"]
- apiGroups: [""]
  resources: ["services/proxy"]
  resourceNames: ["heapster", "http:heapster:", "https:heapster:"]
  verbs: ["get"]
---  
# Dashboard RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: kubernetes-dashboard-minimal
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: kubernetes-dashboard-minimal
subjects:
- kind: ServiceAccount
  name: kubernetes-dashboard
  namespace: kube-system
```