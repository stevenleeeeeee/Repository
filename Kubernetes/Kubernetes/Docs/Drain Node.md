```bash
#将指定工作节点中的所有pod调度到其他节点中运行，用于维护节点时
kubectl drain <node name> --delete-local-data --force --ignore-daemonsets
kubectl delete node <node name>
```