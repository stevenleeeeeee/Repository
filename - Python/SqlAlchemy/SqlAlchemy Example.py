#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 用于将数据库表结构用对象表示出来

from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey

# 创建对象的基类
Base = declarative_base()

# 定义User对象
class User(Base):
    # 表名字
    __tablename__ = 'user'
    
    # 表结构
    id = Column(String(20), primary_key = True)
    name = Column(String(20))
    
# 初始化数据库连接，字串表示连接信息：数据库类型+数据库驱动名称://用户名:口令@机器地址:端口号/数据库名
engine = create_engine('mysql+mysqlconnector://root:wangh@localhost:3306/test')
# 创建DBSession类型
DBSession = sessionmaker(bind = engine)
# 初始化完成

# 创建session对象
session = DBSession()
# 创建User对象，添加到session
new_user = User(id = '5', name = 'Bob')
session.add(new_user)
# 提交及保存到数据库
session.commit()
# 关闭
session.close()

# 创建session并创建Query查询，filter是where条件，最后调用one 是返回为一行，all则返回所有行
session = DBSession()
user = session.query(User).filter(User.id == '5').one()
# 打印
print 'type: ', type(user)
print 'name: %s' % user.name
session.close()

# 如果一个User拥有多个Book，则可以对那个一一对多关系
class User(Base):
    __tablename__ = 'user'
    
    id = Column(String(20), primary_key = True)
    name = Colum(String(2))
    
    # 一对多
    books = relationship('Book')

class Book(Base):
    __tablename__ = 'book'
    
    id = Column(String(20), primary_key = True)
    name = Column(String(20))
    # ‘多’的一方book表是通过外键关联到user表
    user_id = Column(String(20)), ForeignKey('user.id')
# 当我们查询一个User对象时，该对象的books属性将返回一个包含若干个Book对象的list，这会不会影响效率，因为我值查询User，可能并不关心Book

# -------------------------------------------------

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql+pymysql://fxq:123456@192.168.100.101/sqlalchemy')
DBsession = sessionmaker(bind=engine)
session = DBsession()

Base = declarative_base()

class Student(Base):
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    age = Column(Integer)
    address = Column(String(100))

student1 = Student(id=1001, name='ling', age=25, address="beijing")
student2 = Student(id=1002, name='molin', age=18, address="jiangxi")
student3 = Student(id=1003, name='karl', age=16, address="suzhou")

session.add_all([student1, student2, student3])
session.commit()
session.close()

# ------------------------------------------------- CRUD

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Student(Base):
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    age = Column(Integer)
    address = Column(String(100))

engine = create_engine('mysql+pymysql://fxq:123456@192.168.100.101/sqlalchemy')
DBSession = sessionmaker(bind=engine)
session = DBSession()

my_stdent = session.query(Student).filter_by(name="fengxiaoqing2").first()
print(my_stdent)
# 在查询出来的数据sqlalchemy直接给映射成一个对象
# 对象和建表时的class是一致的，也可以直接通过对象的属性就可以直接调用:
my_stdent = session.query(Student).filter_by(name="fengxiaoqing2").first()
print(my_stdent.id, my_stdent.name, my_stdent.age, my_stdent.address)

# Example:
session.query(Student).filter(Student.name.like("%feng%"))

# equals:
query(Student).filter(Student.id == 10001)

# not equals:
query(Student).filter(Student.id != 100)

# LIKE:
query(Student).filter(Student.name.like(“%feng%”))

# IN:
query(Student).filter(Student.name.in_(['feng', 'xiao', 'qing']))

# not in
query(Student).filter(~Student.name.in_(['feng', 'xiao', 'qing']))

# AND:
from sqlalchemy import and_
query(Student).filter(and_(Student.name == 'fengxiaoqing', Student.id ==10001))
# 或者
query(Student).filter(Student.name == 'fengxiaoqing').filter(Student.address == 'chengde')

# OR:
from sqlalchemy import or_
query.filter(or_(Student.name == 'fengxiaoqing', Student.age ==18))

# all() 返回一个列表，可以通过遍历列表来获取每个对象
session.query(Student).filter(Student.name.like("%feng%")).all()

# 查询User表中所有数据：
User.query.all()

# one() 返回且仅返回一个查询结果。当结果的数量不足一个或者多于一个时会报错
# first() 返回至多一个结果，且以单项形式，而不是只有一个元素的tuple形式返回这个结果

# filter()和filter_by()的区别：
# Filter：        可以像写 sql 的 where 条件那样写 > < 等条件，但引用列名时，需通过 类名.属性名 的方式。
# filter_by：     可以使用 python 的正常参数传递方法传递条件，指定列名时，不需要额外指定类名。
#                 参数名对应名类中的属性名，但似乎不能使用 > < 等条件。

# 当使用filter时条件之间是使用"=="，fitler_by使用的是"="
user1 = session.query(User).filter_by(id=1).first()
user1 = session.query(User).filter(User.id==1).first()

# filter不支持组合查询，只能连续调用filter来变相实现。
# 而filter_by的参数是**kwargs，直接支持组合查询。比如：
q = session.query(IS).filter(IS.node == node and IS.password == password).all()

# 按照一个条件过滤数据记录:
User.query.filter_by(name = 'Administrator').first()
User.query.filter_by(name = 'Administrator').all()
User.query.filter_by(name = 'Administrator').one()

# 按照两个条件过滤数据记录（where and）
User.query.filter_by(role_id = 3, username = 'susan').first()
User.query.filter_by(role_id = 3, username = 'susan').all()

# 更新就是查出来然后直接更改就可以了:
my_stdent = session.query(Student).filter(Student.id == 1002).first()
my_stdent.name = "fengxiaoqing"
my_stdent.address = "chengde"
session.commit()

# 删除其实也是跟查询相关的，直接查出来，调用delete()方法直接就可以删除：
session.query(Student).filter(Student.id == 1001).delete()
session.commit()
session.close()

# 统计：
session.query(Student).filter(Student.name.like("%feng%")).count()

# 求和：
User.query.with_entities(func.sum(User.role_id)).all()

# 平均数:
User.query.with_entities(func.avg(User.role_id)).all()

# 限制：
User.query.filter_by(role_id = 3).limit(1).offset(1).all()

# 分组：
session.query(Student).group_by(Student.age)

# 排序 order_by() 反序在order_by里面用desc()方法：
session.query(Student).filter(Student.name.like("%feng%")).order_by(Student.id.desc()).all()

# 将ORM的查询语句转换为SQL
str(User.query.limit(1))

# ------------------------------------------------- relationship
# 一对多关系：
# 一个客户可以创建多个订单，而一个订单只能对应一个客户：
# 订单表通过外键（foreign key）来引用客户表，客户表通过 relationship() 方法来关联订单表：

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    order = relationship('Order', backref='users')      # 一个客户可以创建多个订单(相当于Order.users.name 可查本表对应的数据)
    # relationship根据定义的表之间的外键"ForeignKey"来关联表间数据的关系
    # backref是反向引用，这里即使得Order实体可通过Order.users.name可获取到此Order实例相关联的User表的name属性的值!
    # 此外，抛开backref参数，也可以使用User.order(对象)的方式获取用户实体对应的Order信息

class Order(Base):
    __tablename__ = 'order'
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))   # 限制此列的外键为User表中的id列，一个订单只能对应一个客户

# 依据用户查询订单：
order = session.query(User).filter(User.name == 'kein').first().order
# 依据订单查询用户：
user = session.query(Order).filter(Order.number == 1).first().users

# 大多数情况下 relationship() 都能自行找到关系中的外键, 但有时却无法决定把哪一列作为外键
# 例如 Order 模型中有两个或以上的列定义为 Role 模型的外键, SQLAlchemy 就不知道该使用哪列
# 如果无法决定外键, 就要为 relationship() 提供额外参数, 从而确定所用外键



# 一对一关系：
# 在一个表中有一条记录，则在另一张表中有一条记录相匹配。一般是看主表每一个字段对应另一张表的匹配记录条数
# 一对一本质上是两个表之间的双向关系，只需要在一对多关系的基础上设置 relationship 方法的 uselist 参数为 false 即可

# 多对多关系：
# 一个表中的多个记录与另一个表中的多个记录相关联时即产生多对多关系
# 而我们常用的关系数据库往往不支持直接在两个表之间进行多对多的联接，为了解决这个问题，就需要引入第三个表
# 将多对多关系拆分为两个一对多的关系，我们称这个表为联接表
# 大学中选修课和学生之间的关系就是一个典型的多对多关系，一个学生可以选修多个选修课，一个选修课有多个学生学习

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

association_table = Table('association',Base.metadata,
    Column('course_id', Integer, ForeignKey('course.id')),
    Column('student_id', Integer, ForeignKey('student.id'))
)

class Course(Base):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    student = relationship("Student", secondary=association_table, backref='course')

    def __repr__(self):
        return "name:%r" %self.name

class Student(Base):
    __tablename__ = 'student'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    def __repr__(self):
        return "name:%r" %self.name

s1 = Student(name = 's1')
s2 = Student(name = 's2')
c1 = Course(name = 'c1')
c2 = Course(name = 'c2')

c1.student = [s1, s2]
c2.student = [s1, s2]

session.add(c1)
session.add(c2)
session.commit()

s1_course = session.query(Student).filter(Student.name == 's1').first().course
print(s1_course)
c1_student = session.query(Course).filter(Course.id == 1).first().student
print(c1_student)