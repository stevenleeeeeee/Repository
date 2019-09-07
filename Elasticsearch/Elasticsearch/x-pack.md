`https://www.elastic.co/guide/en/elasticsearch/reference/current/configuring-security.html`

#### 创建角色
```txt
curl -XPOST -u elastic 'localhost:9200/_security/role/events_admin' -H "Content-Type: application/json" -d '{
  "indices" : [
    {
      "names" : [ "events*" ],      # 索引名称
      "privileges" : [ "all" ]      # 权限
    },
    {
      "names" : [ ".kibana*" ], 
      "privileges" : [ "manage", "read", "index" ]
    }
  ]
}'
```

#### 创建用户
```txt
curl -XPOST -u elastic 'localhost:9200/_security/user/johndoe' -H "Content-Type: application/json" -d '{
  "password" : "userpassword",
  "full_name" : "John Doe",
  "email" : "john.doe@anony.mous",
  "roles" : [ "events_admin" ]
}'
```
#### 重置密码
```txt
PUT /_xpack/security/user/my_user/_password
{
  "password" : "elastic123"
}
```

#### 查询/禁用/启用/删除用户
```txt
GET /_xpack/security/user/<username>            # 查询特定用户
GET /_xpack/security/user/my_user,ctr           # 查询多个用户
GET /_xpack/security/user                       # 查询所有用户

PUT /_xpack/security/user/<username>/_disable   # 禁用
PUT /_xpack/security/user/<username>/_enable    # 启用

DELETE /_xpack/security/user/<username>         # 删除用户

GET _xpack/security/user/_has_privileges        # 查看当前用户的权限信息
# {
#   "cluster": [ "monitor", "manage" ],
#   "index" : [
#     {
#       "names": [ "suppliers", "products" ],
#       "privileges": [ "read" ]
#     },
#     {
#       "names": [ "inventory" ],
#       "privileges" : [ "read", "write" ]
#     }
#   ]
# }
```

