```txt
https://yunlzheng.gitbook.io/prometheus-book/part-ii-prometheus-jin-jie/exporter/commonly-eporter-usage/install_blackbox_exporter

白盒监控，黑盒监控：
我们监控主机的资源用量、容器的运行状态、数据库中间件的运行数据。这些都是支持业务和服务的基础设施
通过白盒能够了解其内部的实际运行状态，通过对监控指标的观察能够预判可能出现的问题，从而对潜在的不确定因素进行优化。
而从完整的监控逻辑的角度，除了大量的应用白盒监控以外，还应该添加适当的黑盒监控
黑盒监控即以用户身份测试服务的外部可见性，常见黑盒监控包括HTTP、TCP探针等用于检测站点或服务的可访问性、访问效率等
黑盒监控较于白盒监控不同在于黑盒监控是以故障为导向当故障发生时，黑盒监控能快速发现故障
而白盒监控则侧重于主动发现或预测潜在问题
一个完善的监控目标是要能够从白盒的角度发现潜在问题，能够在黑盒的角度快速发现已经发生的问题
```
#### Blackbox Exporter
```txt
Blackbox Exporter是Prometheus社区提供的官方黑盒监控解决方案，允许通过：HTTP、HTTPS、DNS、TCP、ICMP方式对网络进行探测
用户可以直接使用go get命令获取Blackbox Exporter源码并生成本地可执行文件：go get prometheus/blackbox_exporter

        modules:
          http_2xx:
            prober: http
            http:
              method: GET
          http_post_2xx:
            prober: http
            http:
              method: POST

从返回的样本中可以获取站点的DNS解析耗时、站点响应时间、HTTP响应状态码等和站点访问质量相关的监控指标，从而主动发现问题

与Prometheus集成：
只需要在Prometheus下配置对Blockbox Exporter实例的采集任务即可：

    - job_name: baidu_http2xx_probe
      params:
        module:            探针
        - http_2xx
        target:            探测目标
        - baidu.com
      metrics_path: /probe
      static_configs:
      - targets:            blackbox_exporter的地址
        - 127.0.0.1:9115
```