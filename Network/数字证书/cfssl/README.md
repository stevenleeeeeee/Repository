#### Download CFSSL
```bash
[root@node1 ~]# curl -sL -o /bin/cfssl   https://pkg.cfssl.org/R1.2/cfssl_linux-amd64                    
[root@node1 ~]# curl -sL -o /bin/cfssljson   https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64            
[root@node1 ~]# curl -sL -o /bin/cfssl-certinfo   https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64  
[root@node1 ~]# chmod a+x /bin/cfssl*
#以上可执行文件已下载保存在与此目录同级的软件目录中
```
```bash
容器相关证书类型

    1.client certificate：    #用于服务端认证客户端，如 etcdctl、etcd proxy、fleetctl、docker 客户端
    2.server certificate:     #服务端使用，客户端以此验证服务端身份，如docker服务端、kube-apiserver
    3.peer certificate:       #双向证书，用于etcd集群成员之间的双向通信 ( 本文档修改为"kubernetes" )

#cfssl常用命令：
cfssl gencert -initca ca-csr.json | cfssljson -bare ca                  # 初始化ca
cfssl gencert -initca -ca-key key.pem ca-csr.json | cfssljson -bare ca  # 使用现有私钥重新生成
cfssl certinfo -cert ca.pem
cfssl certinfo -csr ca.csr
```
#### 创建CA并生成各类服务证书
```bash
#创建CA认证中心
#运行认证中心需要CA证书和相应的CA私钥。任何知道私钥的人都可以充当CA颁发证书，因此私钥的保护至关重要
[root@node1 ~]# mkdir -p /opt/ssl && cd /opt/ssl
[root@node1 ssl]# cfssl print-defaults config > ca-config.json          #生成CA证书配置文件
[root@node1 ssl]# cfssl print-defaults csr > ca-csr.json                #生成CA证书请求文件

[root@node1 ssl]# vim ca-config.json            #CA证书配置文件
{
    "signing": {
        "default": {
            "expiry": "43800h"                  #分别配置针对3种不同证书类型的profile，有效期为5年
        },
        "profiles": {
         #可定义多个profiles，分别指定不同的过期时间、使用场景等参数；后续在签名证书时使用某个profile
            "server": {                         #指定证书用途、场景 
                "expiry": "43800h",
                "usages": [                     #具体参数
                    "signing",                  #表示该证书可用于签名其它证书；生成的 ca.pem 证书中 CA=TRUE
                    "key encipherment",
                    "server auth"
                ]
            },
            "client": {                         #指定证书用途、场景 
                "expiry": "43800h",
                "usages": [                     #具体参数
                    "signing",                  #表示该证书可用于签名其它证书；生成的 ca.pem 证书中 CA=TRUE
                    "key encipherment",
                    "client auth"
                ]
            },
            "kubernetes": {                     #指定证书用途、场景 
                "expiry": "43800h",
                "usages": [                     #具体参数
                    "signing",                  #表示该证书可用于签名其它证书，生成的 ca.pem 证书中 CA=TRUE
                    "key encipherment",         #
                    "server auth",              #表示 Client 可用该 CA 对 Server 提供的证书进行验证
                    "client auth"               #表示 Server 可用该 CA 对 Client 提供的证书进行验证
                ]
            }
        }
    }
}

[root@node1 ssl]# vim ca-csr.json               #CA证书请求文件
{
    "CN": "admin",                              #apiserver提取该字段作为请求用户名；浏览器使用其验证网站是否合法
    "key": {
        "algo": "rsa",                          #加密算法
        "size": 2048                            #算法强度
    },
    "names": [
        {
            "C": "CN",                          #国家
            "ST": "SH",                         #州、省
            "L": "SH",                          #地区、城市
            "O": "system:masters",              #组织名，公司名 ( apiserver提取该字段作为请求用户所属的组(Group) )
            "OU": "OT"                          #组织单位名称，公司部门
        }
    ]
}

#初始化CA，生成CA证书、CA私钥、CA证书的签名请求：ca.pem、ca.csr、ca-key.pem
[root@node1 ssl]# cfssl gencert -initca ca-csr.json | cfssljson -bare ca - 

#CA证书是集群所有节点共享的，只需要创建一个CA证书，后续创建的所有证书都由它签名!

#创建证书签名请求文件，签发 Server Certificate
[root@node1 ssl]# cfssl print-defaults csr > server.json
[root@node1 ssl]# vim server.json
{
    "CN": "admin",                  #apiserver提取该字段作为请求用户名；浏览器使用其验证网站是否合法
    "hosts": [
        "192.168.0.3"               #当有多个服务端时这里需要要把所有服务器的IP地址/域名写入
    ],                              #如果hosts字段不为空则需要指定授权使用该证书的 IP 或域名列表!
    "key": {
        "algo": "ecdsa",
        "size": 256
    },
    "names": [
        {
            "C": "CN",
            "L": "SH",
            "O":"system:masters",   #组织名，公司名 ( apiserver提取该字段作为请求用户所属的组(Group) )
            "ST": "SH"              #使用该证书访问apiserver时由于被CA签名所以认证通过
        }                           #同时由于证书用户组为经过预授权的 system:masters 所以被授予访问所有 API 的权限!
    ]
}

#使用 "server.json" 生成服务端证书和私钥
[root@node1 ssl]# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=server \
server.json | cfssljson -bare server
#证书没有"主机"字段，这使得它不适合网站。因此输出中的提示可略过，因为集群中仅用IP进行互联

#创建证书签名请求文件，签发 Client Certificate
[root@node1 ssl]# cfssl print-defaults csr > client.json
[root@node1 ssl]# vim client.json 
{
    "CN": "admin",
    "hosts": [
        "x.x.x.x",                  #当有多个服务端时这里需要要把所有服务器的IP/域名都写入
        "x.x.x.x",
        "x.x.x.x"
     ],
    "key": {
        "algo": "ecdsa",
        "size": 256
    },
    "names": [
        {
            "C": "CN",
            "L": "SH",
            "O": "system:masters",
            "ST": "SH"
        }
    ]
}

#生成客户端证书和私钥
[root@node1 ssl]# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=client \
client.json | cfssljson -bare client

#----------------------------------------------------------------------------------------

#创建证书签名请求文件，签发 kubernetes certificate
[root@node1 ssl]# cfssl print-defaults csr > kubernetes.json
[root@node1 ssl]# vim kubernetes.json
{
    "CN": "admin",
    "hosts": [
        "192.168.1.1",              #注意此处要把集群中所有对等节点的地址都写入
        "192.168.1.2",
        "192.168.1.3",
        "192.168.1.4",
        "127.0.0.1",
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
            "O": "system:masters",
            "ST": "SH"
        }
    ]
}

#为节点kubernetes生成证书和私钥:
[root@node1 ssl]# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes \
kubernetes.json | cfssljson -bare kubernetes

# ls ---> kubernetes.csr kubernetes.json kubernetes-key.pem kubernetes.pem

# 分发kubernetes证书：-------------------------
# 在每台etcd机器中运行：
# mkdir -p /etc/kubernetes/ssl
# cp *.pem /etc/kubernetes/ssl  #将CA证书、kubernetes证书、kubernetes私钥传输到所有集群对等节点

```
###### 校验生成的证书是否和配置相符
```bash
[root@node1 ssl]# openssl x509 -in ca.pem -text -noout
openssl x509 -in server.pem -text -noout
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            20:b1:2d:53:47:9d:2c:64:1e:d7:e6:3d:1e:d5:92:57:01:3e:4d:d5
    Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=CN, ST=SH, L=SH, OU=OT, CN=Self Signed Ca
        Validity
            Not Before: Dec 28 09:20:00 2017 GMT
            Not After : Dec 27 09:20:00 2022 GMT
        Subject: C=CN, ST=SH, L=SH, OU=OT, CN=Self Signed Ca
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)
                Modulus:
                    00:b3:ec:02:cf:4c:6c:6e:34:e0:26:f9:9c:46:a7:
                    0e:ac:77:56:36:67:e6:7a:ce:3e:e3:3b:c8:dc:d4:
                    65:fc:00:ea:ce:25:b7:c3:7f:55:d2:cf:48:86:b9:
                    20:0a:49:f2:ff:3f:ac:09:d7:7e:dc:b1:f3:3e:68:
                    a7:3c:05:36:f3:fe:f4:fa:11:c6:1c:48:38:3a:6d:
                    65:18:43:22:88:0f:66:c9:7e:1c:0d:8b:65:fa:31:
                    89:ee:27:d9:46:63:fb:75:10:7a:94:70:ab:44:77:
                    0f:be:d7:78:fd:4b:e7:3f:93:c5:66:23:4b:d2:08:
                    67:ab:2c:94:ae:83:7a:ad:24:cf:3e:57:25:d1:e5:
                    8b:74:e2:89:28:05:e3:70:d8:65:35:83:21:55:18:
                    36:81:13:de:5e:8d:28:25:e2:b8:a4:49:4a:74:c4:
                    f0:8b:f4:30:77:1d:42:49:79:cb:d3:e3:b0:17:10:
                    ba:bb:b4:2f:b5:93:84:78:32:ae:3f:66:84:91:18:
                    71:ac:11:dd:c8:8c:8a:c4:86:25:f9:45:38:8c:bd:
                    43:54:89:d5:ea:97:3f:01:d6:e4:57:6d:5e:4d:1f:
                    01:dd:7c:11:80:07:da:77:08:ed:3a:25:a3:9e:e3:
                    3b:b9:46:aa:25:6b:61:0d:67:a3:e5:09:b5:e0:21:
                    ce:11
                Exponent: 65537 (0x10001)
        X509v3 extensions:
            X509v3 Key Usage: critical
                Certificate Sign, CRL Sign
            X509v3 Basic Constraints: critical
                CA:TRUE, pathlen:2
            X509v3 Subject Key Identifier: 
                D2:8F:2D:70:92:4B:22:19:AE:BB:45:E7:F9:0A:1E:46:7B:6D:F6:21
            X509v3 Authority Key Identifier: 
                keyid:D2:8F:2D:70:92:4B:22:19:AE:BB:45:E7:F9:0A:1E:46:7B:6D:F6:21

    Signature Algorithm: sha256WithRSAEncryption
         34:84:82:5a:da:5e:4e:27:35:fc:0d:11:ee:a6:d5:e6:aa:65:
         f8:f7:16:c4:0f:91:34:0c:77:b5:89:a3:19:df:4c:f6:be:12:
         46:8e:1e:c9:94:d0:65:59:3b:ec:44:da:c3:f4:84:12:34:98:
         b4:fa:22:ce:d1:8b:66:f4:b3:26:d8:a3:35:f6:ac:2b:f4:b9:
         75:a3:11:8f:9b:61:bd:4d:d5:28:55:f2:9b:14:e7:c4:73:ef:
         b1:17:d9:20:6f:1b:b4:d7:2b:6d:7c:41:6f:7f:c9:9e:eb:a3:
         1e:b0:f8:4c:d5:24:9c:9f:82:6b:98:e3:82:e7:8f:aa:a4:4c:
         0b:da:59:0a:d9:b4:d8:76:58:63:d7:cf:c3:2a:4f:5b:a4:55:
         bc:6e:19:47:37:89:c0:b9:2c:b3:8e:23:ea:f7:c2:83:ac:30:
         5f:c4:68:38:ab:db:c1:cd:cc:8b:87:15:f6:d9:24:77:ac:e0:
         cf:29:3c:cf:01:d7:04:fd:87:37:7c:5b:d5:fd:a2:3c:6a:73:
         f3:89:df:73:23:5a:36:3a:f5:81:d9:10:ab:87:68:c7:24:a0:
         c7:0c:a8:68:88:60:bd:59:5f:88:49:05:9a:92:20:d0:f2:0c:
         5f:49:32:5a:25:35:33:6c:9c:73:4b:77:e0:76:5f:52:0c:fc:
         d3:ec:56:a6
         
[root@node1 ssl]# openssl x509 -in server.pem -text -noout
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            28:af:b9:97:b7:48:80:90:f3:4b:a6:fa:07:2a:45:e5:9b:13:27:45
    Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=CN, ST=SH, L=SH, OU=OT, CN=Self Signed Ca
        Validity
            Not Before: Dec 28 09:27:00 2017 GMT
            Not After : Dec 27 09:27:00 2022 GMT
        Subject: C=CN, ST=SH, L=SH, CN=server
        Subject Public Key Info:
            Public Key Algorithm: id-ecPublicKey
openssl x509 -in client.pem -text -noout                Public-Key: (256 bit)
                pub: 
                    04:6d:ed:b5:34:a8:32:96:df:25:23:ea:8f:55:f4:
                    93:fc:d5:5b:d8:88:ae:d2:cd:45:19:ab:8c:a7:0e:
                    cf:df:0c:0e:d1:75:77:df:78:22:d6:82:82:e0:8d:
                    ab:63:84:79:4e:84:3b:a9:f4:d8:18:13:aa:8f:55:
                    34:e2:a9:de:5c
                ASN1 OID: prime256v1
                NIST CURVE: P-256
        X509v3 extensions:
            X509v3 Key Usage: critical
                Digital Signature, Key Encipherment
            X509v3 Extended Key Usage: 
                TLS Web Server Authentication
            X509v3 Basic Constraints: critical
                CA:FALSE
            X509v3 Subject Key Identifier: 
                6D:1E:1B:9B:FD:E7:6E:18:CA:CC:DF:DC:06:DB:1B:93:C9:FB:D8:FA
            X509v3 Authority Key Identifier: 
                keyid:D2:8F:2D:70:92:4B:22:19:AE:BB:45:E7:F9:0A:1E:46:7B:6D:F6:21

            X509v3 Subject Alternative Name: 
                IP Address:192.168.0.3
    Signature Algorithm: sha256WithRSAEncryption
         5b:ed:cb:b0:26:b6:ec:48:44:df:19:6e:52:33:db:49:f8:b1:
         33:ed:c2:d1:cd:58:4e:25:ae:18:51:51:eb:11:f7:54:89:0e:
         09:63:83:6f:24:d9:72:c9:dc:ab:a9:c1:63:d8:b4:d1:d7:3e:
         71:0c:9c:e9:a7:97:6a:39:ff:0f:56:c7:5c:38:83:a3:e5:f3:
         a5:b5:d1:f2:1e:81:87:79:52:9c:0d:84:55:d2:0a:6b:e0:85:
         a4:e4:a8:6d:4e:14:7b:ec:79:c1:b4:1d:a2:6f:f7:ef:46:0b:
         61:dc:6d:63:68:4a:6a:3d:f7:9a:e0:15:1a:8d:4c:ee:d0:58:
         db:ca:ca:dc:2f:cb:23:78:76:1b:1d:2f:99:f8:fe:48:fd:24:
         49:07:8a:21:a5:d9:ec:21:42:ed:6d:43:3d:7b:ba:b2:50:e5:
         ec:5b:85:9b:74:3b:8f:c9:78:3e:2c:d9:2d:6d:c8:76:0f:e9:
         62:b4:a5:88:fc:cb:3d:7b:c5:dc:78:2b:b3:c9:07:e0:8a:e2:
         3b:5c:82:ec:0d:a2:37:57:56:db:98:56:a7:87:00:23:c3:01:
         88:f8:eb:e3:59:1e:81:57:24:88:93:e1:6d:ec:4b:c5:7c:6f:
         0c:b8:59:06:58:1b:6b:16:9f:7f:27:9f:d3:05:15:5e:38:54:
         58:6a:07:a3
[root@node1 ssl]# openssl x509 -in client.pem -text -noout
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            61:81:e3:b0:32:86:4b:aa:c4:a5:33:ff:02:f6:ca:c3:cf:48:64:ee
    Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=CN, ST=SH, L=SH, OU=OT, CN=Self Signed Ca
        Validity
            Not Before: Dec 28 09:31:00 2017 GMT
            Not After : Dec 27 09:31:00 2022 GMT
        Subject: C=CN, ST=SH, L=SH, CN=Client
        Subject Public Key Info:
            Public Key Algorithm: id-ecPublicKey
                Public-Key: (256 bit)
                pub: 
                    04:06:8b:20:23:16:1e:a9:6a:13:06:90:30:66:b9:
                    0c:22:75:6a:fd:54:e4:d6:e5:b3:0e:42:be:d4:5f:
                    d0:7d:1c:0a:18:d3:43:b1:79:64:df:18:58:c9:da:
                    5e:67:17:31:72:7d:10:4f:b0:84:3b:75:51:d4:22:
                    3a:69:5d:67:42
                ASN1 OID: prime256v1
                NIST CURVE: P-256
        X509v3 extensions:
            X509v3 Key Usage: critical
                Digital Signature, Key Encipherment
            X509v3 Extended Key Usage: 
                TLS Web Client Authentication
            X509v3 Basic Constraints: critical
                CA:FALSE
            X509v3 Subject Key Identifier: 
                CA:50:92:9B:8B:BB:86:39:72:81:1B:0D:9F:CF:42:A0:B9:57:F0:A5
            X509v3 Authority Key Identifier: 
                keyid:D2:8F:2D:70:92:4B:22:19:AE:BB:45:E7:F9:0A:1E:46:7B:6D:F6:21

    Signature Algorithm: sha256WithRSAEncryption
         83:c1:17:e3:9c:60:45:bd:d1:b9:18:dc:2e:c9:ba:a1:be:b6:
         88:be:f9:1b:01:56:46:79:c8:06:bd:7b:6b:0a:58:00:1d:a2:
         1e:01:b2:fa:01:fb:9b:34:8d:36:b7:66:fd:93:f4:31:53:ec:
         e8:1a:59:e2:6c:c9:b2:ff:42:5a:3a:10:3d:07:cc:4a:0a:42:
         21:e3:60:30:b6:b1:02:2b:5b:97:8c:66:c5:68:09:34:1b:de:
         4f:f3:6e:80:eb:f0:5d:b7:94:de:67:08:28:39:90:5b:9b:3a:
         4b:da:76:0c:58:57:cb:d8:3d:c1:de:02:e8:91:96:75:b5:48:
         70:fc:ad:27:6f:96:b1:8a:48:03:30:87:65:72:5f:5a:b5:85:
         95:43:d3:b2:3c:5e:28:0d:d2:2b:33:9e:f5:6e:c8:36:58:17:
         09:26:83:a1:9f:57:61:11:d7:ef:8b:98:06:9f:f5:6b:c1:2e:
         ac:0b:6b:b9:dd:5e:c5:2f:2d:b6:7f:c2:d4:83:da:1c:b9:c8:
         79:95:83:43:30:1f:bb:da:07:eb:fc:33:28:ca:27:35:c3:40:
         d0:5d:45:8f:7d:15:80:22:68:4a:66:0b:79:c1:a4:48:a9:71:
         5f:77:5c:40:7d:0b:35:a8:4f:5b:c6:03:39:69:f5:36:5d:e5:
         61:b7:6f:9d
```
