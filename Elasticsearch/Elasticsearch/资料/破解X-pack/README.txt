使用此JAR替换掉：（先备份旧的jar）
~/elasticsearch/master-1/plugins/x-pack/x-pack-5.5.0.jar



替换所有ES节点的jar之后，重启所有ES节点，然后执行如下命令导入当前目录的许可文件：


curl -XPUT -u elastic:changeme 'http://192.168.86.128:9200/_xpack/license?acknowledge=true' -d @license.json


启用x-pack后，需要修改head插件的index.html文件：

    位于24、25行：
        auth_user : args["auth_user"] || "",
        auth_password : args["auth_password"],
    改为：
        auth_user : "elasticseach",     #账号
        auth_password: "changeme"       #密码