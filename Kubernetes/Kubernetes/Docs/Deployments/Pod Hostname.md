```bash
#用户可以指定Pod注解: pod.beta.kubernetes.io/hostname (用于指定Pod的hostname)
#这个Pod注解一旦被指定，将优先于Pod的名称成为pod的hostname

#比如一个Pod其注解为 pod.beta.kubernetes.io/hostname: my-pod-name
#那么该Pod的hostname会被设置为 my-pod-name
```