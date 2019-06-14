```bash
官方网址：https://github.com/AliyunContainerService/log-pilot

ref:
https://www.cnblogs.com/weifeng1463/p/10274021.html
https://github.com/AliyunContainerService/log-pilot/blob/master/docs/filebeat/docs.md
https://help.aliyun.com/document_detail/86552.html
https://www.jianshu.com/p/a56ecb2a3151
```
#### deploy application
```bash
# log-Pilot是阿里开源的智能容器日志采集工具
# 不仅能高效便捷地将容器日志采集输出到多种存储日志后端，同时还能够动态地发现和采集容器内部的日志文件
# 能动态监听容器的事件变化然后依据容器的标签来进行解析，生成日志采集配置文件后交由采集插件来进行采集

Log-Pilot依据环境变量 "aliyun_logs_$name=$path" 动态地生成日志采集配置文件：
  ...$name   在不同的场景指代不同含义，将日志采集到 ElasticSearch 时它表示的是 Index
  ...$path   支持2种输入形式，1：stdout、2：容器内部日志文件的路径
  ...$name_format=<format>      以什么格式解析日志：none|json|csv|nginx|apache2|regexp
  ...$name_tags="K1=V1,K2=V2"   在采集时将 K1=V1 和 K2=V2 添加到容器的日志输出，方便进行日志统计、路由、过滤

# 被采集对象设置环境变量： ( 本例中$name是catalina、access 它们在ES中以 ${name}-yyyy.MM.dd 的方式存在 )
  ......
    env:
     - name: aliyun_logs_catalina                                 
       value: "stdout"                                       # 采集标准输出
     - name: aliyun_logs_access
       value: "/usr/local/tomcat/logs/catalina.*.log"        # 采集容器内日志
     - name: aliyun_logs_catalina_format
       value: "none"
     - name: aliyun_logs_access_format
       value: "none"
     - name: aliyun_logs_catalina_tags                       # 打标签方便后端处理，如syslog对标签进行分类
       value: "tomcat-catalina-tag"
     - name: aliyun_logs_access_tags                         #
       value: "tomcat-access-tag"
    volumeMounts:
    - name: tomcat-log                                       # 容器内文件日志路径需配置emptyDir
      mountPath: /usr/local/tomcat/logs
   volumes:
     - name: tomcat-log
       emptyDir: {}
  ......
```
#### deploy log-pilot
```yaml
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: log-pilot
  labels:
    app: log-pilot
  namespace: kube-system
spec:
  template:
    metadata:
      labels:
        app: log-pilot
      annotations:
        scheduler.alpha.kubernetes.io/critical-pod: ''
    spec:
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      containers:
      - name: log-pilot
        # 版本请参考https://github.com/AliyunContainerService/log-pilot/releases  fluentd版本支持syslog
        image: registry.cn-hangzhou.aliyuncs.com/acs/log-pilot:0.9.6-filebeat
        resources:
          limits:
            memory: 500Mi
          requests:
            cpu: 200m
            memory: 200Mi
        env:
          - name: "NODE_NAME"
            valueFrom:
              fieldRef:
                fieldPath: spec.nodeName
          - name: "LOGGING_OUTPUT"
            value: "elasticsearch"
          - name: "ELASTICSEARCH_HOSTS"
            value: "{es_endpoint}:{es_port}"
          - name: "ELASTICSEARCH_USER"
            value: "{es_username}"
          - name: "ELASTICSEARCH_PASSWORD"
            value: "{es_password}"
        volumeMounts:
        - name: sock
          mountPath: /var/run/docker.sock
        - name: root
          mountPath: /host
          readOnly: true
        - name: varlib
          mountPath: /var/lib/filebeat
        - name: varlog
          mountPath: /var/log/filebeat
        - name: localtime
          mountPath: /etc/localtime
          readOnly: true
        livenessProbe:
          failureThreshold: 3
          exec:
            command:
            - /pilot/healthz
          initialDelaySeconds: 10
          periodSeconds: 10
          successThreshold: 1
          timeoutSeconds: 2
        securityContext:
          capabilities:
            add:
            - SYS_ADMIN
      terminationGracePeriodSeconds: 30
      volumes:
      - name: sock
        hostPath:
          path: /var/run/docker.sock
      - name: root
        hostPath:
          path: /
      - name: varlib
        hostPath:
          path: /var/lib/filebeat
          type: DirectoryOrCreate
      - name: varlog
        hostPath:
          path: /var/log/filebeat
          type: DirectoryOrCreate
      - name: localtime
        hostPath:
          path: /etc/localtime
```
#### 多种日志后端类型
```bash
kafka:
#KAFKA_BROKERS         "(required) kafka brokers"
#KAFKA_VERSION         "(optinal) kafka version"
#KAFKA_USERNAME        "(optianl) kafka username"
#KAFKA_PASSWORD        "(optianl) kafka password"
#KAFKA_PARTITION_KEY   "(optinal) kafka partition key"
#KAFKA_PARTITION       "(optinal) kafka partition strategy"
#KAFKA_CLIENT_ID       "(optinal) the configurable ClientID used for logging, debugging, and auditing purposes. The default is beats"
#KAFKA_BROKER_TIMEOUT  "(optinal) the number of seconds to wait for responses from the Kafka brokers before timing out. The default is 30 (seconds)."
#KAFKA_KEEP_ALIVE      "(optinal) keep-alive period for an active network connection. If 0s, keep-alives are disabled, default is 0 seconds"
#KAFKA_REQUIRE_ACKS    "(optinal) ACK reliability level required from broker. 0=no response, 1=wait for local commit, -1=wait for all replicas to commit. The default is 1"

elasticsearch:
#ELASTICSEARCH_HOST       "(required) elasticsearch host"
#ELASTICSEARCH_PORT       "(required) elasticsearch port"
#ELASTICSEARCH_USER       "(optinal) elasticsearch authentication username"
#ELASTICSEARCH_PASSWORD   "(optinal) elasticsearch authentication password"
#ELASTICSEARCH_PATH       "(optinal) elasticsearch http path prefix"
#ELASTICSEARCH_SCHEME     "(optinal) elasticsearch scheme, default is http"

logstash:
#LOGSTASH_HOST            "(required) logstash host"
#LOGSTASH_PORT            "(required) logstash port"

file:
#FILE_PATH             "(required) output log file directory"
#FILE_NAME             "(optinal) the name of the generated files, default is filebeat"
#FILE_ROTATE_SIZE      "(optinal) the maximum size in kilobytes of each file. When this size is reached, the files are rotated. The default value is 10240 KB"
#FILE_NUMBER_OF_FILES  "(optinal) the maximum number of files to save under path. When this number of files is reached, the oldest file is deleted, and the rest of the files are shifted from last to first. The default is 7 files"
#FILE_PERMISSIONS      "(optinal) permissions to use for file creation, default is 0600"
```