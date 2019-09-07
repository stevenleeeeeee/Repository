#### 处理
```bash
# 禁用120s超时消息
echo 0 > /proc/sys/kernel/hung_task_timeout_secs

# 调小缓存 ( 脏页数量 )
sysctl -w vm.dirty_background_ratio=5
# 这个参数指定了当文件系统缓存脏页数量达到系统内存百分之多少时（如5%）就会触发pdflush/flush/kdmflush等后台回写进程运行
# 将一定缓存的脏页异步地刷入外存

sysctl -w vm.dirty_ratio=10
# 当文件缓存中脏数据到到vm.dirty_background_ratio设定的阀值后，所有新的I/O块都会被阻塞，直到脏页被写入磁盘。
```

#### 总结
```txt
关于内核hang住，导致ssh登录失败，系统响应缓慢。是由io阻塞应用程序导致的。

默认情况下Linux最多使用40%的可用内存作为文件系统缓存
当超过这个阈值后，文件系统会把将缓存中的数据全部写入磁盘，导致后续的IO请求都是同步的
将缓存写入磁盘时，有一个默认120秒的超时时间。

出现IO hang的问题的原因是IO子系统的处理速度不够快，不能在120秒将缓存中的数据全部写入磁盘。
IO系统响应缓慢，导致越来越多的请求堆积，导致系统失去响应

观察当前系统等待写盘的脏页数数量：
cat /proc/vmstat |egrep "dirty|writeback"

关于页缓存与脏页的原理说明：
https://www.cnblogs.com/linux130/p/5905582.html
```