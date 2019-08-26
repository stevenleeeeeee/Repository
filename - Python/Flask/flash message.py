from flask import Flask, flash, redirect, render_template, request, url_for
# http://www.pythondoc.com/flask/patterns/flashing.html

app = Flask(__name__)
app.secret_key = 'some_secret'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or \
           request.form['password'] != 'secret':
            error = 'Invalid credentials'
        else:
            flash('You were successfully logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

if __name__ == "__main__":
    app.run()

# 以下是实现闪现的 layout.html 模板：
# <!doctype html>
# <title>My Application</title>
# {% with messages = get_flashed_messages() %}
# {% if messages %}
#     <ul class=flashes>
#     {% for message in messages %}
#     <li>{{ message }}</li>
#     {% endfor %}
#     </ul>
# {% endif %}
# {% endwith %}
# {% block body %}{% endblock %}

# 以下是 index.html 模板：
# {% extends "layout.html" %}
# {% block body %}
#   <h1>Overview</h1>
#   <p>Do you want to <a href="{{ url_for('login') }}">log in?</a>
# {% endblock %}

# login 模板：
# {% extends "layout.html" %}
# {% block body %}
#   <h1>Login</h1>
#   {% if error %}
#     <p class=error><strong>Error:</strong> {{ error }}
#   {% endif %}
#   <form action="" method=post>
#     <dl>
#       <dt>Username:
#       <dd><input type=text name=username value="{{ request.form.username }}">
#       <dt>Password:
#       <dd><input type=password name=password>
#     </dl>
#     <p><input type=submit value=Login>
#   </form>
# {% endblock %}