#### 安装 GeoIP
```bash
wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz
tar -zxvf GeoLite2-City.tar.gz
cp GeoLite2-City.mmdb /data/logstash/       #注:"/data/logstash"是Logstash的安装目录
```
#### Logstash-filter-geoip
```bash
if [message] !~ "^127\.|^192\.168\.|^172\.1[6-9]\.|^172\.2[0-9]\.|^172\.3[01]\.|^10\." {        # 排除私网地址
    geoip {
        source => "message"     #设置解析IP地址的字段
        target => "geoip"       #将geoip数据保存到一个字段内
        database => "/usr/share/GeoIP/GeoLite2-City.mmdb"       #IP地址数据库
    }
}

# Output：
"geoip" => {
                      "ip" => "112.90.16.4",
           "country_code2" => "CN",
           "country_code3" => "CHN",
            "country_name" => "China",
          "continent_code" => "AS",
             "region_name" => "30",
               "city_name" => "Guangzhou",
                "latitude" => 23.11670000000001,
               "longitude" => 113.25,
                "timezone" => "Asia/Chongqing",
        "real_region_name" => "Guangdong",
                "location" => [
            [0] 113.25,
            [1] 23.11670000000001
        ]
    }
```
#### 指定GeoIP输出的字段
```bash
#GeoIP库输出的数据较多，若不需要这么多内容可以通过fields选项指定所需。下例为全部可选内容
geoip {
　　fields => ["city_name", "continent_code", "country_code2", "country_code3", "country_name",
               "dma_code", "ip", "latitude", "longitude", "postal_code", "region_name", "timezone"]
}
```
#### logstash 的正则表达式
```bash
#调用自带的正则模式：         %{SYNTAX:field_name}
#Logstash自定义正则的格式：  (?<field_name>the pattern)   或： (?<field_name>(the pattern))
#自定义正则内套用自带正则：   (?<str>(%{USERNAME}))
#当自定义正则未匹配时输出"-"  (?:%{}|-)

#先使用|左边的表达式进行匹配，若匹配不成功在使用右边的: 注:包裹表达式的括号没有特殊含义
(?:(?:[0-9]+(?:\.[0-9]+)?)|(?:\.[0-9]+))        #此处 | 的含义！

#使用多个表达式进行测试匹配:
(?:%{CISCOMAC}|%{WINDOWSMAC}|%{COMMONMAC})

#正则表达式中对分组进行命名：
#用户可以自己指定子表达式的组名。要指定一个子表达式的组名，请使用这样的语法：(?<Word>\w+)
#或者把尖括号换成'也行：(?'Word'\w+)) ，这样就把\w+的组名指定为Word了
#要反向引用这个分组捕获的内容，可以使用: \k<Word> ， 所以可以写成这样：\b(?<Word>\w+)\b\s+\k<Word>\b
#就是说，使用\k<word>对分组中匹配的内容进行反向引用再使用这个内容对文本进行匹配

#常用分组语法：
(exp)	            #匹配exp,并捕获文本到自动命名的组里
(?<name>exp)	    #匹配exp,并捕获文本到名称为name的组里，也可以写成(?'name'exp)
(?:exp)	            #匹配exp,不捕获匹配的文本，也不给此分组分配组号? ( 匹配pattern但不获取匹配结果，说这是非获取匹配 )
(?<=exp)	        #匹配exp后面的位置，Example: grep -oP '(?<=<(\w+)>).*(?=<\/\1>)'
(?=exp)	            #匹配exp前面的位置，Example: grep -oP '(?<=begin).*(?=end)'
(?<!exp)	        #匹配前面不是exp的位置： (?<![a-z])\d{7} ---> 匹配前面不是小写字母的七位数字
                    #匹配前面不是小写字母的七位数字 ---> (?<![a-z])\d{7}
(?!exp)	            #匹配后面跟的不是exp的位置： \d{3}(?!\d) ---> 匹配三位数字而且这三位数字的后面不能是数字
                    #匹配不包含连续字符串abc的单词 ---> \b((?!abc)\w)+\b
(?#comment)	        #这种类型的分组不对正则表达式的处理产生任何影响，用于提供注释让人阅读

#零宽断言：
#详细分析表达式  (?<=<(\w+)>).*(?=<\/\1>)  这个表达式最能表现零宽断言的真正用途

\w                  #一个单词
\s+                 #此处的\s代表空格，+代表1个或无穷多个 ( 匹配任何空白字符，包括空格、制表符、换页符等等 )
\S	                #匹配任何非空白字符。等价于 [^ \f\n\r\t\v]
\b	                #匹配一个字边界，即字与空格间的位置
\B	                #非字边界匹配
%{PATH:envpath}     #调用Grok库里的%{PATH}，match Unix或Windows路径；重命名为envpath
|                   #或的关系

(?<Url>[\/A-Za-z0-9\.]+)                                #/AUTO/users/loginSuccess.do
(?<Date>[0-9\-]+\s[0-9\:]+)                             #2018-11-22 16:30:58 ( 此处使用自定义正则 )
(?<User_ip>[0-9\.]+)                                    #10.173.28.112 ( 此处使用自定义正则 )
\[\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3}\]          #[2016-11-01 16:48:24,946]
(?<Date>(\d*[./-]\d*[./-]\d* \d*:\d*:\d*[.,][0-9]+))    #匹配时间

#使用自定义的表达式时需要指定"patterns_dir"变量，变量内容指向表达式文件所在的目录
#通过形如 (?:%{WORD:user_name}|-) 的方式进行匹配，即为空时显示 "-"
#自定义正则模式时若使用 "(...)" 的方式时，此括号用于标记一个子表达式的开始和结束位置。子表达式可以获取供以后使用!
#如果在捕获数据时想进行数据类型转换可使用这种语法: %{NUMBER:Number:int} 
#默认情况下所有的返回结果都是string类型，当前Logstash所支持的转换类型仅有 int、float
#一般的正则表达式只能匹配单行文本，如果一个Event的内容为多行，可以在pattern前加"(?m)"
```
#### filter
```bash
# 哈希是键值对的集合中指定的格式，多键值对的条目以空格分隔而不是逗号：match => { "Key1" => "value1" "Key2" =>"value2" }
# 条件语法: if EXPRESSION { ... } else if EXPRESSION { ... } else { ... }
# 条件表达式支持的比较运算符:
    比较： ==, !=, <, >, <=, >=
    正则： =~, !~(是否使用正则匹配)
    包含： in,not in (是否包含)
    支持的布尔运算符:  and，or，nand，xor
    支持的一元运算符:  ！
# Grok的原理是将文本模式组合成与日志匹配的内容，语法: %{预定义的匹配标识:标识符:[int/float]]}

#Example:
#原文：
55.3.244.1 GET/index.html 15824 0.043
#匹配:
grok {          #其中的 "message" 这个key，特指从名为 "message" 的key中执行grok的匹配操作!
 match => { "message" => "%{IP:client} %{WORD:method} %{URIPATHPARAM:request} %{NUMBER:bytes}%{NUMBER:duration}"}   
}
#输出：
{
    client: 55.3.244.1
    method: GET
    request: /index.html
    bytes: 15824
    duration: 0.043
}

#注：有时logstash没有需要的模式。为此，可以有几个选择
#使用Oniguruma语法进行命名捕获，它可以匹配一段文本并将其保存为字段，格式：(?<field_name>自定义模式）
#例如后缀日志具有queue id10或11个字符的十六进制值。可以像这样轻松捕获：(?<queue_id>[0-9A-F] {10,11})
#这样经过过滤之后会多一个标识符为queue_id的json字段：queue_id: BEF25A72965

#注：一般的正则表达式只能匹配单行文本，如果一个Event的内容为多行，可以在pattern前加 (?m)

#如果把"message"里所有的信息通过grok匹配成不同的字段，数据实质上就相当于是重复存储了两份。
#所以可用 remove_field 参数删除掉 message 字段或用 overwrite 参数来重写默认的 message 字段，只保留最重要的部分
#示例：
filter {
    grok {
 match => {"message" => "%{IP:client} %{WORD:method} %{URIPATHPARAM:request} %{NUMBER:bytes}%{NUMBER:duration}"}
        overwrite => ["message"]
        #remove_field => ["message"]
    }
}

#add_tag增加一些标签

#mutate过滤器允许对字段执行常规突变。可重命名、删除、替换、修改事件中的字段
#它提供了丰富的基础类型数据处理能力。包括类型转换，字符串处理和字段处理等
#示例：
mutate {
        convert => ["reqTime","integer","statusCode","integer","bytes","integer"]
        convert => {"port"=>"integer"}
}

#copy过滤器将现有字段覆盖到另一个字段，并覆盖现有的目标字段，copy的值类型是哈希
#示例：
mutate {
        copy => {"source_field" => "dest_field" }
}

#gsub用于字符串的替换，替换的值可以用正则表达式和字符串
#gsub配置的值类型为数组，三个为一组，分别表示：字段名、待匹配字串或正则、待替换字符串
#示例：( 在使用正则表达式的时候要注意需要转义的字符用反斜杠转义 )
mutate {
    gsub => [
        "fieldname", "/", "_",             #将斜杠替换成_
        "fieldname2", "[\\?#-]", "."       #将\?#-替换成-
    ]
}

#split将字符串以分隔符分割成数组，只能用于字符串字段，值类型为哈希
#示例:
mutate {
    split => { "message" => "," }
}

#join使用分隔符将数组连接成字符串，join的值类型是哈希
#示例：
mutate {
    join => { "fieldname" => "," }
}

#lowercase和uppercase将字符串转换成小写或大写，值类型默认是数组
#示例:
mutate {
    lowercase => [ "fieldname" ]
    uppercase => [ "fieldname" ]
}

#merge合并两个数组或者哈希的字段，若是字符串格式自动转化成数组，值类型是哈希，合并多个字段可以用数组格式
#示例:
mutate {
    merge => {"message" => "host"}
}
#或:
mutate {
    merge => ["message","host","@version","@timestamp"]
}

#rename重命名某个字段，值类型为哈希
#示例:
mutate {
    rename => {"host" => "hostname"}     #将host字段重命名为hostname
}

#update更新一个已存在字段的内容，如果字段不存在则不会新建，值类型为哈希
#示例:
mutate {
    update => { "message" => "asd" }
}

#replace替换一个字段的内容，如果字段不存在会新建一个新的字段，值类型为哈希
#示例:
mutate {
    replace => {"type" =>"mutate"}    #添加一个新的字段type
}

#coerce为一个值为空的字段添加默认值，可以配合add_field,值类型为哈希
#示例:
mutate {
    coerce =>{"field"=>"a123"}
    add_field =>{"field"=>"asd"}
}

#strip去掉字段首尾的空格，值类型是数组
#示例:
mutate {
    strip=>["field1","field2"]
}

filter {        # 小demo 要注意...
        if [loglevel] == "debug" {      #删除调试级别的日志消息
            drop { }
        }
        grok{
                match => {"message" => "\ -\ -\ \[%{HTTPDATE:timestamp}\]"}
        }
                #date插件用于解析字段中的日期，然后使用该日期或时间戳作为事件的logstash时间戳
        date{   #从字段解析日期以用作事件的Logstash时间戳。以下配置解析名为logdate的字段以设置Logstash时间戳
                match => ["timestamp","dd/MMM/yyyy:HH:mm:ss Z"]
        }
        remove_field => "example"
}

#mutate插件的执行顺序：
rename(event) if @rename
update(event) if @update
replace(event) if @replace
convert(event) if @convert
gsub(event) if @gsub
uppercase(event) if @uppercase
lowercase(event) if @lowercase
strip(event) if @strip
remove(event) if @remove
split(event) if @split
join(event) if @join
merge(event) if @merge

#解析键值对, 假设有一条包含以下键值对的日志消息：
    ip=1.2.3.4 error=REFUSED
    #以下配置将键值对解析为字段：
    filter {
      kv { }
    }
    #应用过滤器后，示例中的事件将具有以下字段：
    ip: 1.2.3.4
    error: REFUSED

#根据散列或文件中指定的替换值替换字段内容。目前支持这些文件类型：YAML，JSON和CSV
#以下示例采用response_code字段的值，将其翻译为基于字典中指定的值的描述，然后从事件中删除response_code字段：
filter {
  translate {
    field => "response_code"
    destination => "http_response"
    dictionary => {
      "200" => "OK"
      "403" => "Forbidden"
      "404" => "Not Found"
      "408" => "Request Timeout"
    }
    remove_field => "response_code"
  }
}

filter{
        #date插件用于解析字段中的日期，然后使用该日期或时间戳作为事件的logstash时间戳
    date{
        #还记得grok插件剥离出来的字段logdate吗，就是在这里使用的。你可以格式化为需要的样子。
        #对于老数据来说这非常重要，因为需修改@timestamp字段的值，如果不修改，保存进ES的时间就是系统但前时间（+0 时区）
        #当格式化以后就可以通过target属性来指定到 @timestamp，这样数据的时间就是准确的，这对以后图表的建设来说万分重要!
        #最后，logdate这个字段已经没有任何价值，所以顺手将此字段从event对象中移除
        match => ["logdate","dd/MMM/yyyy:HH:mm:ss Z"]   #用于将指定的字段按照指定的格式解析
        target => "@timestamp"  #值类型是字符串，默认值即为: "@timestamp"
        timezone => 'xxx/xxx'   #值类型是字符串，没有默认值
        remove_field => 'logdate'
        #还需强调的是，@timestamp字段的值是不可以随便修改的，最好就按照数据的某个时间点来使用
    }
}
```