from flask import Flask, current_app, request, render_template
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class MyForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])

app = Flask(__name__,template_folder='static/html')

@app.route('/',methods=['GET','POST'])
def login():
    form = MyForm()
    # if request.method == 'POST' and form.validate():
    if form.validate_on_submit():
        return 'OK'
    return render_template('forms/index.html', form=form)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)


# 模板文件： cat forms/index.html
# <form method="POST" action="/">
# {{ form.csrf_token }}
# {{ form.name.label }} {{ form.name(size=20) }}
# <input type="submit" value="Go">
# </form>


# ------------------------------------------------- Example 1

# use Jinja2 Bootstrap wtf
# coding=utf-8

from flask import Flask
from flask import render_template
from flask_wtf import FlaskForm
from wtforms.fields import (StringField, PasswordField, DateField, BooleanField,
                            SelectField, SelectMultipleField, TextAreaField,
                            RadioField, IntegerField, DecimalField, SubmitField)
from wtforms.validators import DataRequired, InputRequired, Length, Email, EqualTo, NumberRange


app = Flask(__name__)
app.secret_key = 'asdfs'


class WtfForm(FlaskForm):

    # StringField 文本输入框，必填，用户名长度为4到25之间，占位符
    username = StringField('用户名：', validators=[Length(min=4, max=25)], render_kw={'placeholder': '请输入用户名'})

    # Email格式
    email = StringField('邮箱地址：', validators=[Email()], render_kw={'placeholder': '请输入邮箱地址'})

    # PasswordField，密码输入框，必填
    password = PasswordField('密码：', validators=[DataRequired()], render_kw={'placeholder': '请输入密码'})

    # 确认密码，必须和密码一致
    password2 = PasswordField('确认密码：', validators=[InputRequired(), EqualTo('password', '两次密码要一致')])

    # IntegerField，文本输入框，必须输入整型数值，范围在16到70之间
    age = IntegerField('年龄：', validators=[NumberRange(min=16, max=70)])

    # DecimalField，文本输入框，必须输入数值，显示时保留一位小数
    height = DecimalField('身高(cm):', places=1)

    # DateField，文本输入框，必须输入是"年-月-日"格式的日期
    birthday = DateField('出生日期：', format='%Y-%m-%d')

    # RadioField，单选框，choices里的内容会在ul标签里，里面每个项是(值，显示名)对
    gender = RadioField('性别：', choices=[('0', '男'), ('1', '女')], validators=[DataRequired()])

    # SelectField，下拉单选框，choices里的内容会在Option里，里面每个项是(值，显示名)对
    job = SelectField('职业：', choices=[
        ('teacher', '教师'),
        ('doctor', '医生'),
        ('engineer', '工程师'),
        ('lawyer', '律师')
    ])

    # Select类型，多选框，choices里的内容会在Option里，里面每个项是(值，显示名)对
    hobby = SelectMultipleField('爱好：', choices=[
        ('0', '吃饭'),
        ('1', '睡觉'),
        ('2', '敲代码')
    ])

    # TextAreaField，段落输入框
    description = TextAreaField('自我介绍：', validators=[InputRequired()], render_kw={'placeholder': '例：小明，18岁，未婚找女友'})

    # BooleanField，Checkbox类型，加上default='checked'即默认是选上的
    accept_terms = BooleanField('是否接受上述条款', default='checked', validators=[DataRequired()])

    # SubmitField，Submit按钮
    submit = SubmitField('提交')


@app.route('/', methods=['POST', 'GET'])
def index():
    form = WtfForm()
    return render_template('wtf.html', form=form)

if __name__ == "__main__":
    app.run(debug=True)

# 模板代码：
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <title>Title</title>
# </head>
# <body>
# <form action="">
#     {{ form.csrf_token }}
#     {{ form.username.label }}{{ form.username }}
#     <br>
#     {{ form.email.label }}{{ form.email }}
#     <br>
#     {{ form.password.label }}{{ form.password }}
#     <br>
#     {{ form.password2.label }}{{ form.password2 }}
#     <br>
#     {{ form.age.label }}{{ form.age }}
#     <br>
#     {{ form.height.label }}{{ form.height }}
#     <br>
#     {{ form.birthday.label }}{{ form.birthday }}
#     <hr>
#     {{ form.gender.label }}{{ form.gender }}
#     <br>
#     {{ form.job.label }}{{ form.job }}
#     <br>
#     {{ form.hobby.label }}{{ form.hobby }}
#     <br>
#     {{ form.description.label }}{{ form.description }}
#     <br>
#     {{ form.accept_terms.label }}{{ form.accept_terms }}
#     <br>
#     {{ form.submit }}
#     <br>

# </form>
# </body>
# </html>

# ------------------------------------------------- Example 2

from wtforms import Form, BooleanField, StringField, PasswordField, validators

class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [validators.DataRequired(),validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(form.username.data, form.email.data,
                    form.password.data)
        db_session.add(user)
        flash('Thanks for registering')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# 宏定义模板：_formhelpers.html
# {% macro render_field(field) %}
#   <dt>{{ field.label }}
#   <dd>{{ field(**kwargs) | safe }}
#   {% if field.errors %}
#     <ul class=errors>
#     {% for error in field.errors %}
#       <li>{{ error }}</li>
#     {% endfor %}
#     </ul>
#   {% endif %}
#   </dd>
# {% endmacro %}

# 模板调用宏：
# {% from "_formhelpers.html" import render_field %}
# <form method=post>
#   <dl>
#     {{ render_field(form.username) }}
#     {{ render_field(form.email) }}
#     {{ render_field(form.password) }}
#     {{ render_field(form.confirm) }}
#     {{ render_field(form.accept_tos) }}
#   </dl>
#   <p><input type=submit value=Register>
# </form>