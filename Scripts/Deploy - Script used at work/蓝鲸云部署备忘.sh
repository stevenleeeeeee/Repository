【SSH端口 10022】


#关闭SELinux，检查SELinux的状态，如果它已经禁用，可以跳过后面的命令
sestatus
sed -i 's/^SELINUX=enforcing/SELINUX=disabled/g' /etc/sysconfig/selinux

#重启机器:
reboot

#安装rsync命令:
yum -y install rsync

#关闭防火墙：
systemctl stop firewalld    # 停止firewalld
systemctl disable firewalld # 禁用firewall开机启动


#调整最大文件打开数 （修改后，重新使用root登录检查是否生效）
cat <<EOF > /etc/security/limits.d/99-nofile.conf
root soft nofile 102400
root hard nofile 102400
EOF

#确认服务器时间同步
ntpdate -d cn.pool.ntp.org

#蓝鲸服务器之间会有的http请求，如果存在http代理，且未能正确代理这些请求，会发生不可预见的错误。
#检查http_proxy https_proxy变量是否设置，若为空可以跳过后面的操作
echo "$http_proxy" "$https_proxy"



【https://bk.tencent.com/download/】
#将下载的蓝鲸社区版完整包上传到中控机，并解压到 同级 目录下。以解压到/data 目录为例：
tar xf bkce_src-5.0.3.tar.gz  -C /data
#解压之后, 得到两个目录: src, install
	#src: 存放蓝鲸产品软件, 以及依赖的开源组件
	#install: 存放安装部署脚本、安装时的参数配置、日常运维脚本等


#在所有蓝鲸服务器上配置好 yum 源，要求该 yum 源包含 EPEL

在install目录下, 共有三个配置：
	install.config
	globals.env
	ports.env

#-----------------------------------------------------------------------------------------------
#install.config 是模块和服务器对应关系的配置文件，描述在哪些机器上安装哪些模块。
#每行两列，第一列是IP地址；第二列是以英文逗号分隔的模块名称。
#可将install.config.3IP.sample 复制为install.config
10.0.1.1 nginx,appt,rabbitmq,kafka,zk,es,bkdata,consul,fta
10.0.1.2 mongodb,appo,kafka,zk,es,mysql,beanstalk,consul
10.0.1.3 paas,cmdb,job,gse,license,kafka,zk,es,redis,consul,influxdb

#gse 与 redis 需要部署在同一台机器上
#gse 若需要跨云支持， gse 所在机器必须有外网 IP
#增加机器数量时， 可以将以上配置中的服务挪到新的机器上，分担负载。 要保证: kafka，es，zk 的每个组件的总数量为3

#globals.env
#HAS_DNS_SERVER 配置默认为0，表示配置的蓝鲸域名需要通过/etc/hosts来解析，
#此时部署脚本会自动修改每台机器的/etc/hosts添加相关域名。如果想走自己的dns配置，改为非0即可。
#该文件定义了各类组件的账号密码信息. 功能开关控制选项等. 可根据实际情况进行修改
#该配置文件中提供了访问蓝鲸三大平台的域名配置, 需要提前准备好.
export BK_DOMAIN="bk.com"                # 蓝鲸根域名(不含主机名)
export PAAS_FQDN="paas.$BK_DOMAIN"       # PAAS 完整域名
export CMDB_FQDN="cmdb.$BK_DOMAIN"       # CMDB 完整域名
export JOB_FQDN="job.$BK_DOMAIN"         # JOB 完整域名

#ports.env 端口定义。 默认情况下, 不用修改。特殊场景下，若有端口冲突，可以自行定义。


#非标准私有地址处理方法:
#蓝鲸社区版部署脚本中(install目录)下有以下文件中有获取 ip 的函数 get_lan_ip, 非标准地址, 均需要在安装部署前完成修改。
./appmgr/docker/saas/buildsaas
./appmgr/docker/build
./functions
./scripts/gse/server/gsectl
./scripts/gse/plugins/reload.sh
./scripts/gse/plugins/start.sh
./scripts/gse/plugins/stop.sh
./scripts/gse/agent/gsectl
./scripts/gse/proxy/gsectl
./scripts/gse/agentaix/gsectl.ksh
./agent_setup/download#agent_setup_pro.sh
./agent_setup/download#agent_setup_aix.ksh
./agent_setup/download#agent_setup.sh
#这些文件列表，可能随版本迭代变动，也可以用以下命令查找出来包含这个函数的脚本文件有哪些：
grep -l 'get_lan_ip *()' -r /data/install
#修改方法: 假设服务器的的ip是：138.x.x.x，它不在标准的私有地址范围，那么你需要修改get_lan_ip ()函数为：
get_lan_ip  () {
...省略
               if ($3 ~ /^10\./) {
                   print $3
               }
               if ($3 ~ /^138\./) {
                   print $3
               }
          }

   return $?
}

#在线安装时，依赖pip，需要配置可用的 pip 源。
vi src/.pip/pip.conf
#设置为能连上的 pip 源，默认的pip源配置通常无法使用，验证方式如下：
#在每台机器上对 pip.conf 中配置的url进行操作：curl http://xxxxxxx，若能正常返回列表信息则为成功。
#-----------------------------------------------------------------------------------------------

#获取证书
通过ifconfig或者ip addr命令获取install.config文件中，license和gse模块所在服务器的第一个内网网卡的MAC地址。如果分别属于两台服务器，那么两个的MAC地址以英文;分隔。
在官网证书生成页面根据输入框提示填入MAC地址，生成并下载证书。
上传证书到中控机，并解压到 src/cert 目录下


#配置 SSH 免密登陆
#登录到中控机，执行以下操作
cd /data/install
bash configure_ssh_without_pass  # 根据提示输入各主机的 root 密码完成免密登陆配置


#安装前校验环境是否满足
#按文档要求做完环境和部署的配置后，准备开始安装前，请运行以下脚本，来校验是否满足：
cd /data/install
bash precheck.sh
#如果发现有[FAIL]的报错，按照提示和本文档修复。修复后，可继续跑precheck.sh脚本,直到不再出现[FAIL]。如果需要从头开始检查，请使用 precheck.sh -r 参数。



#从官网下载完整包，并解压到/data/下
tar xf bkce_src-5.0.3.tar.gz  -C /data
#获取机器的MAC地址后，下载证书文件: http://bk.tencent.com/download/#ssl, 解压到 src/cert 目录下 【单机时】
tar xf ssl_certificates.tar.gz -C /data/src/cert


#-----------------------------------------------------------------------------------------------
#部署蓝鲸
#以下步骤若有报错/失败，需要根据提示修复错误后，在重新执行相同的命令（断点续装）。
#每一个步骤执行如果有报错，需要修复错误，保证安装成功后，才可以继续。因为安装蓝鲸平台的顺序是有依赖关系的。 前面的平台没有成功，如果继续往下安装，会遇到更多的报错。
cd /data/install

# 该步骤后,可以打开 paas 平台
./bk_install paas  # 安装paas 平台及其依赖服务

# 该步骤完成后, 可以打开 cmdb, 看到蓝鲸业务及示例业务
./bk_install cmdb  # 安装 cmdb 及其依赖服务

# 该步骤完成后, 可以打开作业平台, 并执行作业
# 同时在配置平台中可以看到蓝鲸的模块下加入了主机
./bk_install job # 安装作业平台及其依赖组件,并在安装蓝鲸的服务器上装好 gse_agent 供验证

# 该步骤完成后可以在开发者中心的 服务器信息 和 第三方服务信息 中看到已经成功激活的服务器
# 同时也可以进行 saas 应用(除蓝鲸监控和日志检索)的上传部署
./bk_install app_mgr # 部署正式环境及测试环境

#  安装该模块后,可以开始安 saas 应用: 蓝鲸监控及日志检索
./bk_install bkdata     # 安装蓝鲸数据平台基础模块及其依赖服务

# 安装 fta 后台
./bk_install fta    # 安装故障自愈的后台服务

# 重装一下 gse_agent 并注册正确的集群模块到配置平台
./bkcec install gse_agent

# 部署官方SaaS到正式环境(通过命令行从/data/src/official_saas/目录自动部署SaaS)
./bkcec install saas-o
#-----------------------------------------------------------------------------------------------


#访问蓝鲸
#根据 install/globals.env 里配置的PaaS域名(PAAS_FQDN)、账号(PAAS_ADMIN_USER)、密码(PAAS_ADMIN_PASS)信息，登录访问(若域名没设置 DNS 解析，需配置本机 hosts)
#域名信息
export BK_DOMAIN="xxx.com"
export PAAS_FQDN="paas.$BK_DOMAIN"
export CMDB_FQDN="cmdb.$BK_DOMAIN"
export JOB_FQDN="job.$BK_DOMAIN"

#账号信息
export PAAS_ADMIN_USER=admin
export PAAS_ADMIN_PASS="xxx"



#坑：
systemctl disable NetworkManager	#！！！
systemctl stop NetworkManager




