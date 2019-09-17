```bash
Jun 18 17:19:02 node1 kubelet: E0618 17:19:02.440519    8707 kubelet.go:2244] node "node1" not found
Jun 18 17:19:02 node1 kubelet: E0618 17:19:02.540841    8707 kubelet.go:2244] node "node1" not found
Jun 18 17:19:02 node1 systemd: Removed slice User Slice of root.
Jun 18 17:19:02 node1 kubelet: E0618 17:19:02.641314    8707 kubelet.go:2244] node "node1" not found
Jun 18 17:19:02 node1 kubelet: E0618 17:19:02.741886    8707 kubelet.go:2244] node "node1" not found


# 格式说明：
# PRI
#     即Priority(优先级)，有效值范围为0 - 191。不能有空格、数字前也不能补0，合法的形式如：<15>
# 
#     PRI值包含两部分信息：Facility和Level
#         Facility值用于判断哪个程序产生了日志信息
#         Level值用于判断严重等级
# 
#     计算机方法：
#         PRI = Facility * 8 + Level
#         Facility = PRI / 8
#         Level = PRI % 8
# 
#     Facility可选值为：
#         0  kernel messages
#         1  user-level messages
#         2  mail system
#         3  system daemons
#         4  security/authorization messages
#         5  messages generated internally by syslogd
#         6  line printer subsystem
#         7  network news subsystem
#         8  UUCP subsystem
#         9  clock daemon
#         10 security/authorization messages
#         11 FTP daemon
#         12 NTP subsystem
#         13 log audit
#         14 log alert
#         15 clock daemon
#         16 local use 0 (local0)
#         17 local use 1 (local1)
#         18 local use 2 (local2)
#         19 local use 3 (local3)
#         20 local use 4 (local4)
#         21 local use 5 (local5)
#         22 local use 6 (local6)
#         23 local use 7 (local7)
# 
#     Level可选值为：
#         0  Emergency:     system is unusable
#         1  Alert:         action must be taken immediately
#         2  Critical:      critical conditions
#         3  Error:         error conditions
#         4  Warning:       warning conditions
#         5  Notice:        normal but significant condition
#         6  Informational: informational messages
#         7  Debug:         debug-level messages
# 
# HEADER
#     HEAD包含两部分信息：TIMESTAMP和HOSTNAME。
#         TIMESTAMP为时间值，格式为：Mmm dd hh:mm:ss。表示月日时分秒。
#         HOSTNAME为主机IP地址或主机名。
# 
#     注意：TIMESTAMP和HOSTNAME后都必须跟一个空格。
# 
# MESSAGE
#     MESSAGE包含两部分信息：TAG和CONTENT。
#         TAG为产生消息的程序或进程名称。为长度不超过32的字母数字字符串。
#         CONTENT为信息的详细内容。
# 
#     注意：TAG后的任何一个非字母数字字符都会表示TAG结束且CONTENT开始。
#           一般TAG结束的字符为左大括号([)或分号(;)或空格
```