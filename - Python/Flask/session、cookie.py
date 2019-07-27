-------------------------------------------------- # session

@app.route('/set_session/')
def set_session():
    #设置session的持久化
    session.permanent = True 
    #设置session存活时间为10分钟
    app.permanent_session_lifetime = timedelta(minutes=10)
    session['username'] = 'wangyu'
    return '设置session'

@app.route('/get_session/')
def get_session():
    val = session.get('username','username值不存在')
    return '获取的seesion的值为{}'.format(val)

@app.route('/del_session/')
def del_session():
    username = session.pop('username')
    return '删除了session中{}的值'.format(username)

-------------------------------------------------- # cookie

#cookie常见参数设置:
response.set_cookie(
    key,        # 键
    value,      # 值
    max_age,    # 以秒为单位的cookie存活时间 
    expires,    # 失效时间需要datetime的对象
    path = '/'  # 存储的路径    
)

@app.route('/set_cookie/')
def set_cookie():
    response = make_response('设置cookie')
    response.set_cookie('name','zhangsan')              # 不设置存活时间 默认为当期浏览会话结束 
    response.set_cookie('name','zhangsan',max_age=10)   # 设置存活时间为None
    expires = time.time() + 10
    response.set_cookie('name','zhangsan',expires=expires) # 设置存活时间为时间戳的秒数
    return response


@app.route('/get_cookie/')
def get_cookie():
    var = request.cookies.get('name','获取不到name的值')
    return '获取cookie的值为{}'.format(var)


@app.route('/del_cookie/')
def del_cookie():
    response = make_response('清除cookie')
    response.delete_cookie('name')                      # 移除cookie的值
    expiraes = time.time()-10
    response.set_cookie('name','',expires=expires)      # 不设置存活时间默认为当期浏览会话结束 
    return response

-------------------------------------------------- # 以登录注册作例子


from flask import Flask, session, redirect, url_for, request

app = Flask(__name__)
app.secret_key = 'a3f:4AD3/3yXR~XHH!jm[s]daLWX/,?RT'

@app.route('/')
def index():
    #登录用户显示login username
    if 'username' in session:
        return 'login {}'.format(session['username'])
    return '还未登录'

@app.route('/login', methods=['GET', 'POST'])
def login():
    #登录界面
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return 'method is support'

@app.route('/logout')
def logout():
    #注销退出登录
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()