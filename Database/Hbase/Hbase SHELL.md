#### hbase shell
```bash
# 查看hbase状态
status

# 查看所有表            
list

# 显示表名以abc开头的表
list 'abc.*'

# 描述表
describe '表名'

# 创建表
create '表名','列族名1','列族名2','列族名N'

# 判断表存在
exists '表名'

# 判断是否禁用启用表
is_enabled '表名'
is_disabled '表名'

# 添加记录
put '表名','rowkey','列族:列'，'值'

# 获取某个列族的某个列
get '表名','rowkey','列族:列'

# 查看记录rowkey下的所有数据
get '表名','rowkey'

# 查看所有记录
scan '表名'

# 查看表中的记录总数（行数）
count '表名'

# 删除记录 
delete '表名','行名','列族:列'

# 删除整行
deleteall '表名','rowkey'

# 删除一张表（先要屏蔽该表，才能对该表进行删除）
#第一步
disable '表名'
#第二步
drop '表名'

# 清空表
truncate '表名'

# 查看某个表某个列中所有数据
scan '表名',{COLUMNS=>'列族：列名'}

# 查看某个表中前10行的所有数据
scan '表名'，{LIMIT => 10}

# 扫描命名空间hbase下的meta表的列族info的列regioninfo，显示出meta表的列族info下的regioninfo列的所有数据
scan 'hbase:meta', {COLUMNS => 'info:regioninfo'}

# 范围查询
scan '表名',{STARTROW => 'row2',ENDROW => 'row3'}

# 更新记录
就是重新一遍，进行覆盖，hbase没有修改，都是追加

# 修改表属性，这里修改的TTL
alter 'tableName', NAME => 'cfname', TTL => 20

# 按时间范围取数据：
scan 'TraceV2', {TIMERANGE => [$yescurrentTimeStamp, $currentTimeStamp]}    # 这2个变量的以毫秒为单位的时间戳

```