
```bash
helm create mychart && tree mychart/        #创建名为 mychart 的 Chart:
mychart/
├── charts
├── Chart.yaml
├── requirements.yaml
├── templates
│   ├── deployment.yaml
│   ├── _helpers.tpl
│   ├── ingress.yaml
│   ├── NOTES.txt
│   └── service.yaml
└── values.yaml

2 directories, 7 files

# Chart.yaml            描述 Chart 的相关信息，包括名字、描述信息以及版本等
# requirements.yaml     列出chart依赖关系的YAML文件。如，lnmp的依赖关系。自动处理依赖
# values.yaml           存储 templates 目录中模板文件中用到变量的值
# NOTES.txt             介绍 Chart 部署后的信息，如：如何使用这个 Chart、列出缺省设置等
# Templates             目录下是 YAML 清单模板，该模板文件遵循 Go template 语法

# Templates 目录下YAML模板的值默认是在 values.yaml 里定义的
# 比如在 deployment.yaml 中定义的容器镜像：image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}" 
# 其中的 .Values.image.repository 的值就是在 values.yaml 里定义的 nginx，.Values.image.tag 的值就是 stable

#检查依赖和模板配置是否正确
$ helm lint mychart/
==> Linting .
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, no failures

#将应用打包
$ helm package mychart
Successfully packaged chart and saved it to: /home/k8s/mychart-0.1.0.tgz
```
```bash
#列出所有仓库：
helm repo list
#NAME    URL                                             
#stable  https://kubernetes-charts.storage.googleapis.com
#local   http://127.0.0.1:8879/charts 

#显示所有已部署版本的列表：
$ helm ls
NAME            	REVISION	UPDATED                 	STATUS  	CHART       	APP VERSION	NAMESPACE
wintering-rodent	1       	Thu Oct 18 15:06:58 2018	DEPLOYED	mysql-0.10.1	5.7.14     	default

#卸载：
$ helm delete wintering-rodent
#这将从Kubernetes卸载，但仍然可以请求有关该版本的信息：
$ helm status wintering-rodent

#在仓库中查找chart
helm search 

#查看该chart的介绍信息：
helm inspect stable/mongodb 

#直接下载该chart并安装该chart ( 获取chart：helm [fetch/get] stable/redis )
helm install stable/mongodb --set "persistence.enabled=false,serviceType=NodePort" --namespace default

#验证，该输出包含了模板的变量配置与最终渲染的YAML清单：
helm install --dry-run --debug <chart_dir> --name <release_name> --namespace default --values=values-My.yaml

#依据requirements文件将所有依赖项下载到"charts/"中。这样在部署时打包内的依赖都被自动完成安装
helm dependency update <CHARTS_NAME>

#删除已安装的服务
helm delete prometheus

#移除指定 Release 所有相关的 Kubernetes 资源和 Release 的历史记录
helm delete --purge prometheus

#版本升级：
helm upgrade releaseName .

#查看一个 Release 的所有变更记录
helm history mike-test

#回滚到版本1
helm rollback releaseName 1
```
#### chart example
```yaml
apiVersion：        #chartAPI版本，始终为v1（必填）
name：              #chart名称（必填），与目录名称保持一致
Version：           #SemVer 2版本（必填），版本格式
kubeVersion：       #SemVer系列兼容的Kubernetes版本（可选）
description：       #该项目的单句描述（可选）
keywords：
   -                #关于此项目的关键字列表（可选）
home：              #该项目主页的URL（可选）
sources：
   -                #此项目源代码的URL列表（可选）
maintainers：       #（可选）
   - name：         #维护者的名字（每个维护者都需要）
     email：        #维护者的电子邮件（每个维护者可选）
     url：          #维护者的URL（每个维护者可选）
engine：gotpl       #模板引擎的名称（可选，默认为gotpl）
icon：              #要用作图标的SVG或PNG图像的URL（可选）
appVersion：        #包含的应用程序版本（可选）。这不一定是SemVer。
deprecated：        #是否弃用此chart（可选，布尔值）
tillerVersion：     #此chart所需的Tiller版本。这应该表示为SemVer范围：> 2.0.0（可选）
```
#### requirements.yaml example
```yaml
dependencies:
  - name: apache
    version: 1.2.3
    repository: http://example.com/charts
  - name: mysql
    version: 3.2.1
    repository: http://another.example.com/charts
    alias: new-subchart-1   #有些依赖是通过特殊的名称进行依赖，此时可以用alias别名来定义依赖关系即可
```