import csv

import bcrypt
from flask import Flask, session, redirect, render_template, flash, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

from forms import LoginForm, RegisterForm, ContactForm
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = 'CIM'
login_manager = LoginManager()
login_manager.init_app(app)
# without setting the login_view, attempting to access @login_required endpoints will result in an error
# this way, it will redirect to the login page
login_manager.login_view = 'login'
app.config['USE_SESSION_FOR_NEXT'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///users.sqlite'
db = SQLAlchemy(app)

from models import DBUser


class SessionUser(UserMixin):
    def __init__(self, username, email, phone, password=None):
        self.id = username
        self.email = email
        self.phone = phone
        self.password = password


# this is used by flask_login to get a user object for the current user
@login_manager.user_loader
def load_user(user_id):
    user = find_user(user_id)
    # user could be None
    if user:
        # if not None, hide the password by setting it to None
        user.password = None
    return user


def find_user(username):
    # res = db.session.execute(db.select(DBUser).filter_by(username=username)).first()
    res = DBUser.query.get(username)
    if res:
        # user = SessionUser(res[0].username, res[0].email, res[0].phone, res[0].password)
        user = SessionUser(res.username, res.email, res.phone, res.password)
    else:
        user = None
    return user


@app.route('/')
def index():  # put application's code here
    return render_template('index.html', username=session.get('username'))


@app.route('/product')
def product():  # put application's code here
    return render_template('product.html')


@app.route('/product-detail')
def product_detail():  # put application's code here
    return render_template('product-detail.html')


@app.route('/about')
def about():  # put application's code here
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        with open('data/messages.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow([form.name.data, form.email.data, form.message.data])
        return redirect(url_for('contact_response', name=form.name.data))
    return render_template('contact.html', form=form)


@app.route('/contact_response/<name>')
def contact_response(name):
    return render_template('contact_response.html', name=name)


@app.route('/cart')
@login_required
def cart():  # put application's code here
    return render_template('cart.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = find_user(form.username.data)
        # user could be None
        # passwords are kept in hashed form, using the bcrypt algorithm
        if user and bcrypt.checkpw(form.password.data.encode(), user.password.encode()):
            login_user(user)
            flash('Logged in successfully.')
            next_page = session.get('next', '/')
            session['next'] = '/'
            return redirect(next_page)
        else:
            flash('Incorrect username/password!')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    # flash(str(session))
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # check first if user already exists
        user = find_user(form.username.data)
        if not user:
            salt = bcrypt.gensalt()
            password = bcrypt.hashpw(form.password.data.encode(), salt)
            user = DBUser(username=form.username.data, email=form.email.data, phone=form.phone.data,
                          password=password.decode())
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully.')
            return redirect('/login')
        else:
            flash('This username already exists, choose another one')
    return render_template('register.html', form=form)


if __name__ == '__main__':
    app.run()
