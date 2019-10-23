#### 安装 GeoIP
```bash
wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz
tar -zxvf GeoLite2-City.tar.gz
cp GeoLite2-City.mmdb /data/logstash/       # 注:"/data/logstash"是Logstash的安装目录
```
#### Logstash-filter-geoip ( 排除私网地址 )
```bash
if [message] !~ "^127\.|^192\.168\.|^172\.1[6-9]\.|^172\.2[0-9]\.|^172\.3[01]\.|^10\." {
    geoip {
        source => "message"     #设置解析IP地址的字段
        target => "geoip"       #将geoip数据保存到一个字段内
        database => "/usr/share/GeoIP/GeoLite2-City.mmdb"       #IP地址数据库
    }
}

# Output：
# "geoip" => {
#                       "ip" => "112.90.16.4",
#            "country_code2" => "CN",
#            "country_code3" => "CHN",
#             "country_name" => "China",
#           "continent_code" => "AS",
#              "region_name" => "30",
#                "city_name" => "Guangzhou",
#                 "latitude" => 23.11670000000001,
#                "longitude" => 113.25,
#                 "timezone" => "Asia/Chongqing",
#         "real_region_name" => "Guangdong",
#                 "location" => [
#             [0] 113.25,
#             [1] 23.11670000000001
#         ]
#     }
```
#### 指定GeoIP输出的字段
```bash
# GeoIP库输出的数据较多，若不需要这么多内容可以通过fields选项指定所需。下例为全部可选内容
geoip {
　　fields => ["city_name", "continent_code", "country_code2", "country_code3", "country_name",
               "dma_code", "ip", "latitude", "longitude", "postal_code", "region_name", "timezone"]
}
```
#### 模拟geoip数据并在kibana端实现可视化展示（version 7.3+）
```bash
# 创建模板，指定geoip.localtion的类型为: geo_point
PUT _template/map_test
{
    "index_patterns" : [
      "map_test"                                # 要匹配的索引前缀
    ],
    "mappings" : {
      "properties" : {
        "geoip" : {
          "properties" : {
            "location" : {
                "type" : "geo_point",
                "ignore_malformed": "true"      # 忽略错误坐标信息
              }
            }
          }
        }
      }
    }
}

# 上传数据，geoip.localtion.lon、geoip.localtion.lat为经纬度信息
PUT /map_test/_doc/1233213213233
{
  "geoip": {
    "location": {
      "lon": 123.7167,
      "lat": 23.0333
    }
  }
}

# 在Kibana的管理界面设置索引模式，添加针对map_test索引的匹配规则

# 在Kibana的可视化见面创建座标地图"coordinate map" （其也能够根据坐标信息生成热力图）
# 存储桶的聚合类型为： Geohash
# 存储桶的聚合字段为： geoip.location

# 目前缺少上传地图图形: ( 需要处于外网，使Kibana能够访问到高德地图提供的坐标地图功能 )
# tilemap.url: 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}'
# tilemap.options.minZoom: "1"
# tilemap.options.maxZoom: "10"

# 目前缺少根据城市名称设置location的匹配
```