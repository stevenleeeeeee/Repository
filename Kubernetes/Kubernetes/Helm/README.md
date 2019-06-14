#### 备忘
```txt
helm:       CLI，把安装chart请求发送给tiller
tiller:     相当于helm-server，部署在集群内并接收部署请求，调用apiserver完成部署
repo:       相当于yum源，里面存放着一系列包，可以是远程的，也可以是本地目录
chart:      相当于rpm包，包含服务的一系列配置信息，可以通过远程获取，也可以本地创建
```
```bash
wget https://storage.googleapis.com/kubernetes-helm/helm-v2.9.1-linux-amd64.tar.gz
tar -zxvf helm-v2.9.1-linux-amd64.tar .gz
cp linux-amd64/helm /usr/local/bin/        #复制客户端执行文件到bin目录下

#Helm客户端与k8s中的TillerServer是通过k8s提供的port-forward实现的，而port-forward需要在指定节点上部署socat

#初始化tiller: ( init将获取本地默认的kubeconfig文件，然后在k8s上面部署 deploy/tiller-deploy )
helm init --history-max 200  --service-account tiller
#使用阿里云镜像安装并​​把默认仓库设置为阿里云上的镜像仓库
$ helm init --upgrade --tiller-image registry.cn-hangzhou.aliyuncs.com/google_containers/tiller:v2.9.1 \
--stable-repo-url https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts --history-max 200 \
--service-account tiller

#创建 Kubernetes 的服务帐号和绑定角色：
kubectl create serviceaccount -n kube-system tiller
kubectl create clusterrolebinding tiller-cluster-rule \
    --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
kubectl patch deploy -n kube-system tiller-deploy -p '{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}'

#查看是否授权成功
kubectl get deploy -n kube-system tiller-deploy --output yaml | grep  serviceAccount
# serviceAccount: tiller
# serviceAccountName: tiller

#验证 Tiller 是否安装成功  ( 卸载Helm服务器端Tiller: helm reset )
kubectl -n kube-system get pods | grep tiller
helm version

#从repo里面更新chart ( 相当于 yum update )
helm repo update 

# 安装Helm后，通过执行以下命令将service-catalog Helm存储库添加到本地计算机： ( 添加仓库 )
# 通过 helm repo list 命令可以看到目前 Helm 中已配置的 Repository 信息
helm repo add svc-cat https://svc-catalog-charts.storage.googleapis.com

#通过执行以下命令检查以确保安装成功：
helm search service-catalog
helm search incubator

#Helm提供自动补全:
source <(helm completion bash)
```
#### 创建内部repo
```yaml
helm serve --address 0.0.0.0:8879 --repo-path /data/helm/repository/ --url http://192.168.70.128:8879/charts/

# 更新 Helm Repository 的索引文件
cd /home/k8s/.helm/repository/local
helm repo index --url=http://192.168.100.211:8879 .

#添加helm仓库
helm repo add local http://127.0.0.1:8879
```