#Pushgateway的客户端采用push方式将数据发送，Prometheus只需要到Pushgateway拉取数据即可
wget http://github.com/prometheus/pushgateway/releases/download/v0.7.0/pushgateway-0.7.0.linux-amd64.tar.gz
tar xf pushgateway-0.7.0.linux-amd64.tar.gz -C /usr/local/
mv /usr/local/pushgateway-0.7.0.linux-amd64 /usr/local/pushgateway
/usr/local/pushgateway/pushgateway

#Prometheus配置文件指定pushgateway地址
[root@nagios ~]# tail -3 /usr/local/prometheus/prometheus.yml
  - job_name: 'pushgateway'
    static_configs:
    - targets: ['localhost:9091']

[root@jenkins_test ~]# cat user_login.sh 
#!/bin/bash
for((i=1;i<=4;i++));
  do 
  count=$(w| awk 'NR==1{print $4}')
  label="Count_login_users"
  instance_name=$(hostname)
  echo "$label $count" | curl -d @- http://<ip>:<port>/metrics/job/pushgateway/instance/${instance_name}
  sleep 15
done

[root@jenkins_test ~]# crontab -l
*/1 * * * * /bin/bash /root/user_login.sh  &>/dev/null