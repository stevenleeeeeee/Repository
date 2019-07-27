# HTML表单中指定enctype = 'multipart/form-data'属性,已上传的文件存储在内存中或者文件系统的临时位置
# 可以通过request.files来进行访问,每个上传的文件都会存储在这个字典里.

from flask import request,Flask
@app.route('/upload',methods=['GET','POST'])

def upload_file():
    if request.method == 'POST':
        file = request.files['file_name']   # 文件存储是一个字典,采用键值对方式取值
        flie.save('/usr/local/file.py')     # 可以保存到本地文件系统

        # 如果把文件按客户端提供的文件名存储在服务器上,文件名的访问最好采用secure_filename
        # file.save('/usr/local/file.py'+ secure_filename(file.filename))
