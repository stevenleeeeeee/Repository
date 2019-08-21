#! /usr/bin/env python
# -*- coding: utf-8 -*-

import platform
import os
import threading
from datetime import datetime
import commands
import copy
import re
import sys

res = {}

def decorator(func):
    ''' 使用装饰器以字典的方式返回所有基线检查函数的输出结果 '''
    def addValues():
        res.update(func())
        return res
    return addValues


@decorator
def check_system_version():		
    ''' Linux发行版信息 '''
    sys_version = dict(system_version = str(platform.dist()[0] + "-" + platform.dist()[1]),kernel_version = platform.release())
    return sys_version


@decorator
def check_repo():
    ''' 检查yum仓库是否设置为内网地址 '''
    if os.path.isfile('/etc/yum.repos.d/rhel7.repo'):
        with open('/etc/yum.repos.d/rhel7.repo',"r") as f:
            for line in f.readlines():
                if 'http://20.58.27.3/html/centos7-x86_64-epel' in line:
                    return dict(repo = 1)
    elif os.path.isfile('/etc/yum.repos.d/rhel6.repo'):
        with open('/etc/yum.repos.d/rhel6.repo',"r") as f:
            for line in f.readlines():
                if 'http://20.58.27.3/html/centos6-x86_64-epel' in line:
                    return dict(repo = 1)
    else:
        return dict(repo = 0)


@decorator
def check_date():
    ''' 检查时区是否为 Asia/Shanghai '''
    if int(short_v) == 7:
        timezone_string = (commands.getoutput(''' ls -l /etc/localtime | awk -F'/' '{print $(NF-1)"/"$NF}' '''))
        return dict(timezone = 1 if timezone_string == 'Asia/Shanghai' else 0)
    else:
        pre_zone = (commands.getoutput('cat /etc/sysconfig/clock')).split('"')[1]
        return dict(timezone = 1 if timezone_string == 'Asia/Shanghai' else 0)


@decorator
def check_firewall():
	''' 检查防火墙状态 '''
	if commands.getoutput('systemctl status firewalld &> /dev/null && echo 0 '):
		return {"firewall_stat":"1"}
	if commands.getoutput('service  iptables  status &> /dev/null && echo 0'):
		return {"firewall_stat":"1"}
	return {"firewall_stat":"0"}


@decorator
def check_se():
	''' 检查SElinux状态 '''
	return dict(SElinux = 1 if str(commands.getoutput('getenforce')) == 'Disabled' else 0)

#@decorator
#def check_rpmlist():
#	''' 所有已安装的RPM (列表类型) 按字母排序 【不需要】'''
#	rpm_list = sorted(commands.getoutput('rpm -qa').split('\n'),key=str.lower)
#	return dict(rpm_pkg_list = rpm_list)

#@decorator
#def check_service():
#	''' 输出系统中正在运行的服务及端口，依赖于netstat 【修改小于1W不合规，展示不合规端口】'''
#	tcp_services = commands.getoutput(''' netstat -tnlp | awk 'NR>2{gsub(/.*\//,"",$NF);print $NF,$4}' ''').replace('\n',',')
#	udp_services = commands.getoutput(''' netstat -unlp | awk 'NR>2{gsub(/.*\//,"",$NF);print $NF,$4}' ''').replace('\n',',')
#	tcp_services_dict={}
#	udp_services_dict={}
#	for i in tcp_services.split(','):
#		k,v = i.split(" ")
#		tcp_services_dict[k]=v
#	for i in udp_services.split(','):
#		k,v = i.split(" ")
#		udp_services_dict[k]=v
#	return dict(tcp=tcp_services_dict,udp=udp_services_dict)

	
@decorator
def check_service():
	''' 输出系统中正在运行的服务及端口，依赖于netstat 【修改小于1W不合规，展示不合规端口】
		若tcp/udp端口都小于1W，则输出json中的键值为：right_port_rangs: 1
		否则输出大于1W的端口号及应用名称: xxxx: 'address:port'
	'''
	tcp_services = commands.getoutput(''' netstat -tnlp | awk 'NR>2{gsub(/.*\//,"",$NF);print $NF,$4}' | awk -F':' '{if($NF < 10000){print $0}}' ''').replace('\n',',')
	udp_services = commands.getoutput(''' netstat -unlp | awk 'NR>2{gsub(/.*\//,"",$NF);print $NF,$4}' | awk -F':' '{if($NF < 10000){print $0}}' ''').replace('\n',',')
	tcp_services_dict={}
	udp_services_dict={}
	for i in tcp_services.split(','):
		if len(tcp_services_dict) == 0:
			tcp_services_dict['right_port_rangs']='1'
			break
		else:
			k,v = i.split(" ")
			tcp_services_dict[k]=v
	for i in udp_services.split(','):
		if len(udp_services) == 0:
			udp_services_dict['right_port_rangs']='1'
			break
		else:
			k,v = i.split(" ")
			udp_services_dict[k]=v
	return dict(tcp=tcp_services_dict,udp=udp_services_dict)


@decorator
def check_shell():
	''' 检查/etc/bashrc中的变量设置 '''
	HISTFILESIZE,_ = commands.getstatusoutput(''' grep -v '^#' /etc/bashrc | grep -oP -q '(?<=HISTFILESIZE=)65536' ''')
	HISTSIZE,_ = commands.getstatusoutput(''' grep -v '^#' /etc/bashrc | grep -oP -q '(?<=HISTSIZE=)4096$' ''')
	HISTTIMEFORMAT,_ = commands.getstatusoutput(''' grep -v '^#' /etc/bashrc | grep -oP -q '(?<=HISTTIMEFORMAT=).*$' ''')
	HISTCONTROL,_ = commands.getstatusoutput(''' grep -v '^#' /etc/bashrc | grep -oP -q '(?<=HISTCONTROL=)ignoredups' ''')
	HISTIGNORE,_ = commands.getstatusoutput(''' grep -v '^#' /etc/bashrc | grep -oP -q '(?<=HISTIGNORE=).*$' ''')
	PROMPT_COMMAND,_ = commands.getstatusoutput(''' grep -v '^#' /etc/bashrc | grep -oP -q '(?<=PROMPT_COMMAND=).*$' ''')
	shopt,_ = commands.getstatusoutput(''' grep -v '^#' /etc/bashrc | grep -oP -q 'shopt -s histappend' ''')
	
	CHECK_LIST = {
		'HISTFILESIZE' : HISTFILESIZE,
		'HISTSIZE' : HISTSIZE,
		'HISTTIMEFORMAT' : HISTTIMEFORMAT,
		'HISTCONTROL' : HISTCONTROL,
		'HISTIGNOREs' : HISTIGNORE,
		'PROMPT_COMMAND' : PROMPT_COMMAND,
		'SHOPT' : shopt
	}
	
	result = copy.deepcopy(CHECK_LIST)
	
	for k,v in CHECK_LIST.items():
		#print(k,v)
		if v != 0:
			result[k]=1
		else:
			result[k]=0
			
	return dict(shell_config=result)
			

#@decorator
#def check_env():
#	''' 收集系统env环境变量 【非判断，暂时不要】'''
#	env_strings = commands.getoutput('env').replace('\n',",").replace('=',':')
#	system_env = dict(System_env = str(env_strings))
#	return system_env


@decorator
def check_auth():
	''' PAM 用户检查 '''
	if os.path.isfile('/etc/pam.d/login'):
		with open('/etc/pam.d/login', 'r') as f:
			fhandle = f.readlines()
			auth_config_list = {}
			for line in fhandle:
				line = line.strip().strip('[|]')
				# 这里可能要改一下
				lock_user = re.match('auth required pam_tally2.so file=/var/log/tallylog', line)
				if lock_user:
					lock_user = dict(lock_user = 1)
					return auth_config_list.update(lock_user)
	if not auth_config_list:
		lock_user = dict(lock_user = 0)
		auth_config_list.update(lock_user)
	return auth_config_list


@decorator
def check_passwd_com():
	''' 密码复杂度检查 '''
	if os.path.isfile('/etc/pam.d/system-auth-ac'):
		with open('/etc/pam.d/system-auth-ac', 'r') as f:
			pass_config_list = {}
			for line in f.readlines():
				line = line.strip().strip('[|]')
				pass_com = re.match('password requisite pam_cracklib.so minlen=8 dcredit=-1 ucredit=-1 ocredit=-1 lcredit=-1 retry=5 difok=3',line)
				if pass_com:
					pass_complex = dict(pass_com = 1)
					return  pass_config_list.update(pass_complex)
	if not pass_config_list:
		pass_complex = dict(pass_com = 0)
		pass_config_list.update(pass_complex)
		return pass_config_list


#@decorator
#def check_java():
#	''' JAVA版本信息 【展示版本号，需要修改】'''
#	s1,o1 = commands.getstatusoutput(''' grep -v '^#' /etc/profile | grep JAVA_HOME ''')
#	if int(s1) != 256:
#		if int(s1) >= 0:
#			pre_s1 = re.findall('JAVA_HOME=.*',o1)
#			pre_java_bin = o1.split('=')[1]
#			java_bin = pre_java_bin + '/bin/java -version'
#			res_java_version = str(re.findall('\d\.\d\.\d_\d{,4}', java_bin)).replace('[', '').replace(']', '')
#			return dict(java_version = res_java_version)
#	else:
#		(s,o) = commands.getstatusoutput('java -version')
#		if (int(s) == 0):
#			Version = str(re.findall('.*version.*',o))
#			java_Version = str(re.findall('\d\.\d\.\d_\d{,4}', Version)).replace('[', '').replace(']', '')
#			return dict(built_in_java_version = java_Version)
#		elif s == 32512:
#			return dict(built_in_env_java = 0)
#		else:
#			return dict(built_in_command_java = 0)

@decorator
def check_java():
	''' 展示java版本号信息，若存在则输出版本号，若不存在则返回值为0 '''
	s1,o1 = commands.getstatusoutput(''' grep -v '^#' /etc/profile | grep JAVA_HOME ''')
	if s1 == 0:
		JAVA_VERSION = commands.getoutput(''' $(grep -v '^#' /etc/profile | grep -oP '(?<=JAVA_HOME=).*')/bin/java -version &> /dev/stdout  | awk -F'\"' 'NR==1{print $(NF-1)}' ''')
		return dict(built_in_java_version = JAVA_VERSION )
	else:
		s1,o1 = commands.getstatusoutput(''' java -version ''')
		if s1 == 0:
			JAVA_VERSION = commands.getoutput(''' java -version &> /dev/stdout | awk -F'\"' 'NR==1{print $(NF-1)}' ''')
			return dict(built_in_java_version = JAVA_VERSION )
	return dict(built_in_java_version = 0 )

 
#@decorator
#def check_weblogic():
#	''' weblogic信息 【再检查,梳理，要改为判断】'''
#    ps = commands.getoutput(''' ps -ef | grep 'java.*weblogic' | grep -v 'python\|grep' ''')
#    if not ps:
#        weblogic = dict(weblogic_version = 'weblogic not install')
#        return weblogic
#        return 0
#    s = ps.split()
#    res = ""
#    result = ""
#    try:
#        for i in s:
#            if re.match('.*?platform.*', i, re.I):
#                result = i.split("=")[1]
#                rest = result.split("/")
#                res = "/".join(rest[:len(rest) - 1])
#        bsu_dir = res + "/utils/bsu"
#        os.chdir(bsu_dir)
#    except OSError as e:
#        weblogic = dict(bsu_version = 'BSU not install')		#需要存在bsu，
#        return weblogic
#        return 0
#    else:
#        bsu_script = bsu_dir + "/bsu.sh"
#        bsu_cmd = bsu_script + " -prod_dir=" + result + " -status=applied -verbose -view"
#        status = commands.getoutput(bsu_cmd)
#        msg = status.splitlines()
#        messages = dict()
#        for ms in msg:
#            ls = re.split(':\s+', ms)
#            if re.match('ProductVersion', ls[0], re.I):
#                messages['weblogic_version'] = ls[1]
#        for ms in msg:
#            ls = re.split(':\s+', ms)
#            if re.match('Description', ls[0], re.I):
#                #pre_bsu = str(ls[1].split(' ')[4:])
#                #messages['BSU_version'] = pre_bsu.replace('[','').replace(']','')
#                messages['BSU_version'] = ls[1]
#        jdk_msg = commands.getoutput('java -version')
#        messages['jdk_version'] = jdk_msg.splitlines()[0]
#        if 'weblogic_version' not in messages:
#           messages['weblogic_version'] = 'weblogic not install'
#        if 'BSU_version' not in messages:
#           messages['BSU_version'] = 'BSU not install'
#        return messages
#
#    # def addGrains(self,msg):
#    #     cmds = "salt-call grains.setvals \"%s\"" % msg
#    #     status = commands.getoutput(cmds)
#    #     return status

@decorator
def check_weblogic():
	''' 检查weblogic是否存在，若存在检查bsu是否设置，正确返回1，不存在返回0 '''
    status,ps_find_weblogic = commands.getstatusoutput(''' ps -ef | grep startWebLogic | grep -v 'grep|python' | grep -oP '/[^ ]*Middleware' | uniq ''')
    if status != 0:
        return dict(weblogic = 0,bsu_version = 0)
    else:
        status,weblogic_bsu_path = commands.getstatusoutput(''' echo $(ps -ef | grep startWebLogic | grep -v 'grep|python' | grep -oP '/[^ ]*Middleware' | uniq)/utils/bsu ''')
        if status !=0:
            return dict(weblogic = 1,bsu_version = 0)
        else:
            if os.path.isdir(weblogic_bsu_path):
                return dict(weblogic = 1,bsu_version = 1)
            else:
                return dict(weblogic = 1,bsu_version = 0)


@decorator
def check_ssh():
	''' openssh版本 【展示SSH版本号】'''
	version = str(commands.getoutput('ssh -V')).replace(',','').split()[0]
	ssh_version = dict(ssh_version = version)
	return ssh_version

@decorator
def check_ntpd():
	''' 检查NTP进程或crontab中是否存在有NTP进程 '''
	pre_ntp = commands.getoutput('ps -ef | grep ntpd | grep -v grep')					#检查进程
	pre_cron_ntp = commands.getoutput('crontab -l | grep -v ^# | grep ntpdate' )		#检查crontab
	result = dict(ntpd_status = 0 if pre_ntp == '' else 1,cron_ntp = 0 if pre_cron_ntp == '' else 1)
	return result		

@decorator
def check_zabbix():
	''' 检查zabbix-agent
	    若存在输出版本号，不存在为0
	'''
	s,Pre_zabbix = commands.getstatusoutput('rpm -qa | grep zabbix-agent')
	s1,pre_zabbix = commands.getstatusoutput('ps -ef | grep "/usr/local/zabbix" | grep -v grep | wc -l ')
	s2,so_pre_zabbix = commands.getstatusoutput('/usr/local/zabbix/sbin/zabbix_agentd -V | grep zabbix_agentd')
	if int(s) == 0:
		Zabbix_version = Pre_zabbix.split('.el')[0]
		return dict(zabbix_version = Zabbix_version)
	if int(pre_zabbix) >= 3 and os.path.isfile('/usr/local/zabbix/conf/zabbix_agentd.conf'):
		Zabbix_version = str(re.findall('\d\.{,4}',so_pre_zabbix))
		return dict(zabbix_agent = Zabbix_version)
	else:
		return dict(zabbix_agent = '0')

@decorator
def check_S6000agent():
	''' 检查S6000 '''
	pre_s6 = commands.getoutput('ps -ef|grep daemon_agent |grep -v grep|wc -l')
	if int(pre_s6) >= 1:
		return dict(S6000agent = 1)
	else:
		return dict(S6000agent = 0)


#@decorator
#def check_saltminion():
#	''' 检查salt-minion版本及进程是否存在 【非判断，改判断不合理】 '''
#    s, Pre_saltminion = commands.getstatusoutput('rpm -qa | grep salt-minion')
#    if s == 0:
#        Saltminion_version = Pre_saltminion.split('.el')[0]
#        salt_minion = dict(salt_minion_version = Saltminion_version )
#        return salt_minion
#    else:
#        salt_minion = dict(salt_minion_version = 'salt minion not install')
#        return salt_minion


@decorator
def check_rsyslog():
	''' 检查Rsyslog信息 【需要再讨论】 '''
	if os.path.isfile('/etc/rsyslog.d/sys_tmpl.conf'):
		with open('/etc/rsyslog.d/sys_tmpl.conf','r')as f:
			fh = f.readlines()
			fhandle = str(fh)
			Is_es = re.findall('module\(load="omelasticsearch"\)',fhandle)	#通过配置文件中的关键字判断
			if len(Is_es):
				return dict(rsyslog = '1')
			else:
				return dict(rsyslog='0')
	else:
		return dict(rsyslog='0')
	return dict(rsyslog='0')


@decorator
def check_dict():
	''' 校验密码检查功能是否是通过字典进行，参考地址: https://www.jianshu.com/p/e09bbf1e4b25 '''
    (s, o) = commands.getstatusoutput('echo "hndl#1234" | cracklib-check')
    res = re.findall('it is based on a dictionary word',o)
    if not res:
        return dict(poor_dictionary = '1')
    else:
        return dict(poor_dictionary = '0')


@decorator
def check_psacct():
	''' yum install psacct / 用户登陆信息等行为检查【需先安装psacct】 '''
	if int(short_v) == 7:
		pre_psacct,_ = commands.getstatusoutput(''' systemctl status  psacct | grep -q Active ''')
		return dict(psacct = 1 if pre_psacct == 0 else 0 )
	if int(short_v) == 6:
		pre_psacct,_ = commands.getstatusoutput(''' service psacct status | grep -q running ''')
		return dict(psacct = 1 if pre_psacct == 0 else 0 )

@decorator
def check_tmout():
	''' 判断登陆超时的TIMEOUT时间是否设置正确 '''
	pre_tmout,_ = commands.getstatusoutput(''' grep -v '^#' /etc/profile | grep -oP '(?<=TMOUT=)600' ''')
	return dict(TMOUT = 1 if pre_tmout == 0 else 0 )

def main():
    function_map = {
        'shell': check_shell,
        'repo': check_repo,
        'ntp': check_ntpd,
        'firewall': check_firewall,
        'timezone': check_date,
        'pass': check_passwd_com,
        'system_version': check_system_version,
        'selinux': check_se,
        'service_port':  check_service,
        'rsyslog': check_rsyslog,
        'env': check_env,
        'auth': check_auth,
        'java': check_java,
        'weblogic': check_weblogic,
        'ssh': check_ssh,
        'zabbix': check_zabbix,
        's6000': check_S6000agent,
        'poor_dictionary': check_dict,
        'psacct': check_psacct,
        'tmout': check_tmout,
    }

    input_arg = len(sys.argv)
	
	#若参数是一个（默认）则调用所有巡检函数
    if  input_arg == 1:
        threads = []
        t1 = threading.Thread(target = check_shell)
        threads.append(t1)
        t2 = threading.Thread(target = check_ntpd)
        threads.append(t2)
        t3 = threading.Thread(target = check_firewall)
        threads.append(t3)
        t4 = threading.Thread(target = check_date)
        threads.append(t4)
        t5 = threading.Thread(target = check_repo)
        threads.append(t5)
        t6 = threading.Thread(target = check_passwd_com)
        threads.append(t6)
        t7 = threading.Thread(target = check_auth)
        threads.append(t7)
        t8 = threading.Thread(target = check_service)
        threads.append(t8)
        t9 = threading.Thread(target = check_se)
        threads.append(t9)
        t10 = threading.Thread(target = check_S6000agent )
        threads.append(t10)
        t11 = threading.Thread(target = check_zabbix)
        threads.append(t11)
        t12 = threading.Thread(target = check_rsyslog)
        threads.append(t12)
        t13 = threading.Thread(target = check_weblogic)
        threads.append(t13)
        t14 = threading.Thread(target = check_java)
        threads.append(t14)
        # t15 = threading.Thread(target=check_env)
        # threads.append(t15)
        t16 = threading.Thread(target = check_system_version)
        threads.append(t16)
        t19 = threading.Thread(target = check_ssh)
        threads.append(t19)
        t20 = threading.Thread(target = check_dict)
        threads.append(t20)
        t21 = threading.Thread(target = check_psacct)
        threads.append(t21)
        t22 = threading.Thread(target = check_tmout)
        threads.append(t22)

        for t in threads:
            t.setDaemon(True)
            t.start()
            t.join()
	
	#若携带参数（调用特定函数）则仅返回此函数的字典
    if input_arg == 2:
        input_key = sys.argv[1]
        return function_map[input_key]()
		
    if input_arg > 2:
        print 'nonsupport more args'
        return False

    return res

if __name__ == '__main__':

	#获取发行版主版本号:7/6
    short_v = str(list(platform.dist())[1]).split('.')[0]
    main()
	
	
	