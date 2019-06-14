> 环境：centos 6.5  
OpenSSL Version 1.0.1e  
by inmoonlight@163.com 2017.05.2

#### 网络安全4要素
```txt
机密性：    对称/非对称加密（非对称可防止"中间人"攻击和伪造）
完整性：    摘要算法，如哈希函数的MD5（防篡改）常用发送方私钥加密摘要数据后发出
身份验证：   数字签名/数字证书：与谁沟通以及是否有权沟通，是安全四要素前提条件！
不可抵赖：   数字签名：是否本人发出和收到信息
```
#### 非对称加密原理
```txt
C把其把公匙放在S端，当C->S请求时S在家目录寻找C的公钥并用其加密质询给C，C收到质询后用私钥解密再发给S
公私钥角色可互换，公钥在网络传输而私钥仅保存本地（双方使用对方公钥加密发出数据并使用自己的私钥解密收到数据）
非对称加密加/解密时间长、速度慢，适合少量数据加密，一般用公钥加密对称算法的密钥后发出
```
#### 公钥基础设施
```txt
CA机构的公钥存储在浏览器中（PKI：公钥基础设施）。所有对象都认可CA机构的证书（及公钥）。CA机构是PKI的核心
PKI是树形结构，其间的信任关系是可 以传递的（CA下的每个子节点可再次创建其下的证书并授权）
注：自身的公钥存储在自己的证书当中
```
#### SSL / TLS / HTTPS
```txt
SSL安全套接字层： 在应用层与传输层间加入一层，将上层数据处理后交给下层
TLS传输层安全： 直接在TCP传输层实现（目前的主流）

HTTPS：
在TCP三次握手后即开始协商使用SSL会话还是TLS会话.........
```

## Openssl CA 环境设置

### 1.设置CA工作目录 /etc/pki/tls/openssl.cnf 
```Bash
[ CA_default ]

dir             = /etc/pki/CA           # <-----
certs           = $dir/certs            # Where the issued certs are kept
crl_dir         = $dir/crl              # Where the issued crl are kept
database        = $dir/index.txt        # database index file.
#unique_subject = no                    # Set to 'no' to allow creation of
                                        # several ctificates with same subject.
new_certs_dir   = $dir/newcerts         # default place for new certs.

certificate     = $dir/cacert.pem       # The CA certificate
serial          = $dir/serial           # The current serial number
crlnumber       = $dir/crlnumber        # the current crl number
                                        # must be commented out to leave a V1 CRL
crl             = $dir/crl.pem          # The current CRL
private_key     = $dir/private/cakey.pem # The private key
RANDFILE        = $dir/private/.rand    # private random number file
```

### 2.初始化CA证书编号的初始值
```Bash
cd /etc/pki/CA
echo 01 > serial
```
### 3.创建CA根私钥
```Bash
CA_dir="/etc/pki/CA"
openssl genrsa -out ${CA_dir}/private/cakey.pem 2048
chmod 700 ${CA_dir}/private/cakey.pem
```

### 4.创建CA根证书
```Bash
CA_dir="/etc/pki/CA"
openssl req -new -x509 -days 3650 -key ${CA_dir}/private/cakey.pem -out ${CA_dir}/cacert.pem

Country Name (2 letter code) [XX]:CN					#国家（大写缩写）
State or Province Name (full name) []:shanghai				#省份或洲
Locality Name (eg, city) [Default City]:shanghai			#城市
Organization Name (eg, company) [Default Company Ltd]:company		#公司
Organizational Unit Name (eg, section) []:yanfa				#部门    
Common Name (eg, your name or your server’s hostname)[]:xx.xx.xx.xx	#须与证书能解析到的名字一致
Email Address []:admin@paybay.cn

#以上参数可通过配置文件修改：/etc/pki/tls/openssl.cnf
```

## Server 环境设置
### 1.创建服务器私钥
```Bash
mkdir /etc/certs && cd /etc/certs && openssl genrsa -out ./webserv.key 2048
chmod 644 -R /etc/certs/*
```
### 2.服务器证书申请
```Bash
openssl req -new -key /etc/certs/webserv.key -out /etc/certs/webserv.csr
Country Name (2 letter code) [AU]:CN                    
State or Province Name (full name) [Some-State]:shanghai
Locality Name (eg, city) []:shanghai
Organization Name (eg, company) [Internet Widgits Pty Ltd]:company
Organizational Unit Name (eg, section) []:yanfa
Common Name (e.g. server FQDN or YOUR name) []:xxx.xxx.xxx.xxx
Email Address []:admin@company.cn
```
### 3.将证书请求:"csr" 传至CA进行签名
```Bash
scp /etc/certs/webserv.csr root@<CA_Ip-Address>:/etc/ssl
```
### 4.在CA机构对此csr进行签名
```Bash
cd /etc/ssl
openssl x509 -req -in /etc/ssl/webserv.csr -CA /etc/pki/CA/cacert.pem \
-CAkey /etc/pki/CA/private/cakey.pem -CAcreateserial -out webserv.crt
#将签名后的crt传至Server服务器：
scp webserv.crt root@<Server_Ip-Adress>:/etc/certs
```

### 5.在服务端的：ngixn/mqtt/apache中设置使用https
```Bash
nginx-example：
ht.. 
	ssl_session_cache   shared:SSL:10..	
	ssl_session_timeout 10m;	.. 
	......
	server {
		listen              443 ssl;
		server_name         example.com
		ssl_certificate     webserv.crt;
		ssl_certificate_key webserv.key;
		ssl_protocols       TLSv1 TLSv1.1 TLSv1.2; 
		ssl_ciphers         HIGH:!aNULL:!MD5;
		add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;	
		add_header X-Content-Type-Options nosniff;    
		add_header X-Xss-Protection 1;		          
		......
	}
}
	
#注：由于是自建CA，客户端或浏览器自身没有此私有CA证书，需在使用前提前导入CA根证书否则S端发来的证书不被C端承认
```

## 在CA端吊销证书

### 1.在S端获取证书serial
```Bash
openssl x509 -in /etc/serts/webserv.crt -noout -serial -subject
#stdout-example...
serial=01
subject=/C=CN/ST=shanghai/O=paybay/OU=yanfa/CN=xxx.xxx.xxx.xxx	#保留输出内容供CA端验证
```	
### 2.在CA端验证：	
```Bash
cat /etc/pki/CA/index.txt
V	251227084917Z		01	unknown	/C=CN/ST=shanghai/O=paybay/OU=yanfa/CN=xxx.xxx.xxx.xxx
#依S端提交的serial和subject信息来验证与index.txt中的信息是否一致
```

### 3.在CA端吊销：
```Bash
openssl ca -revoke newcerts/01.pem
```	 
### 4.CA生成吊销编号（仅在第1次吊销证书时）
```Bash
echo 01 > /etc/pki/CA/crlnumber
```
### 5.CA更新证书吊销列表:
```Bash
cd /etc/pki/CA/crl &&  openssl ca -gencrl -out ca.crl
```
## 附
### 以非交互的命令行方式生成服务器端X.509证书
```Bash
openssl req -new -newkey rsa:2048 -sha256 -nodes -out example_com.csr -keyout example_com.key -subj \
"/C=CN/ST=ShenZhen/L=ShenZhen/O=Example Inc./OU=Web Security/CN=example.com"

# C：	Country ，单位所在国家，为两位数的国家缩写，如：CN
# ST： 	State/Province ，单位所在州或省
# L： 	Locality ，单位所在城市 / 或县区
# O： 	Organization ，此网站的单位名称
# OU： 	Organization Unit，下属部门名称;常用于显示其他证书相关信息，如证书类型，证书产品名或身份验证类型或验证内容等
# CN： 	Common Name ，网站的域名
#
# 生成 csr 后提供给 CA 并签署成功后会得到 example.crt 证书，SSL 证书文件获得后，就可以在 Nginx 里配置 HTTPS 了
```
### 其他常用命令
- 测算法速度：	openssl speed <算法>
- 生成随机数：	openssl rand [ -base64 / -hex ] <length>
- 生成公私钥：	openssl genrsa -out private.key 2048  /   openssl rsa -in private.key -pubout -out public.pubkey
- 文件加解密：	openssl enc -e -des3 -in sec.key -out file.secrite  /   openssl enc -d -des3 -in file.secrite -out sec.key.dec
- 计算摘要值：	openssl [md5/sha1] < file <---> echo -n "***"  /   [ md5sum / sh1sum ] <---> openssl dgst [-md5/sha1] < file

