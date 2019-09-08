tar -zxf node-v8.1.4-linux-x64.tar.gz 
ln -sv node-v8.1.4-linux-x64 node

cat >> ~/.bash_profile <<'EOF'
NODE_HOME=/root/node
PATH=$NODE_HOME/bin:$PATH:$HOME/bin
export NODE_HOME
export PATH
EOF


# 软件
/root/node/node_modules/.bin/elasticdump

./elasticdump  --input=http://192.168.1.1:9200/original --output=http://192.168.1.2:9200/newCopy --type=mapping  
./elasticdump  --input=http://192.168.1.1:9200/original --output=http://192.168.1.2:9200/newCopy --type=data

# 如果索引很多懒得一个个迁移，那么可改用这个命令
# 加个--all=true，input与output里不需要把索引名加上，这样就可以自动把原机器上的所有索引迁移到目标机器
./elasticdump  --input=http://192.168.1.1:9200/ --output=http://192.168.1.2:9200/ --all=true  

elasticdump \
  --input=http://production.es.com:9200/my_index \
  --output=/data/my_index_mapping.json \
  --type=mapping

elasticdump \
  --input=http://production.es.com:9200/my_index \
  --output=/data/my_index.json \
  --type=data

# ---------------------------------------------------------------------------------------------------
# 使用logstash:
# 执行后会将源Cluster中所有index全部copy到目标Cluster中，并将mapping信息携带过去，随后开始逐步做index内的数据迁移
# 建议：正式执行的时候 ---> stdout { codec => rubydebug { metadata => true } }

# metadata：
# logstash 1.5版本后使用了metadata的概念来描述1次event并允许被用户修改，但不会写到event的结果中对event的结果产生影响
# 除此之外metadata将作为event的元数据描述信息，可以在input、filter、output三种插件的全执行周期内存活

# docinfo：
# elasticsearch input插件中的一个参数，默认是false
# 官网原文是"If set, include Elasticsearch document information such as index, type, and the id in the event."
# 意味着设置此字段后，会将index、type、id等信息全部记录到event中去，即metadata中去
# 这也就意味着可以在整个event执行周期内，使用者可随意的使用index、type、id这些参数了 

# elasticsearch input插件中的index参数支持通配符，可使用"*"这样的模糊匹配通配符来表示所有对象 
# 由于metadata的特性，我们可以在output中直接"继承"input中的index、type信息
# 并在目标Cluster中直接创建和源Cluster一摸一样的index和type，甚至是id（还需要处理映射!）

input {
    elasticsearch {
        hosts => ["host"]
        user => "**********"
        password => "*********"
        docinfo => true             # 读取文档的元数据并出书到filter、output ( 均是以"@"符号开头 )
        index => "*"                # 该通配符代表需要读取所有index信息
        size => 1000
        scroll => "1m"
        codec => "json"
    }
}

# 该部分filter是可选的
filter { }

output {
    elasticsearch {
        hosts => ["yourhost"]
        user => "********"
        password => "********"
        index => "%{[@metadata][_index]}"
    }
    stdout {
        codec => rubydebug {
            metadata => true
        } 
    }
}