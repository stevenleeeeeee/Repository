#/bin/python

# 请求钩子 使用装饰器实现。 Flask 支持以下 4 种钩子:
# before_first_request: 注册一个函数, 在处理第一个请求之前运行。
# before_request: 注册一个函数, 在每次请求之前运行。
# after_request: 注册一个函数, 如果没有未处理的异常抛出, 则在每次请求之后运行。
# teardown_request: 注册一个函数, 即使有未处理的异常抛出, 也在每次请求之后运行。

#在请求钩子和视图函数之间共享数据一般使用上下文全局变量  g。 
#例如 before_request 处理程序可以从数据库中加载已登录用户, 并将其保存到 g.user 中。随后调用视图函数时, 视图函数再使用 g.user 获取用户。

#Demo
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(debug=True)

#多个路由指向同一个视图
from flask import render_template

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

#重定向和错误
from flask import abort, redirect, url_for

@app.errorhandler(404)
def not_found(error):
    resp = make_response(render_template('error.html'), 404)
    resp.headers['X-Something'] = 'A value'
    return resp

@app.route('/')
def index():
    return redirect(url_for('login'))       #重定向

@app.route('/login')
def login():
    abort(404)          #返回错误码，调用not_found()视图函数进行执行
    this_is_never_executed()

#requests库
coding=utf-8
import requests
data={"username":"zhangsan","password":"123",}
r = requests.post('http://127.0.0.1:5000/login', data)

print r.status_code
print r.headers['content-type']
print r.encoding
print r.text

#Example
from flask import Flask,render_template,request
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

'''
<form action="/login" method="post">
    username: <input type="text" name="username">
    password: <input type="password" name="password">
    <input type="submit" id="submit">
</form>
'''

@app.route("/login",methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if username=="zhangsan" and password=="123":
            return "<h1>welcome, %s !</h1>" %username
        else:
            return "<h1>login Failure !</h1>"    
    else:
        return "<h1>login Failure !</h1>"

if __name__ == '__main__':
    app.run(debug=True)


#设置COOKIE 并设置过期时间
@app.route('/set_cookie')
def set_cookie():
	outdate=datetime.datetime.today() + datetime.timedelta(days=30)
    response=make_response('Hello World');
    response.set_cookie('Name','Hyman',expires=outdate)
    return response

#获取COOKIE
@app.route('/get_cookie')
def get_cookie():
    name=request.cookies.get('Name')
    return name

#删除COOKIE
@app.route('/del_cookie2')
def del_cookie2():
    response=make_response('delete cookie2')
    response.delete_cookie('Name')
    return response

#会话
from flask import Flask, session, redirect, url_for, escape, request

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

@app.route('/')
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return '''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
    '''
	
@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))


#会话7天有效
#encoding: utf-8

from flask import Flask,session
from datetime import timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7) # 配置7天有效


# 设置session
@app.route('/')
def set():
    session['username'] = 'liefyuan'
    session.permanent = True
    return 'success'

#表单提交
'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Document</title>
</head>
<body>
	<div align="center">
		<h2>User Management</h2>
			{% if message %} {{message}} {% endif %}
		<form method="POST">
			username:{{form.username}}
			<br>
			password:{{form.password}}
			<br>
			<input type="submit" value="Submit">
			<input type="reset" value="reset">
		</form>
	</div>
</body>
</html>
'''
from flask import Flask,request,render_template,redirect
from wtforms import Form,TextField,PasswordField,validators

app = Flask(__name__)

class LoginForm(Form):	#从wtforms 导入Form类,所有自定义的表单都需要继承这个类
    username = TextField("username",[validators.Required()])	#创建对象,[validators.Required()]表明这个值必须要输入
    password = PasswordField("password",[validators.Required()])

@app.route("/user",methods=['GET','POST'])
def login():
    myForm = LoginForm(request.form)
    if request.method =='POST':
		#一系列的Field对应html的input标签控件
        if myForm.username.data =="user" and myForm.password.data=="password" and myForm.validate():
            return redirect("http://www.baidu.com")
        else:
            message = "Failed Login"
            return render_template('login1.html',message=message,form=myForm)
    return render_template('login1.html',form=myForm)

if __name__ == '__main__':
    app.run(debug=True)

#文件上传
# coding:utf-8

from flask import Flask,render_template,request,redirect,url_for
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        basepath = os.path.dirname(__file__)  # 当前文件所在路径
        upload_path = os.path.join(basepath, 'static\uploads',secure_filename(f.filename))  #注意：没有的文件夹一定要先创建，不然会提示没有该路径
        f.save(upload_path)
        return redirect(url_for('upload'))
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
<<<<<<< HEAD:- Python/Flask/READEME.py


# 模板for语句自带的特殊变量
# loop.index	当前循环迭代的次数（从 1 开始）
# loop.index0	当前循环迭代的次数（从 0 开始）
# loop.revindex	到循环结束需要迭代的次数（从 1 开始）
# loop.revindex0	到循环结束需要迭代的次数（从 0 开始）
# loop.first	如果是第一次迭代，为 True 。
# loop.last	如果是最后一次迭代，为 True 。
# loop.length	序列中的项目数。
# loop.cycle	在一串序列间期取值的辅助函数。见下面的解释。


#模板内宏定义：
{% macro input(name, value='', type='text', size=20) -%}
    <input type="{{ type }}" name="{{ name }}" value="{{
        value|e }}" size="{{ size }}">
{%- endmacro %}

#模板内宏调用：
<p>{{ input('username') }}</p>
<p>{{ input('password', type='password') }}</p>

#模板宏的定义和调用：
{%macro showinfo(info)%}
    这是{{info}}！！！<br />
{%endmacro%}

{%for info in infos%}
    {{showinfo(info)}}
{%endfor%}

#导入外部 ( 从其他文件引入 ) 模板宏：{% import "minput.html" as minput %} or {% from 'base/macro/submit.macro' import test %}
=======
>>>>>>> 682048815943a27451270f861e8d07ea6c95ee34:- Python/Flask/README.py
