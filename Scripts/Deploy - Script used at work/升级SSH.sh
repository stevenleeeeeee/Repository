# rpm -q zlib
# openssl version
# ssh -V

#先安装依赖的软件
yum -y install wget tar gcc gcc-c++ make pam-devel

#下载更新需要的软件
wget -c https://cdn.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-7.9p1.tar.gz
wget -c https://www.openssl.org/source/openssl-1.0.2q.tar.gz
wget -c http://www.zlib.net/fossils/zlib-1.2.11.tar.gz

tar -zxf openssh-7.9p1.tar.gz
tar -zxf openssl-1.0.2q.tar.gz
tar -zxf zlib-1.2.11.tar.gz

cd zlib-1.2.11
./configure --prefix=/usr/local/zlib
make && make install 

cd ../openssl-1.0.2q
./config --prefix=/usr/local/ssl -d shared 	#默认没有编译出.so文件而openssh编译时需要，所以手动添加 -d shared选项
make && make install 

#将共享库文件注册到系统
echo '/usr/local/ssl/lib' >> /etc/ld.so.conf.d/ssl.conf
ldconfig -v

#安装新版本SSH
mv /etc/ssh /etc/ssh.bak.`date '+%F'`
cd ../openssh-7.9p1
#./configure --prefix=/usr/local/openssh --sysconfdir=/etc/ssh --with-zlib=/usr/local/zlib --with-ssl-dir=/usr/local/ssl --with-md5-passwords --with-pam
#./configure --prefix=/usr --sysconfdir=/etc/ssh --with-zlib=/usr/local/zlib --with-ssl-dir=/usr/local/ssl --with-md5-passwords --with-pam
make && make install

cp /usr/bin/ssh-copy-id /usr/bin/ssh-copy-id.bak.`date '+%F'`

install -v -m755    contrib/ssh-copy-id /usr/bin
install -v -m644    contrib/ssh-copy-id.1 /usr/share/man/man1
install -v -m755 -d /usr/share/doc/openssh-7.4p1
install -v -m644    INSTALL LICENCE OVERVIEW README* /usr/share/doc/openssh-7.4p1 #可能有警告，但没有影响

echo 'X11Forwarding yes' >> /etc/ssh/sshd_config
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config 

#/usr/local/openssh/sbin/sshd -f /usr/local/openssh/etc/sshd_config （需要查看旧配置文件根据修改的部分编辑新配置）

#如果是CentOS6可以修改/etc/init.d/sshd中的对应路径即可 ( 卸载：rpm -qa |grep openssh|xargs -i rpm -e --nodeps {} )
#mv /etc/init.d/sshd /etc/init.d/sshd.bak &>> /dev/null
#cp -p contrib/redhat/sshd.init /etc/init.d/sshd
#chmod +x /etc/init.d/sshd
#chkconfig --add sshd

#如果是CentOS7需要修改：/usr/lib/systemd/system/sshd.service
\cp /usr/lib/systemd/system/sshd.service /usr/lib/systemd/system/sshd.service.bak
sed -i 's|/usr/sbin/sshd|/usr/local/openssh/sbin/sshd|g' /usr/lib/systemd/system/sshd.service 
systemctl daemon-reload

echo 'PATH=/usr/local/openssh/bin:/usr/local/openssh/sbin:$PATH' >> /etc/profile.d/sshenv.sh
source /etc/profile
ssh -V


#回退
#如果是使用yum一般都是没有问题，都是经过测试的。
yum -y install openssh-clients.x86_64 openssh-server.x86_64  

#如果是源码编译回退也是简单，只要把启动脚本里面的程序路径修改一下即可

#完善更新流程和回退流程：
#https://www.cnblogs.com/xshrim/p/6472679.html


# sshd启动报错：
#    Unsupported option GSSAPIAuthentication
#    Unsupported option GSSAPICleanupCredentials
# 
# 解决方法：（ 建议将旧的配置文件中使用的配置写入新的配置文件 ）
#    #注销sshd的配置文件（sshd_config）的如下配置: 
#    #GSSAPIAuthentication yes
#    #GSSAPICleanupCredentials yes
#    #UsePAM yes
# sed -i '/^GSSAPICleanupCredentials/s/GSSAPICleanupCredentials yes/#GSSAPICleanupCredentials yes/' /etc/ssh/sshd_config
# sed -i '/^GSSAPIAuthentication/s/GSSAPIAuthentication yes/#GSSAPIAuthentication yes/' /etc/ssh/sshd_config
# sed -i '/^GSSAPIAuthentication/s/GSSAPIAuthentication no/#GSSAPIAuthentication no/' /etc/ssh/sshd_config


#----------------------------------------------------------------------------------------------
#回退：
rm -f /etc/profile.d/sshenv.sh
source /etc/profile

cp -f /usr/lib/systemd/system/sshd.service.bak /usr/lib/systemd/system/sshd.service

rm -rf /etc/ssh
cp  /etc/ssh.bak.`date '+%F'` /etc/ssh

\cp -f /usr/bin/ssh-copy-id.bak /usr/bin/ssh-copy-id   

#安装路径：
/usr/local/zlib
/usr/local/ssl