```bash
# https://www.cnblogs.com/hseagle/p/6015245.html

# 为避免fields data占用大量的jvm内存
# 可通过定期清理的方式来释放缓存的数据。释放的内容包括field data, filter cache, query cache

curl -XPOST "localhost:9200/_cache/clear"
```