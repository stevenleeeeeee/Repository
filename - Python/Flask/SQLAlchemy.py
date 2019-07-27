#pip install flask-sqlalchemy

from flask.ext.sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

app=Flask(__name__)
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']=True
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(basedir,'data.sqlite')
# MySQL :  		mysql://username:password@hostname/database
# Postgres ：  	postgresql://username:password@hostname/database
# SQLite : 		sqlite:////absolute/path/to/database

# 程序使用数据库，并且获得所有功能
db=SQLAlchemy(app)


# 定义模型
class Role(db.Model):											# 角色 （1个角色对多个用户）
	__tablename__='roles'										# 定义表名
	# db.Column函数指定数据库中字段类型及各种属性
	id=db.Column(db.Integer,primary_key=True)					# 是否是主键 primary_key
	name=db.Column(db.String(64),unique=True,nullable=True)		# 是否唯一 unique, 是否可以为空 nullable
	info=db.Column(db.String(64),default='123',index=True)		# 默认值, 是否创建索引
	users=db.relationship('User',backref='role',uselist=True)	# 若uselist为False时为一对一关系
	# 添加到Role模型中的users属性代表这个关系的面向对象视角
	# 对于此Role类实例的users属性将返回与角色相关联的用户组成的列表类型
	# 第1个参数表明这个关系的另一端是哪个模型（类）。如果模型类尚未定义，可使用字符串形式指定
	# 第2个参数backref将向User类中添加一个role属性，从而定义反向关系
	# 此backref属性可替代role_id访问Role模型，此时获取的是模型对象，而不是外键的值。

	def __repr__(self):
		return '<Role %r>' % self.name

class User(db.Model):											# 用户
	__tablename__='users'
	id=db.Column(db.Integer,primary_key=True)					#
	username=db.Column(db.String(64),unique=True,index=True) 
	role_id=db.Column(db.Integer,db.ForeignKet('roles.id'))		# 指定外键是哪个表中哪个id ( 多的一方通过外键关联 )
	books = db.relationship('Book')								# 一对多
	
	def __repr__(self):
		return '<User %r>' % self.username

-------------------------------------------------- #数据库操作：

# 创建数据库和表
db.create_all()

# 删除数据库
db.drop_all()

# 初始化数据库连接: '数据库类型+数据库驱动名称://用户名:口令@机器地址:端口号/数据库名'
engine = create_engine('mysql+mysqlconnector://root:password@localhost:3306/test')

# 创建DBSession类型: ( SQLAlchemy )
DBSession = sessionmaker(bind=engine)

# 插入行
# 通过数据库会话管理对数据库所做的改动，在Flask-SQLAlchemy中由db.session表示，准备把队形写入数据库前先要将其添加到会话中
# 写入数据库需调用db.session.commit()
role_admin = Role(name='Admin')
user_tom = User(username='tom',role=role_admin)
user_jim = User(username='jim',role=role_admin)
user_tim = User(username='tim',role=role_admin)
user_sam = User(username='sam',role=role_admin)
db.session.add(role_admin)
db.session.add(user_tom)
db.session.add(user_jim)
db.session.commit()

# 修改行
# 我们将role_admin变量中name为Admin改成Administrator。
role_admin.name='Administrator'
db.session.add(role_admin)
db.session.commit()

# 删除行
# 删除Jim用户
db.session.delete(user_jim)
db.session.commit()

# 查询行
# 查询所有用户
User.query.all() #返回结果：[<User 'tom'>, <User 'tim'>, <User 'sam'>]

# 创建Query查询，filter是where条件，最后调用one()返回唯一行，如果调用all()则返回所有行:
user = session.query(User).filter(User.id=='5').one()

# 关闭session:
session.close()