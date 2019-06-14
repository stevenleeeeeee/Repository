```bash
#使用非DSL语言的查询格式：/_search?q=key=value

#查询response=404的信息：
curl -XGET 'localhost:9200/logstash-2015.12.23/_search?q=response=404&pretty'

#查询来源地址:
curl -XGET 'localhost:9200/logstash-2015.12.23/_search?q=geoip.city_name=Buffalo&pretty'

```