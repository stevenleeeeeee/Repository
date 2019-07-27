# Doc ref: http://www.pythondoc.com/Flask-RESTful/quickstart.html
# pip install flask-restful


# ------------------------------------------------- Example

# 一个最小的 Flask-RESTful API 像这样:
from flask import Flask
from flask.ext import restful

app = Flask(__name__)
api = restful.Api(app)

class HelloWorld(restful.Resource):
    def get(self):
        return {'hello': 'world'}

api.add_resource(HelloWorld, '/')  

if __name__ == '__main__':
    app.run(debug=True)

# curl http://127.0.0.1:5000/
# {"hello": "world"}


# -------------------------------------------------  get put

from flask import Flask, request
from flask.ext.restful import Resource, Api

app = Flask(__name__)
api = Api(app)

todos = {}

class TodoSimple(Resource):
    def get(self, todo_id):
        return {
                todo_id: todos[todo_id]
            }

    def put(self, todo_id):
        return {
                todo_id: request.form['data']
            }

api.add_resource(TodoSimple, '/<string:todo_id>')

if __name__ == '__main__':
    app.run(debug=True)

# $ curl http://localhost:5000/todo1 -d "data=Remember the milk" -X PUT
# {"todo1": "Remember the milk"}
# $ curl http://localhost:5000/todo1
# {"todo1": "Remember the milk"}
# $ curl http://localhost:5000/todo2 -d "data=Change my brakepads" -X PUT
# {"todo2": "Change my brakepads"}
# $ curl http://localhost:5000/todo2
# {"todo2": "Change my brakepads"}


# -------------------------------------------------  Endpoints
# 很多时候在一个 API 中，资源可以通过多个 URLs 访问
# 可以把多个 URLs 传给 Api 对象的 Api.add_resource() 方法。每个 URL 都能访问到你的 Resource

api.add_resource(HelloWorld,'/','/hello')

# 也可以为资源方法指定 endpoint 参数
api.add_resource(Todo,'/todo/<int:todo_id>', endpoint='todo_ep')
# endpoint是用来给url_for反转url的时候指定的。如果不写endpoint，那么将会使用视图的名字的小写来作为endpoint


# -------------------------------------------------  参数解析
# 尽管 Flask 能够简单地访问请求数据(比如查询字符串或者 POST 表单编码的数据)，验证表单数据仍然很痛苦。
# Flask-RESTful 内置了支持验证请求数据，它使用了一个类似 argparse 的库。

from flask.ext.restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('rate', type=int, help='Rate to charge for this resource',required=True)
args = parser.parse_args()

# 需注意地是与 argparse 模块不同，reqparse.RequestParser.parse_args() 返回一个 Python 字典而不是一个自定义的数据结构
# 使用 reqparse 模块同样可以自由地提供聪明的错误信息
# 如果参数没有通过验证，Flask-RESTful 将会以一个 400 错误请求以及高亮的错误信息回应。
# $ curl -d 'rate=foo' http://127.0.0.1:5000/
# {'status': 400, 'message': 'foo cannot be converted to int'}

# default：默认值，如果这个参数没有值，那么将使用这个参数指定的值
# required：是否必须。默认为False，如果设置为True，那么这个参数就必须提交上来
# type：这个参数的数据类型，如果指定，那么将使用指定的数据类型来强制转换提交上来的值
# choices：选项。提交上来的值只有满足这个选项中的值才符合验证通过，否则验证不通过
# help：错误信息。如果验证失败后，将会使用这个参数指定的值作为错误信息
# trim：是否要去掉前后的空格

# -------------------------------------------------  数据格式化

from collections import OrderedDict
from flask.ext.restful import fields, marshal_with

resource_fields = {
    'task':   fields.String,
    'uri':    fields.Url('todo_ep')
}

class TodoDao(object):
    def __init__(self, todo_id, task):
        self.todo_id = todo_id
        self.task = task

        # This field will not be sent in the response
        self.status = 'active'

class Todo(Resource):
    @marshal_with(resource_fields)
    def get(self, **kwargs):
        return TodoDao(todo_id='my_todo', task='Remember the milk')

# 上面的例子接受一个 python 对象并准备将其序列化。marshal_with() 装饰器将会应用到由 resource_fields 描述的转换。
# 从对象中提取的唯一字段是 task。fields.Url 域是一个特殊的域，它接受端点（endpoint）名作参数并在响应中为该端点生成URL
# 许多你需要的字段类型都已经包含在内。请参阅 fields 指南获取一个完整的列表。


# ------------------------------------------------- 完整的例子

from flask import Flask
from flask.ext.restful import reqparse, abort, Api, Resource

app = Flask(__name__)
api = Api(app)

# 事先定义JSON模板
TODOS = {
    'todo1': {'task': 'build an API'},
    'todo2': {'task': '?????'},
    'todo3': {'task': 'profit!'},
}


def abort_if_todo_doesnt_exist(todo_id):
    ''' 若请求的参数(todo_id)不存在TODOS变量中时则返回404并携带错误消息 '''
    if todo_id not in TODOS:
        abort(404, message="Todo {} doesn't exist".format(todo_id))

# 定义参数解析 (类型检查)
parser = reqparse.RequestParser()
parser.add_argument('task', type=str)           # 数据类型检查对象，其检查key为task的类型为str，将在下面调用


# show a single todo item and lets you delete them
class Todo(Resource):
    def get(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)     # 调用 abort_if_todo_doesnt_exist 对参数进行检查其是否存在
        return TODOS[todo_id]                   # 返回请求的json

    def delete(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)     # 调用 abort_if_todo_doesnt_exist 对参数进行检查其是否存在
        del TODOS[todo_id]                      # 删除请求的json
        return '', 204                          # 返回204状态码

    def put(self, todo_id):                     # put 针对新建资源，其参数为新建的资源的key
        args = parser.parse_args()              # 实例化对上传的类型进行检查的对象
        task = {'task': args['task']}           # 检查名为task的子key的value是否为str类型
        TODOS[todo_id] = task                   # 添加JSON
        return task, 201

#   shows a list of all todos, and lets you POST to add new tasks
class TodoList(Resource):
    def get(self):
        return TODOS

    def post(self):
        # 使用 strict=True 调用 parse_args 能确保当请求包含你的解析器中未定义的参数时抛出一个异常
        args = parser.parse_args(strict=True)                   # 实例化对上传的类型进行检查的对象
        todo_id = int(max(TODOS.keys()).lstrip('todo')) + 1     # 新增Key编号
        todo_id = 'todo%i' % todo_id                            # 新增key名称: todo4
        TODOS[todo_id] = {'task': args['task']}                 # 设置json的key与value
        return TODOS[todo_id], 201                              # 返回数据及状态码

# 通过 api.add_resource() 方法来添加路由
# 第一个参数是视图类名（该类继承自Resource类），其成员函数定义了不同的 HTTP 请求方法的逻辑；第二个参数定义了 URL 路径
api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<todo_id>')


if __name__ == '__main__':
    app.run(debug=True)

# 获取列表
# 
# $ curl http://localhost:5000/todos
# {"todo1": {"task": "build an API"}, "todo3": {"task": "profit!"}, "todo2": {"task": "?????"}}
# 获取一个单独的任务
# 
# $ curl http://localhost:5000/todos/todo3
# {"task": "profit!"}
# 删除一个任务
# 
# $ curl http://localhost:5000/todos/todo2 -X DELETE -v
# 
# > DELETE /todos/todo2 HTTP/1.1
# > User-Agent: curl/7.19.7 (universal-apple-darwin10.0) libcurl/7.19.7 OpenSSL/0.9.8l zlib/1.2.3
# > Host: localhost:5000
# > Accept: */*
# >
# * HTTP 1.0, assume close after body
# < HTTP/1.0 204 NO CONTENT
# < Content-Type: application/json
# < Content-Length: 0
# < Server: Werkzeug/0.8.3 Python/2.7.2
# < Date: Mon, 01 Oct 2012 22:10:32 GMT
# 增加一个新的任务
# 
# $ curl http://localhost:5000/todos -d "task=something new" -X POST -v
# 
# > POST /todos HTTP/1.1
# > User-Agent: curl/7.19.7 (universal-apple-darwin10.0) libcurl/7.19.7 OpenSSL/0.9.8l zlib/1.2.3
# > Host: localhost:5000
# > Accept: */*
# > Content-Length: 18
# > Content-Type: application/x-www-form-urlencoded
# >
# * HTTP 1.0, assume close after body
# < HTTP/1.0 201 CREATED
# < Content-Type: application/json
# < Content-Length: 25
# < Server: Werkzeug/0.8.3 Python/2.7.2
# < Date: Mon, 01 Oct 2012 22:12:58 GMT
# <
# * Closing connection #0
# {"task": "something new"}
# 更新一个任务
# 
# $ curl http://localhost:5000/todos/todo3 -d "task=something different" -X PUT -v
# 
# > PUT /todos/todo3 HTTP/1.1
# > Host: localhost:5000
# > Accept: */*
# > Content-Length: 20
# > Content-Type: application/x-www-form-urlencoded
# >
# * HTTP 1.0, assume close after body
# < HTTP/1.0 201 CREATED
# < Content-Type: application/json
# < Content-Length: 27
# < Server: Werkzeug/0.8.3 Python/2.7.3
# < Date: Mon, 01 Oct 2012 22:13:00 GMT
# <
# * Closing connection #0
# {"task": "something different"}