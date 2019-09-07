#### KQL
```bash
# 布尔运算符 AND、OR、NOT 允许通过逻辑运算符组合多个子查询、运算符 AND、OR、NOT 必须大写

# 直接搜索关键字
输入关键字 "safari"，这样就可以搜索到所有有关 "safari" 的字段！

# 排除特定主机的三种日志类型后的日志，且消息中含有weblogic关键字
ip: xx.xx.xx.xx and messages: weblogic and not loglevel: info || warning || notice 

# 使用双引号包起来作为一个短语搜索
"like Gecko"

# 对关键字搜索时的引号使用上的区别：
field:value         # 限定字段全文搜索
filed:"value"       # 精确搜索：关键字加上双引号 

# 字段本身是否存在：
_exists_:http       # 返回结果中需要有http字段
_missing_:http      # 不能含有http字段

# 通配符：
# ? 匹配单个字符   * 匹配0到多个字符 ( ? * 不能用作第一个字符，例如：?text *text )
kiba?a, el*search

# Elasticsaerch支持部分正则功能，不过性能较差：
name: /joh?n(ath[oa]n)/

# 模糊搜索：
# 在一个单词后面加上~启用模糊搜索，可以搜到一些拼写错误的单词
key: quikc~
key: first~         # 这种也能匹配到 frist
# 还可以设置编辑距离（整数），指定需要多少相似度
cromm~1             # 会匹配到 from 和 chrome
# 默认2，越大越接近搜索的原始值，设置为1基本能搜到80%拼写错误的单词

# 近似搜索
# 在短语后面加上~，可以搜到被隔开或顺序不同的单词
"where select"~5    # 表示 select 和 where 中间可以隔着5个单词，可以搜到 select password from users where id=1

# 字段匹配200或404的文档
response:(200 or 404)

# 包含术语列表的多值字段的文档
tags:(success and info and security)

# 匹配响应不是200的所有文档以及使用简单正则匹配
not response: 200 and status: tex*

# 范围查询
account_number: < 100 OR balance: > 47500

# 中括号范围查询表示查询范围
status:[400 TO 499]
sip:["172.24.20.110" TO "172.24.20.140"]        # 对IP范围进行搜索需要先设置此字段为IP类型的映射
date:{"now-6h" TO "now"}                        # 时间范围
tag:{b TO e}                                    # 搜索b到e中间的字符
count:[10 TO *]                                 # * 表示一端不限制范围
count:[1 TO 5}                                  # [ ] 表示端点数值包含在范围内，{ } 表示端点数值不包含在范围内，可混合使用，此语句为1到5，包括1，不包括5

# 花括号范围查询表示排除此范围
account_number：{20 to *}

# 结果排除
# +：搜索结果中必须包含此项
# -：不能含有此项
+apache -jakarta test aaa bbb                   # 结果中必须存在apache，不能有jakarta，剩余部分尽量都匹配到
# Example:
status:[400 TO 499] AND (extension:php OR extension:html)
title:(+return +"pink panther")
host:(baidu OR qq OR google) AND host:(com OR cn)
mysql.method: SELECT AND mysql.size: [10000 TO *]
(mysql.method: INSERT OR mysql.method: UPDATE) AND responsetime: [30 TO *]

# 转义特殊字符
+ - = && || > < ! ( ) { } [ ] ^ " ~ * ? : \ /   # 左边的字符当作值搜索的时候需要用\转义
\(1\+1\)\=2                                     # 用来查询(1+1)=2
```

#### Kibana Monitoring UI
```txt
Search Rate：		    对于单个索引，它是每秒查找次数*分片数，对于多个索引，它是每个索引的搜索速率的总和
Search Latency：		每个分片中的平均延迟
Indexing Rate：		    对于单个索引，它是每秒索引的数量*分片数量，对于多个索引，它是每个索引的索引速率的总和
Indexing Latency：	    每个分片中的平均延迟

查看Kibana自身的状态信息：( 返回JSON格式状态信息 )
http://192.168.101.5:5601/api/status 
```
#### 可视化编辑器中 metric 和 bucket 的 Aggregations
```bash
Metric:
# 1、Count      count 聚合返回选中索引模式中元素的原始计数。
# 2、Average    这个聚合返回一个数值字段的 average 。从下拉菜单选择一个字段。
# 3、Sum sum    聚合返回一个数值字段的总和。从下拉菜单选择一个字段。
# 4、Min min    聚合返回一个数值字段的最小值。从下拉菜单选择一个字段。
# 5、Max max    聚合返回一个数值字段的最大值。从下拉菜单选择一个字段。
# 6、Unique Count cardinality           聚合返回一个字段的去重数据值。从下拉菜单选择一个字段。
# 7、Standard Deviation extended stats  聚合返回一个数值字段数据的标准差。从下拉菜单选择一个字段。
# 8、Percentile percentile              
# 聚合返回一个数值字段中值的百分比分布。从下拉菜单选择一个字段，然后在 Percentiles 框内指定范围。
# 点击 X 移除一个百分比框，点击 +Add 添加一个百分比框
# 9、Percentile Rank percentile ranks
# 聚合返回一个数值字段中你指定值的百分位排名。
# 从下拉菜单选择一个字段，然后在 Values 框内指定一到多个百分位排名值。
# 点击 X 移除一个百分比框，点击 +Add 添加一个数值框。

Bucket:
# 1、Date Histogram       基于数值字段创建，由时间组织起来。可指定时间片的间隔，单位: 秒/分/时/天/星期/月/年
# 2、Histogram            标准 histogram 基于数值字段创建。为这个字段指定整数间隔。勾选 Show empty buckets 让直方图中包含空的间隔
# 3、Range                通过 range 聚合。可以为一个数值字段指定一系列区间。点击 Add Range 添加一对区间端点。点击红色 (x) 符号移除一个区间
# 4、Date Range           聚合计算指定的时间区间内的值。你可以使用 date math 表达式指定区间。点击 Add Range 添加新的区间端点。点击红色 (/) 符号移除区间。
# 5、IPv4 Range           聚合用来指定 IPv4 地址的区间。点击 Add Range 添加新的区间端点。点击红色 (/) 符号移除区间。
# 6、Terms                terms 聚合允许你指定展示一个字段的首尾几个元素，排序方式可以是计数或者其他自定义的metric。
# 7、Filters              为数据指定一组filters。可以用querystring (全文搜索简易检所语法) 或 JSON 来指定过滤器，就像在 Discover 页的搜索栏一样。点击 Add Filter 添加下一个过滤器。
# 8、Significant Terms    展示实验性的 significant terms 聚合的结果。
# 9、也许你需要对某一个数据进行计算，你可以使用json表达式：
# { "script" : "doc['grade'].value * 1.2" }   <--- grade代表字段，后面后面是算数表达式。
```

#### 基于 Timelion 的可视化展示
```bash
# 参考：https://segmentfault.com/a/1190000016679290

# 将创建的第一个可视化将比较在用户空间中花费的CPU时间与一小时的结果偏移量的实时百分比，
# 为了创建这个可视化，我们需要创建两个Timelion表达式，一个是system.cpu.user.pct的实时平均数，另一个是1小时的平均偏移量。
# 首先，你需要在第一个表达式中定义 index、timefield、metric，并在Timelion查询栏中输入以下表达式。
.es(index=metricbeat-*, timefield='@timestamp', metric='avg:system.cpu.user.pct')

# 现在需要添加另一个具有前一小时数据的系列，以便进行比较，为此，你必须向.es()函数添加一个offset参数 
# offset将用日期表达式偏移序列检索。
# 对于本例，你希望将数据偏移一小时，并使用日期表达式-1h，使用逗号分隔这两个系列，在Timelion查询栏中新增以下表达式：
.es(offset=-1h,index=metricbeat-*, timefield='@timestamp', metric='avg:system.cpu.user.pct').label('last hour')

# 最终的表达式如下，另外可以对表达式来定制标签以便区分、设置title定义标题：
.es(index=metricbeat-*, timefield='@timestamp', metric='avg:system.cpu.user.pct').label('current hour'),
.es(offset=-1h,index=metricbeat-*, timefield='@timestamp', metric='avg:system.cpu.user.pct').label('last hour').title('CPU usage over time')

# 也可以在.es()函数后添加.lines()后缀来定义线条的类型，如：
.es(index=metricbeat-*, timefield='@timestamp', metric='avg:system.cpu.user.pct').label('current hour').lines(fill=1,width=0.5),.......

# 也可以对图表设置颜色：
.es(index=metricbeat-*, timefield='@timestamp', metric='avg:system.cpu.user.pct').label('current hour').title('CPU usage over time').color(#1E90FF)

# 也可以设置其可视化展示的位置：
.es(................).legend(columns=2, position=nw)
```

#### 状态码饼图展示
![饼图状态码](Docs/Images/饼图状态码.png)
#### Nginx返回时间统计
![Nginx返回时间统计](Docs/Images/Nginx返回时间统计.png)
#### 地区分布折线图
![地区分布折线图](Docs/Images/地区分布折线图.png)
#### 具体key数据计算
![具体key数据计算](Docs/Images/具体key数据计算.png)
#### 排除某部分数据
![排除某部分数据](Docs/Images/排除某部分数据.png)
#### 条形图分组
![条形图分组](Docs/Images/条形图分组.png)

#### Kibana 中常见的英文
```bash
Area chart                  # 面积图
Data table                  # 数据表
Heatmap chart               # 热力图
Line chart                  # 折线图
Markdown widget             
Metric                      # 度量标准
Pie chart                   # 饼图
Tag cloud                   # 标签云
Tile map                    # 拼贴地图
Timeseries                  # 时间序列
Vertical bar chart          # 直方图

metrics                     # 度量
Y-axis                      # Y轴
dot size                    # 点尺寸
Aggregation                 # 聚合
    Count                   # 数量统计
    Average                 # 平均数
    Sum                     # 求和
    Median                  # 中位数
    Min                     # 最小值
    Max                     # 最大值
    Standard Deviation      # 标准偏差
    Unique Count            # 唯一 数量统计
    Percentiles             # 百分位数
    Top Hit 
    Percentile Ranks        # 百分等级 
     
    Histogram               # 直方图
    Date Histogram 
    Range                   # 范围
    Date Range
    IPv4 Range
    Terms
    Filters
    Significant Terms
Field                       # 字段
Interval            
Custom Label                # *标注说明
buckets                     # 桶
```