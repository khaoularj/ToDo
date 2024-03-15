# Importing necessary modules
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_bcrypt import Bcrypt


# Initializing Flask application
app = Flask(__name__)
# Configuration for SQLAlchemy database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'
app.config['SECRET_KEY'] = 'SecretKey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)   # Initializing SQLAlchemy
# Initializing Bcrypt for password hashing
bcrypt = Bcrypt(app)
# Pushing the application context
app.app_context().push()
# Initializing Flask-Login for user authentication
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "log_in"

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Database models
class User(db.Model, UserMixin):
    """User model for database"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    tasks = db.relationship('ToDo', backref='user', lazy=True)  # One-to-many relationship with ToDo model

class ToDo(db.Model):
    """ToDo model for database"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    complete = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key referencing User model

# Forms for user registration and login
class SignUp(FlaskForm):
    """Form for user sign up"""
    username = StringField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder":"Username"})
    email = EmailField(validators=[InputRequired(), Email(), Length(min=8, max=120)], render_kw={"placeholder":"Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder":"Password"})
    submit = SubmitField("Sign Up")

    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            raise ValidationError('This email is already registered! Please sign up with another one.')


class LogIn(FlaskForm):
    """Form for user login"""
    email = EmailField(validators=[InputRequired(), Email(message='Invalid email address'), Length(min=8, max=120)], render_kw={"placeholder":"Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder":"Password"})
    submit = SubmitField("Log In")


# Routes for application functionality
@app.route('/change_background_color', methods=['POST'])
def change_background_color():
    """Route for changing background color"""
    if request.method == 'POST':
        color = request.form.get('color')
        session['background_color'] = color
        return redirect(url_for('dashboard'))


@app.route('/auth/login', methods=['GET', 'POST'])
def log_in():
    """Route for user login"""
    form = LogIn()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('dashboard/log_in.html', form=form)


@app.route('/auth/signup', methods=['GET', 'POST'])
def sign_up():
    """Route for user sign up"""
    form = SignUp()
    if form.validate_on_submit():
        if form.validate_on_submit():
            hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            new_user = User(username=form.username.data, email=form.email.data, password=hashed_pwd)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('log_in'))
    return render_template('dashboard/sign_up.html', form=form)


@app.route('/auth/logout', methods=['GET', 'POST'])
@login_required
def log_out():
    """Route for user logout"""
    logout_user()
    return redirect(url_for('log_in'))

@app.route('/')
def index():
    """Route for index page"""
    return render_template('dashboard/index.html')


@app.route('/dashboard/add', methods=['POST'])
def add():
    """Route for adding a new task"""
    title = request.form.get('title')
    new_task = ToDo(title=title, complete=False, user_id=current_user.id)  # Include user_id
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/dashboard/update/<int:id>')
def update(id):
    """Route for updating task completion status"""
    todo = ToDo.query.filter_by(id=id).first()
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/dashboard/delete/<int:id>')
def delete(id):
    """Route for deleting a task"""
    todo = ToDo.query.filter_by(id=id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/about')
def about_page():
    """Route for about page"""
    return render_template('dashboard/about.html')


@app.route('/dashboard/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    """Route for displaying user's tasks"""
    todo_list = current_user.tasks
    total = len(todo_list)
    completed_tasks = sum(1 for task in todo_list if task.complete)
    uncompleted_tasks = total - completed_tasks
    return render_template('dashboard/current_tasks.html', todo_list=todo_list, total=total, completed_tasks=completed_tasks, uncompleted_tasks=uncompleted_tasks) 


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Route for displaying user's dashboard"""
    todo_list = ToDo.query.filter_by(user_id=current_user.id).all()
    total = ToDo.query.filter_by(user_id=current_user.id).count()
    completed_tasks = ToDo.query.filter_by(user_id=current_user.id, complete=True).count()
    uncompleted_tasks = ToDo.query.filter_by(user_id=current_user.id, complete=False).count()
    return render_template('dashboard/dashboard.html', todo_list=todo_list, total=total, completed_tasks=completed_tasks, uncompleted_tasks=uncompleted_tasks)


if __name__ == '__main__':
    db.create_all()   # Creating all database tables
    app.run(host='0.0.0.0', port=5000, debug=True)   # Running the Flask application
