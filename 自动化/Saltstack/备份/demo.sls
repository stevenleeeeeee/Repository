[root@rbtnode1 master.d]# pwd
/etc/salt/master.d
[root@rbtnode1 master.d]# cat ex_api.conf 
file_roots:
  base:
    - /srv/salt

fileserver_backend:
  - roots
  - git

gitfs_remotes:
  - http://root:Chang123123@20.59.20.173/root/salt_sls.git:
    - mountpoint: salt://

gitfs_base: master

pillar_roots:
  base:
    - /srv/pillar

ext_pillar:
  - git:
    - master http://root:Chang123123@20.59.20.173/root/salt_pillar.git:
      - mountpoint: salt://


rest_cherrypy:
  port: 8000
  host: 0.0.0.0
  debug: True
  disable_ssl: True

external_auth:
  pam:
    saltapi:
        - .*
        - '@runner'
        - '@wheel'

reactor:
  - 'salt/netapi/hook/gitfs/*':
    - /srv/reactor/gitfs.sls

[root@rbtnode1 salt]# cat base.sls 
base:
  '*':
   - jdk8.init
   - tomcat.init
   - weblogic.install
   - patch
   - weblogic.useradd
   - tomcat.tomcatuseradd
   - domain
   - restart_biz
   - weblogic.jdk8_weblogic
[root@rbtnode1 salt]# cat tomcat/init.sls 
 include:
  - tomcat.tomcatuseradd
  - jdk8.init
 tomcat-install:
  file.managed:
    - name: /app/tomcat.zip
    - source: salt://files/middleware/tomcat/tomcat.zip
    - makedirs: true
    - user: great
    - group: great
    - mode: 755
  cmd.run:
    - name: cd /app/;unzip tomcat.zip;chown -R great:great tomcat
    - unless: test -e /app/tomcat
[root@rbtnode1 salt]# cat tomcat/tomcatuseradd.sls 
great:
  user.present:
    - fullname: great
    - shell: /bin/bash
    - home: /home/great
    - uid: 504
    - gid_from_name: true
    - password: '$1$tomcat$/UGDUcTox0ykrOt7/ZfBw/'
    - enforce_password: false
bash_profile:
  file.append:
    - name: /home/great/.bash_profile
    - text:
      - export JAVA_HOME=/app/jdk
      - export CLASSPATH=.:$JAVA_HOME/lib:$JAVA_HOME/jre/lib
      - export PATH=$JAVA_HOME/bin::$JAVA_HOME/bin:$PATH
      - export LANG= C
#    - require:
#      - file: jdk8.init
[root@rbtnode1 salt]# cat jdk8/init.sls 
jdk_file:
  file.managed:
   - name: /app/jdk-8u11-linux-x64.tar.gz
   - source: salt://files/jdk/jdk-8u11-linux-x64.tar.gz
   - makedirs: true
   - user: root
   - group: root
   - mode: 755
jdk_install:
  cmd.run:
   - name: cd /app/;tar xf jdk-8u11-linux-x64.tar.gz;mv jdk1.8.0_11 jdk
   - unless: test -e /app/jdk
   - require:
     - file: jdk_file
jdk8-1env:
  file.append:
    - name: /etc/profile
    - text:
      - export JAVA_HOME=/app/jdk
      - export CLASSPATH=.:$JAVA_HOME/lib:$JAVA_HOME/jre/lib
      - export PATH=$JAVA_HOME/bin::$JAVA_HOME/bin:$PATH
    - require:
      - file: jdk_file
jdk8-random:
  file.replace:
    - name: /app/jdk/jre/lib/security/java.security
    - pattern: securerandom.source=file:/dev/random
    - repl: securerandom.source=file:/dev/./urandom
    - count: 1
    - show_changes: True