# -*- coding: utf-8 -*-

# 属性装饰器
class Student(object):
    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        if not isinstance(value,int):
            raise ValueError('必须输入数字！')
        if value<0 or value>100:
            raise ValueError('必须大于0小于100！')
        self._score = value

s = Student()
s.score = 101
print(s.score)


# -------------------------------------------------

# 自定义property

class property_my:

    def __init__(self, fget=None, fset=None, fdel=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel

    # 对象被获取(self自身, instance调用该对象的对象, owner调用该对象的对象类对象)
    def __get__(self, instance, owner):
        print("get %s %s %s"%(self, instance, owner))
        return self.fget(instance)

    # 对象被设置属性时
    def __set__(self, instance, value):
        print("set %s %s %s"%(self, instance, value))
        self.fset(instance, value)

    # 对象被删除时
    def __delete__(self, instance):
        print("delete %s %s"%(self, instance))
        self.fdel(instance)


class demo10:

    def __init__(self):
        self.num = None

    def setvalue(self, value):
        self.num = value

    def getvalue(self):
        return self.num

    def delete(self):
        del self.num

    x = property_my(getvalue, setvalue, delete)