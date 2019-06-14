#!/bin/bash
# exec ---> source thisfile...

#PS1
export PS1='\e[31;1m[ \e[0m\e[36;1m\A\e[0m \e[31m\u@\h\e[0m \e[31;1m\W\e[0m \e[31;1m]\$\e[0m '

#HISTORY
export HISTTIMEFORMAT="[ %F %T `whoami` ] "
export HISTFILESIZE="5000"
export HISTSIZE="200"

export PROMPT_COMMAND='{
	date "+%Y%m%d %T \
	| $(who am i | awk "{print \$1\" \"\$2\" \"\$5}" | sed -E "s/[(|)]//g") \
	| $(pwd) \
	| $(history 1 | { read x cmd; echo "$cmd"; } | grep -oP "(?<=. ] ).*")"; 
} >> /var/log/history-$(date '+%Y%m%d').log'


function initenv() {
  yum -y install wget
  mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup
  wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
  yum makecache
  yum -y install epel-release gcc gcc-c++ cmake openssl openssl-devel net-tools vim git
}

export -f initenv
