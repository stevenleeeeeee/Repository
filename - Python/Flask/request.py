@app.route('/request/')
def get_http_message():
    print('获取完整的请求url',request.url)     
    print('获取去掉get传参的url',request.base_url)  
    print('获取主机名部分的url',request.host_url)   
    print('获取路由地址',request.path)           
    print('获取请求的方法',request.method)

    print('获取get传参',request.args['name'])
    print('获取get传参',request.args.get('name','该key不存在'))
    request.args.getlist(key)   #当key值存在相同时

    print('获取form表单传递过来的数据',request.form)
    print('获取form表单文件上传的数据',request.files)
    print('获取请求头信息',request.headers)
    print('获取cookie信息',request.cookies)
    print('获取传递过来的json',request.json)
    return  'request对象'

#应用到验证登录界面
from flask import Flask,request

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'], request.form['password']):
            return log_the_user_in(request.form['username'])
        else:
            error = '不合法username/password'
    return render_template('login.html', error=error)

    #当访问form中属性不存在时,会抛出一个特殊的 KeyError 异常,你可以像捕获标
    #准的 KeyError 一样来捕获它,不捕获它会显示一个 HTTP 400 Bad Request 错误页面。

#因此可以采用args属性来访问URL中提交的参数
value = request.args.get('name','')
#推荐使用该方式访问URL,因为用户可能会修改 URL，向他们展现一个 400 bad request 页面会影响用户体验