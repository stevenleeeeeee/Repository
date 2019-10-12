#### 跨索引关联查询，实现SQL关联查询的效果
```bash
curl -XGET 'http://localhost:9200/_msearch?pretty=true' -d '
{"index" : "<索引1>"}       # 索引1
{  "query" : { "bool" : { "filter" : {  "terms" : { "key1" : [ "123" ]} } } }, "fields" : [ "id", "title", "author", "publishTime"]}    # 索引1查询条件
{"index" : "<索引2>"}       # 索引2
{  "query" : { "bool" : { "filter" : {  "terms" : { "key2" : [ "123" ]} } } }, "fields" : [ "id", "title", "author", "publishTime"]}    # 索引2查询条件
'

-------------------------------------

# query demo:
{
	"query": {
		"bool": {
			"must": [{
				"term": {
					"data.arg.keyword": "123"
				}
			}, {
				"term": {
					"data.cmd.keyword": "456"
				}
			}],
		}
	},
}
```