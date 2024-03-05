from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_bcrypt import Bcrypt
import sqlite3



app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'
app.config['SECRET_KEY'] = 'SecretKey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

app.app_context().push()


#Create models

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    

class SignUp(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder":"Username"})
    email = StringField(validators=[InputRequired(), Email(), Length(min=8, max=120)], render_kw={"placeholder":"Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder":"Password"})
    submit = SubmitField("Sign Up")

    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            raise ValidationError('This email is already registered! Please sign up with another one.')


class LogIn(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(message='Invalid email address'), Length(min=8, max=120)], render_kw={"placeholder":"Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder":"Password"})
    submit = SubmitField("Log In")


class ToDo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    complete = db.Column(db.Boolean, default=False)



@app.route('/auth/login', methods=['GET', 'POST'])
def log_in():
    form = LogIn()
    pass
    return render_template('dashboard/log_in.html', form=form)


@app.route('/auth/signup', methods=['GET', 'POST'])
def sign_up():
    form = SignUp()
    if form.validate_on_submit():
        print('Form data:', request.form)
        hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        print('Hashed password:', hashed_pwd)
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('log_in'))
    return render_template('dashboard/sign_up.html', form=form)

@app.route('/')
def index():
    return render_template('dashboard/index.html')


@app.route('/dashboard/add', methods=['POST'])
def add():
    title = request.form.get('title')
    new_task = ToDo(title=title, complete=False)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/dashboard/update/<int:id>')
def update(id):
    todo = ToDo.query.filter_by(id=id).first()
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/dashboard/delete/<int:id>')
def delete(id):
    todo = ToDo.query.filter_by(id=id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/about')
def about_page():
    return render_template('dashboard/about.html')

@app.route('/dashboard')
def dashboard():
    todo_list = ToDo.query.all()
    total = ToDo.query.count()
    completed_tasks = ToDo.query.filter_by(complete=True).count()
    uncompleted_tasks = ToDo.query.filter_by(complete=False).count()
    return render_template('dashboard/dashboard.html', todo_list=todo_list, total=total, completed_tasks=completed_tasks, uncompleted_tasks=uncompleted_tasks)



if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)