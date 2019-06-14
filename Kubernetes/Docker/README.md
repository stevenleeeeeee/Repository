#### 下载Docker及说明 （ 环境：CentOS 7.3 ）
```bash
[root@localhost ~]# uname -r                          #内核版本至少需要 >= 3.8
3.10.0-327.el7.x86_64
[root@localhost ~]# systemctl disable firewalld
[root@localhost ~]# systemctl stop firewalld   
[root@localhost ~]# yum -y install iptables-services  #docker需要使用iptables进行网络的NAT转换
[root@localhost ~]# systemctl start iptables
[root@localhost ~]# systemctl enable iptables
[root@localhost ~]# yum -y install docker
[root@localhost ~]# systemctl enable docker
[root@localhost ~]# systemctl start docker

[root@localhost ~]# systemctl cat docker.service      #Docker Daemon的service unit文件
# /usr/lib/systemd/system/docker.service
[Unit]
Description=Docker Application Container Engine
Documentation=http://docs.docker.com
After=network.target
Wants=docker-storage-setup.service
Requires=docker-cleanup.timer

[Service]
Type=notify
NotifyAccess=all
EnvironmentFile=-/run/containers/registries.conf
EnvironmentFile=-/etc/sysconfig/docker
EnvironmentFile=-/etc/sysconfig/docker-storage                  #存储相关参数在此设置
EnvironmentFile=-/etc/sysconfig/docker-network                  #网络相关参数...
Environment=GOTRACEBACK=crash                                   #环境变量
Environment=DOCKER_HTTP_HOST_COMPAT=1                           #...
Environment=PATH=/usr/libexec/docker:/usr/bin:/usr/sbin         #...
ExecStart=/usr/bin/dockerd-current \                            #启动命令及默认的参数...
          --add-runtime docker-runc=/usr/libexec/docker/docker-runc-current \
          --default-runtime=docker-runc \
          --exec-opt native.cgroupdriver=systemd \
          --userland-proxy-path=/usr/libexec/docker/docker-proxy-current \
          $OPTIONS \
          $DOCKER_STORAGE_OPTIONS \
          $DOCKER_NETWORK_OPTIONS \
          $ADD_REGISTRY \
          $BLOCK_REGISTRY \
          $INSECURE_REGISTRY\
          $REGISTRIES
ExecReload=/bin/kill -s HUP $MAINPID
LimitNOFILE=1048576
LimitNPROC=1048576
LimitCORE=infinity
TimeoutStartSec=0
Restart=on-abnormal
MountFlags=slave
KillMode=process

[Install]
WantedBy=multi-user.target

[root@localhost ~]# docker version          #查看其客户端与服务端的版本信息...
Client:
 Version:         1.12.6
 API version:     1.24
 Package version: docker-1.12.6-68.gitec8512b.el7.centos.x86_64
 Go version:      go1.8.3
 Git commit:      ec8512b/1.12.6
 Built:           Mon Dec 11 16:08:42 2017
 OS/Arch:         linux/amd64

Server:
 Version:         1.12.6
 API version:     1.24
 Package version: docker-1.12.6-68.gitec8512b.el7.centos.x86_64
 Go version:      go1.8.3
 Git commit:      ec8512b/1.12.6
 Built:           Mon Dec 11 16:08:42 2017
 OS/Arch:         linux/amd64

[root@node129 ~]# docker info
Containers: 0
 Running: 0
 Paused: 0
 Stopped: 0
Images: 8
Server Version: 18.09.5
Storage Driver: devicemapper
 Pool Name: docker-253:0-101441603-pool
 Pool Blocksize: 65.54kB
 Base Device Size: 10.74GB
 Backing Filesystem: xfs
 Udev Sync Supported: true
 Data file: /dev/loop0
 Metadata file: /dev/loop1
 Data loop file: /var/lib/docker/devicemapper/devicemapper/data
 Metadata loop file: /var/lib/docker/devicemapper/devicemapper/metadata
 Data Space Used: 2.931GB
 Data Space Total: 107.4GB
 Data Space Available: 6.212GB
 Metadata Space Used: 2.597MB
 Metadata Space Total: 2.147GB
 Metadata Space Available: 2.145GB
 Thin Pool Minimum Free Space: 10.74GB
 Deferred Removal Enabled: true
 Deferred Deletion Enabled: true
 Deferred Deleted Device Count: 0
 Library Version: 1.02.107-RHEL7 (2015-10-14)
Logging Driver: json-file
Cgroup Driver: cgroupfs
Plugins:
 Volume: local
 Network: bridge host macvlan null overlay
 Log: awslogs fluentd gcplogs gelf journald json-file local logentries splunk syslog
Swarm: inactive
Runtimes: runc
Default Runtime: runc
Init Binary: docker-init
containerd version: bb71b10fd8f58240ca47fbb579b9d1028eea7c84
runc version: 2b18fe1d885ee5083ef9f0838fee39b62d653e30
init version: fec3683
Security Options:
 seccomp
  Profile: default
Kernel Version: 3.10.0-327.el7.x86_64
Operating System: CentOS Linux 7 (Core)
OSType: linux
Architecture: x86_64
CPUs: 2
Total Memory: 3.845GiB
Name: node129
ID: AFFX:DANT:RCGO:G7F5:V7TA:V2QX:4JQR:STMW:525A:QC5O:5HJX:GPPH
Docker Root Dir: /var/lib/docker
Debug Mode (client): false
Debug Mode (server): false
Registry: https://index.docker.io/v1/
Labels:
Experimental: false
Insecure Registries:
 127.0.0.0/8
Live Restore Enabled: false
Product License: Community Engine
```
#### 下载 docker 镜像 ...
```bash
[root@localhost ~]# docker search bash
INDEX       NAME                                  DESCRIPTION                        STARS  OFFICIAL  AUTOMATED
docker.io   docker.io/bash                        Bash is the GNU Project's Bour....  47     [OK]      
docker.io   docker.io/bashell/alpine-bash         Alpine Linux with /bin/bash as....  13               [OK]
docker.io   docker.io/frolvlad/alpine-bash        Docker image with Bash and com....  5                [OK]
docker.io   docker.io/andthensome/alpin......     Container with Hugo, Git & Bas....  2                [OK]
docker.io   docker.io/cosmintitei/bash-curl       bash image with curl                2                [OK]
docker.io   docker.io/andthensome/alpine....      Minimal container with Node & ....  1                [OK]
docker.io   docker.io/casimir/blinux-bash         Bash in blinux                      1                [OK]
docker.io   docker.io/contentanalyst/java-bash    Alpine with Java and Bash           1                [OK]
docker.io   docker.io/ellerbrock/bash-it          Bash Shell v.4.4 with bash-it,....  1                [OK]
docker.io   docker.io/tianon/bash                 Several versions of Bash, Dock....  1                
docker.io   docker.io/amd64/bash                  Bash is the GNU Project's Bour....  0                
docker.io   docker.io/blang/alpine-bash                                               0                [OK]
docker.io   docker.io/brenix/alpine-bash-git-ssh  Simple alpine image with bash,....  0                [OK]
......(略)         
[root@localhost ~]# docker pull  docker.io/bash                 #下载特定的docker镜像...
Using default tag: latest
Trying to pull repository docker.io/library/bash ... 
latest: Pulling from docker.io/library/bash

1160f4abea84: Pull complete 
35c12c862670: Pull complete 
50313e686d4e: Pull complete 
Digest: sha256:b146a2e9aadaf2ed4a540324094412f2cd3f609f8a2f55ed608285f85f12a0f1
[root@localhost ~]# docker images                               #查看本地的docker镜像
REPOSITORY          TAG                 IMAGE ID            CREATED                  SIZE
docker.io/bash      latest              a853bea42baa        Less than a second ago   12.22 MB

# 注：
# docker官方建议配置信息以参数形式传递进入容器，并且一个容易最好只运行一个进程...
# docker容器中的程序是在前台执行的...，若运行后台程序则需要在容器内使用supervisor...

[root@localhost ~]# ip link show dev docker0                    #默认的docker虚拟桥（交换），所有的容器均连接至此设备
3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN mode DEFAULT 
    link/ether 02:42:ad:8f:48:42 brd ff:ff:ff:ff:ff:ff
[root@localhost ~]# ip address show dev docker0
3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN 
    link/ether 02:42:ad:8f:48:42 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 scope global docker0     #docker为网桥分配的私有地址，其仅能够在本机进行访问
       valid_lft forever preferred_lft forever
```

#### 容器相关的操作
```bash
[root@localhost etc]# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED                  SIZE
docker.io/bash      latest              a853bea42baa        Less than a second ago   12.22 MB
[root@localhost etc]# docker run docker.io/bash:latest ip add show  #此处的ip add show为docker.io/bash运行的命令
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN 
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
4: eth0@if5: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue state UP 
    link/ether 02:42:ac:11:00:02 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.2/16 scope global eth0                    #此处的地址与宿主机的docker0网桥处于同一个逻辑网段
       valid_lft forever preferred_lft forever
    inet6 fe80::42:acff:fe11:2/64 scope link tentative 
       valid_lft forever preferred_lft forever
[root@localhost etc]# docker ps -a                          #显示所有容器（包括已经运行退出的容器）
CONTAINER ID        IMAGE                   COMMAND                  CREATED             STATUS                     PORTS               NAMES
8829aa998c35        docker.io/bash:latest   "docker-entrypoint.sh"   2 minutes ago       Exited (0) 2 minutes ago                    drunk_spence
[root@localhost etc]# docker ps -aq                         #仅显示容器ID
8829aa998c35
[root@localhost etc]# docker rm -f $(docker ps -aq)         #删除所有容器
8829aa998c35

# docker run 参数：(docker create 与 docker run 类似，但其仅创建容器而不运行)
# --name       容器名，存在于相同网络内的DNS中(在自定义网络中相同网络的容器可直接使用名称找到对方而在不同网络中的不能够直接通信)
# -v           指定宿主机与容器间映射的目录或文件
# -i           提供交互式接口
# -t           提供一个伪终端
# -p           指定宿主机与容器的端口间的映射关系
# -P           根据容器dockerfile中EXPOSE的端口与宿主机随机的端口进行映射
# -e           传递给容器的环境变量
# -d           使容器后台执行，相当于linux中的nohup
# -m           内存使用量的限制
# -h           容器的主机名（--hostname）
# exec         进入到容器内部 eg: docker exec -it <xxx> /bin/bash
# attach       不建议...
# -net         容器使用的网络类型
# --rm         当容器运行结束后自动删除
# -w           容器的工作目录
# --ip         容器的IPV4地址
# --dns        容器使用的DNS服务器
# --restart    容器运行结束后的动作? eg:--restart=always
```
#### Dockerfile
```bash
[root@localhost ~]# docker commit <container> [repo:tag]     #将容器打包为镜像（此方式方便快速但不规范且无法自动化）
[root@localhost ~]# cat Dockerfile
# FROM         以哪个镜像为基础进行制作
# MAINTAINER   维护者信息
# ARG          由外部启动时必须传入的参数，用--build-arg传递参数：docker build --build-arg v=2.1 Dockerfile
# ENV          定义容器的环境变量
# RUN          构建镜像时执行的命令（每个RUN均创建一个新的AUFS层）
# ADD          将本地文件添加到容器中，identity, gzip, bzip2，xz，tar.gz，tgz等类型将被tar自动解压
# COPY         同ADD，但不会解压文件
# VOLUME       用于指定持久化目录
# EXPOSE       容器需要暴露的端口
# LABEL        给镜像添加信息。用docker inspect可查看镜像的相关信息，如：LABEL version="1.0"
# ENTRYPOINT   配置容器，使其可执行化（若CMD也存在则CMD的内容相当于ENTRYPOINT的参数）
# CMD          在容器启动时进行调用的命令
# WORKDIR      工作目录
# USER         用于设定容器的运行用户名或UID
# LABLE        为容器打标签元数据，使用docker inspect <ImageName> 可查看到其元数据信息，包括部分Dockerfile中的指令

[root@localhost ~]# docker build -t "name:tag" .            #根据当前路径下的Dockerfile开始构建镜像

#注：
#entrypoint总是被执行，即使在docker run命令后指定了要运行的命令。此命令会被认为是entrypoint的参数，替换掉CMD中的默

[root@node2 ~]# docker history docker.io/nginx              #查看镜像的构建历史...
IMAGE               CREATED             CREATED BY                                      SIZE                COMMENT
3f8a4339aadd        4 days ago          /bin/sh -c #(nop)  CMD ["nginx" "-g" "daemon    0 B                 
<missing>           4 days ago          /bin/sh -c #(nop)  STOPSIGNAL [SIGTERM]         0 B                 
<missing>           4 days ago          /bin/sh -c #(nop)  EXPOSE 80/tcp                0 B                 
<missing>           4 days ago          /bin/sh -c ln -sf /dev/stdout /var/log/nginx/   0 B                 
<missing>           4 days ago          /bin/sh -c set -x  && apt-get update  && apt-   53.23 MB            
<missing>           4 days ago          /bin/sh -c #(nop)  ENV NJS_VERSION=1.13.8.0.1   0 B                 
<missing>           4 days ago          /bin/sh -c #(nop)  ENV NGINX_VERSION=1.13.8-1   0 B                 
<missing>           2 weeks ago         /bin/sh -c #(nop)  LABEL maintainer=NGINX Doc   0 B                 
<missing>           2 weeks ago         /bin/sh -c #(nop)  CMD ["bash"]                 0 B                 
<missing>           2 weeks ago         /bin/sh -c #(nop) ADD file:f30a8b5b7cdc9ba33a   55.25 MB 
```
#### 查看镜像信息
```txt
[root@node129 ~]# docker image history  registry.cn-hangzhou.aliyuncs.com/google_containers/coredns:1.3.1            
IMAGE               CREATED             CREATED BY                                      SIZE                COMMENT
eb516548c180        3 months ago        /bin/sh -c #(nop)  ENTRYPOINT ["/coredns"]      0B                  
<missing>           3 months ago        /bin/sh -c #(nop)  EXPOSE 53 53/udp             0B                  
<missing>           3 months ago        /bin/sh -c #(nop) ADD file:f8e53e4ac50b8298d…   40MB                
<missing>           5 months ago        /bin/sh -c #(nop) COPY dir:f312a04b4e58d3be2…   235kB               

[root@node129 ~]# docker image inspect  registry.cn-hangzhou.aliyuncs.com/google_containers/coredns:1.3.1          
[
    {
        "Id": "sha256:eb516548c180f8a6e0235034ccee2428027896af16a509786da13022fe95fe8c",
        "RepoTags": [
            "registry.cn-hangzhou.aliyuncs.com/google_containers/coredns:1.3.1"
        ],
        "RepoDigests": [],
        "Parent": "",
        "Comment": "",
        "Created": "2019-01-13T14:53:32.560242381Z",
        "Container": "b586914ebabf365305eba735d3a5ece44915f5dc5f531c29b6b0aa621c36b9da",
        "ContainerConfig": {
            "Hostname": "b586914ebabf",
            "Domainname": "",
            "User": "",
            "AttachStdin": false,
            "AttachStdout": false,
            "AttachStderr": false,
            "ExposedPorts": {
                "53/tcp": {},
                "53/udp": {}
            },
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ],
            "Cmd": [
                "/bin/sh",
                "-c",
                "#(nop) ",
                "ENTRYPOINT [\"/coredns\"]"
            ],
            "Image": "sha256:c3d031f19b19efb4dfebbd10d37333ce9d44ae9e3cec5c0401f6e96ed3bbd59e",
            "Volumes": null,
            "WorkingDir": "",
            "Entrypoint": [
                "/coredns"
            ],
            "OnBuild": null,
            "Labels": {}
        },
        "DockerVersion": "18.09.0",
        "Author": "",
        "Config": {
            "Hostname": "",
            "Domainname": "",
            "User": "",
            "AttachStdin": false,
            "AttachStdout": false,
            "AttachStderr": false,
            "ExposedPorts": {
                "53/tcp": {},
                "53/udp": {}
            },
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ],
            "Cmd": null,
            "Image": "sha256:c3d031f19b19efb4dfebbd10d37333ce9d44ae9e3cec5c0401f6e96ed3bbd59e",
            "Volumes": null,
            "WorkingDir": "",
            "Entrypoint": [
                "/coredns"
            ],
            "OnBuild": null,
            "Labels": null
        },
        "Architecture": "amd64",
        "Os": "linux",
        "Size": 40283416,
        "VirtualSize": 40283416,
        "GraphDriver": {
            "Data": {
                "DeviceId": "3",
                "DeviceName": "docker-253:0-101441603-9b007c951fe01f9fee281c7f1095b91f55e6e406bbb0641adea659b3f4828e60",
                "DeviceSize": "10737418240"
            },
            "Name": "devicemapper"
        },
        "RootFS": {
            "Type": "layers",
            "Layers": [
                "sha256:fb61a074724df9ebf0f3ea2fc07cf9a25d19c66ecb926c248549641e4ecd7037",
                "sha256:c6a5fc8a3f01ec05d0f50e9c182d903d3302091e83febe4f58f7523a0072cb79"
            ]
        },
        "Metadata": {
            "LastTagTime": "0001-01-01T00:00:00Z"
        }
    
```
#### Notice
```txt
不要依赖于IP地址:
每套容器都拥有自己的内部IP地址，而容器的每次启动与停止都有可能导致IP地址发生改变。
如果应用程序或者微服务需要与其它容器通信，那么请使用能够将相关信息由此容器传递至彼容器的名称与/或环境变量。
```