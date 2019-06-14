`https://kubernetes.io/docs/tasks/administer-cluster/static-pod/`
```txt
如果正在运行Kubernetes并且需要使用pod在每个节点上运行pod，那么应使用DaemonSet!
静态pod由特定节点的kubelet直接管理并且APIServer不会观察其状态, 它没有关联的RC/RS，kubelet本身会监视它并在崩溃时重启
它没有健康检查，静态pod始终绑定到1个kubelet，并始终与它一起运行在同一节点
静态pod在APIServer可见，但无法从那里进行控制

通过启动参数设置kubelet时读取的静态Pod所在目录（或者在kubelet的KubeletConfiguration文件中添加staticPodPath字段指定）
kubelet --pod-manifest-path=<the directory>
```
#### Example
```bash
[root@my-node1 ~] $ mkdir /etc/kubelet.d/
[root@my-node1 ~] $ cat <<EOF >/etc/kubelet.d/static-web.yaml   # kubelet --pod-manifest-path=/etc/kubelet.d/
apiVersion: v1
kind: Pod
metadata:
  name: static-web
  labels:
    role: myrole
spec:
  containers:
    - name: web
      image: nginx
      ports:
        - name: web
          containerPort: 80
          protocol: TCP
EOF

[root@my-node1 ~] $ systemctl restart kubelet
```
