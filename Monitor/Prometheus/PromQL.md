```txt
Prometheus提供函数式表达式，实现实时查找和聚合时间序列数据
表达式计算结果可在图表中展示，也可在Prometheus表达式浏览器中以表格形式展示，或作为数据源,以HTTP API的方式向外提供能力

ref: https://yunlzheng.gitbook.io/prometheus-book/introduction
```
#### Example
```bash
#选择所有时间序列度量名称为http_requests_total的样本数据：
http_requests_total

#通过在度量指标名称后增加"{一组标签}"可进一步地过滤这些时间序列数据:
#这里选择度量指标名称为http_requests_total且其中标签名为job=prometheus, group=canary的时间序列数据
http_requests_total{job="prometheus",group="canary"}

#标签匹配操作如下所示：
=          #精确匹配标签给定的值
!=         #排除给定的标签值
=~         #正则匹配给定的标签值
!=~        #正则排除给定的标签值

#正则匹配标签environment为staging/testing,/development的值，且http方法不是GET：
http_requests_total{environment=~"staging|testing|development", method!="GET"}

#匹配空标签值的标签匹配器也可选择没有设置任何标签的所有时间序列数据。正则表达式完全匹配。
#向量选择器必须指定一个度量指标名称或者至少不能为空字符串的标签值。以下表达式是非法的:
{job=~".*"} #Bad!
#上面这个例子既没有度量指标名称，标签选择器也可以正则匹配空标签值，所以不符合向量选择器的条件
#相反地，下面这些表达式是有效的，第一个一定有一个字符。第二个有一个有用的标签method
{job=~".+"} # Good!
{job=~".*", method="get"} # Good!

#标签匹配器能够被应用到度量指标名称，使用__name__标签筛选度量指标名称:
#例如: 表达式: http_requests_total 等价于: {__name __="http_requests_total"}
#其他的匹配器，如：= ( !=, =~, !~) 都可以使用。下面的表达式选择了度量指标名称以"job:"开头的时间序列数据：
{name=~"^job:.*"}

#仅查询标签:
{instance="192.168.88.10"}

#范围向量选择器
#范围向量类似瞬时向量, 不同在于它们从当前实例选择样本范围区间。
#在语法上，时间长度被追加在向量选择器尾部的方括号[]中，用以指定对于每个样本范围区间中的每个元素应该抓取的时间范围样本区间
#时间长度由数值决定，后面可以跟下面的单位：
    s - seconds
    m - minutes
    h - hours
    d - days
    w - weeks
    y - years

#选择过去5分钟内度量指标名称为http_requests_total，标签为job="prometheus"的时间序列数据:
http_requests_total{job="prometheus"}[5m]

#偏移修饰符offset：
#偏移修饰符允许在查询中改变单个瞬时向量和范围向量中时间的偏移量
#例如下面表达式返回度量指标名称为http_requests_total相对于当前时间的前5分钟时刻的时间序列数据：
http_requests_total offset 5m

#注意：offset偏移修饰符必须直接跟在选择器后面，例如：
sum(http_requests_total{method="GET"} offset 5m) #正确的语法
#然而下面这种情况是不正确的：
sum(http_requests_total{method="GET"}) offset 5m #错误的语法

#offset偏移修饰符在范围向量上和瞬时向量用法一样的
#下面返回相对于当前时间前一周的过去5分钟的度量指标名称为http_requests_total的速率：
rate(http_requests_total[5m] offset 1w)

#rate函数直接计算区间向量v在时间窗口内平均增长速率
#主机节点最近两分钟内的平均CPU使用率
rate(node_cpu[2m])
#通过irate函数绘制的图标能够更好的反应样本数据的瞬时变化状态
irate(node_cpu[2m])
#irate函数相比于rate函数提供了更高灵敏度，不过当分析长期趋势或者在告警规则中，irate的这种灵敏度反而容易造成干扰
#因此在长期趋势分析或者告警中更推荐使用rate函数


#操作符
#Prometheus支持二元和聚合操作符：https://prometheus.io/docs/prometheus/latest/querying/operators/
#Prometheus的PromQL支持基本的逻辑运算和算术运算。对于两个瞬时向量, 匹配行为可以被改变：
#二元运算操作符支持scalar/scalar(标量/标量)、vector/scalar(向量/标量)、和vector/vector(向量/向量)间的操作
+       #加法
-       #减法
*       #乘法
/       #除法
%       #取模
^       #幂等

#在Prometheus系统中，比较二元操作符有：
==      #等于
!=      #不等于
>       #大于
<       #小于
>=      #大于等于
<=      #小于等于
#比较二元操作符被应用于scalar/scalar（标量/标量）、vector/scalar(向量/标量)，和vector/vector（向量/向量）
#比较操作符得到的结果是bool布尔类型值，返回: 1 or 0

#聚合操作符
#这些聚合操作符被用于聚合单个即时向量的所有时间序列列表，把聚合的结果值存入到新的向量中
sum             #在维度上求和
max             #在维度上求最大值
min             #在维度上求最小值
avg             #在维度上求平均值
stddev          #求标准差
stdvar          #求方差
count           #统计向量元素的个数
count_values    #统计相同数据值的元素数量（对value进行计数）
bottomk         #样本值第k个最小值（后n条时序）
topk            #样本值第k个最大值 eg: 查询最近5分钟内访问量前10的HTTP地址：topk(10, http_requests_total[5m])
quantile        #统计分位数（分布统计）

#这些操作符被用于聚合所有标签维度，或者通过without或by子句来保留不同的维度
<aggr-op>([parameter,] <vector expr>) [without | by (<label list>)] [keep_common]

#例如包含由group、application、instance的标签组成的时间序列数据，可通过以下方式计算去除instance标签的http请求总数：
sum(http_requests_total) without (instance)

#统计每个编译版本的二进制文件数量：
count_values("version", build_version)
#count_values用于时间序列中每个样本的唯一的值出现的次数
#count_values会为每个唯一的样本值输出一个时间序列，并且每个时间序列包含一个额外的标签

#通过所有实例获取http请求第5个最大值：
topk(5, http_requests_total)

#逻辑/集合二元操作符只能作用在即时向量：
and     #交集
or      #并集
unless  #补集

#函数：
#Prometheus提供了一些函数列表操作时间序列数据：https://prometheus.io/docs/prometheus/latest/querying/functions/
#中文参考：https://www.kancloud.cn/cdh0805010118/prometheus/719356

#一些函数有默认的参数，例如：
year(v=vector(time()) instant-vector)       #v是参数值，instant-vector是参数类型。vector(time())是默认值。

#返回输入向量的所有样本的绝对值
abs(v instant-vector)       

#如果赋值给它的向量具有样本数据，则返回空向量
#如果传递的瞬时向量参数没有样本数据，则返回不带度量指标名称且带有标签的样本值为1的结果
absent(v instant-vector)    

#当监控度量指标时如果获取到的样本数据是空的， 使用absent方法对告警是非常有用的
absent(nonexistent{job="myjob"})                        # => key: value = {job="myjob"}: 1
absent(nonexistent{job="myjob", instance=~".*"})        # => {job="myjob"} 1
absent(sum(nonexistent{job="myjob"}))                   # => key:value {}: 0

#返回度量指标名称是http_requests_total的所有时间序列样本数据：
http_requests_total

#返回度量指标名称是http_requests_total, 标签分别是job="apiserver, handler="/api/comments，且是5分钟内的所有时间序列：
http_requests_total{job="apiserver", handler="/api/comments"}[5m]
#注意：范围向量表达式结果不能直接在Graph图表中，但可以在"console"视图中展示

#使用正则可通过特定模式匹配标签为job的特定任务名，获取这些任务的时间序列：
http_requests_total{job=~"server$"}

#返回度量指标名称是http_requests_total且http返回码不以4开头的所有时间序列数据：
http_requests_total{status!~"^4..$"}

#使用函数，操作符等
#返回度量指标名称http_requests_total且过去5分钟的所有时间序列数据值速率：
rate(http_requests_total[5m])

#假设度量名称是http_requests_total且过去5分钟的所有时间序列数据的速率和，速率维度是job：
sum(rate(http_requests_total)[5m]) by (job)

#如果有相同维度的标签，可以使用二元操作符计算样本数据，返回值：key: value=标签列表：计算样本值。
#例如下面这个表达式返回每个实例剩余内存，单位是M, 如果两者的标签不同则需要忽略不同的部分：ignoring(label_lists)
#如果多对一，则采用group_left, 如果是一对多，则采用group_right：
(instance_memory_limit_byte - instant_memory_usage_bytes) / 1024 / 1024

#相同表达式，求和可以采用下面表达式：
sum( instance_memory_limit_bytes - instance_memory_usage_bytes) by (app, proc) / 1024 / 1024

#如果相同集群调度器任务，显示CPU使用率度量指标的话，如下所示：
instance_cpu_time_ns{app="lion", pro="web", rev="34d0f99", env="prod", job="cluster-manager"}
instance_cpu_time_ns{app="elephant", proc="worker", rev="34d0f99", env="prod", job="cluster-manager"}
instance_cpu_time_ns{app="turtle", proc="api", rev="4d3a513", env="prod", job="cluster-manager"}
......

#我们可以获取最高的3个CPU使用率，按照标签列表app和proc进行分类：
topk(3, sum(rate(instance_cpu_time_ns[5m])) by(app, proc))

#假设一个服务实例只有一个时间序列数据，那么通过下面表达式可以统计出每个应用的实例数量：
count(instance_cpu_time_ns) by (app)

#5分钟前的瞬时样本数据，或昨天一天的区间内的样本数据
http_request_total{} offset 5m
http_request_total{}[1d] offset 1d
---------------------------------------------------------------------------------  Example
#通过up指标可以获取到当前所有运行的Exporter实例以及其状态：
up{instance="localhost:8080",job="cadvisor"}    1
up{instance="localhost:9090",job="prometheus"}    1
up{instance="localhost:9100",job="node"}    1

#可通过label_replace标签为时间序列添加额外的标签：
label_replace(up, "host", "$1", "instance",  "(.*):.*")
#函数处理后，时间序列将包含一个host标签，host标签的值为Exporter实例的IP地址：
up{host="localhost",instance="localhost:8080",job="cadvisor"}    1
up{host="localhost",instance="localhost:9090",job="prometheus"}    1
up{host="localhost",instance="localhost:9100",job="node"} 1

#Histogram和Summary主用用于统计和分析样本的分布情况 ( summary是客户端计算后上报，histogram中位数涉及服务端计算 )
#例如统计延迟在0~10ms之间的请求数有多少而10~20ms之间的请求数又有多少。通过这种方式可以快速分析系统慢的原因
#Histogram和Summary都是为了能够解决这样问题的存在，通过Histogram和Summary类型的监控指标，可以快速了解监控样本的分布情况
#Histogram和Summary都可以同于统计和分析数据的分布情况，区别在于：Summary是直接在客户端计算了数据分布的分位数情况
#Histogram的分位数计算需要通过 histogram_quantile (φ float, b instant-vector) 函数进行计算
#其中φ（0<φ<1）表示需要计算的分位数，如果需要计算中位数φ取值为0.5，以此类推即可 ( 中位数：将数据按排序后处于中间的数值 )
#Summary提供一个quantiles的功能，可按"%"划分跟踪的结果。例如：quantile取值0.95，表示取采样值里面的95%数据。

#Histogram由以下形式组成：
<basename>_bucket{le="<upper inclusive bound>"}
<basename>_bucket{le="+Inf"}
<basename>_sum          #Value总和
<basename>_count        #总数
#主要表示一段时间范围内对数据进行采样（通常是请求持续时间或响应大小）并能对其指定区间及总数进行统计，通常展示为直方图
#Histogram需要通过<basename>_bucket计算quantile, 而 Summary 直接存储了 quantile 的值!
#例如一个直方图指标名称为 employee_age_bucket_bucket，要计算过去 10 分钟内 第 90 个百分位数，请使用以下表达式：
histogram_quantile(0.9, rate(employee_age_bucket_bucket[10m]))
#返回：
{instance="10.0.86.71:8080",job="prometheus"} 35.714285714285715
#这表示最近 10 分钟之内 90% 的样本的最大值为 35.714285714285715

#当φ为0.5时，即表示找到当前样本数据中的中位数：
quantile(0.5, http_requests_total)

#Summary:
#Summary和Histogram类似，由 <basename>{quantile="<φ>"}，<basename>_sum，<basename>_count 组成
#主要用于表示一段时间内数据采样结果（通常是请求持续时间或响应大小）它直接存储了quantile数据，而不是根据统计区间计算出来的

#k8s中的node在线率：
sum(kube_node_status_condition{condition="Ready", status="true"}) / sum(kube_node_info) * 100

#node的内存容量，转为GB单位:
node_memory_free_bytes_total / (1024 * 1024)

#获取http_requests_total请求总数是否超过10000，返回0和1，若为1则报警：
http_requests_total > 10000         # 结果为 true / false
http_requests_total > bool 10000    # 结果为 1 / 0

#查询主机的CPU使用率，可以使用表达式：
100 * (1 - avg(irate(node_cpu{mode='idle'}[5m])) by(job) )  
#其中irate是PromQL中的内置函数，用于计算区间向量中时间序列每秒的即时增长率

#对于Gauge类型的监控指标，通过PromQL内置函数delta可获取样本在一段时间内的变化，如计算CPU温度在2个小时内的差异：
delta(cpu_temp_celsius{host="zeus"}[2h])

#使用predict_linear()对数据的变化趋势进行预测。如预测系统磁盘空间在4小时之后的剩余情况：
predict_linear(node_filesystem_free{job="node"}[1h], 4 * 3600)

#基于2小时的样本数据，来预测主机可用磁盘空间的是否在4个小时候被占满：
predict_linear(node_filesystem_free{job="node"}[2h], 4 * 3600) < 0

#以主机为单位查询各主机的CPU使用率：
sum(sum(irate(node_cpu{mode!='idle'}[5m])) / sum(irate(node_cpu[5m]))) by (instance)

#数学运算，对单位进行转换
node_memory_free_bytes_total / (1024 * 1024)

#根据node_disk_bytes_written和node_disk_bytes_read获取主机磁盘IO的总量：
node_disk_bytes_written + node_disk_bytes_read

#通过数学运算符我们可以很方便的计算出当前所有主机的内存使用率：
(node_memory_bytes_total - node_memory_free_bytes_total) / node_memory_bytes_total

#当前内存使用率超过95%的主机：( 通过使用布尔运算符可以方便的获取 )
(node_memory_bytes_total - node_memory_free_bytes_total) / node_memory_bytes_total > 0.95
#通过以上可知，布尔运算符的默认行为是对时序数据进行过滤
#而在某些情况下可能需要的是真正的布尔结果而不是过滤结果，例如当前模块的HTTP请求量是否>=1000，如果大于等于1000则返回：1
#此时可用bool修饰符改变布尔运算的默认行为： ( eg: 2 == bool 2 # 结果为1 )
http_requests_total > bool 1000

#查询主机的CPU使用率: ( irate是PromQL中的内置函数，用于计算区间向量中时间序列每秒的即时增长率 )
100 * (1 - avg (irate(node_cpu{mode='idle'}[5m])) by(job) )

#count_values用于时间序列中每一个样本值出现的次数。
#count_values会为每一个唯一的样本值输出一个时间序列，并且每个时间序列包含一个额外的标签:
count_values("count", http_requests_total)

#topk和bottomk则用于对样本值进行排序，返回当前样本值前n位，或者后n位的时间序列:
#获取HTTP请求数前5位的时序样本数据，可以使用表达式：
topk(5, http_requests_total)

#quantile用于计算当前样本数据值的分布情况quantile(φ, express)其中 0 ≤ φ ≤ 1
#例如，当φ为0.5时，即表示找到当前样本数据中的中位数：
quantile(0.5, http_requests_total)

#increase(v range-vector)函数是PromQL中提供的众多内置函数之一
#其中参数v是一个区间向量，increase函数获取区间向量中的第一个后最后一个样本并返回其增长量。
#因此，可以通过以下表达式Counter类型指标的增长率：
increase(node_cpu[2m]) / 120
#这里通过node_cpu[2m]获取时间序列最近两分钟的所有样本
#increase计算出最近两分钟的增长量，最后除以时间120秒得到node_cpu样本在最近两分钟的平均增长率
#并且这个值也近似于主机节点最近两分钟内的平均CPU使用率。

#rate函数可以直接计算区间向量v在时间窗口内平均增长速率。因此，通过以下表达式可以得到与increase函数相同的结果：
rate(node_cpu[2m])

#预测Gauge指标变化趋势：
#predict_linear函数可预测时间序列v在t秒后的值。它基于简单线性回归的方式对时间窗口内的样本数据进行统计从而做出预测
#例如基于2小时的样本数据来预测主机可用磁盘空间的是否在4个小时候被占满，可以使用如下表达式：
predict_linear(node_filesystem_free{job="node"}[2h], 4 * 3600) < 0

#容器的 (cadvisor提供) 网络接收量速率（单位：字节/秒）：( without用于从计算结果中移除列举的标签，by相反 )
sum(rate(container_network_receive_bytes_total{image!=""}[1m])) without (interface)

#容器的 (cadvisor提供) 网络传输量速率（单位：字节/秒）：
sum(rate(container_network_transmit_bytes_total{image!=""}[1m])) without (interface)

#容器的 (cadvisor提供) 文件系统写入速率（单位：字节/秒）：
sum(rate(container_fs_writes_bytes_total{image!=""}[1m])) without (device)

#通过CPU使用时间计算CPU的利用率：
rate(node_cpu[2m])

#如果要忽略是哪一个CPU的，只需要使用without表达式，将标签CPU去除后聚合数据即可：
avg without(cpu) (rate(node_cpu[2m]))

#按照mode计算主机CPU的平均使用时间
avg(node_cpu) by (mode)

#如果需要计算系统CPU的总体使用率，通过排除系统闲置的CPU使用率即可获得:
1 - avg without(cpu) (rate(node_cpu{mode="idle"}[2m]))

#内存剩余百分比：
(sum(node_memory_MemTotal) - sum(node_memory_MemFree+node_memory_Buffers+node_memory_Cached) )  \
/ sum(node_memory_MemTotal) * 100

```
```bash
#假设存在如下数据：
method_code:http_errors:rate5m{method="get", code="500"}  24
method_code:http_errors:rate5m{method="get", code="404"}  30
method_code:http_errors:rate5m{method="put", code="501"}  3
method_code:http_errors:rate5m{method="post", code="500"} 6
method_code:http_errors:rate5m{method="post", code="404"} 21

method:http_requests:rate5m{method="get"}  600
method:http_requests:rate5m{method="del"}  34
method:http_requests:rate5m{method="post"} 120
#执行下面的查询：(左边相同标签及元素的数据除以右边相同标签及元素的数据，这里排除了code元素，所以两边能匹配到!)
method_code:http_errors:rate5m{code="500"} / ignoring(code) method:http_requests:rate5m
#输出：
{method="get"}  0.04            # //  24 / 600
{method="post"} 0.05            # //   6 / 120
#即每种 method 里 code 为 500 的请求数占总数的百分比，此处由于method为put/del的没有匹配元素所以没有出现在结果里

#多对一和一对多两种匹配模式指的是"一"侧的每一个向量元素可以与"多"侧的多个元素匹配的情况
#在这种情况下，必须使用group修饰符：group_left 或: group_right 来确定哪个向量具有更高的基数（充当"多"的角色）
#多对一和一对多两种模式一定是出现在操作符两侧表达式返回的向量标签不一致的情况!
#因此需要使用: ignoring和on 修饰符来排除或者限定匹配的标签列表

#例如使用表达式：
method_code:http_errors:rate5m / ignoring(code) group_left method:http_requests:rate5m
#该表达式中，左向量method_code:http_errors:rate5m包含两个标签method和code
#右向量method:http_requests:rate5m中只包含一个标签method，因此匹配时需要使用ignoring限定匹配的标签为code
#在限定匹配标签后，右向量中的元素可能匹配到多个左向量中的元素
#因此该表达式的匹配模式为多对一，需要使用group修饰符group_left指定左向量具有更好的基数
#最终的运算结果如下：
{method="get", code="500"}  0.04            # //  24 / 600
{method="get", code="404"}  0.05            # //  30 / 600
{method="post", code="500"} 0.05            # //   6 / 120
{method="post", code="404"} 0.175           # //  21 / 120
#提醒：group修饰符只能在比较和数学运算符中使用。在逻辑运算and,unless和or才注意操作中默认与右向量中的所有元素进行匹配 
```