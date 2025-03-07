from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Secret key for session management and security
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'  # Database configuration

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager for user authentication
login_manager = LoginManager(app)
# Redirects to login page if user is not authenticated
login_manager.login_view = 'login'

# User model representing registered users
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each user
    username = db.Column(db.String(80), unique=True, nullable=False)  # Unique username
    password = db.Column(db.String(120), nullable=False)  # Hashed password for security
    lists = db.relationship('List', backref='user', lazy=True)  # One-to-many relationship with lists

# List model representing to-do lists
class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each list
    name = db.Column(db.String(100), nullable=False)  # List name
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Owner of the list
    tasks = db.relationship('Task', backref='list', lazy=True)  # One-to-many relationship with tasks

# Task model representing individual tasks
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each task
    content = db.Column(db.String(200), nullable=False)  # Task description
    completed = db.Column(db.Boolean, default=False)  # Whether the task is completed
    collapsed = db.Column(db.Boolean, default=False)  # UI flag for task collapse/expand
    level = db.Column(db.Integer, default=1)  # Task hierarchy level (1: top-level, 2: sub-task, etc.)
    parent_id = db.Column(db.Integer, db.ForeignKey('task.id'))  # Parent task ID for sub-tasks
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False)  # Associated list ID
    children = db.relationship('Task', backref=db.backref('parent', remote_side=[id]))  # Child tasks
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of task creation

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Fetch user by ID

# Route for the home page (requires authentication)
@app.route('/')
@login_required
def index():
    lists = List.query.filter_by(user_id=current_user.id).all()  # Fetch user's lists
    return render_template('index.html', lists=lists)

# Login route (handles both GET and POST requests)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()  # Find user by username
        if user and check_password_hash(user.password, password):  # Verify password
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')  # Show error message
    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
        else:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
    return render_template('register.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route to add a new to-do list
@app.route('/add_list', methods=['POST'])
@login_required
def add_list():
    name = request.form['name']
    new_list = List(name=name, user_id=current_user.id)
    db.session.add(new_list)
    db.session.commit()
    return redirect(url_for('index'))

# Route to add a new task
@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    content = request.form['content']
    list_id = request.form['list_id']
    parent_id = request.form.get('parent_id')
    
    level = 1
    if parent_id:
        parent_task = Task.query.get_or_404(parent_id)
        if parent_task.list.user_id != current_user.id:
            return redirect(url_for('index'))
        level = parent_task.level + 1
        if level > 3:
            flash('Cannot create tasks beyond 3 levels deep')
            return redirect(url_for('index'))
    
    new_task = Task(content=content, list_id=list_id, parent_id=parent_id, level=level)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

# Route to mark a task as complete (deletes the task and its children)
@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.list.user_id == current_user.id:
        def delete_children(task):
            for child in task.children:
                delete_children(child)
                db.session.delete(child)
        delete_children(task)
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('index'))

# Route to toggle task collapse/expand
@app.route('/toggle_collapse/<int:task_id>')
@login_required
def toggle_collapse(task_id):
    task = Task.query.get_or_404(task_id)
    if task.list.user_id == current_user.id:
        task.collapsed = not task.collapsed
        db.session.commit()
    return redirect(url_for('index'))

# Route to move a task to another list
@app.route('/move_task', methods=['POST'])
@login_required
def move_task():
    task_id = request.form['task_id']
    new_list_id = request.form['new_list_id']
    task = Task.query.get_or_404(task_id)
    new_list = List.query.get_or_404(new_list_id)
    if task.list.user_id == current_user.id and new_list.user_id == current_user.id:
        task.list_id = new_list_id
        db.session.commit()
    return redirect(url_for('index'))

# Route to delete a task and its children
@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    return complete_task(task_id)  # Calls the same logic as complete_task

# Route to edit an existing task
@app.route('/edit_task/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.list.user_id == current_user.id:
        task.content = request.form['content']
        db.session.commit()
    return redirect(url_for('index'))

# Run the application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
