# 一般Web应用会需要静态文件渲染页面,通常是CSS与JavaScript文件.Flask的实现方法
# 是在包中或者模块的所在目录创建一个名为static的文件夹,在应用中通过/static访问.
# 给静态文件生成url

url_for('static',filename='style.css')  # 对应文件就存储在static/style.css