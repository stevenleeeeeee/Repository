wget https://www.python.org/ftp/python/2.7.14/Python-2.7.14.tgz
tar -zxvf Python-2.7.14.tgz

yum -y install gcc gcc-c++ openssl openssl-devel ncurses-devel.x86_64 bzip2-devel sqlite-devel python-devel zlib

cd Python-2.7.14
./configure --prefix=/usr/local
make && make altinstall

mv /usr/bin/python /usr/bin/python2.7.5
ln -s /usr/local/bin/python2.7 /usr/bin/python

#修正yum等组件python
vim /usr/bin/yum
首行的#!/usr/bin/python 改为 #!/usr/bin/python2.7.5

vim /usr/libexec/urlgrabber-ext-down
首行的#!/usr/bin/python 改为 #!/usr/bin/python2.7.5

wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
ln -s /usr/local/bin/pip2.7 /usr/bin/pip

pip install kube-shell
